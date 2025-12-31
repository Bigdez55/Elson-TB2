from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration"""

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model parsing
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class TimestampedSchema(BaseSchema):
    """Base schema for models with timestamp fields"""

    created_at: datetime
    updated_at: Optional[datetime] = None
