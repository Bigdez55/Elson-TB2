"""Mock Redis implementation for development and testing.

This module provides a simple in-memory implementation of Redis that can be
used when a real Redis instance is not available.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MockRedis:
    """
    Simple in-memory mock of Redis for development and testing.
    
    This implementation provides basic Redis functionality for the most commonly
    used commands. It is not intended to be a complete Redis implementation.
    """
    
    def __init__(self):
        """Initialize the mock Redis instance."""
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
        logger.info("Initialized mock Redis instance")
    
    def ping(self) -> bool:
        """Ping the Redis instance."""
        return True
    
    def _check_expiry(self, key: str) -> bool:
        """Check if a key has expired and remove it if so."""
        if key in self._expiry and time.time() > self._expiry[key]:
            with self._lock:
                if key in self._expiry and time.time() > self._expiry[key]:
                    del self._data[key]
                    del self._expiry[key]
                    return True
        return False
    
    def set(self, key: str, value: Any, ex: Optional[int] = None, 
            px: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """Set a key-value pair."""
        with self._lock:
            # Check if the key exists for nx/xx
            key_exists = key in self._data and not self._check_expiry(key)
            
            if nx and key_exists:
                return False
            if xx and not key_exists:
                return False
            
            # Set the value
            self._data[key] = value
            
            # Set expiry if provided
            if ex is not None:
                self._expiry[key] = time.time() + ex
            elif px is not None:
                self._expiry[key] = time.time() + (px / 1000.0)
            elif key in self._expiry:
                del self._expiry[key]
                
            return True
    
    def get(self, key: str) -> Any:
        """Get a value by key."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return None
            return self._data[key]
    
    def delete(self, key: str) -> int:
        """Delete a key."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                if key in self._expiry:
                    del self._expiry[key]
                return 1
            return 0
    
    def exists(self, key: str) -> int:
        """Check if a key exists."""
        with self._lock:
            if key in self._data and not self._check_expiry(key):
                return 1
            return 0
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        import fnmatch
        with self._lock:
            # Remove expired keys
            for key in list(self._data.keys()):
                self._check_expiry(key)
            
            # Match pattern
            if pattern == "*":
                return list(self._data.keys())
            else:
                return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]
    
    def expire(self, key: str, seconds: int) -> int:
        """Set a key's expiry in seconds."""
        with self._lock:
            if key in self._data and not self._check_expiry(key):
                self._expiry[key] = time.time() + seconds
                return 1
            return 0
    
    def ttl(self, key: str) -> int:
        """Get the time-to-live for a key."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return -2
            if key not in self._expiry:
                return -1
            ttl = int(self._expiry[key] - time.time())
            return max(0, ttl)
    
    def hset(self, key: str, field: str, value: Any) -> int:
        """Set a hash field."""
        with self._lock:
            self._check_expiry(key)
            
            if key not in self._data:
                self._data[key] = {}
            
            if not isinstance(self._data[key], dict):
                raise Exception(f"Key {key} is not a hash")
            
            is_new = field not in self._data[key]
            self._data[key][field] = value
            return 1 if is_new else 0
    
    def hget(self, key: str, field: str) -> Any:
        """Get a hash field."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return None
            
            if not isinstance(self._data[key], dict):
                raise Exception(f"Key {key} is not a hash")
            
            return self._data[key].get(field)
    
    def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return {}
            
            if not isinstance(self._data[key], dict):
                raise Exception(f"Key {key} is not a hash")
            
            return self._data[key].copy()
    
    def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        count = 0
        with self._lock:
            if key in self._data and not self._check_expiry(key):
                if not isinstance(self._data[key], dict):
                    raise Exception(f"Key {key} is not a hash")
                
                for field in fields:
                    if field in self._data[key]:
                        del self._data[key][field]
                        count += 1
        return count
    
    def hexists(self, key: str, field: str) -> int:
        """Check if a hash field exists."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return 0
            
            if not isinstance(self._data[key], dict):
                raise Exception(f"Key {key} is not a hash")
            
            return 1 if field in self._data[key] else 0
    
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to the beginning of a list."""
        with self._lock:
            self._check_expiry(key)
            
            if key not in self._data:
                self._data[key] = []
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            for value in values:
                self._data[key].insert(0, value)
            
            return len(self._data[key])
    
    def rpush(self, key: str, *values: Any) -> int:
        """Push values to the end of a list."""
        with self._lock:
            self._check_expiry(key)
            
            if key not in self._data:
                self._data[key] = []
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            for value in values:
                self._data[key].append(value)
            
            return len(self._data[key])
    
    def lpop(self, key: str) -> Any:
        """Pop a value from the beginning of a list."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return None
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            if not self._data[key]:
                return None
            
            return self._data[key].pop(0)
    
    def rpop(self, key: str) -> Any:
        """Pop a value from the end of a list."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return None
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            if not self._data[key]:
                return None
            
            return self._data[key].pop()
    
    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get a range of values from a list."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return []
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            if end == -1:
                end = len(self._data[key])
            else:
                end += 1  # Make it inclusive like Redis
                
            return self._data[key][start:end]
    
    def llen(self, key: str) -> int:
        """Get the length of a list."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return 0
            
            if not isinstance(self._data[key], list):
                raise Exception(f"Key {key} is not a list")
            
            return len(self._data[key])
    
    def sadd(self, key: str, *values: Any) -> int:
        """Add values to a set."""
        count = 0
        with self._lock:
            self._check_expiry(key)
            
            if key not in self._data:
                self._data[key] = set()
            
            if not isinstance(self._data[key], set):
                raise Exception(f"Key {key} is not a set")
            
            for value in values:
                if value not in self._data[key]:
                    self._data[key].add(value)
                    count += 1
            
            return count
    
    def smembers(self, key: str) -> Set[Any]:
        """Get all members of a set."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return set()
            
            if not isinstance(self._data[key], set):
                raise Exception(f"Key {key} is not a set")
            
            return self._data[key].copy()
    
    def srem(self, key: str, *values: Any) -> int:
        """Remove values from a set."""
        count = 0
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return 0
            
            if not isinstance(self._data[key], set):
                raise Exception(f"Key {key} is not a set")
            
            for value in values:
                if value in self._data[key]:
                    self._data[key].remove(value)
                    count += 1
            
            return count
    
    def sismember(self, key: str, value: Any) -> int:
        """Check if a value is a member of a set."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return 0
            
            if not isinstance(self._data[key], set):
                raise Exception(f"Key {key} is not a set")
            
            return 1 if value in self._data[key] else 0
    
    def scard(self, key: str) -> int:
        """Get the cardinality of a set."""
        with self._lock:
            if key not in self._data or self._check_expiry(key):
                return 0
            
            if not isinstance(self._data[key], set):
                raise Exception(f"Key {key} is not a set")
            
            return len(self._data[key])
    
    def flushall(self) -> bool:
        """Clear all data."""
        with self._lock:
            self._data.clear()
            self._expiry.clear()
            return True
    
    # Pipeline implementation
    def pipeline(self) -> 'MockRedisPipeline':
        """Get a pipeline for executing multiple commands."""
        return MockRedisPipeline(self)


class MockRedisPipeline:
    """Mock implementation of a Redis pipeline."""
    
    def __init__(self, client: MockRedis):
        """Initialize the pipeline."""
        self.client = client
        self.commands = []
        
    def execute(self) -> List[Any]:
        """Execute the pipeline."""
        results = []
        for cmd, args, kwargs in self.commands:
            method = getattr(self.client, cmd)
            results.append(method(*args, **kwargs))
        return results
    
    def __getattr__(self, name: str):
        """Add a command to the pipeline."""
        def method(*args, **kwargs):
            self.commands.append((name, args, kwargs))
            return self
        return method