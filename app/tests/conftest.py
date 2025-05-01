"""
conftest.py

Provides fixtures for FastAPI testing:
- Test database setup (SQLite)
- Dependency override for DB session
- Automatic DB cleanup between tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models.user import User
from app.models.token import RefreshToken

# --- Test Database Setup ---
# Note: `./test.db` persists; use ":memory:" for full isolation if needed
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created once before tests run
Base.metadata.create_all(bind=engine)


# --- DB Session Fixture ---
@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- FastAPI Client Fixture with DB Dependency Override ---
@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# --- Auto-clean DB Between Tests ---
@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(RefreshToken).delete()
    db.query(User).delete()
    db.commit()
