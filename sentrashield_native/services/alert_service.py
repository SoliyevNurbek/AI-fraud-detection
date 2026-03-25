from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sentrashield_native.db.models import Alert, RiskScore, Transaction
from sentrashield_native.schemas.dashboard import CountryRiskPoint, DashboardSummaryResponse, TrendPoint


def list_alerts(db: Session, limit: int = 20):
    return list(db.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(limit)))


def dashboard_stats(db: Session) -> dict[str, int]:
    transactions = db.scalar(select(func.count()).select_from(Transaction)) or 0
    alerts = db.scalar(select(func.count()).select_from(Alert)) or 0
    high_risk = db.scalar(select(func.count()).select_from(RiskScore).where(RiskScore.final_score >= 60)) or 0
    blocked = db.scalar(select(func.count()).select_from(RiskScore).where(RiskScore.decision == "block")) or 0
    return {"transactions": int(transactions), "alerts": int(alerts), "high_risk": int(high_risk), "blocked": int(blocked)}


def country_risk_breakdown(db: Session, limit: int = 6) -> list[dict[str, object]]:
    rows = db.execute(
        select(
            Transaction.country_code,
            func.count(RiskScore.id).label("count"),
            func.avg(RiskScore.final_score).label("avg_risk"),
        )
        .join(RiskScore, RiskScore.transaction_id == Transaction.id)
        .group_by(Transaction.country_code)
        .order_by(func.avg(RiskScore.final_score).desc())
        .limit(limit)
    )

    breakdown = []
    for country_code, count, avg_risk in rows:
        breakdown.append(
            {
                "country_code": country_code or "N/A",
                "count": int(count or 0),
                "avg_risk": round(float(avg_risk or 0), 2),
            }
        )
    return breakdown


def dashboard_summary(db: Session) -> DashboardSummaryResponse:
    stats = dashboard_stats(db)
    recent_reviews = db.scalar(select(func.count()).select_from(RiskScore).where(RiskScore.decision.in_(("review", "block")))) or 0
    average_risk = db.scalar(select(func.avg(RiskScore.final_score)).select_from(RiskScore)) or 0
    latest_model_version = db.scalar(select(RiskScore.model_version).order_by(RiskScore.created_at.desc()).limit(1)) or "linear-fallback"

    trend = [
        TrendPoint(label="clean", value=max(stats["transactions"] - stats["alerts"], 0)),
        TrendPoint(label="transactions", value=stats["transactions"]),
        TrendPoint(label="high_risk", value=stats["high_risk"]),
        TrendPoint(label="blocked", value=stats["blocked"]),
    ]

    countries = [CountryRiskPoint(**point) for point in country_risk_breakdown(db)]
    return DashboardSummaryResponse(
        transactions=stats["transactions"],
        alerts=stats["alerts"],
        high_risk=stats["high_risk"],
        blocked=stats["blocked"],
        recent_reviews=int(recent_reviews),
        average_risk=round(float(average_risk), 2),
        model_version=latest_model_version,
        trend=trend,
        countries=countries,
    )
