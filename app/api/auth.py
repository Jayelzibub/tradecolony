from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User as UserModel
from app.auth.password import verify_password
from app.auth.jwt import create_access_token
from app.services.token_service import create_refresh_token, verify_and_rotate_refresh_token
from app.models.token import RefreshToken
from app.schemas.user import LoginRequest, LoginResponse

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login_user(login: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == login.email).first()

    if not user or not verify_password(login.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active or user.is_forgotten:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is no longer active.")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id, db)

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # consider True in prod
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return response


@router.post("/refresh", response_model=LoginResponse)
def refresh_token_route(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        new_access_token, new_refresh_token = verify_and_rotate_refresh_token(refresh_token, db)
    except HTTPException as e:
        raise e

    response = JSONResponse(content={"access_token": new_access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # True in prod
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response

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