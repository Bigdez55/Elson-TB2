from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Tuple, List, Callable
import time
from datetime import datetime, timedelta
import jwt
import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
        
    def is_allowed(self, client_id: str) -> Tuple[bool, Optional[float]]:
        now = time.time()
        minute_ago = now - 60
        
        # Clean up old requests
        if client_id in self.requests:
            self.requests[client_id] = [ts for ts in self.requests[client_id] if ts > minute_ago]
        
        # Check rate limit
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            reset_time = self.requests[client_id][0] + 60 - now
            return False, reset_time
            
        self.requests[client_id].append(now)
        return True, None

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.rate_limiter = RateLimiter()

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=403,
                detail="Invalid authorization code."
            )

        # Rate limiting
        client_id = request.client.host
        allowed, reset_time = self.rate_limiter.is_allowed(client_id)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {reset_time:.1f} seconds.",
                headers={"Retry-After": str(int(reset_time))}
            )

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=403,
                detail="Invalid authentication scheme."
            )

        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check token expiration
            exp = payload.get('exp')
            if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return credentials.credentials

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=403,
                detail="Invalid token or expired token."
            )

class APIKeyAuth:
    """API Key authentication for external services"""
    def __init__(self, api_key: str, rate_limit: int = 120):
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)

    async def __call__(self, request: Request):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.api_key:
            raise HTTPException(
                status_code=403,
                detail="Invalid API key"
            )

        # Rate limiting
        client_id = request.client.host
        allowed, reset_time = self.rate_limiter.is_allowed(client_id)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {reset_time:.1f} seconds.",
                headers={"Retry-After": str(int(reset_time))}
            )

        return api_key

# API paths that don't require CSRF protection (e.g., GET methods, login, etc.)
CSRF_EXEMPT_PATHS = [
    re.compile(r"^/api/v1/users/login/access-token$"),
    re.compile(r"^/api/v1/users/refresh-token$"),
    re.compile(r"^/api/v1/users/logout$"),
    re.compile(r"^/api/v1/docs.*$"),
    re.compile(r"^/api/v1/openapi.json$"),
]

# Safe HTTP methods that don't modify state
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection"""
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF checks for safe methods
        if request.method in SAFE_METHODS:
            return await call_next(request)
            
        # Skip CSRF checks for exempt paths
        path = request.url.path
        if any(pattern.match(path) for pattern in CSRF_EXEMPT_PATHS):
            return await call_next(request)
            
        # Get CSRF token from cookies and headers
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        # Validate CSRF token
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            logger.warning(f"CSRF validation failed for {request.method} {path}")
            raise HTTPException(status_code=403, detail="CSRF token validation failed")
            
        # Continue with the request
        return await call_next(request)

# Brute force protection
# Tracks login attempts with exponential backoff
class BruteForceProtection:
    """Brute force protection with exponential backoff"""
    def __init__(self, max_attempts: int = 5, lockout_time: int = 15 * 60):
        self.max_attempts = max_attempts  # Default: 5 attempts
        self.lockout_time = lockout_time  # Default: 15 minutes in seconds
        self.attempts = {}  # IP -> [timestamp1, timestamp2, ...]
        self.lockouts = {}  # IP -> lockout_until_timestamp
        
    def is_locked_out(self, ip: str) -> Tuple[bool, Optional[int]]:
        """Check if an IP is locked out"""
        now = time.time()
        
        # Check if IP is in lockout period
        if ip in self.lockouts and now < self.lockouts[ip]:
            remaining = int(self.lockouts[ip] - now)
            return True, remaining
            
        # Clean up expired attempts
        if ip in self.attempts:
            self.attempts[ip] = [ts for ts in self.attempts[ip] if now - ts < 3600]  # Keep attempts from last hour
            
        return False, None
        
    def record_attempt(self, ip: str, success: bool) -> None:
        """Record a login attempt"""
        now = time.time()
        
        if success:
            # Reset attempts on successful login
            if ip in self.attempts:
                del self.attempts[ip]
            if ip in self.lockouts:
                del self.lockouts[ip]
            return
        
        # Record failed attempt
        if ip not in self.attempts:
            self.attempts[ip] = []
        self.attempts[ip].append(now)
        
        # Apply lockout if necessary
        attempt_count = len(self.attempts[ip])
        if attempt_count >= self.max_attempts:
            # Exponential backoff: 2^(attempts-max_attempts) * lockout_time
            lockout_duration = 2 ** (attempt_count - self.max_attempts) * self.lockout_time
            # Cap at 24 hours
            lockout_duration = min(lockout_duration, 24 * 60 * 60)
            self.lockouts[ip] = now + lockout_duration
            logger.warning(f"IP {ip} locked out for {lockout_duration} seconds after {attempt_count} failed attempts")

# Initialize brute force protection
brute_force_protection = BruteForceProtection()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers and logging"""
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            # Log request details
            process_time = time.time() - start_time
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

# Security tokens handler
security = JWTBearer()
api_key_auth = APIKeyAuth(settings.SCHWAB_API_KEY)