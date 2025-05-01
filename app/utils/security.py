"""
security.py

Minimal bcrypt-based password hashing and verification.

Note:
This is a standalone alternative to using Passlib, useful in lighter setups
or when controlling the hash flow directly (e.g., for non-FastAPI scripts).
"""

import bcrypt


# Hash a plaintext password using bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Verify a plaintext password against a stored bcrypt hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
