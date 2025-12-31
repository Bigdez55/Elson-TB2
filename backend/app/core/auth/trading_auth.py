"""Trading-specific authentication and authorization.

This module provides trading-specific permission checks and exceptions.
"""

from typing import Optional
from fastapi import HTTPException, status


class TradingPermissionError(HTTPException):
    """Exception raised when user lacks trading permissions."""

    def __init__(
        self,
        detail: str = "Trading permission denied",
        required_permission: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
        self.required_permission = required_permission


def check_trading_enabled(user) -> bool:
    """Check if user has trading enabled."""
    if not hasattr(user, 'trading_enabled'):
        return True  # Default to allowed if attribute doesn't exist
    return user.trading_enabled


def require_trading_permission(user, permission: str = "trade") -> None:
    """Require user to have specific trading permission.

    Args:
        user: The user object to check
        permission: The permission required (e.g., 'trade', 'margin', 'options')

    Raises:
        TradingPermissionError: If user lacks the required permission
    """
    if not check_trading_enabled(user):
        raise TradingPermissionError(
            detail=f"Trading is not enabled for this account",
            required_permission=permission,
        )

    # Check specific permissions if user has a permissions attribute
    if hasattr(user, 'trading_permissions'):
        if permission not in user.trading_permissions:
            raise TradingPermissionError(
                detail=f"Permission '{permission}' not granted",
                required_permission=permission,
            )
