from typing import Generator

from fastapi import Depends, HTTPException, status

from app.core.security import (
    get_current_active_user as security_get_current_active_user,
)
from app.core.security import redis_client
from app.db.base import get_db as db_get_db
from app.models.user import User


def get_db() -> Generator:
    """Get database session."""
    yield from db_get_db()


def get_redis():
    """Get Redis client for caching and session storage"""
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service is unavailable. Please try again later.",
        )
    return redis_client


def get_current_active_user(
    current_user: User = Depends(security_get_current_active_user),
) -> User:
    """Get current active user from JWT token."""
    return current_user
