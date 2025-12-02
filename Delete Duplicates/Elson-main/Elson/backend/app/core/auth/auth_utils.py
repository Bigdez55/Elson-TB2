"""
Auth utility functions for WebSocket and API authentication.

This module contains essential utilities for authentication
without introducing circular imports.
"""

from jose import JWTError, jwt
from ..config import settings
from ...db.database import get_token_store
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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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
    """
    try:
        # Get token store
        token_store = await get_token_store()
        
        # Decode token
        payload = decode_jwt_token(token)
        
        # Check if token has been revoked
        token_id = payload.get("jti")
        if not token_id:
            return None
            
        # Check in token store
        is_revoked = token_store.is_token_revoked(token_id)
        if is_revoked:
            return None
            
        return payload
    except Exception:
        return None