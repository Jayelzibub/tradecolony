from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User as UserModel
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from app.auth.password import hash_password
from app.schemas.user import User, CreateUser, UpdateUser


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# ---- Pydantic Schemas ----
class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    notification_email_enabled: bool = True
    notification_sms_enabled: bool = False
    timezone: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_forgotten: bool
    forgotten_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    timezone: str = "UTC"

class UpdateUser(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    notification_email_enabled: Optional[bool] = None
    notification_sms_enabled: Optional[bool] = None
    timezone: Optional[str] = None


# ---- Route: GET /users ----
@router.get("/", response_model=list[User])
def get_users(
    skip: int = 0,
    limit: int = 10,
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    sort_order: str = Query("asc", pattern=r"^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    query = db.query(UserModel)

    if username:
        query = query.filter(UserModel.username == username)
    if email:
        query = query.filter(UserModel.email == email)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    if is_admin is not None:
        query = query.filter(UserModel.is_admin == is_admin)

    if sort_order == "desc":
        query = query.order_by(UserModel.id.desc())
    else:
        query = query.order_by(UserModel.id.asc())

    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# ---- Route: POST /users ----
@router.post("/", response_model=User)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    if db.query(UserModel).filter(UserModel.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    hashed_password = hash_password(user.password)

    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
        notification_email_enabled=True,
        notification_sms_enabled=False,
        timezone=user.timezone,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ---- Route: PATCH /users ----
@router.patch("/{user_id}", response_model=User)
def update_user(user_id: int, updates: UpdateUser, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if updates.password:
        user.hashed_password = hash_password(updates.password)
    if updates.username is not None:
        user.username = updates.username
    if updates.is_active is not None:
        user.is_active = updates.is_active
    if updates.is_admin is not None:
        user.is_admin = updates.is_admin
    if updates.notification_email_enabled is not None:
        user.notification_email_enabled = updates.notification_email_enabled
    if updates.notification_sms_enabled is not None:
        user.notification_sms_enabled = updates.notification_sms_enabled
    if updates.timezone is not None:
        user.timezone = updates.timezone

    db.commit()
    db.refresh(user)
    return user

# ---- Route: DELETE /users ----
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    db.commit()
    return

@router.delete("/{user_id}/forget", status_code=status.HTTP_204_NO_CONTENT)
def forget_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.username = f"deleted_user_{user_id}"
    user.email = f"deleted_user_{user_id}@example.com"
    user.hashed_password = ""
    user.timezone = None
    user.is_active = False
    user.notification_email_enabled = False
    user.notification_sms_enabled = False
    user.is_forgotten = True
    user.forgotten_at = datetime.utcnow()

    db.commit()
    return
