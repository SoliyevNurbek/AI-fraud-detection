# SentraShield Native Optimized

Windows-native fraud detection MVP with FastAPI, a lightweight AI scoring layer, webhook flow, websocket alert streaming, and a premium Next.js dashboard.

## Architecture
```text
Frontend (Next.js SaaS Dashboard)
        |
        v
Backend (FastAPI BFF + REST + Auth + WebSocket)
        |
        v
Fraud Engine (AI + Rules + Behavior)
        |
        v
Feature Store (derived features in DB, Redis-ready)
        |
        v
AI Models (XGBoost-ready fallback model)
        |
        v
Database (SQLite dev mode, PostgreSQL-ready)
        |
        v
External APIs (payment webhooks / PSP / bank adapters)
```

## Backend Quick Start
```powershell
py -3.10 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
uvicorn sentrashield_native.main:app --reload --port 8000
```

Optional model training:
```powershell
python -m sentrashield_native.ai.train_model
```

Open:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/dashboard

Demo login:
- admin / admin123

## Frontend Quick Start
```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Frontend URL:
- http://127.0.0.1:3000

Backend env:
- `JWT_SECRET`
- `JWT_EXPIRE_MINUTES`
- `DATABASE_URL`

Frontend env:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WS_BASE_URL`

Core endpoints:
- `POST /api/v1/auth/login`
- `POST /api/v1/fraud/score-transaction`
- `POST /webhook/transaction`
- `GET /api/v1/alerts`
- `GET /api/v1/dashboard/summary`
- `GET /ws/alerts`

## Product Surface
- Analyst login with JWT auth
- Dashboard KPIs, trend bars, and country risk heatmap
- Live investigation queue via websocket
- Transaction simulator that posts directly to the webhook
- AI + heuristic blended scoring with alert persistence
