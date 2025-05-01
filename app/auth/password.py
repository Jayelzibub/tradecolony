"""
password.py

Handles password hashing and verification using bcrypt via Passlib.

Includes:
- `hash_password`: Hashes plaintext passwords securely.
- `verify_password`: Compares a plaintext password with its hashed version.
"""

from passlib.context import CryptContext

# bcrypt is the selected hashing scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash a plaintext password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Verify a plaintext password against a hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
