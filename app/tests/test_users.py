"""
test_users.py

Tests for user-related endpoints:
- Health check
- User creation
- User listing and filtering
- User retrieval by ID
- User field updates
"""

import pytest
import httpx
import uuid

from httpx import ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User as UserModel


# --- ✅ Health check route ---
@pytest.mark.asyncio
async def test_health_check():
    """
    Expect: 200 OK with welcome message when hitting the root endpoint.
    """
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["message"].startswith("Welcome to")


# --- ✅ Create user ---
def test_create_user(client: TestClient, db: Session):
    """
    Expect: Successfully create a new user and return correct fields.
    """
    response = client.post("/users/", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePass123",
        "timezone": "UTC"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["is_active"] is True
    assert data["is_admin"] is False


# --- ✅ Get users with email filter ---
@pytest.mark.asyncio
async def test_get_users():
    """
    Expect: GET /users/ with email filter should return list containing the test user.
    """
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/users/", json={
            "username": "listtestuser",
            "email": "listtestuser@example.com",
            "password": "SecurePass123",
            "timezone": "UTC"
        })

        response = await ac.get("/users/?email=listtestuser@example.com")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert any(user["email"] == "listtestuser@example.com" for user in users)


# --- ✅ Get user by ID ---
@pytest.mark.asyncio
async def test_get_user_by_id():
    """
    Expect: User can be retrieved by their ID after creation.
    """
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        unique_id = uuid.uuid4().hex[:6]
        unique_email = f"getbyid_{unique_id}@example.com"
        unique_username = f"getbyiduser_{unique_id}"

        create_response = await ac.post("/users/", json={
            "username": unique_username,
            "email": unique_email,
            "password": "SecurePass123",
            "timezone": "UTC"
        })
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]

        get_response = await ac.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == unique_email


# --- ✅ Update user fields ---
@pytest.mark.asyncio
async def test_update_user():
    """
    Expect: PATCH /users/{id} should allow updating username and SMS notification.
    """
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        unique_id = uuid.uuid4().hex[:6]
        unique_email = f"updateuser_{unique_id}@example.com"
        unique_username = f"updatableuser_{unique_id}"

        create_response = await ac.post("/users/", json={
            "username": unique_username,
            "email": unique_email,
            "password": "SecurePass123",
            "timezone": "UTC"
        })
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]

        patch_response = await ac.patch(f"/users/{user_id}", json={
            "username": f"updated_{unique_id}",
            "notification_sms_enabled": True
        })
        assert patch_response.status_code == 200
        updated_user = patch_response.json()
        assert updated_user["username"] == f"updated_{unique_id}"
        assert updated_user["notification_sms_enabled"] is True
