"""Education models for the Elson platform.

This module defines database models for educational content and user progress tracking.
These models support the educational requirements feature for minor accounts.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class ContentLevel(enum.Enum):
    """Difficulty levels for educational content."""
    
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentType(enum.Enum):
    """Types of educational content."""
    
    MODULE = "module"  # Standard learning module
    QUIZ = "quiz"      # Assessment quiz
    ARTICLE = "article"  # Standalone article
    INTERACTIVE = "interactive"  # Interactive learning experience
    VIDEO = "video"    # Video content


class CompletionRequirement(enum.Enum):
    """Types of completion requirements for educational content."""
    
    NONE = "none"  # No completion requirement (just viewing is enough)
    QUIZ = "quiz"  # Must pass associated quiz
    TIME = "time"  # Must spend minimum time on content
    INTERACTION = "interaction"  # Must complete interactive elements


# Association table for prerequisites
content_prerequisites = Table(
    'content_prerequisites',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('educational_content.id'), primary_key=True),
    Column('prerequisite_id', Integer, ForeignKey('educational_content.id'), primary_key=True)
)


class EducationalContent(Base):
    """Model for educational content items."""
    
    __tablename__ = "educational_content"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    content_type = Column(Enum(ContentType), nullable=False)
    level = Column(Enum(ContentLevel), nullable=False, default=ContentLevel.BEGINNER)
    completion_requirement = Column(Enum(CompletionRequirement), nullable=False, default=CompletionRequirement.NONE)
    
    # Content metadata
    estimated_minutes = Column(Integer, nullable=True)  # Estimated time to complete
    min_age = Column(Integer, nullable=True)  # Minimum recommended age
    max_age = Column(Integer, nullable=True)  # Maximum recommended age
    importance_level = Column(Integer, nullable=True)  # 1-10 scale of importance
    
    # Content location
    content_path = Column(String(255), nullable=True)  # Path to content file/component
    
    # Associated quiz if any
    associated_quiz_id = Column(Integer, ForeignKey('educational_content.id'), nullable=True)
    associated_quiz = relationship("EducationalContent", remote_side=[id], 
                                   foreign_keys=[associated_quiz_id], 
                                   backref="module")
    
    # Quiz-specific fields
    passing_score = Column(Float, nullable=True)  # Required passing score (percentage)
    
    # Prerequisites (what content must be completed before this one)
    prerequisites = relationship(
        "EducationalContent",
        secondary=content_prerequisites,
        primaryjoin=(content_prerequisites.c.content_id == id),
        secondaryjoin=(content_prerequisites.c.prerequisite_id == id),
        backref="unlocks"
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EducationalContent {self.title} ({self.content_type.value})>"


class UserProgress(Base):
    """Model for tracking a user's progress through educational content."""
    
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("educational_content.id"), nullable=False)
    
    # Progress state
    is_started = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    progress_percent = Column(Float, default=0.0)  # 0-100
    
    # For quizzes
    score = Column(Float, nullable=True)  # Overall quiz score
    passed = Column(Boolean, nullable=True)  # Whether quiz was passed
    attempts = Column(Integer, default=0)  # Number of attempts
    
    # Usage metrics
    last_accessed = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, default=0)  # Total time spent
    
    # Relationships
    user = relationship("User", back_populates="educational_progress")
    content = relationship("EducationalContent")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    class Meta:
        # Ensure users only have one progress record per content item
        __table_args__ = (
            {"unique_constraint": ("user_id", "content_id")},
        )
    
    def __repr__(self):
        status = "completed" if self.is_completed else f"in-progress ({self.progress_percent}%)"
        return f"<UserProgress {self.user_id} - {self.content_id}: {status}>"


class LearningPath(Base):
    """Model for defining curated learning paths (sequences of content)."""
    
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Age appropriateness
    min_age = Column(Integer, nullable=True)  # Minimum recommended age
    max_age = Column(Integer, nullable=True)  # Maximum recommended age
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    content_items = relationship("LearningPathItem", back_populates="learning_path", 
                                order_by="LearningPathItem.order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LearningPath {self.title}>"


class LearningPathItem(Base):
    """Model for items within a learning path."""
    
    __tablename__ = "learning_path_items"
    
    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("educational_content.id"), nullable=False)
    order = Column(Integer, nullable=False)  # Order within the learning path
    is_required = Column(Boolean, default=True)  # Whether this item is required for completion
    
    # Relationships
    learning_path = relationship("LearningPath", back_populates="content_items")
    content = relationship("EducationalContent")
    
    class Meta:
        # Ensure each content appears only once per learning path
        __table_args__ = (
            {"unique_constraint": ("learning_path_id", "content_id")},
        )
        
    def __repr__(self):
        required = "required" if self.is_required else "optional"
        return f"<LearningPathItem {self.order}: content_id={self.content_id} ({required})>"


class TradingPermission(Base):
    """Model for defining trading permissions based on educational achievement."""
    
    __tablename__ = "trading_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permission details
    permission_type = Column(String(50), nullable=False)  # e.g., 'trade_stocks', 'trade_options'
    requires_guardian_approval = Column(Boolean, default=True)
    min_age = Column(Integer, nullable=True)
    
    # Requirements
    required_learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)
    required_content_id = Column(Integer, ForeignKey("educational_content.id"), nullable=True)
    
    # Required score for the content/quiz (if applicable)
    required_score = Column(Float, nullable=True)  # Minimum score required
    
    # Relationships
    required_learning_path = relationship("LearningPath")
    required_content = relationship("EducationalContent")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TradingPermission {self.name} - {self.permission_type}>"


class UserPermission(Base):
    """Model tracking which trading permissions a user has earned."""
    
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("trading_permissions.id"), nullable=False)
    
    # Permission status
    is_granted = Column(Boolean, default=False)
    granted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Guardian who granted
    override_reason = Column(Text, nullable=True)  # If granted without meeting requirements
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="trading_permissions")
    permission = relationship("TradingPermission")
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    granted_at = Column(DateTime, nullable=True)
    
    class Meta:
        # Ensure each user has only one entry per permission
        __table_args__ = (
            {"unique_constraint": ("user_id", "permission_id")},
        )
    
    def __repr__(self):
        status = "granted" if self.is_granted else "not granted"
        return f"<UserPermission {self.user_id} - {self.permission_id}: {status}>"