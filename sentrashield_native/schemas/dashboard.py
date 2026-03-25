from pydantic import BaseModel


class TrendPoint(BaseModel):
    label: str
    value: int


class CountryRiskPoint(BaseModel):
    country_code: str
    count: int
    avg_risk: float


class DashboardSummaryResponse(BaseModel):
    transactions: int
    alerts: int
    high_risk: int
    blocked: int
    recent_reviews: int
    average_risk: float
    model_version: str
    trend: list[TrendPoint]
    countries: list[CountryRiskPoint]
