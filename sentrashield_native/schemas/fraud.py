from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
class ScoreTransactionRequest(BaseModel):
    external_txn_id: str = Field(min_length=3)
    user_id: str = Field(min_length=1)
    device_fingerprint: str = Field(min_length=3)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=16)
    merchant_category: Optional[str] = None
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    event_time: datetime
class ScoreTransactionResponse(BaseModel):
    transaction_id: str
    risk_score: float
    risk_band: str
    decision: str
    fraud_probability: float
    anomaly_score: float
    device_risk: float
    bot_score: float
    aml_score: float
    graph_risk: float
    reasons: list[str]
    model_version: str
    alert_id: Optional[str] = None


class TransactionWebhookResponse(BaseModel):
    status: str
    decision: str
    risk_score: float
    transaction_id: str
