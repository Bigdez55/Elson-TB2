"""Middleware for FastAPI application including rate limiting, caching, and security monitoring.

This module provides middleware components for enhancing API performance
and security through rate limiting, caching, and other optimizations.
"""

import time
import logging
import re
import json
import traceback
from typing import Any, Callable, Dict, Optional, Tuple, Union, Pattern, List
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.metrics import record_metric
from app.core.caching import get_cache, set_cache
from app.core.security_monitor import get_security_monitor

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse.
    
    This middleware uses Redis (or in-memory fallback) to track request counts
    by IP address and route.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        default_limit: int = 100,  # 100 requests per minute
        window_seconds: int = 60,   # 1 minute window
        enabled: bool = True,
        exclude_paths: Optional[list] = None
    ):
        """Initialize rate limiter.
        
        Args:
            app: ASGI application
            default_limit: Default requests per minute limit
            window_seconds: Time window for rate limiting
            enabled: Whether rate limiting is enabled
            exclude_paths: List of path prefixes to exclude from rate limiting
        """
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc", "/metrics"]
        
        # Route-specific limits
        self.route_limits = {
            "/api/v1/users": 50,        # Lower limit for user operations
            "/api/v1/auth/login": 20,   # Lower limit for login attempts
            "/api/v1/trades": 200       # Higher limit for trade operations
        }
        
        logger.info(f"Rate limiting middleware initialized: {default_limit} req/min")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware/route handler
            
        Returns:
            Response from the route handler or 429 Too Many Requests
        """
        if not self.enabled:
            return await call_next(request)
        
        # Check for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Determine the applicable rate limit
        path = request.url.path
        rate_limit = self.default_limit
        for route_prefix, limit in self.route_limits.items():
            if path.startswith(route_prefix):
                rate_limit = limit
                break
        
        # Check rate limit
        exceed, current_count = await self._check_rate_limit(client_ip, path, rate_limit)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)
        
        # If rate limit exceeded, return 429 Too Many Requests
        if exceed:
            error_response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later."
                }
            )
            error_response.headers.update(response.headers)
            logger.warning(f"Rate limit exceeded: {client_ip} - {path} ({current_count}/{rate_limit})")
            record_metric("rate_limit_exceeded", 1, {"path": path, "client_ip": client_ip})
            
            # Record security event
            try:
                security_monitor = get_security_monitor()
                security_monitor.record_suspicious_activity(
                    activity_type="rate_limit_exceeded",
                    ip=client_ip,
                    details={
                        "path": path,
                        "rate_limit": rate_limit,
                        "count": current_count,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to record security event: {str(e)}")
            
            return error_response
        
        return response
    
    async def _check_rate_limit(
        self, 
        client_ip: str, 
        path: str,
        rate_limit: int
    ) -> Tuple[bool, int]:
        """Check if the request exceeds the rate limit.
        
        Args:
            client_ip: Client IP address
            path: Request path
            rate_limit: Rate limit to apply
            
        Returns:
            Tuple of (limit_exceeded, current_count)
        """
        # Create unique key for this client and route
        cache_key = f"ratelimit:{client_ip}:{path}"
        
        # Get current count
        cached_data = get_cache(cache_key)
        if cached_data is None:
            # New client/route combination
            current_count = 1
            set_cache(cache_key, current_count, ttl=self.window_seconds)
            return False, current_count
        else:
            # Increment count
            current_count = cached_data + 1
            set_cache(cache_key, current_count, ttl=self.window_seconds)
            
            # Check if limit exceeded
            return current_count > rate_limit, current_count

class ResponseCachingMiddleware(BaseHTTPMiddleware):
    """Middleware for caching GET responses.
    
    This middleware caches responses from GET requests to improve performance
    for frequently accessed data.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        enabled: bool = True,
        default_ttl: int = 300,  # 5 minutes
        max_size: int = 1024 * 1024 * 10,  # 10MB
        exclude_paths: Optional[list] = None,
        exclude_auth: bool = True
    ):
        """Initialize response caching middleware.
        
        Args:
            app: ASGI application
            enabled: Whether caching is enabled
            default_ttl: Default cache TTL in seconds
            max_size: Maximum size of cached response in bytes
            exclude_paths: List of path prefixes to exclude from caching
            exclude_auth: Whether to exclude authenticated requests
        """
        super().__init__(app)
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc", "/metrics"]
        self.exclude_auth = exclude_auth
        
        # Path-specific TTLs
        self.path_ttls = {
            "/api/v1/market-data": 60,            # Market data changes frequently
            "/api/v1/reference-data": 86400,      # Reference data rarely changes
            "/api/v1/portfolios": 300,            # Portfolio data changes moderately
            "/api/v1/educational": 86400          # Educational content rarely changes
        }
        
        logger.info(f"Response caching middleware initialized: TTL={default_ttl}s")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through caching middleware.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware/route handler
            
        Returns:
            Cached response or response from the route handler
        """
        # Skip if caching is disabled
        if not self.enabled:
            return await call_next(request)
        
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Skip authenticated requests if configured
        if self.exclude_auth and "authorization" in request.headers:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached_response = get_cache(cache_key)
        if cached_response is not None:
            # Create response from cached data
            response = Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )
            response.headers["X-Cache"] = "HIT"
            record_metric("api_cache_hit", 1, {"path": request.url.path})
            return response
        
        # No cache hit, process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = (time.time() - start_time) * 1000
        
        # Only cache successful responses
        if 200 <= response.status_code < 400:
            # Get path-specific TTL or use default
            ttl = self.default_ttl
            for path_prefix, path_ttl in self.path_ttls.items():
                if request.url.path.startswith(path_prefix):
                    ttl = path_ttl
                    break
            
            # Read and cache response
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Check if response is too large to cache
            if len(body) <= self.max_size:
                # Cache response data
                cache_data = {
                    "content": body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }
                set_cache(cache_key, cache_data, ttl=ttl)
                record_metric("api_cache_store", 1, {
                    "path": request.url.path,
                    "size": len(body),
                    "ttl": ttl
                })
            
            # Create new response with the same body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Cache key string
        """
        # Combine path and query parameters
        key_parts = [request.url.path]
        
        # Add sorted query params
        query_params = sorted(request.query_params.items())
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params)
            key_parts.append(query_string)
        
        # Create key
        key_string = ":".join(key_parts)
        return f"response_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

class PerformanceHeadersMiddleware(BaseHTTPMiddleware):
    """Add performance metrics headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add performance headers to response.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware/route handler
            
        Returns:
            Response with added performance headers
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["Server-Timing"] = f"total;dur={process_time:.2f}"
        
        # Record metrics
        record_metric("request_time", process_time, {
            "method": request.method,
            "path": request.url.path
        })
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request information for debugging and analytics."""
    
    def __init__(
        self, 
        app: ASGIApp, 
        level: str = "DEBUG",
        log_headers: bool = False,
        log_body: bool = False
    ):
        """Initialize request logging middleware.
        
        Args:
            app: ASGI application
            level: Logging level
            log_headers: Whether to log request headers
            log_body: Whether to log request body
        """
        super().__init__(app)
        self.log_level = getattr(logging, level)
        self.log_headers = log_headers
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request information.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware/route handler
            
        Returns:
            Response from the route handler
        """
        # Start timer
        start_time = time.time()
        
        # Prepare log information
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "query_params": dict(request.query_params)
        }
        
        # Log headers if enabled
        if self.log_headers:
            log_data["headers"] = dict(request.headers)
        
        # Log request
        logger.log(self.log_level, f"Request: {json.dumps(log_data)}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Log response
        logger.log(
            self.log_level, 
            f"Response: {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)"
        )
        
        return response

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security monitoring middleware for tracking security events.
    
    This middleware integrates with the security monitoring system to track:
    1. Failed authentication attempts
    2. Suspicious request patterns
    3. Access to sensitive endpoints
    4. Token verification failures
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        enabled: bool = True,
        sensitive_paths: Optional[List[str]] = None,
        suspicious_patterns: Optional[List[Tuple[str, Pattern]]] = None
    ):
        """Initialize security middleware.
        
        Args:
            app: ASGI application
            enabled: Whether security monitoring is enabled
            sensitive_paths: List of paths that are considered sensitive
            suspicious_patterns: List of (name, regex) tuples for suspicious patterns
        """
        super().__init__(app)
        self.enabled = enabled
        self.sensitive_paths = sensitive_paths or [
            "/api/v1/auth/",
            "/api/v1/users/", 
            "/api/v1/admin/",
            "/api/v1/payment/"
        ]
        
        # Default suspicious pattern regexes
        default_suspicious_patterns = [
            ("sql_injection", re.compile(r"['\"]\s*(?:or|and|union|select|from|where|drop|delete|insert|xp_)\s+", re.I)),
            # More specific path traversal pattern that won't match normal URLs
            ("path_traversal", re.compile(r"(?:\.\.\/|\.\.$|%2e%2e\/|%2e%2e$|\.\.\?|\?\.\.)")),
            ("xss_attempt", re.compile(r"<\s*script.*?>|javascript\s*:|on(?:click|load|mouseover|error|focus)=", re.I)),
            ("command_injection", re.compile(r"[;&|`](?:\s*[a-zA-Z0-9_.]+=.*|\s*[a-zA-Z]+\s+-[a-zA-Z]|\s*cat\s+)"))
        ]
        
        self.suspicious_patterns = suspicious_patterns or default_suspicious_patterns
        logger.info(f"Security middleware initialized: monitoring {len(self.sensitive_paths)} sensitive paths")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security monitoring.
        
        Args:
            request: FastAPI request object
            call_next: Function to call the next middleware/route handler
            
        Returns:
            Response from the route handler with security checks
        """
        if not self.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Check if this is a sensitive path
        is_sensitive = any(path.startswith(sensitive) for sensitive in self.sensitive_paths)
        
        # Get security monitor
        security_monitor = get_security_monitor()
        
        # Check if IP is already suspicious
        if security_monitor.is_suspicious_ip(client_ip):
            # Track access from suspicious IP
            security_monitor.record_suspicious_activity(
                activity_type="suspicious_ip_access",
                ip=client_ip,
                details={
                    "path": path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Still allow the request to proceed - we're just monitoring
        
        # Check for suspicious patterns in query parameters and path
        suspicious_matches = []
        
        # Check URL path and query parameters
        full_url = str(request.url)
        for pattern_name, pattern in self.suspicious_patterns:
            # Check if pattern is a compiled regex or a string
            if hasattr(pattern, 'search'):
                # It's a compiled regex
                if pattern.search(full_url):
                    suspicious_matches.append(pattern_name)
            else:
                # It's a string pattern
                import re
                if re.search(pattern, full_url):
                    suspicious_matches.append(pattern_name)
        
        # If suspicious patterns found, log and track
        if suspicious_matches:
            security_monitor.record_suspicious_activity(
                activity_type="suspicious_request_pattern",
                ip=client_ip,
                details={
                    "path": path,
                    "patterns_matched": suspicious_matches,
                    "full_url": full_url,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Allow the request to continue - actual protection is done by other middleware
            # or direct validation in the routes
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Check for authentication failures (401, 403)
            if response.status_code in (401, 403) and is_sensitive:
                # Get auth header if present
                auth_header = request.headers.get("authorization", "")
                auth_type = "bearer" if auth_header.lower().startswith("bearer") else "unknown"
                
                # Record failed authentication
                if response.status_code == 401:
                    # Token verification failure
                    security_monitor.record_token_verification_failure(
                        ip=client_ip,
                        error_type=f"{auth_type}_token_invalid",
                        details={
                            "path": path,
                            "method": request.method,
                            "status_code": response.status_code
                        }
                    )
                else:  # 403 Forbidden
                    # Authorization failure - has token but not allowed
                    security_monitor.record_suspicious_activity(
                        activity_type="authorization_failure",
                        ip=client_ip,
                        details={
                            "path": path,
                            "method": request.method,
                            "auth_type": auth_type,
                            "status_code": response.status_code
                        }
                    )
            
            return response
            
        except Exception as e:
            # Log exceptions as potential security issues if they could 
            # indicate a problem with the application
            logger.error(f"Exception in request processing: {str(e)}")
            
            # Record critical exceptions as security events
            security_monitor.record_suspicious_activity(
                activity_type="request_exception",
                ip=client_ip,
                details={
                    "path": path,
                    "method": request.method,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            
            # Re-raise the exception for the default exception handlers
            raise

def add_middleware(app: FastAPI) -> None:
    """Add all performance middleware to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add security middleware to track security events
    app.add_middleware(
        SecurityMiddleware,
        enabled=True
    )
    
    # Add performance headers to all responses
    app.add_middleware(PerformanceHeadersMiddleware)
    
    # Add request logging (only in debug mode)
    if settings.DEBUG:
        app.add_middleware(
            RequestLoggingMiddleware,
            level="DEBUG",
            log_headers=True
        )
    
    # Add response caching for GET requests
    if getattr(settings, 'CACHE_ENABLED', True):
        app.add_middleware(
            ResponseCachingMiddleware,
            enabled=True,
            default_ttl=settings.CACHE_TTL_MEDIUM,
            exclude_auth=False  # Allow caching authenticated requests
        )
    
    # Add rate limiting
    if getattr(settings, 'RATE_LIMIT_ENABLED', True):
        app.add_middleware(
            RateLimitMiddleware,
            default_limit=settings.RATE_LIMIT_DEFAULT,
            window_seconds=60,
            enabled=True
        )