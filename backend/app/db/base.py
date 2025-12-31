from typing import Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis connection
_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client, creating connection if needed."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
        try:
            _redis_client = redis.Redis.from_url(settings.REDIS_URL)
            _redis_client.ping()  # Test connection
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            return None
    return None
