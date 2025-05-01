"""
token_service.py

Handles creation, verification, rotation, and deletion of refresh tokens.

Key features:
- Secure refresh token generation using random nonce (JTI)
- Database persistence of issued tokens
- Token rotation strategy for enhanced security
- Compatibility with JWT-based access control
"""

from datetime import datetime, timedelta, timezone
import secrets

from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.token import RefreshToken
from app.models.user import User
from app.core.config import settings


# Create a new refresh token, persist it in DB
def create_refresh_token(user_id: int, db: Session) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    nonce = secrets.token_urlsafe(8)  # Adds randomness for uniqueness
    to_encode = {"sub": str(user_id), "exp": expire, "jti": nonce}
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    db_token = RefreshToken(user_id=user_id, token=token, expires_at=expire)
    db.add(db_token)
    db.commit()

    return token


# Store a manually generated refresh token (optional use)
def store_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime):
    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
        revoked=None,
    )
    db.add(db_token)
    db.commit()


# Verify a refresh token exists in DB and is still valid
def verify_refresh_token(db: Session, token: str) -> User | None:
    db_token = db.query(RefreshToken).filter_by(token=token).first()
    if not db_token or db_token.expires_at < datetime.utcnow():
        return None
    return db_token.user


# Rotate a refresh token in-place in the database
def rotate_refresh_token(db: Session, old_token: str, new_token: str, new_expiry: datetime):
    db_token = db.query(RefreshToken).filter_by(token=old_token).first()
    if db_token:
        db_token.token = new_token
        db_token.expires_at = new_expiry
        db.commit()


# Remove a refresh token (used during logout or invalidation)
def delete_refresh_token(db: Session, token: str):
    db_token = db.query(RefreshToken).filter_by(token=token).first()
    if db_token:
        db.delete(db_token)
        db.commit()


# Decode a JWT and raise if invalid
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Verify a refresh token, rotate it, and return new tokens
def verify_and_rotate_refresh_token(token: str, db: Session) -> tuple[str, str]:
    # Deferred import to avoid circular dependency
    from app.auth.jwt import create_access_token

    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    token_record = db.query(RefreshToken).filter_by(token=token).first()
    if not token_record:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    # Rotate: remove old token and issue new one
    db.delete(token_record)
    new_refresh_token = create_refresh_token(user_id, db)
    db.commit()

    new_access_token = create_access_token({"sub": str(user_id)})
    return new_access_token, new_refresh_token
