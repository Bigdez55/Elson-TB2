"""Caching utilities for optimizing database and API performance.

This module provides a Redis-based caching system with fallback to in-memory
caching when Redis is not available.
"""

import json
import logging
import time
import pickle
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast
from functools import wraps
import hashlib
import redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.metrics import record_metric

logger = logging.getLogger(__name__)

# Type variable for generic function return
T = TypeVar('T')

# Initialize Redis client
try:
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        socket_timeout=1.0,
        socket_connect_timeout=1.0,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connection established successfully")
except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
    REDIS_AVAILABLE = False
    logger.warning(f"Redis connection failed: {e}. Using in-memory cache fallback.")
    
# In-memory cache as fallback
MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from the arguments.
    
    Args:
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key
        
    Returns:
        A string hash key
    """
    # Sort kwargs for consistent ordering
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    
    # Create hash of the combined string
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """Set a value in the cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 300s/5min)
        
    Returns:
        True if successful, False otherwise
    """
    start_time = time.time()
    success = False
    
    try:
        if REDIS_AVAILABLE:
            # Use Redis
            serialized = pickle.dumps(value)
            success = redis_client.setex(key, ttl, serialized)
        else:
            # Use in-memory cache
            MEMORY_CACHE[key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            success = True
            
        # Record metrics
        elapsed_ms = (time.time() - start_time) * 1000
        cache_type = "redis" if REDIS_AVAILABLE else "memory"
        record_metric("cache_set_time", elapsed_ms, {"cache_type": cache_type})
        
        return bool(success)
    except Exception as e:
        logger.error(f"Error setting cache key {key}: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """Get a value from the cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    start_time = time.time()
    cache_type = "redis" if REDIS_AVAILABLE else "memory"
    
    try:
        if REDIS_AVAILABLE:
            # Use Redis
            cached = redis_client.get(key)
            if cached:
                value = pickle.loads(cached)
                record_metric("cache_hit", 1, {"cache_type": cache_type})
            else:
                value = None
                record_metric("cache_miss", 1, {"cache_type": cache_type})
        else:
            # Use in-memory cache
            cached_data = MEMORY_CACHE.get(key)
            if cached_data and cached_data.get("expires", 0) > time.time():
                value = cached_data["value"]
                record_metric("cache_hit", 1, {"cache_type": cache_type})
            else:
                if cached_data:
                    # Expired data, clean up
                    del MEMORY_CACHE[key]
                value = None
                record_metric("cache_miss", 1, {"cache_type": cache_type})
        
        # Record timing
        elapsed_ms = (time.time() - start_time) * 1000
        record_metric("cache_get_time", elapsed_ms, {"cache_type": cache_type})
        
        return value
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {e}")
        record_metric("cache_error", 1, {"cache_type": cache_type, "error": str(e)[:100]})
        return None


def delete_cache(key: str) -> bool:
    """Delete a value from the cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if REDIS_AVAILABLE:
            # Use Redis
            success = redis_client.delete(key)
        else:
            # Use in-memory cache
            if key in MEMORY_CACHE:
                del MEMORY_CACHE[key]
                success = True
            else:
                success = False
        
        return bool(success)
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {e}")
        return False


def clear_pattern(pattern: str) -> int:
    """Clear all cache keys matching a pattern.
    
    Args:
        pattern: Key pattern to match (e.g., "user:*")
        
    Returns:
        Number of keys cleared
    """
    try:
        if REDIS_AVAILABLE:
            # Use Redis scan_iter to efficiently find matches
            matching_keys = []
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor, f"{pattern}", 100)
                matching_keys.extend(keys)
                if cursor == 0:
                    break
            
            # Delete matches if any found
            if matching_keys:
                deleted = redis_client.delete(*matching_keys)
                return deleted
            return 0
        else:
            # For in-memory cache, manually check all keys
            keys_to_delete = [k for k in MEMORY_CACHE.keys() if pattern in k]
            for k in keys_to_delete:
                del MEMORY_CACHE[k]
            return len(keys_to_delete)
    except Exception as e:
        logger.error(f"Error clearing cache with pattern {pattern}: {e}")
        return 0


def cached(ttl: int = 300, prefix: str = ""):
    """Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (default: 300s/5min)
        prefix: Optional prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            func_name = func.__name__
            key = f"{prefix}:{func_name}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = get_cache(key)
            if cached_value is not None:
                return cast(T, cached_value)
            
            # Not in cache, execute function
            result = func(*args, **kwargs)
            
            # Store in cache (skip None results)
            if result is not None:
                set_cache(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_prefix(prefix: str) -> int:
    """Invalidate all cache entries with a given prefix.
    
    Args:
        prefix: The prefix to match
        
    Returns:
        Number of cache entries invalidated
    """
    return clear_pattern(f"{prefix}:*")


def clear_all_cache() -> bool:
    """Clear the entire cache.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if REDIS_AVAILABLE:
            # Use Redis
            redis_client.flushdb()
        else:
            # Use in-memory cache
            MEMORY_CACHE.clear()
        
        return True
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
        return False


def cleanup_expired_memory_cache() -> int:
    """Clean up expired entries in the in-memory cache.
    
    Returns:
        Number of entries removed
    """
    if REDIS_AVAILABLE:
        # No need for cleanup with Redis (it handles TTL internally)
        return 0
    
    try:
        now = time.time()
        keys_to_delete = [
            k for k, v in MEMORY_CACHE.items() 
            if v.get("expires", 0) < now
        ]
        
        for k in keys_to_delete:
            del MEMORY_CACHE[k]
            
        return len(keys_to_delete)
    except Exception as e:
        logger.error(f"Error cleaning up memory cache: {e}")
        return 0


# Run periodic cleanup of in-memory cache for long-running processes
import threading
def _periodic_cleanup():
    while True:
        if not REDIS_AVAILABLE:
            count = cleanup_expired_memory_cache()
            if count > 0:
                logger.debug(f"Cleaned up {count} expired cache entries")
        time.sleep(60)  # Run every minute

# Only start background thread if not using Redis
if not REDIS_AVAILABLE:
    cleanup_thread = threading.Thread(target=_periodic_cleanup, daemon=True)
    cleanup_thread.start()