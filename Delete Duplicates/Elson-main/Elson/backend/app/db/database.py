from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional, Any, Dict, Union
from contextlib import contextmanager
import time
import logging
import os
from functools import wraps

import redis
from redis import Redis
from redis.sentinel import Sentinel
from redis.cluster import RedisCluster
from redis.exceptions import RedisError

from ..core.config import settings
from ..core.metrics import record_metric

logger = logging.getLogger(__name__)

# Create database engine with optimized settings
def create_db_engine():
    """Create database engine with configuration based on database type."""
    connect_args = {}
    
    # Add special connection arguments based on database type
    if settings.DATABASE_URL.startswith('postgresql'):
        connect_args = {"options": "-c statement_timeout=30000"}  # 30 second timeout for queries
    elif settings.DATABASE_URL.startswith('sqlite'):
        connect_args = {"check_same_thread": False}
    
    try:
        return create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE if hasattr(settings, 'DB_POOL_RECYCLE') else 3600,
            pool_pre_ping=True,
            echo=settings.DB_ECHO_SQL,
            echo_pool=settings.DEBUG,
            connect_args=connect_args
        )
    except Exception as e:
        logger.error(f"Error creating database engine: {str(e)}")
        
        # Fallback to SQLite for development if configured database fails
        if settings.ENVIRONMENT in ["development", "testing"] and not settings.DATABASE_URL.startswith('sqlite'):
            logger.warning("Falling back to SQLite database for development/testing")
            return create_engine(
                "sqlite:///./fallback.db",
                connect_args={"check_same_thread": False},
                echo=settings.DB_ECHO_SQL
            )
        else:
            # In production, re-raise the error
            raise

engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for declarative models
Base = declarative_base()

# Set up query timing and monitoring
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    if settings.DEBUG:
        logger.debug(f"SQL Query: {statement}")
        logger.debug(f"Parameters: {parameters}")

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop()
    execution_time_ms = total_time * 1000
    
    # Record query execution time
    query_type = statement.split()[0].lower() if statement else "unknown"
    record_metric("db_query_time", execution_time_ms, {"query_type": query_type})
    
    # Log slow queries
    if execution_time_ms > 100:  # Log queries taking more than 100ms
        logger.warning(f"Slow query ({execution_time_ms:.2f}ms): {statement[:200]}...")
        record_metric("db_slow_query", execution_time_ms, {"query_type": query_type})

# FastAPI dependency that yields a database session
def get_db() -> Generator[Session, None, None]:
    """Get a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for database sessions (for scripts and background tasks)
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get a database session using context manager pattern."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Decorator for function that uses a database session
def with_db_session(func):
    """Decorator that provides a db session to the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_context() as db:
            return func(db=db, *args, **kwargs)
    return wrapper

# Helper for optimized bulk operations
def bulk_insert_objects(db: Session, objects: list, chunk_size: int = 1000) -> None:
    """Insert objects in chunks to optimize performance."""
    if not objects:
        return
        
    for i in range(0, len(objects), chunk_size):
        chunk = objects[i:i + chunk_size]
        db.bulk_save_objects(chunk)
        db.flush()

# Redis connection handling
_redis_client: Optional[Union[Redis, RedisCluster]] = None
_redis_mock = None  # Mock Redis for when actual Redis is unavailable

def get_redis_connection(mock_on_failure: bool = True) -> Union[Redis, 'MockRedis', None]:
    """
    Get a Redis connection with proper configuration based on settings.
    
    Args:
        mock_on_failure: If True, return a mock Redis implementation if the 
                         real connection fails. This allows the application to
                         continue functioning with reduced performance.
    
    Returns:
        Redis client, mock client, or None based on configuration and availability
    """
    global _redis_client, _redis_mock
    
    # If the environment is development or testing and USE_MOCK_REDIS is explicitly set,
    # always use the mock implementation regardless of Redis availability
    if settings.ENVIRONMENT in ["development", "testing"] and os.environ.get("USE_MOCK_REDIS", "").lower() in ["1", "true", "yes"]:
        return _get_mock_redis()
    
    # Return existing client if we have one
    if _redis_client is not None:
        return _redis_client
    
    try:
        # Redis Sentinel configuration (high availability)
        if settings.REDIS_SENTINEL_ENABLED:
            logger.info("Connecting to Redis using Sentinel")
            sentinel_hosts = settings.REDIS_SENTINEL_HOSTS
            if isinstance(sentinel_hosts, str):
                sentinel_hosts = sentinel_hosts.split(',')
                
            # Parse host:port format
            sentinel_instances = []
            for host in sentinel_hosts:
                if isinstance(host, str) and ':' in host:
                    hostname, port = host.split(':')
                    sentinel_instances.append((hostname, int(port)))
                else:
                    logger.warning(f"Invalid sentinel host format: {host}")
            
            if not sentinel_instances:
                raise ValueError("No valid sentinel hosts found")
                
            sentinel = Sentinel(
                sentinel_instances,
                socket_timeout=settings.REDIS_TIMEOUT,
                password=settings.REDIS_PASSWORD,
                db=0
            )
            _redis_client = sentinel.master_for(
                settings.REDIS_SENTINEL_MASTER,
                socket_timeout=settings.REDIS_TIMEOUT,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Connected to Redis Sentinel master: {settings.REDIS_SENTINEL_MASTER}")
            
        # Redis Cluster configuration (horizontal scaling)
        elif settings.REDIS_CLUSTER_ENABLED and hasattr(settings, 'REDIS_CLUSTER_NODES'):
            logger.info("Connecting to Redis Cluster")
            cluster_nodes = settings.REDIS_CLUSTER_NODES
            if isinstance(cluster_nodes, str):
                cluster_nodes = cluster_nodes.split(',')
                
            # Parse nodes
            startup_nodes = []
            for node in cluster_nodes:
                if isinstance(node, str) and ':' in node:
                    hostname, port = node.split(':')
                    startup_nodes.append({"host": hostname, "port": int(port)})
                else:
                    logger.warning(f"Invalid cluster node format: {node}")
            
            if not startup_nodes:
                raise ValueError("No valid cluster nodes found")
                
            _redis_client = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                socket_timeout=settings.REDIS_TIMEOUT,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            # Test connection
            _redis_client.ping()
            logger.info("Connected to Redis Cluster")
            
        # Standard Redis connection
        else:
            logger.info(f"Connecting to Redis: {settings.REDIS_URL}")
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                decode_responses=False
            )
            # Test connection
            _redis_client.ping()
            logger.info("Connected to Redis successfully")
            
        # Set up metrics for Redis operations
        record_metric("redis_connection", 1, {"status": "success"})
        return _redis_client
        
    except (RedisError, ValueError, ConnectionError) as e:
        logger.warning(f"Failed to connect to Redis: {str(e)}")
        record_metric("redis_connection", 1, {"status": "failure"})
        
        # Return mock Redis implementation if requested and allowed in this environment
        if mock_on_failure and settings.ENVIRONMENT in ["development", "testing"]:
            return _get_mock_redis()
            
        # For production, don't use mock if Redis is required
        if settings.ENVIRONMENT == "production":
            logger.error("Redis connection required in production but unavailable")
            
        # Return None to indicate Redis is unavailable
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {str(e)}")
        record_metric("redis_connection", 1, {"status": "failure"})
        
        # In development, still use mock Redis
        if mock_on_failure and settings.ENVIRONMENT in ["development", "testing"]:
            return _get_mock_redis(reason="unexpected_error")
            
        return None

def _get_mock_redis(reason: str = "connection_failure") -> 'MockRedis':
    """Get the mock Redis implementation."""
    global _redis_mock
    
    if _redis_mock is None:
        try:
            # First try external mockredis package
            from mockredis import MockRedis
            logger.info("Using mockredis package for Redis mock")
        except ImportError:
            # Fall back to our built-in implementation
            from ..core.mock_redis import MockRedis
            logger.info("Using built-in MockRedis implementation")
                
        _redis_mock = MockRedis()
        
        # Record a metric that we're using the mock
        record_metric("redis_mock_usage", 1, {"environment": settings.ENVIRONMENT, "reason": reason})
    
    return _redis_mock

def get_redis() -> Union[Redis, RedisCluster]:
    """FastAPI dependency for Redis connections."""
    return get_redis_connection()

@contextmanager
def get_redis_context() -> Generator[Optional[Union[Redis, RedisCluster]], None, None]:
    """
    Context manager for Redis connections.
    
    Handles the case where Redis might be unavailable.
    """
    redis_conn = get_redis_connection(mock_on_failure=True)
    try:
        yield redis_conn
    except RedisError as e:
        logger.error(f"Redis error: {str(e)}")
        record_metric("redis_error", 1, {"error_type": type(e).__name__})
        # Don't raise, return None
        yield None
    except Exception as e:
        logger.error(f"Unexpected Redis error: {str(e)}")
        record_metric("redis_error", 1, {"error_type": "unexpected"})
        yield None

# Database initialization function
def init_db() -> None:
    """Initialize the database by creating all tables."""
    try:
        # Import all models here to ensure they are registered
        from ..models import user, portfolio, trade, account, notification, education, subscription
        
        # Create tables
        logger.info(f"Creating database tables using {settings.DATABASE_URL}")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    # Initialize Redis connection
    try:
        redis_client = get_redis_connection(mock_on_failure=True)
        if redis_client is None:
            logger.warning("Redis unavailable but continuing with reduced functionality")
        else:
            logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Could not initialize Redis connection: {str(e)}")
        logger.warning("Application will start, but Redis-dependent features may not work properly.")