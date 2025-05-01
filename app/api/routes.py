from fastapi import APIRouter
from app.api import auth, users, protected

router = APIRouter()

router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(protected.router, tags=["protected"])
