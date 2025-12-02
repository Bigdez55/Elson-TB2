"""Dependency functions for use in routes."""

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.auth import get_current_user, get_current_active_user
from app.core.auth.guardian_auth import check_guardian_authentication, is_guardian
from app.db.database import get_db

def get_current_user_with_role(required_role: UserRole) -> Callable:
    """Returns a dependency function that ensures the current user has the required role."""
    async def _get_user_with_role(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {required_role.value} role required",
            )
        return current_user
    return _get_user_with_role

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    """Dependency that ensures the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: admin role required",
        )
    return current_user

def get_verified_guardian(db: Session = Depends(get_db)) -> Callable:
    """Returns a dependency function that ensures the current user is a guardian with 2FA enabled."""
    async def _get_verified_guardian(current_user: User = Depends(check_guardian_authentication)):
        if not is_guardian(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: user is not a guardian",
            )
        return current_user
    return _get_verified_guardian