from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sentrashield_native.core.config import TEMPLATES_DIR
from sentrashield_native.core.security import decode_access_token
from sentrashield_native.db.session import get_db
from sentrashield_native.schemas.alert import AlertOut
from sentrashield_native.schemas.auth import LoginRequest, TokenResponse
from sentrashield_native.schemas.dashboard import DashboardSummaryResponse
from sentrashield_native.schemas.fraud import ScoreTransactionRequest, ScoreTransactionResponse, TransactionWebhookResponse
from sentrashield_native.services.alert_service import country_risk_breakdown, dashboard_stats, dashboard_summary, list_alerts
from sentrashield_native.services.auth_service import authenticate_user, issue_token
from sentrashield_native.services.fraud_service import score_transaction_service
from sentrashield_native.services.realtime_service import alert_stream
router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
bearer = HTTPBearer(auto_error=False)
def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not credentials: raise HTTPException(status_code=401, detail="Missing bearer token")
    try: return decode_access_token(credentials.credentials)
    except Exception as exc: raise HTTPException(status_code=401, detail="Invalid token") from exc
@router.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat(), "service": "sentrashield-native-optimized"}
@router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user: raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=issue_token(user))
@router.post("/api/v1/fraud/score-transaction", response_model=ScoreTransactionResponse)
async def score_transaction(payload: ScoreTransactionRequest, db: Session = Depends(get_db), _user: dict = Depends(get_current_user)):
    return await score_transaction_service(db, payload)
@router.post("/webhook/transaction", response_model=TransactionWebhookResponse)
async def transaction_webhook(payload: ScoreTransactionRequest, db: Session = Depends(get_db)):
    result = await score_transaction_service(db, payload)
    status = "blocked" if result.decision == "block" else "approved"
    return TransactionWebhookResponse(status=status, decision=result.decision, risk_score=result.risk_score, transaction_id=result.transaction_id)
@router.get("/api/v1/alerts", response_model=list[AlertOut])
def get_alerts(db: Session = Depends(get_db), _user: dict = Depends(get_current_user)):
    return list_alerts(db)
@router.get("/api/v1/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db), _user: dict = Depends(get_current_user)):
    return dashboard_summary(db)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    stats = dashboard_stats(db)
    alerts = list_alerts(db, limit=10)
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request, "stats": stats, "alerts": alerts, "trend": [max(stats["transactions"] - stats["alerts"], 0), stats["transactions"], stats["high_risk"], stats["blocked"]], "countries": country_risk_breakdown(db)})
@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await alert_stream.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message.lower() == "ping":
                await alert_stream.heartbeat(websocket)
    except WebSocketDisconnect:
        alert_stream.disconnect(websocket)
    except Exception:
        alert_stream.disconnect(websocket)
@router.get("/")
def root():
    return {"name": "SentraShield Native Optimized", "docs": "/docs", "dashboard": "/dashboard", "health": "/health"}
