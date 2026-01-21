"""Database module - re-exports from base for compatibility."""

from app.db.base import (
    Base,
    SessionLocal,
    engine,
    get_db,
    get_db_session,
    get_redis,
    is_database_healthy,
    is_using_fallback_database,
    update_db_connection_settings,
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_session",
    "get_redis",
    "is_database_healthy",
    "is_using_fallback_database",
    "update_db_connection_settings",
]
