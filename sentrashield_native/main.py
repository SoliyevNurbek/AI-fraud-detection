from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentrashield_native.api.routes import router
from sentrashield_native.db.session import init_db
app = FastAPI(title="SentraShield Native Optimized", version="0.2.0", description="Windows-native AI fraud detection starter, optimized for local development.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
@app.on_event("startup")
def on_startup() -> None:
    init_db()
app.include_router(router)
