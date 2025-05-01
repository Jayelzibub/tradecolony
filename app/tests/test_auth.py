import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.auth.password import hash_password
from app.db import get_db  # Required for dependency override

# ----------------------------
# ✅ Test: Successful login
# ----------------------------
@pytest.mark.asyncio
async def test_successful_login(db: Session):
    """
    Expect: User can log in with correct credentials and receive access token and refresh cookie.
    """
    email = "testuser@example.com"
    password = "strongpassword"
    hashed_password = hash_password(password)

    user = User(
        username="testuser",
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_forgotten=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "set-cookie" in response.headers

# ----------------------------
# ❌ Test: Incorrect password
# ----------------------------
@pytest.mark.asyncio
async def test_login_wrong_password(db: Session):
    """
    Expect: Login fails with 401 if password is incorrect.
    """
    email = "wrongpass@example.com"
    password = "correctpassword"
    wrong_password = "incorrectpassword"

    user = User(
        username="wrongpassuser",
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_forgotten=False
    )
    db.add(user)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": email, "password": wrong_password})

    assert response.status_code == 401

# ----------------------------
# ❌ Test: User does not exist
# ----------------------------
@pytest.mark.asyncio
async def test_login_nonexistent_user(db: Session):
    """
    Expect: Login fails with 401 if email is not in database.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": "ghost@example.com", "password": "nopass"})

    assert response.status_code == 401

# ----------------------------
# ❌ Test: Inactive user
# ----------------------------
@pytest.mark.asyncio
async def test_login_inactive_user(db: Session):
    """
    Expect: Login fails with 403 if user is inactive.
    """
    email = "inactive@example.com"
    password = "pass123"

    user = User(
        username="inactiveuser",
        email=email,
        hashed_password=hash_password(password),
        is_active=False,
        is_forgotten=False
    )
    db.add(user)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 403

# ----------------------------
# ❌ Test: Forgotten user
# ----------------------------
@pytest.mark.asyncio
async def test_login_forgotten_user(db: Session):
    """
    Expect: Login fails with 403 if user is marked as forgotten.
    """
    email = "forgotten@example.com"
    password = "pass123"

    user = User(
        username="forgottenuser",
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_forgotten=True
    )
    db.add(user)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 403

# ----------------------------
# ❌ Test: Missing fields
# ----------------------------
@pytest.mark.asyncio
async def test_login_missing_fields(db: Session):
    """
    Expect: Login fails with 422 if email/password fields are missing (validation error).
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={})

    assert response.status_code == 422
