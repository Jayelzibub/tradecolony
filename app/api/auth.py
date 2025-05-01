"""
auth.py

Handles authentication endpoints for the FastAPI application.

Includes:
- User login with JWT and refresh token generation.
- Access token refresh using HTTP-only cookie.
- Logout by invalidating the stored refresh token in the database.

This module relies on:
- SQLAlchemy for database interaction
- HTTP-only cookies for refresh token storage
- JSON Web Tokens (JWT) for access control
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User as UserModel
from app.models.token import RefreshToken
from app.schemas.user import LoginRequest, LoginResponse
from app.auth.password import verify_password
from app.auth.jwt import create_access_token
from app.services.token_service import (
    create_refresh_token,
    verify_and_rotate_refresh_token,
)

router = APIRouter()


# Authenticates the user and issues access and refresh tokens.
# - Checks credentials and account status.
# - Returns access token in response body.
# - Sets refresh token in HTTP-only cookie.
@router.post("/login", response_model=LoginResponse)
def login_user(login: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == login.email).first()

    if not user or not verify_password(login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not user.is_active or user.is_forgotten:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is no longer active.",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id, db)

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return response


# Verifies and rotates the refresh token, issuing a new access and refresh token.
# - Requires refresh token from HTTP-only cookie.
# - Returns new access token and sets updated refresh token.
@router.post("/refresh", response_model=LoginResponse)
def refresh_token_route(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )

    try:
        new_access_token, new_refresh_token = verify_and_rotate_refresh_token(refresh_token, db)
    except HTTPException as e:
        raise e

    response = JSONResponse(content={"access_token": new_access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


# Logs the user out by deleting the refresh token from the database.
# - Also deletes the cookie from the client.
@router.post("/logout")
def logout_user(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_record = db.query(RefreshToken).filter_by(token=refresh_token).first()
        if token_record:
            db.delete(token_record)
            db.commit()

    response = JSONResponse(content={"message": "Logged out successfully."})
    response.delete_cookie(key="refresh_token")
    return response
