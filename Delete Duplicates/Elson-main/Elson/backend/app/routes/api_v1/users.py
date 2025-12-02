from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import secrets

from ...db.database import get_db
from ...models.user import User
from ...core.auth import get_current_user
from ...schemas.user import UserCreate, UserUpdate, UserResponse, Token
from ...services.user import UserService
from ...core.session_management import get_token_store, DistributedTokenStore
from ...core.config import settings

router = APIRouter()

# Generate CSRF tokens
def generate_csrf_token() -> str:
    return secrets.token_hex(32)

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    user_service = UserService(db)
    try:
        return await user_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    csrf_token: str = Cookie(None),
    x_csrf_token: str = Cookie(None)
):
    """Update current user information with CSRF protection"""
    # Validate CSRF token
    if not csrf_token or not x_csrf_token or csrf_token != x_csrf_token:
        raise HTTPException(status_code=403, detail="CSRF token validation failed")
        
    user_service = UserService(db)
    try:
        return await user_service.update_user(current_user.id, user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/access-token")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login with HttpOnly cookies"""
    user_service = UserService(db)
    try:
        auth_data = await user_service.authenticate_user(form_data.username, form_data.password)
        
        # Set access token in HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=auth_data["access_token"],
            httponly=True,
            secure=not settings.DEBUG,  # Secure in production
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=auth_data["refresh_token"],
            httponly=True,
            secure=not settings.DEBUG,  # Secure in production
            samesite="strict",
            max_age=30 * 24 * 60 * 60  # 30 days in seconds
        )
        
        # Generate and set CSRF token
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,  # Accessible to JavaScript
            secure=not settings.DEBUG,
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        # Return user and token data (excluding the tokens themselves)
        return {
            "user": auth_data["user"],
            "token_type": auth_data["token_type"],
            "csrf_token": csrf_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh-token")
async def refresh_access_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    try:
        token_data = await user_service.refresh_token(refresh_token)
        
        # Set new access token in HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        # Set new refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            httponly=True,
            secure=not settings.DEBUG,  # Secure in production
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
        )
        
        # Generate and set new CSRF token
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=not settings.DEBUG,
            samesite="strict",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return {"token_type": token_data["token_type"], "csrf_token": csrf_token}
    except HTTPException as e:
        # Re-raise HTTP exceptions with their original status code and detail
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
    token_store: DistributedTokenStore = Depends(get_token_store)
):
    """Clear auth cookies and revoke tokens on logout"""
    from ...core.auth import revoke_token
    
    # Revoke both tokens if present
    try:
        if access_token:
            await revoke_token(access_token, token_store)
        
        if refresh_token:
            await revoke_token(refresh_token, token_store)
    except Exception as e:
        # Log error but continue with cookie removal
        print(f"Error revoking tokens: {str(e)}")
    
    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="csrf_token")
    
    return {"message": "Logout successful"}