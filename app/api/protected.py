"""
protected.py

Handles authenticated user routes for FastAPI.

Includes:
- Login with token generation (access + refresh).
- Access to protected user info (via `/me`).
- Refreshing access tokens via cookie-stored refresh token.
- Sliding session simulation by issuing a new access token when the access token is expired but a valid refresh token exists.
"""

from datetime import timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    Cookie,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db import get_db
from app.models.user import User as UserModel
from app.schemas.user import User  # for response_model in /me
from app.auth.password import verify_password
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# ---- Pydantic Schemas ----

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- POST /auth/login ----
# Logs in a user by validating credentials and setting tokens.
@router.post("/login", response_model=LoginResponse)
def login_user(
    login: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.email == login.email).first()

    if not user or not verify_password(login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active or user.is_forgotten:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is no longer active.")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60  # seconds
    )

    return {"access_token": access_token}


# ---- Dependency: get_current_user ----
# Validates access token or refresh token, simulates sliding sessions.
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None)
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid auth header")

    token = auth_header.split(" ")[1]

    try:
        token_data = verify_token(token)
    except HTTPException:
        if not refresh_token:
            raise
        # Fallback to refresh token if access token expired
        token_data = verify_token(refresh_token)
        user = db.query(UserModel).filter(UserModel.id == int(token_data.sub)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        new_access_token = create_access_token({"sub": str(user.id)})
        request.state.new_access_token = new_access_token
        return user

    user = db.query(UserModel).filter(UserModel.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---- GET /auth/me ----
# Returns the current authenticated user and optionally a new token.
@router.get("/me")
def read_current_user_full(
    request: Request,
    user: UserModel = Depends(get_current_user)
):
    new_token = getattr(request.state, "new_access_token", None)
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        },
        "new_access_token": new_token
    }


# ---- GET /auth/me (simplified version with schema) ----
# Returns the current authenticated user as a Pydantic response model.
@router.get("/me", response_model=User)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    return current_user


# ---- POST /auth/refresh ----
# Refreshes the access token using a valid refresh token from cookies.
@router.post("/refresh", response_model=LoginResponse)
def refresh_token_route(
    refresh_token: Optional[str] = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        token_data = verify_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    new_access_token = create_access_token({"sub": token_data.sub})
    return {"access_token": new_access_token}
