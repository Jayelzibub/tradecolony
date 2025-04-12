from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User as UserModel
from pydantic import BaseModel, EmailStr
from datetime import datetime
import hashlib  # temporary, will switch to bcrypt

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
    timezone: str = "UTC"
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True

class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    timezone: str = "UTC"

# ---- Route: POST /users ----
@router.post("/", response_model=User)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

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
