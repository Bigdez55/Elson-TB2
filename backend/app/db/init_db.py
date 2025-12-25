from sqlalchemy.orm import Session

from app.db.base import Base, engine

# Import all models to ensure they're registered with Base
from app.models import user, portfolio, trade, market_data, holding, notification, subscription  # noqa


def init_db() -> None:
    """Initialize database with tables"""
    # Create all tables
    Base.metadata.create_all(bind=engine)


def create_initial_data(db: Session) -> None:
    """Create initial data for the application"""
    # This can be expanded to create default assets, etc.
    pass
