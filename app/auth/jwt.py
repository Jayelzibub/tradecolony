"""
jwt.py

Handles JWT creation and validation for both access and refresh tokens.

Includes:
- Token generation (`create_access_token`, `create_refresh_token`)
- Token verification and decoding
- Use of Pydantic model for structured payload access

Relies on:
- PyJWT for encoding/decoding
- Settings config for secret key, algorithm, and expiry settings
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import os

import jwt  # PyJWT
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings

# Configuration
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES


# Pydantic model for decoded JWT data
class TokenData(BaseModel):
    sub: str
    exp: datetime


# Generates an access token with optional expiry override
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(8),  # Adds randomness to reduce replay attacks
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Generates a refresh token with optional expiry override
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Verifies a JWT and returns typed TokenData
def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# (Optional) Returns decoded payload as a raw dict without validation
def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
