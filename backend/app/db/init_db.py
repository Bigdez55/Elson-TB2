from sqlalchemy.orm import Session
import structlog

from app.db.base import Base, engine

# Import all models to ensure they're registered with Base.metadata
from app.models import user, portfolio, trade, notification, subscription, user_settings  # noqa

logger = structlog.get_logger()


async def init_db() -> None:
    """Initialize database with tables on startup"""
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def create_initial_data(db: Session) -> None:
    """Create initial data for the application"""
    # This can be expanded to create default assets, etc.
    pass
