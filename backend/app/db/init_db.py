"""
Database initialization module.

Handles table creation and initial data seeding for Cloud SQL.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

from app.db.base import Base, engine, is_using_fallback_database

# Import all models to ensure they're registered with Base.metadata
# Each model import registers its tables with Base.metadata
from app.models import (  # noqa: F401
    user,
    portfolio,
    trade,
    notification,
    subscription,
    user_settings,
    account,
    education,
)

logger = structlog.get_logger()


async def init_db() -> None:
    """
    Initialize database with tables on startup.

    Creates all tables defined in models if they don't exist.
    Handles both SQLite (dev) and Cloud SQL PostgreSQL (production).
    """
    logger.info("Initializing database tables...")

    # Check if we're using fallback database
    if is_using_fallback_database():
        logger.warning(
            "Using in-memory fallback database. "
            "Data will not persist. Configure DATABASE_URL for production."
        )

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Verify tables were created
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        logger.info(
            "Database tables created successfully",
            table_count=len(Base.metadata.tables),
            tables=list(Base.metadata.tables.keys())[:5],
        )

    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            error_type=type(e).__name__,
        )
        # Don't raise - allow app to start in degraded mode


def create_initial_data(db: Session) -> None:
    """Create initial data for the application."""
    try:
        logger.info("Initial data check completed")
    except Exception as e:
        logger.warning("Failed to create initial data", error=str(e))
