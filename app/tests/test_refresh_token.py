import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.auth.password import hash_password
from app.models.user import User
from app.db import get_db
from app.services.token_service import decode_token  # ✅ fixed import

client = TestClient(app)


@pytest.fixture
def create_user(db: Session):
    def _create_user(email="refresh@example.com", password="testpass123"):
        user = User(
            username="refreshuser",
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return _create_user


def test_refresh_flow_success(client, create_user):
    user = create_user()
    user_id = str(user.id)
    login_data = {"email": user.email, "password": "testpass123"}

    with client:
        login_response = client.post("/login", json=login_data)
        assert login_response.status_code == 200
        access_token_before = login_response.json()["access_token"]

        # ✅ Explicitly set the cookie from login response
        client.cookies.set("refresh_token", login_response.cookies.get("refresh_token"))

        refresh_response = client.post("/refresh")
        assert refresh_response.status_code == 200

        data = refresh_response.json()
        access_token_after = data["access_token"]

        assert access_token_before != access_token_after
        decoded = decode_token(access_token_after)
        assert decoded["sub"] == user_id

def test_refresh_missing_token(client):
    response = client.post("/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing refresh token"


def test_refresh_with_invalid_token(client):
    response = client.post("/refresh", cookies={"refresh_token": "invalid.token.here"})
    assert response.status_code == 401
