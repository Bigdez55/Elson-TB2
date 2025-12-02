from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
import re
import uuid
from redis import Redis

from .config import settings
from ..db.database import get_db, get_redis
from ..models.user import User
from .session_management import get_token_store, DistributedTokenStore

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication (legacy - used as fallback)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login/access-token")

# Password complexity regex
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def validate_password_complexity(password: str) -> bool:
    """
    Validate password complexity:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    return bool(PASSWORD_PATTERN.match(password))

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Add token ID for revocation capability
    token_id = str(uuid.uuid4())
    to_encode.update({"jti": token_id})
    
    # Mark as access token type
    to_encode.update({"type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token with longer expiry"""
    to_encode = data.copy()
    
    # Calculate expiry - default is longer than access token
    refresh_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expire = datetime.utcnow() + timedelta(days=refresh_expire_days)
    
    # Update with expiry and issued at time
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(),
        "type": "refresh"  # Mark as refresh token
    })
    
    # Add token ID for revocation capability
    token_id = str(uuid.uuid4())
    to_encode.update({"jti": token_id})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Token operations using distributed token store
async def revoke_token(
    token: str, 
    token_store: DistributedTokenStore = Depends(get_token_store)
) -> None:
    """Add a token to the revocation list with Redis storage for distributed systems"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_id = payload.get("jti")
        expiry = payload.get("exp")
        
        if token_id and expiry:
            # Calculate seconds until expiry
            now = datetime.utcnow().timestamp()
            expires_in = max(1, int(expiry - now))  # Ensure at least 1 second
            
            # Store in Redis with expiry
            token_store.revoke_token(token_id, expires_in)
    except Exception as e:
        # Log the error but don't raise (best effort token revocation)
        pass

async def is_token_revoked(
    token: str,
    token_store: DistributedTokenStore = Depends(get_token_store)
) -> bool:
    """Check if a token has been revoked using Redis for distributed systems"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_id = payload.get("jti")
        if not token_id:
            return True
            
        # Check in Redis
        return token_store.is_token_revoked(token_id)
    except:
        return True  # Invalid tokens are considered revoked

async def get_token_from_cookie_or_header(request: Request) -> str:
    """Get JWT token from cookie or header"""
    # Try to get from cookie first
    token = request.cookies.get("access_token")
    
    # If not in cookie, try to get from header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

async def refresh_access_token(
    refresh_token: str,
    db: Session,
    token_store: DistributedTokenStore
) -> Dict[str, str]:
    """
    Create a new access token using a valid refresh token
    
    Returns a dict with both new access and refresh tokens
    """
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is revoked
    if await is_token_revoked(refresh_token, token_store):
        raise invalid_token_exception
    
    try:
        # Decode and validate the refresh token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            raise invalid_token_exception
            
        # Extract user ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise invalid_token_exception
            
        # Validate user exists
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise invalid_token_exception
        
        # Generate new tokens
        access_token_data = {"sub": str(user.id)}
        new_access_token = create_access_token(access_token_data)
        
        # Revoke the used refresh token for security
        await revoke_token(refresh_token, token_store)
        
        # Create a new refresh token
        refresh_token_data = {"sub": str(user.id)}
        new_refresh_token = create_refresh_token(refresh_token_data)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise invalid_token_exception

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
    token_store: DistributedTokenStore = Depends(get_token_store)
) -> User:
    """Get current user from JWT token in cookie or header"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from cookie or header
    token = access_token
    if not token:
        try:
            token = await get_token_from_cookie_or_header(request)
        except HTTPException:
            # Fallback to OAuth2 scheme
            try:
                token = await oauth2_scheme(request)
            except:
                raise credentials_exception
    
    # Check if token is revoked
    if await is_token_revoked(token, token_store):
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Check token type - must be an access token
        if payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_current_adult_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current adult user"""
    if not current_user.is_adult:
        raise HTTPException(
            status_code=403, detail="This action requires an adult account"
        )
    return current_user

async def get_current_user_ws(
    token: str,
    db: Session = Depends(get_db)
) -> Dict:
    """Get current user for WebSocket connections"""
    try:
        # Check if token is revoked
        if is_token_revoked(token):
            raise ValueError("Token has been revoked")
            
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise ValueError("User not found")
            
        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active
        }
        
    except (InvalidTokenError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )