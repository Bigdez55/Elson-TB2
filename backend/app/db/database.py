"""Database module - re-exports from base for compatibility."""

from app.db.base import (
    engine,
    SessionLocal,
    Base,
    get_db,
    get_redis,
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_redis",
]
