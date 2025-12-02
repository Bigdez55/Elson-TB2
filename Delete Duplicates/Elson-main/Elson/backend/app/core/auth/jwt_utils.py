"""JWT token utilities for authentication.

This module provides utilities for JWT token handling to prevent circular imports.
"""

from jose import JWTError, jwt
from ...core.config import settings

def decode_jwt_token(token: str):
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