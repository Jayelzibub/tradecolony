import pytest
import httpx
import uuid
from app.main import app
from httpx import ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User as UserModel

# ----------------------------
# ✅ Test: Health check route
# ----------------------------
@pytest.mark.asyncio
async def test_health_check():
    """
    Expect: 200 OK with welcome message when hitting the root endpoint.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["message"].startswith("Welcome to")

# ----------------------------
# ✅ Test: Create user
# ----------------------------
def test_create_user(client: TestClient, db: Session):
    """
    Expect: Successfully create a new user and return correct fields.
    """
    # Ensure no conflicting user already exists
    db.query(UserModel).filter(UserModel.email == "testuser@example.com").delete()
    db.commit()

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

    # Clean up test data
    db.query(UserModel).filter(UserModel.email == "testuser@example.com").delete()
    db.commit()

# ----------------------------
# ✅ Test: Get users with email filter
# ----------------------------
@pytest.mark.asyncio
async def test_get_users():
    """
    Expect: GET /users/ with email filter should return list containing the test user.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a test user
        await ac.post("/users/", json={
            "username": "listtestuser",
            "email": "listtestuser@example.com",
            "password": "SecurePass123",
            "timezone": "UTC"
        })

        # Fetch users filtered by email
        response = await ac.get("/users/?email=listtestuser@example.com")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert any(user["email"] == "listtestuser@example.com" for user in users)

        # Cleanup
        user_id = next(user["id"] for user in users if user["email"] == "listtestuser@example.com")
        await ac.delete(f"/users/{user_id}")

# ----------------------------
# ✅ Test: Get user by ID
# ----------------------------
@pytest.mark.asyncio
async def test_get_user_by_id():
    """
    Expect: User can be retrieved by their ID after creation.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a unique user
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

        # Fetch the user by ID
        get_response = await ac.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == unique_email

        # Cleanup
        await ac.delete(f"/users/{user_id}")

# ----------------------------
# ✅ Test: Update user fields
# ----------------------------
@pytest.mark.asyncio
async def test_update_user():
    """
    Expect: PATCH /users/{id} should allow updating username and SMS notification.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a unique user
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

        # Update the user
        patch_response = await ac.patch(f"/users/{user_id}", json={
            "username": f"updated_{unique_id}",
            "notification_sms_enabled": True
        })
        assert patch_response.status_code == 200
        updated_user = patch_response.json()
        assert updated_user["username"] == f"updated_{unique_id}"
        assert updated_user["notification_sms_enabled"] is True

        # Cleanup
        await ac.delete(f"/users/{user_id}")