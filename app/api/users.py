from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from datetime import datetime

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
    updated_at: datetime

class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str  # Raw password (to be hashed before storing)
    timezone: str = "UTC"

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=list[User])
def get_users():
    return [
        User(id=1, username="gentlevillain"),
        User(id=2, username="jayelzibub"),
        User(id=3, username="debugpanda")
    ]

@router.post("/", response_model=User)
def create_user(user: CreateUser):
    fake_id = 100  # pretend we got this from a DB sequence
    return User(id=fake_id, username=user.username)