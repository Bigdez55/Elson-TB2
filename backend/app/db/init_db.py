from sqlalchemy.orm import Session

from app.db.base import Base, engine

# Imports are handled by Base.metadata.create_all which discovers all models


async def init_db() -> None:
    """Initialize database with tables"""
    # Tables are managed by Alembic migrations, not auto-created
    # Use: alembic upgrade head
    pass


def create_initial_data(db: Session) -> None:
    """Create initial data for the application"""
    # This can be expanded to create default assets, etc.
    pass
