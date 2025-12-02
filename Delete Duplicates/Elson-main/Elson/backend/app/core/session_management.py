"""
Distributed session management using Redis for horizontal scaling.
This module provides tools for maintaining user sessions across multiple
application instances.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from fastapi import Depends
from redis import Redis

from app.core.config import settings
from app.core import metrics
from app.db.database import get_redis


class DistributedSessionManager:
    """
    Session management for horizontal scaling using Redis as a shared storage.
    Maintains session state across multiple application instances.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:"
        self.expiry = settings.SESSION_EXPIRY_MINUTES * 60  # in seconds
        
        # Register metrics
        metrics.register_counter(
            "session_operations_total", 
            "Total number of session operations",
            ["operation"]
        )
    
    def create_session(self, user_id: str) -> str:
        """Create a new session for a user and return the session ID"""
        session_id = str(uuid.uuid4())
        session_key = f"{self.prefix}{session_id}"
        
        # Store basic session data
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "ip_address": None,
            "user_agent": None,
        }
        
        # Store in Redis
        self.redis.setex(
            session_key,
            self.expiry,
            json.dumps(session_data)
        )
        
        # Track sessions by user ID for lookup
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis.sadd(user_sessions_key, session_id)
        self.redis.expire(user_sessions_key, self.expiry)
        
        metrics.increment_counter("session_operations_total", {"operation": "create"})
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for a given session ID"""
        session_key = f"{self.prefix}{session_id}"
        data = self.redis.get(session_key)
        
        if not data:
            metrics.increment_counter("session_operations_total", {"operation": "get_miss"})
            return None
        
        # Refresh expiry
        self.redis.expire(session_key, self.expiry)
        
        # Update last active
        session_data = json.loads(data)
        session_data["last_active"] = datetime.utcnow().isoformat()
        self.redis.setex(
            session_key,
            self.expiry,
            json.dumps(session_data)
        )
        
        metrics.increment_counter("session_operations_total", {"operation": "get_hit"})
        return session_data
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data for a given session ID"""
        session_key = f"{self.prefix}{session_id}"
        existing_data = self.redis.get(session_key)
        
        if not existing_data:
            metrics.increment_counter("session_operations_total", {"operation": "update_miss"})
            return False
        
        # Merge existing data with new data
        session_data = json.loads(existing_data)
        session_data.update(data)
        session_data["last_active"] = datetime.utcnow().isoformat()
        
        # Store updated data
        self.redis.setex(
            session_key,
            self.expiry,
            json.dumps(session_data)
        )
        
        metrics.increment_counter("session_operations_total", {"operation": "update"})
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.prefix}{session_id}"
        data = self.redis.get(session_key)
        
        if not data:
            metrics.increment_counter("session_operations_total", {"operation": "delete_miss"})
            return False
        
        # Get user ID to remove from user sessions set
        session_data = json.loads(data)
        user_id = session_data.get("user_id")
        
        # Remove from Redis
        self.redis.delete(session_key)
        
        # Remove from user sessions set
        if user_id:
            user_sessions_key = f"user_sessions:{user_id}"
            self.redis.srem(user_sessions_key, session_id)
        
        metrics.increment_counter("session_operations_total", {"operation": "delete"})
        return True
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        user_sessions_key = f"user_sessions:{user_id}"
        sessions = self.redis.smembers(user_sessions_key)
        
        # Convert bytes to str
        session_ids = [s.decode("utf-8") if isinstance(s, bytes) else s for s in sessions]
        
        metrics.increment_counter("session_operations_total", {"operation": "get_user_sessions"})
        return session_ids
    
    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user, returns count of deleted sessions"""
        user_sessions_key = f"user_sessions:{user_id}"
        sessions = self.redis.smembers(user_sessions_key)
        
        # Convert bytes to str
        session_ids = [s.decode("utf-8") if isinstance(s, bytes) else s for s in sessions]
        
        # Delete each session
        count = 0
        for session_id in session_ids:
            session_key = f"{self.prefix}{session_id}"
            if self.redis.delete(session_key):
                count += 1
        
        # Delete the set itself
        self.redis.delete(user_sessions_key)
        
        metrics.increment_counter("session_operations_total", {"operation": "delete_user_sessions"})
        return count


# Dependency for FastAPI
async def get_session_manager(
    redis: Redis = Depends(get_redis)
) -> DistributedSessionManager:
    """FastAPI dependency for getting the session manager"""
    return DistributedSessionManager(redis)


class DistributedTokenStore:
    """
    Token management for horizontal scaling.
    Handles token revocation across multiple application instances.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "revoked_token:"
    
    def revoke_token(self, token_id: str, expires_in: int) -> None:
        """Revoke a token by adding it to the revoked tokens list"""
        key = f"{self.prefix}{token_id}"
        self.redis.setex(key, expires_in, "1")
    
    def is_token_revoked(self, token_id: str) -> bool:
        """Check if a token has been revoked"""
        key = f"{self.prefix}{token_id}"
        return bool(self.redis.exists(key))


# Dependency for FastAPI
async def get_token_store(
    redis: Redis = Depends(get_redis)
) -> DistributedTokenStore:
    """FastAPI dependency for getting the token store"""
    return DistributedTokenStore(redis)


class DistributedLock:
    """
    Distributed locking mechanism using Redis.
    Ensures that only one instance can execute a critical section at a time.
    """
    
    def __init__(self, redis_client: Redis, lock_name: str, timeout: int = 10):
        self.redis = redis_client
        self.lock_name = lock_name
        self.lock_key = f"lock:{lock_name}"
        self.lock_id = str(uuid.uuid4())
        self.timeout = timeout
    
    async def __aenter__(self):
        """Acquire the lock"""
        # Use NX to only set if the key doesn't exist
        acquired = self.redis.set(
            self.lock_key, 
            self.lock_id, 
            ex=self.timeout, 
            nx=True
        )
        
        if not acquired:
            raise LockAcquisitionError(f"Could not acquire lock: {self.lock_name}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release the lock"""
        # Only release if the lock is still ours
        pipe = self.redis.pipeline()
        try:
            pipe.watch(self.lock_key)
            current_value = pipe.get(self.lock_key)
            
            if current_value and current_value.decode("utf-8") == self.lock_id:
                pipe.multi()
                pipe.delete(self.lock_key)
                pipe.execute()
        finally:
            pipe.reset()


class LockAcquisitionError(Exception):
    """Raised when a lock cannot be acquired"""
    pass


# Factory function for creating locks
def create_distributed_lock(
    redis_client: Redis, 
    lock_name: str, 
    timeout: int = 10
) -> DistributedLock:
    """Create a distributed lock"""
    return DistributedLock(redis_client, lock_name, timeout)