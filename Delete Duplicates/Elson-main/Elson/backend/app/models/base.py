# Import Base from database.py to avoid circular imports
from ..db.database import Base

# This file exists to provide a common import point for all models 
# that need to inherit from the SQLAlchemy Base class