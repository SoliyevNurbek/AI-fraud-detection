import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sentrashield_native.core.config import DATABASE_URL
from sentrashield_native.core.security import hash_password
from sentrashield_native.db.models import Alert, AnalystUser, AuditLog, Base
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        admin = db.scalar(select(AnalystUser).where(AnalystUser.username == "admin"))
        if not admin:
            db.add(AnalystUser(username="admin", password_hash=hash_password("admin123"), role="admin"))
        if not db.scalar(select(Alert)):
            db.add(Alert(transaction_id="sample-txn", severity="medium", status="open", title="Sample alert", description="This seed alert shows how analyst alerts will appear.", risk_score=47.3))
        db.add(AuditLog(actor="system", action="startup_seed", metadata_json=json.dumps({"ok": True})))
        db.commit()
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
