from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from typing import Dict, Optional

from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, UserResponse, Token
from ..core.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    refresh_access_token
)
from ..core.session_management import get_token_store, DistributedTokenStore
from ..db.database import get_db
from ..core.config import settings

class UserService:
    """Service for user operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user with this email already exists
        db_user = self.db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        
        # Sync the encrypted fields
        db_user.sync_encrypted_email()
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Update fields that are provided
        if user_data.email is not None:
            # Check if email already exists for another user
            existing_user = self.db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            db_user.email = user_data.email
            # Sync the encrypted email
            db_user.sync_encrypted_email()
        
        if user_data.first_name is not None:
            db_user.first_name = user_data.first_name
            
        if user_data.last_name is not None:
            db_user.last_name = user_data.last_name
            
        if user_data.password is not None:
            db_user.hashed_password = get_password_hash(user_data.password)
        
        db_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Dict:
        """Authenticate user and return tokens"""
        # Get user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login time
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Check if user is a guardian (has minor accounts)
        from ..models.account import Account
        is_guardian = self.db.query(Account).filter(
            Account.guardian_id == user.id,
            Account.is_active == True
        ).first() is not None
        
        # Check if 2FA is required for this user
        requires_2fa = user.two_factor_enabled
        guardian_without_2fa = is_guardian and not user.two_factor_enabled
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Create refresh token with longer expiry
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "two_factor_enabled": user.two_factor_enabled,
                "is_guardian": is_guardian,
                "requires_2fa_setup": guardian_without_2fa
            }
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Create new access token from refresh token using the improved refresh system"""
        try:
            # Use the token store for managing token revocation
            token_store = await get_token_store(redis=self.db.session._redis_client)
            
            # Use our dedicated refresh token function
            tokens = await refresh_access_token(
                refresh_token=refresh_token,
                db=self.db,
                token_store=token_store
            )
            
            return tokens
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Handle any other exceptions
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()