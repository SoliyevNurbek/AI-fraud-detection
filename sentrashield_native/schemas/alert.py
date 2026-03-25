from datetime import datetime
from pydantic import BaseModel
class AlertOut(BaseModel):
    id: str
    severity: str
    status: str
    title: str
    description: str
    risk_score: float
    created_at: datetime
    class Config:
        from_attributes = True
