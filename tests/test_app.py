import asyncio
from datetime import datetime, timezone

from sentrashield_native.api.routes import health
from sentrashield_native.db.session import SessionLocal, init_db
from sentrashield_native.schemas.fraud import ScoreTransactionRequest
from sentrashield_native.services.fraud_service import score_transaction_service


def test_health():
    response = health()
    assert response["status"] == "ok"


def test_webhook_transaction_flow():
    init_db()
    db = SessionLocal()
    payload = ScoreTransactionRequest(
        external_txn_id="txn-test-001",
        user_id="user-001",
        device_fingerprint="device-risk-x",
        amount=9200,
        currency="USD",
        merchant_category="crypto",
        ip_address="185.23.1.10",
        country_code="RU",
        event_time=datetime(2026, 3, 23, 9, 0, tzinfo=timezone.utc),
    )

    response = asyncio.run(score_transaction_service(db, payload))
    db.close()

    assert response.decision in {"allow", "monitor", "review", "block"}
    assert response.risk_score >= 0
    assert response.transaction_id
