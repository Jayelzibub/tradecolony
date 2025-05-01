"""
schemas/user.py

Defines Pydantic models for user-related data validation and serialization.

Includes:
- Public user model (`User`)
- Creation and update input schemas
- Auth request/response models
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---- Output schema for user data ----
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


# ---- Input schema for user creation ----
class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    timezone: str = "UTC"

    model_config = ConfigDict(from_attributes=True)


# ---- Input schema for partial user update ----
class UpdateUser(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    notification_email_enabled: Optional[bool] = None
    notification_sms_enabled: Optional[bool] = None
    timezone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---- Input schema for login ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---- Output schema for login response ----
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
