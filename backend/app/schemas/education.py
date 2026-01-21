"""Pydantic schemas for the education system."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ==================== Educational Content Schemas ====================


class EducationalContentBase(BaseModel):
    """Base schema for educational content."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: str  # MODULE, QUIZ, ARTICLE, INTERACTIVE, VIDEO
    level: str  # BEGINNER, INTERMEDIATE, ADVANCED
    completion_requirement: str  # NONE, QUIZ, TIME, INTERACTION
    estimated_minutes: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    importance_level: Optional[int] = Field(None, ge=1, le=5)
    content_path: Optional[str] = None
    associated_quiz_id: Optional[int] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)


class EducationalContentCreate(EducationalContentBase):
    """Schema for creating educational content."""

    pass


class EducationalContentUpdate(BaseModel):
    """Schema for updating educational content."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content_path: Optional[str] = None
    estimated_minutes: Optional[int] = None
    importance_level: Optional[int] = Field(None, ge=1, le=5)


class EducationalContentResponse(EducationalContentBase):
    """Schema for educational content response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== User Progress Schemas ====================


class UserProgressBase(BaseModel):
    """Base schema for user progress."""

    content_id: int
    is_started: bool = False
    is_completed: bool = False
    progress_percent: float = Field(0.0, ge=0, le=100)
    score: Optional[float] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    attempts: int = 0
    time_spent_seconds: int = 0


class UserProgressCreate(BaseModel):
    """Schema for creating user progress (user_id from token)."""

    content_id: int


class UserProgressUpdate(BaseModel):
    """Schema for updating user progress."""

    is_started: Optional[bool] = None
    is_completed: Optional[bool] = None
    progress_percent: Optional[float] = Field(None, ge=0, le=100)
    score: Optional[float] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    attempts: Optional[int] = None
    time_spent_seconds: Optional[int] = None


class UserProgressResponse(UserProgressBase):
    """Schema for user progress response."""

    id: int
    user_id: int
    last_accessed: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Learning Path Schemas ====================


class LearningPathItemBase(BaseModel):
    """Base schema for learning path item."""

    content_id: int
    order: int
    is_required: bool = True


class LearningPathItemResponse(LearningPathItemBase):
    """Schema for learning path item response."""

    id: int
    learning_path_id: int

    class Config:
        from_attributes = True


class LearningPathBase(BaseModel):
    """Base schema for learning path."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None


class LearningPathCreate(LearningPathBase):
    """Schema for creating a learning path."""

    items: List[LearningPathItemBase] = []


class LearningPathResponse(LearningPathBase):
    """Schema for learning path response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[LearningPathItemResponse] = []

    class Config:
        from_attributes = True


# ==================== Trading Permission Schemas ====================


class TradingPermissionBase(BaseModel):
    """Base schema for trading permission."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    permission_type: str  # e.g., 'trade_stocks', 'trade_options', 'margin'
    requires_guardian_approval: bool = True
    min_age: Optional[int] = None
    required_learning_path_id: Optional[int] = None
    required_content_id: Optional[int] = None
    required_score: Optional[float] = Field(None, ge=0, le=100)


class TradingPermissionCreate(TradingPermissionBase):
    """Schema for creating a trading permission."""

    pass


class TradingPermissionResponse(TradingPermissionBase):
    """Schema for trading permission response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== User Permission Schemas ====================


class UserPermissionBase(BaseModel):
    """Base schema for user permission."""

    permission_id: int
    is_granted: bool = False
    override_reason: Optional[str] = None


class UserPermissionCreate(BaseModel):
    """Schema for granting a permission (user_id from token)."""

    permission_id: int
    is_granted: bool = True
    override_reason: Optional[str] = None


class UserPermissionResponse(UserPermissionBase):
    """Schema for user permission response."""

    id: int
    user_id: int
    granted_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    granted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Composite Response Schemas ====================


class ContentWithProgress(EducationalContentResponse):
    """Educational content with user progress."""

    user_progress: Optional[UserProgressResponse] = None


class LearningPathWithProgress(LearningPathResponse):
    """Learning path with user progress."""

    completion_percent: float = 0.0
    items_completed: int = 0
    total_items: int = 0


class PermissionCheckResponse(BaseModel):
    """Response for permission eligibility check."""

    is_granted: bool
    is_eligible: bool
    permission: TradingPermissionResponse
    missing_requirements: List[str] = []
    completed_requirements: List[str] = []
