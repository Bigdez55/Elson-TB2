from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import redis
import hashlib

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

# Redis connection for caching and rate limiting
try:
    redis_client = (
        redis.Redis.from_url(settings.REDIS_URL)
        if hasattr(settings, "REDIS_URL")
        else None
    )
except (redis.ConnectionError, redis.TimeoutError, AttributeError):
    redis_client = None

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds
LOGIN_RATE_LIMIT = 5  # login attempts per window
LOGIN_RATE_WINDOW = 300  # 5 minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with JTI for token tracking"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add unique token ID for revocation support
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    # Store token in Redis if available
    if redis_client:
        try:
            redis_client.setex(
                f"token:{jti}",
                int(expires_delta.total_seconds())
                if expires_delta
                else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "valid",
            )
        except (redis.ConnectionError, redis.TimeoutError):
            pass  # Continue without Redis caching

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days

    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    # Store refresh token in Redis
    if redis_client:
        try:
            redis_client.setex(f"refresh_token:{jti}", 7 * 24 * 60 * 60, "valid")
        except (redis.ConnectionError, redis.TimeoutError):
            pass

    return encoded_jwt


def revoke_token(jti: str, token_type: str = "access") -> bool:
    """Revoke a token by its JTI"""
    if redis_client:
        try:
            if token_type == "refresh":
                redis_client.delete(f"refresh_token:{jti}")
            else:
                redis_client.delete(f"token:{jti}")
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            pass
    return False


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type", "access")

        if email is None or jti is None:
            return None

        # Check if token is revoked (if Redis is available)
        if redis_client:
            try:
                key = (
                    f"refresh_token:{jti}"
                    if token_type == "refresh"
                    else f"token:{jti}"
                )
                if not redis_client.exists(key):
                    return None  # Token has been revoked
            except (redis.ConnectionError, redis.TimeoutError):
                pass  # Continue without Redis check

        return payload
    except InvalidTokenError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Generate new access token from refresh token"""
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    email = payload.get("sub")
    if not email:
        return None

    # Create new tokens
    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})

    # Revoke old refresh token
    old_jti = payload.get("jti")
    if old_jti:
        revoke_token(old_jti, "refresh")

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    email = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current admin user - raises exception if not admin"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_current_active_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if credentials is None:
        return None

    payload = verify_token(credentials.credentials)
    if payload is None:
        return None

    email = payload.get("sub")
    if email is None:
        return None

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user_ws(token: str, db: Session) -> Optional[User]:
    """Get current user from WebSocket token"""
    if not token:
        return None

    payload = verify_token(token)
    if payload is None:
        return None

    email = payload.get("sub")
    if email is None:
        return None

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return None

    return user


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(
    request: Request, limit: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW
) -> bool:
    """Check if request is within rate limit"""
    if not redis_client:
        return True  # Skip rate limiting if Redis not available

    client_ip = get_client_ip(request)
    key = f"rate_limit:{client_ip}"

    try:
        current = redis_client.get(key)
        if current is None:
            # First request from this IP
            redis_client.setex(key, window, 1)
            return True
        elif int(current) < limit:
            # Within limit
            redis_client.incr(key)
            return True
        else:
            # Rate limit exceeded
            return False
    except (redis.ConnectionError, redis.TimeoutError, ValueError):
        # Redis error, allow request
        return True


def check_login_rate_limit(email: str, client_ip: str) -> bool:
    """Check login rate limit for email/IP combination"""
    if not redis_client:
        return True

    # Create a hash of email+IP for privacy
    identifier = hashlib.sha256(f"{email}:{client_ip}".encode()).hexdigest()
    key = f"login_attempts:{identifier}"

    try:
        current = redis_client.get(key)
        if current is None:
            redis_client.setex(key, LOGIN_RATE_WINDOW, 1)
            return True
        elif int(current) < LOGIN_RATE_LIMIT:
            redis_client.incr(key)
            return True
        else:
            return False
    except (redis.ConnectionError, redis.TimeoutError, ValueError):
        return True


def reset_login_attempts(email: str, client_ip: str) -> None:
    """Reset login attempts after successful login"""
    if not redis_client:
        return

    identifier = hashlib.sha256(f"{email}:{client_ip}".encode()).hexdigest()
    key = f"login_attempts:{identifier}"

    try:
        redis_client.delete(key)
    except (redis.ConnectionError, redis.TimeoutError) as e:
        pass


def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    if not check_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
    return call_next(request)
