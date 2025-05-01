"""
routes.py

Aggregates all API route modules into the main FastAPI router.

Includes:
- Authentication routes (login, refresh, logout).
- User CRUD or management routes.
- Protected routes requiring authentication.
"""

from fastapi import APIRouter

from app.api import auth, users, protected

router = APIRouter()

# Auth routes: login, refresh, logout
router.include_router(auth.router, tags=["auth"])

# User-related routes (e.g. registration, profile)
router.include_router(users.router, tags=["users"])

# Protected routes: require authentication
router.include_router(protected.router, tags=["protected"])
