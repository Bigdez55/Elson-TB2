"""Schemas for education-related models.

This module contains Pydantic models for educational content, progress tracking,
and permissions related to trading based on educational requirements.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.models.education import ContentLevel, ContentType, CompletionRequirement


class ContentBase(BaseModel):
    """Base schema for educational content."""
    
    title: str
    slug: str
    description: Optional[str] = None
    content_type: ContentType
    level: ContentLevel
    completion_requirement: CompletionRequirement
    estimated_minutes: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    importance_level: Optional[int] = Field(None, ge=1, le=10)
    content_path: Optional[str] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('importance_level')
    def validate_importance(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Importance level must be between 1 and 10')
        return v


class ContentCreate(ContentBase):
    """Schema for creating new educational content."""
    pass


class ContentUpdate(BaseModel):
    """Schema for updating existing educational content."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[ContentLevel] = None
    completion_requirement: Optional[CompletionRequirement] = None
    estimated_minutes: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    importance_level: Optional[int] = Field(None, ge=1, le=10)
    content_path: Optional[str] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('importance_level')
    def validate_importance(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Importance level must be between 1 and 10')
        return v


class ContentResponse(ContentBase):
    """Schema for retrieving educational content."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    associated_quiz_id: Optional[int] = None
    prerequisites: List[int] = []
    
    class Config:
        orm_mode = True


class ProgressBase(BaseModel):
    """Base schema for user progress."""
    
    user_id: int
    content_id: int
    is_started: bool = False
    is_completed: bool = False
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    score: Optional[float] = None
    passed: Optional[bool] = None
    attempts: int = 0
    time_spent_seconds: int = 0


class ProgressCreate(ProgressBase):
    """Schema for creating new progress record."""
    pass


class ProgressUpdate(BaseModel):
    """Schema for updating progress."""
    
    is_started: Optional[bool] = None
    is_completed: Optional[bool] = None
    progress_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    score: Optional[float] = None
    passed: Optional[bool] = None
    attempts: Optional[int] = None
    time_spent_seconds: Optional[int] = None


class ProgressResponse(ProgressBase):
    """Schema for retrieving progress."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    content: ContentResponse
    
    class Config:
        orm_mode = True


class LearningPathBase(BaseModel):
    """Base schema for learning paths."""
    
    title: str
    slug: str
    description: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None


class LearningPathCreate(LearningPathBase):
    """Schema for creating new learning paths."""
    pass


class LearningPathUpdate(BaseModel):
    """Schema for updating learning paths."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None


class LearningPathItemBase(BaseModel):
    """Base schema for learning path items."""
    
    content_id: int
    order: int
    is_required: bool = True


class LearningPathItemCreate(LearningPathItemBase):
    """Schema for creating learning path items."""
    pass


class LearningPathItemUpdate(BaseModel):
    """Schema for updating learning path items."""
    
    order: Optional[int] = None
    is_required: Optional[bool] = None


class LearningPathItemResponse(LearningPathItemBase):
    """Schema for retrieving learning path items."""
    
    id: int
    content: ContentResponse
    
    class Config:
        orm_mode = True


class LearningPathResponse(LearningPathBase):
    """Schema for retrieving learning paths."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    content_items: List[LearningPathItemResponse] = []
    
    class Config:
        orm_mode = True


class TradingPermissionBase(BaseModel):
    """Base schema for trading permissions."""
    
    name: str
    description: Optional[str] = None
    permission_type: str
    requires_guardian_approval: bool = True
    min_age: Optional[int] = None
    required_learning_path_id: Optional[int] = None
    required_content_id: Optional[int] = None
    required_score: Optional[float] = None


class TradingPermissionCreate(TradingPermissionBase):
    """Schema for creating trading permissions."""
    pass


class TradingPermissionUpdate(BaseModel):
    """Schema for updating trading permissions."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    requires_guardian_approval: Optional[bool] = None
    min_age: Optional[int] = None
    required_learning_path_id: Optional[int] = None
    required_content_id: Optional[int] = None
    required_score: Optional[float] = None


class TradingPermissionResponse(TradingPermissionBase):
    """Schema for retrieving trading permissions."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    required_learning_path: Optional[LearningPathBase] = None
    required_content: Optional[ContentBase] = None
    
    class Config:
        orm_mode = True


class UserPermissionBase(BaseModel):
    """Base schema for user permissions."""
    
    user_id: int
    permission_id: int
    is_granted: bool = False
    granted_by_user_id: Optional[int] = None
    override_reason: Optional[str] = None


class UserPermissionCreate(UserPermissionBase):
    """Schema for creating user permissions."""
    pass


class UserPermissionUpdate(BaseModel):
    """Schema for updating user permissions."""
    
    is_granted: Optional[bool] = None
    granted_by_user_id: Optional[int] = None
    override_reason: Optional[str] = None


class UserPermissionResponse(UserPermissionBase):
    """Schema for retrieving user permissions."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    granted_at: Optional[datetime] = None
    permission: TradingPermissionResponse
    
    class Config:
        orm_mode = True


class QuizSubmission(BaseModel):
    """Schema for quiz submissions."""
    
    content_id: int
    answers: Dict[str, Any]  # Question ID to answer mapping
    time_spent_seconds: int


class UserProgressSummary(BaseModel):
    """Summary of a user's educational progress."""
    
    total_content_count: int
    completed_count: int
    started_count: int
    completion_percentage: float
    total_time_spent_minutes: int
    learning_paths_progress: Dict[str, float]  # Path slug to completion percentage
    recent_activities: List[ProgressResponse]