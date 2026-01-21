"""Education service wrapper.

Provides a class-based interface to education functionality.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


class EducationService:
    """Service for educational content and user progress."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get trading permissions for a user based on their education progress."""
        # Default permissions for all users
        return ["basic_trading", "market_orders", "view_portfolio"]

    def check_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific trading permission."""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def get_required_courses(self, permission: str) -> List[str]:
        """Get required courses for a permission."""
        # Placeholder - would return actual course requirements
        return []

    def get_user_progress(self, user_id: int) -> dict:
        """Get user's educational progress."""
        return {
            "completed_courses": 0,
            "in_progress": 0,
            "available": 0,
            "permissions_earned": self.get_user_permissions(user_id),
        }
