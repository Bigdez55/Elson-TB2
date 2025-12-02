"""
Bootstrap module for initializing the application.

This module is used to initialize various components of the application
without introducing circular imports. It's responsible for setting up
components such as authentication, session management, etc.
"""

from jose import JWTError, jwt
from .config import settings
from typing import Dict, Any, Optional


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