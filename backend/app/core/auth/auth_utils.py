"""
Auth utility functions for WebSocket and API authentication.

This module contains essential utilities for authentication
without introducing circular imports.
"""

from jose import JWTError, jwt
from ..config import settings

# from ...db.database import get_token_store  # Not available in current setup
from typing import Optional, Dict, Any


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode

    Returns:
        The decoded payload if valid

    Raises:
        JWTError: If the token is invalid or expired
    """
    try:
        algorithm = getattr(settings, "ALGORITHM", "HS256")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[algorithm])
        return payload
    except JWTError as e:
        # Re-raise to be caught by the caller
        raise e


async def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token and check if it's been revoked.

    Args:
        token: The JWT token string to validate

    Returns:
        The decoded payload if valid and not revoked, None otherwise

    Note: Token revocation checking is not implemented in current setup.
    Only validates token signature and expiration.
    """
    try:
        # Decode token (validates signature and expiration)
        payload = decode_jwt_token(token)

        # TODO: Implement token revocation checking when token store is available
        # token_store = await get_token_store()
        # token_id = payload.get("jti")
        # if token_id and token_store.is_token_revoked(token_id):
        #     return None

        return payload
    except Exception:
        return None
