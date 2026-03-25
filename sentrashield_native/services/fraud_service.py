import json
from dataclasses import dataclass
from datetime import timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sentrashield_native.ai.inference import predict_risk
from sentrashield_native.db.models import Alert, RiskScore, Transaction
from sentrashield_native.schemas.fraud import ScoreTransactionRequest, ScoreTransactionResponse
from sentrashield_native.services.realtime_service import AlertEvent, alert_stream
HIGH_RISK_CATEGORIES = {"crypto", "gift_cards", "electronics", "luxury", "gaming"}
RISKY_COUNTRIES = {"RU", "IR", "KP", "SY"}
HIGH_RISK_IP_PREFIXES = ("185.", "103.", "45.", "91.")
@dataclass
class Components:
    ai_score: float
    fraud_probability: float
    anomaly_score: float
    device_risk: float
    bot_score: float
    aml_score: float
    graph_risk: float
    reasons: list[str]
    model_version: str
    suggested_decision: str
def clamp01(value: float) -> float: return max(0.0, min(1.0, value))
def score_to_band(score: float) -> tuple[str, str]:
    if score >= 80: return "critical", "block"
    if score >= 60: return "high", "review"
    if score >= 30: return "medium", "monitor"
    return "low", "allow"
def build_ai_features(payload: ScoreTransactionRequest, user_tx_24h: int, device_reuse_count: int, recent_same_ip: int) -> dict[str, float]:
    return {
        "amount": float(payload.amount),
        "device_score": 0.7 if payload.device_fingerprint.lower().endswith("x") else min(0.2 + device_reuse_count * 0.12, 0.95),
        "ip_risk": 0.8 if payload.ip_address and payload.ip_address.startswith(HIGH_RISK_IP_PREFIXES) else min(0.15 + recent_same_ip * 0.08, 0.9),
        "country_risk": 0.9 if payload.country_code and payload.country_code.upper() in RISKY_COUNTRIES else 0.1,
        "velocity": float(max(user_tx_24h, 1)),
    }
def build_components(db: Session, payload: ScoreTransactionRequest) -> Components:
    reasons = []
    user_avg_amount = db.scalar(select(func.avg(Transaction.amount)).where(Transaction.user_id == payload.user_id)) or 0.0
    user_tx_24h = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == payload.user_id, Transaction.event_time >= payload.event_time - timedelta(hours=24))) or 0
    device_reuse_count = db.scalar(select(func.count(func.distinct(Transaction.user_id))).select_from(Transaction).where(Transaction.device_fingerprint == payload.device_fingerprint)) or 0
    recent_same_ip = 0
    if payload.ip_address:
        recent_same_ip = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.ip_address == payload.ip_address, Transaction.event_time >= payload.event_time - timedelta(hours=2))) or 0
    amount_ratio = (payload.amount / user_avg_amount) if user_avg_amount else 1.0
    fraud_probability, anomaly_score, device_risk, bot_score, aml_score, graph_risk = 0.12, 0.10, 0.05, 0.03, 0.04, 0.04
    if payload.amount >= 5000:
        fraud_probability += 0.30; anomaly_score += 0.20; aml_score += 0.12; reasons.append("high_amount")
    if amount_ratio >= 5 and user_avg_amount > 0:
        anomaly_score += 0.22; reasons.append("amount_vs_user_average_spike")
    if payload.merchant_category and payload.merchant_category.lower() in HIGH_RISK_CATEGORIES:
        fraud_probability += 0.18; reasons.append("risky_merchant_category")
    if payload.country_code and payload.country_code.upper() in RISKY_COUNTRIES:
        aml_score += 0.26; fraud_probability += 0.08; reasons.append("risky_country")
    if payload.device_fingerprint.lower().endswith("x"):
        device_risk += 0.18; reasons.append("untrusted_device_pattern")
    if device_reuse_count >= 3:
        device_risk += 0.26; graph_risk += 0.18; reasons.append("device_shared_by_multiple_users")
    if user_tx_24h >= 10:
        bot_score += 0.18; anomaly_score += 0.12; reasons.append("high_transaction_velocity")
    if payload.ip_address and payload.ip_address.startswith(HIGH_RISK_IP_PREFIXES):
        bot_score += 0.10; reasons.append("suspicious_ip_range")
    if recent_same_ip >= 6:
        bot_score += 0.18; graph_risk += 0.10; reasons.append("repeated_ip_activity")
    if 0 <= payload.event_time.hour <= 4:
        anomaly_score += 0.10; reasons.append("odd_hour_activity")
    ai_score, ai_decision, model_version = predict_risk(build_ai_features(payload, user_tx_24h, device_reuse_count, recent_same_ip))
    ai_probability = clamp01(ai_score / 100)
    fraud_probability = clamp01(fraud_probability * 0.55 + ai_probability * 0.45)
    if ai_score >= 80:
        reasons.append("ml_model_high_confidence")
    elif ai_score >= 60:
        reasons.append("ml_model_review_flag")
    return Components(
        ai_score=ai_score,
        fraud_probability=clamp01(fraud_probability),
        anomaly_score=clamp01(anomaly_score),
        device_risk=clamp01(device_risk),
        bot_score=clamp01(bot_score),
        aml_score=clamp01(aml_score),
        graph_risk=clamp01(graph_risk),
        reasons=list(dict.fromkeys(reasons)),
        model_version=model_version,
        suggested_decision=ai_decision,
    )
async def score_transaction_service(db: Session, payload: ScoreTransactionRequest) -> ScoreTransactionResponse:
    existing = db.scalar(select(Transaction).where(Transaction.external_txn_id == payload.external_txn_id))
    if existing:
        existing_score = db.scalar(select(RiskScore).where(RiskScore.transaction_id == existing.id).order_by(RiskScore.created_at.desc()))
        reasons = json.loads(existing_score.reasons) if existing_score else []
        return ScoreTransactionResponse(transaction_id=existing.id, risk_score=existing_score.final_score if existing_score else 0, risk_band=existing_score.risk_band if existing_score else "low", decision=existing_score.decision if existing_score else "allow", fraud_probability=existing_score.fraud_probability if existing_score else 0, anomaly_score=existing_score.anomaly_score if existing_score else 0, device_risk=existing_score.device_risk if existing_score else 0, bot_score=existing_score.bot_score if existing_score else 0, aml_score=existing_score.aml_score if existing_score else 0, graph_risk=existing_score.graph_risk if existing_score else 0, reasons=reasons, model_version=existing_score.model_version if existing_score else "linear-fallback", alert_id=None)
    txn = Transaction(external_txn_id=payload.external_txn_id, user_id=payload.user_id, device_fingerprint=payload.device_fingerprint, amount=payload.amount, currency=payload.currency, merchant_category=payload.merchant_category, ip_address=payload.ip_address, country_code=payload.country_code, event_time=payload.event_time)
    db.add(txn); db.flush()
    c = build_components(db, payload)
    rules_score = 100 * (0.28*c.fraud_probability + 0.22*c.anomaly_score + 0.14*c.device_risk + 0.12*c.bot_score + 0.12*c.aml_score + 0.12*c.graph_risk)
    final_score = max(0.0, min(100.0, rules_score * 0.55 + c.ai_score * 0.45))
    risk_band, decision = score_to_band(final_score)
    if c.suggested_decision == "block" and decision != "block":
        decision = "review" if final_score < 80 else "block"
    risk = RiskScore(transaction_id=txn.id, fraud_probability=c.fraud_probability, anomaly_score=c.anomaly_score, device_risk=c.device_risk, bot_score=c.bot_score, aml_score=c.aml_score, graph_risk=c.graph_risk, final_score=round(final_score,2), risk_band=risk_band, decision=decision, reasons=json.dumps(c.reasons), model_version=c.model_version)
    db.add(risk); db.flush()
    alert_id = None
    if final_score >= 30:
        severity = "critical" if final_score >= 80 else "high" if final_score >= 60 else "medium"
        alert = Alert(transaction_id=txn.id, severity=severity, status="open", title=f"{risk_band.title()} risk transaction", description=", ".join(c.reasons) if c.reasons else "Transaction flagged by scoring engine", risk_score=round(final_score,2))
        db.add(alert); db.flush(); alert_id = alert.id
    db.commit()
    if alert_id:
        await alert_stream.broadcast(
            AlertEvent(
                alert_id=alert.id,
                severity=alert.severity,
                status=alert.status,
                title=alert.title,
                description=alert.description,
                risk_score=round(alert.risk_score, 2),
                created_at=alert.created_at.isoformat(),
            )
        )
    return ScoreTransactionResponse(transaction_id=txn.id, risk_score=round(final_score,2), risk_band=risk_band, decision=decision, fraud_probability=round(c.fraud_probability,4), anomaly_score=round(c.anomaly_score,4), device_risk=round(c.device_risk,4), bot_score=round(c.bot_score,4), aml_score=round(c.aml_score,4), graph_risk=round(c.graph_risk,4), reasons=c.reasons, model_version=c.model_version, alert_id=alert_id)
