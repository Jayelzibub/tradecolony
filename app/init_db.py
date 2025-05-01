"""
init.py

Initialises the database by importing models and creating all tables.

Usage:
    python app/init.py

This script is typically used during development to bootstrap the database.
"""

from app.db import engine, Base
from app.models.user import User  # Ensure model is registered
from app.models.token import RefreshToken  # Include all models explicitly

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database tables created.")
