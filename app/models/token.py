"""
token.py

SQLAlchemy model for refresh tokens.

Includes:
- Token string (JWT)
- User foreign key with cascade delete
- Timestamps for creation, expiration, and optional revocation
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(DateTime, nullable=True)

    # Linked user relationship (User.refresh_tokens must exist)
    user = relationship("User", back_populates="refresh_tokens")
