from sqlalchemy import select
from sqlalchemy.orm import Session
from sentrashield_native.core.security import create_access_token, verify_password
from sentrashield_native.db.models import AnalystUser
def authenticate_user(db: Session, username: str, password: str) -> AnalystUser | None:
    user = db.scalar(select(AnalystUser).where(AnalystUser.username == username))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
def issue_token(user: AnalystUser) -> str:
    return create_access_token(subject=user.username, role=user.role)
