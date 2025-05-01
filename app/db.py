"""
db.py

Handles database setup, session management, and base model declaration.

- Loads credentials from environment variables (.env)
- Sets up SQLAlchemy engine and session
- Exposes `get_db` dependency for FastAPI
- Automatically creates tables when not under pytest
"""

import os
import sys
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi import Depends

# --- Load environment variables ---
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tradecolony")
DB_USER = os.getenv("DB_USER", "tradecolony")
DB_PASS = os.getenv("DB_PASS", "yourpassword")

# --- SQLAlchemy setup ---
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- FastAPI DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Model imports for metadata reflection ---
from app.models.user import User
from app.models.token import RefreshToken


# --- Create tables if not running tests ---
if "pytest" not in sys.modules:
    Base.metadata.create_all(bind=engine)
