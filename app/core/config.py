"""
config.py

Central configuration module using Pydantic's `BaseSettings`.

This allows environment variable overrides and ensures typed config access.

Includes settings for:
- JWT secret and algorithm
- Access and refresh token expiry durations
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "super-secret-key"  # Override in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(case_sensitive=True)


# Singleton instance used throughout the app
settings = Settings()
