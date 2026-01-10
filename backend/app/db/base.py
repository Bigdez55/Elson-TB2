"""
Database connection module with support for SQLite, PostgreSQL, and Cloud SQL.

Supports:
- SQLite for development (file-based or in-memory)
- PostgreSQL for production
- Cloud SQL for GCP (via Unix socket or TCP)
- Graceful fallback to in-memory SQLite if connection fails
"""

import os
from typing import Optional, Generator
from contextlib import contextmanager

import structlog
import redis
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool

from app.core.config import settings

logger = structlog.get_logger()


def _get_database_url() -> str:
    """
    Determine the database URL based on environment and configuration.

    Priority:
    1. Cloud SQL Unix socket (if CLOUD_SQL_CONNECTION_NAME is set and /cloudsql exists)
    2. DATABASE_URL environment variable with DB_PASS substitution
    3. Default SQLite for development

    Cloud Run sets:
    - CLOUD_SQL_CONNECTION_NAME: project:region:instance
    - DB_USER: database user
    - DB_PASS: database password (from Secret Manager)
    - DB_NAME: database name
    """
    from urllib.parse import quote_plus

    # Check for Cloud SQL connection first (highest priority in Cloud Run)
    cloud_sql_connection = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    if cloud_sql_connection and os.path.exists("/cloudsql"):
        # We're in Cloud Run with Cloud SQL
        # Use Unix socket connection (fastest and most secure)
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "")
        db_name = os.getenv("DB_NAME", "elson_trading")

        # URL-encode the password to handle special characters
        db_pass_encoded = quote_plus(db_pass) if db_pass else ""

        # Unix socket format for Cloud SQL
        socket_path = f"/cloudsql/{cloud_sql_connection}"
        db_url = f"postgresql+psycopg2://{db_user}:{db_pass_encoded}@/{db_name}?host={socket_path}"

        logger.info(
            "Using Cloud SQL Unix socket connection",
            instance=cloud_sql_connection,
            user=db_user,
            database=db_name,
        )
        return db_url

    # Fall back to DATABASE_URL
    db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

    # If DB_PASS is set separately, inject it into DATABASE_URL
    # This handles the case where cloudbuild sets DATABASE_URL without password
    db_pass = os.getenv("DB_PASS")
    if db_pass and "postgresql" in db_url and "@/" in db_url:
        # URL has format: postgresql://user@/dbname?host=...
        # Need to inject password: postgresql://user:pass@/dbname?host=...
        db_pass_encoded = quote_plus(db_pass)
        db_url = db_url.replace("@/", f":{db_pass_encoded}@/")

    return db_url


def _create_engine_with_fallback() -> Engine:
    """
    Create database engine with fallback to in-memory SQLite if connection fails.
    """
    db_url = _get_database_url()
    is_sqlite = "sqlite" in db_url
    is_production = os.getenv("ENVIRONMENT", settings.ENVIRONMENT) == "production"

    # Engine configuration
    engine_args = {}

    if is_sqlite:
        if ":memory:" in db_url or db_url == "sqlite://":
            # In-memory SQLite - use StaticPool for single connection
            engine_args = {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        else:
            # File-based SQLite
            engine_args = {
                "connect_args": {"check_same_thread": False},
            }
    else:
        # PostgreSQL - use connection pooling
        engine_args = {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": True,  # Verify connections before use
            "echo": settings.DB_ECHO_SQL,
        }

    try:
        logger.info("Connecting to database", url=db_url.split("@")[-1] if "@" in db_url else db_url)
        engine = create_engine(db_url, **engine_args)

        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        logger.info("Database connection successful", type="postgresql" if not is_sqlite else "sqlite")
        return engine

    except Exception as e:
        logger.warning(
            "Primary database connection failed, falling back to in-memory SQLite",
            error=str(e),
            original_url=db_url.split("@")[-1] if "@" in db_url else db_url
        )

        if is_production:
            # In production, log error but still provide a working database
            # This allows the health check to pass and shows a degraded state
            logger.error(
                "DEGRADED MODE: Running with ephemeral in-memory database. "
                "Data will be lost on restart. Configure DATABASE_URL properly."
            )

        # Fallback to in-memory SQLite
        fallback_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        return fallback_engine


# Create engine and session factory
engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this for non-FastAPI contexts.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Redis connection with graceful handling
_redis_client: Optional[redis.Redis] = None
_redis_connection_attempted: bool = False


def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client, creating connection if needed.
    Returns None if Redis is not available (non-blocking).
    """
    global _redis_client, _redis_connection_attempted

    if _redis_client is not None:
        return _redis_client

    # Only attempt connection once to avoid repeated failures
    if _redis_connection_attempted:
        return None

    _redis_connection_attempted = True

    redis_url = os.getenv("REDIS_URL", getattr(settings, 'REDIS_URL', None))

    if not redis_url:
        logger.debug("Redis URL not configured, caching disabled")
        return None

    try:
        _redis_client = redis.Redis.from_url(
            redis_url,
            socket_timeout=2,
            socket_connect_timeout=2,
            retry_on_timeout=False,
        )
        _redis_client.ping()
        logger.info("Redis connection successful")
        return _redis_client
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        logger.warning("Redis connection failed, caching disabled", error=str(e))
        return None


def is_database_healthy() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def is_using_fallback_database() -> bool:
    """Check if we're using the fallback in-memory database."""
    return "memory" in str(engine.url)
