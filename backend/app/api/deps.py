from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user as security_get_current_active_user
from app.db.base import get_db as db_get_db
from app.models.user import User


def get_db() -> Generator:
    """Get database session."""
    yield from db_get_db()


def get_current_active_user(
    current_user: User = Depends(security_get_current_active_user),
) -> User:
    """Get current active user from JWT token."""
    return current_user