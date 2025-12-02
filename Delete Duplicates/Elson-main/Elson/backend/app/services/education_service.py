"""Education service for managing educational content and user progress.

This module provides services for handling educational content, tracking user progress,
and managing trading permissions based on educational achievements.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from fastapi import HTTPException, status

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session, joinedload

from app.models.education import (
    EducationalContent, UserProgress, LearningPath, LearningPathItem,
    TradingPermission, UserPermission, ContentType, CompletionRequirement
)
from app.models.user import User, UserRole
from app.schemas.education import (
    ContentCreate, ContentUpdate, ProgressCreate, ProgressUpdate,
    LearningPathCreate, LearningPathUpdate, LearningPathItemCreate,
    TradingPermissionCreate, TradingPermissionUpdate, UserPermissionCreate,
    UserPermissionUpdate, QuizSubmission, UserProgressSummary
)

logger = logging.getLogger(__name__)


class EducationService:
    """Service for managing educational content and user progress."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    # ===== Educational Content Management =====
    
    def get_all_content(self, skip: int = 0, limit: int = 100) -> List[EducationalContent]:
        """Get all educational content items with pagination."""
        return (self.db.query(EducationalContent)
                .order_by(EducationalContent.level, EducationalContent.title)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_content_by_id(self, content_id: int) -> Optional[EducationalContent]:
        """Get educational content by ID."""
        return self.db.query(EducationalContent).filter(EducationalContent.id == content_id).first()
    
    def get_content_by_slug(self, slug: str) -> Optional[EducationalContent]:
        """Get educational content by slug."""
        return self.db.query(EducationalContent).filter(EducationalContent.slug == slug).first()
    
    def create_content(self, content_data: ContentCreate) -> EducationalContent:
        """Create new educational content."""
        # Check if slug already exists
        existing = self.db.query(EducationalContent).filter(
            EducationalContent.slug == content_data.slug
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content with slug '{content_data.slug}' already exists"
            )
            
        content = EducationalContent(**content_data.dict())
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        
        return content
    
    def update_content(self, content_id: int, content_data: ContentUpdate) -> EducationalContent:
        """Update existing educational content."""
        content = self.get_content_by_id(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID {content_id} not found"
            )
            
        # Update attributes
        for key, value in content_data.dict(exclude_unset=True).items():
            setattr(content, key, value)
            
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        
        return content
    
    def delete_content(self, content_id: int) -> bool:
        """Delete educational content."""
        content = self.get_content_by_id(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID {content_id} not found"
            )
            
        # Check for dependencies before deletion
        dependencies = self._check_content_dependencies(content_id)
        if dependencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete content with dependencies: {dependencies}"
            )
            
        self.db.delete(content)
        self.db.commit()
        
        return True
    
    def _check_content_dependencies(self, content_id: int) -> Dict[str, int]:
        """Check for dependencies on this content item."""
        dependencies = {}
        
        # Check for content that has this as a prerequisite
        prereq_count = self.db.query(func.count()).filter(
            EducationalContent.prerequisites.any(id=content_id)
        ).scalar()
        
        if prereq_count > 0:
            dependencies["prerequisites_for"] = prereq_count
            
        # Check for learning paths that include this content
        path_item_count = self.db.query(func.count(LearningPathItem.id)).filter(
            LearningPathItem.content_id == content_id
        ).scalar()
        
        if path_item_count > 0:
            dependencies["learning_path_items"] = path_item_count
            
        # Check for trading permissions that require this content
        permission_count = self.db.query(func.count(TradingPermission.id)).filter(
            TradingPermission.required_content_id == content_id
        ).scalar()
        
        if permission_count > 0:
            dependencies["trading_permissions"] = permission_count
            
        # Check for quizzes that are associated with this content
        quiz_count = self.db.query(func.count(EducationalContent.id)).filter(
            EducationalContent.associated_quiz_id == content_id
        ).scalar()
        
        if quiz_count > 0:
            dependencies["associated_quizzes"] = quiz_count
            
        return dependencies
    
    def add_prerequisite(self, content_id: int, prerequisite_id: int) -> EducationalContent:
        """Add a prerequisite to educational content."""
        content = self.get_content_by_id(content_id)
        prerequisite = self.get_content_by_id(prerequisite_id)
        
        if not content or not prerequisite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content or prerequisite not found"
            )
            
        # Avoid circular prerequisites
        if content_id == prerequisite_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be a prerequisite of itself"
            )
            
        # Check if prerequisite already exists
        if prerequisite in content.prerequisites:
            return content
            
        content.prerequisites.append(prerequisite)
        self.db.commit()
        self.db.refresh(content)
        
        return content
    
    def remove_prerequisite(self, content_id: int, prerequisite_id: int) -> EducationalContent:
        """Remove a prerequisite from educational content."""
        content = self.get_content_by_id(content_id)
        prerequisite = self.get_content_by_id(prerequisite_id)
        
        if not content or not prerequisite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content or prerequisite not found"
            )
            
        if prerequisite in content.prerequisites:
            content.prerequisites.remove(prerequisite)
            self.db.commit()
            self.db.refresh(content)
            
        return content
    
    def associate_quiz(self, content_id: int, quiz_id: int) -> EducationalContent:
        """Associate a quiz with educational content."""
        content = self.get_content_by_id(content_id)
        quiz = self.get_content_by_id(quiz_id)
        
        if not content or not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content or quiz not found"
            )
            
        # Verify that quiz has the correct type
        if quiz.content_type != ContentType.QUIZ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated content must be a quiz"
            )
            
        content.associated_quiz_id = quiz_id
        self.db.commit()
        self.db.refresh(content)
        
        return content
    
    # ===== Learning Path Management =====
    
    def get_all_learning_paths(self, skip: int = 0, limit: int = 100) -> List[LearningPath]:
        """Get all learning paths with pagination."""
        return (self.db.query(LearningPath)
                .options(joinedload(LearningPath.content_items).joinedload(LearningPathItem.content))
                .order_by(LearningPath.title)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_learning_path_by_id(self, path_id: int) -> Optional[LearningPath]:
        """Get learning path by ID."""
        return (self.db.query(LearningPath)
                .options(joinedload(LearningPath.content_items).joinedload(LearningPathItem.content))
                .filter(LearningPath.id == path_id)
                .first())
    
    def get_learning_path_by_slug(self, slug: str) -> Optional[LearningPath]:
        """Get learning path by slug."""
        return (self.db.query(LearningPath)
                .options(joinedload(LearningPath.content_items).joinedload(LearningPathItem.content))
                .filter(LearningPath.slug == slug)
                .first())
    
    def create_learning_path(self, path_data: LearningPathCreate) -> LearningPath:
        """Create new learning path."""
        # Check if slug already exists
        existing = self.db.query(LearningPath).filter(
            LearningPath.slug == path_data.slug
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Learning path with slug '{path_data.slug}' already exists"
            )
            
        path = LearningPath(**path_data.dict())
        self.db.add(path)
        self.db.commit()
        self.db.refresh(path)
        
        return path
    
    def update_learning_path(self, path_id: int, path_data: LearningPathUpdate) -> LearningPath:
        """Update existing learning path."""
        path = self.get_learning_path_by_id(path_id)
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID {path_id} not found"
            )
            
        # Update attributes
        for key, value in path_data.dict(exclude_unset=True).items():
            setattr(path, key, value)
            
        self.db.add(path)
        self.db.commit()
        self.db.refresh(path)
        
        return path
    
    def delete_learning_path(self, path_id: int) -> bool:
        """Delete learning path."""
        path = self.get_learning_path_by_id(path_id)
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID {path_id} not found"
            )
            
        # Check for dependencies
        dependencies = self._check_learning_path_dependencies(path_id)
        if dependencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete learning path with dependencies: {dependencies}"
            )
            
        self.db.delete(path)
        self.db.commit()
        
        return True
    
    def _check_learning_path_dependencies(self, path_id: int) -> Dict[str, int]:
        """Check for dependencies on this learning path."""
        dependencies = {}
        
        # Check for trading permissions that require this path
        permission_count = self.db.query(func.count(TradingPermission.id)).filter(
            TradingPermission.required_learning_path_id == path_id
        ).scalar()
        
        if permission_count > 0:
            dependencies["trading_permissions"] = permission_count
            
        return dependencies
    
    def add_content_to_path(self, path_id: int, item_data: LearningPathItemCreate) -> LearningPathItem:
        """Add content to a learning path."""
        path = self.get_learning_path_by_id(path_id)
        content = self.get_content_by_id(item_data.content_id)
        
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID {path_id} not found"
            )
            
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID {item_data.content_id} not found"
            )
            
        # Check if content is already in path
        existing = self.db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path_id,
            LearningPathItem.content_id == item_data.content_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content {item_data.content_id} already exists in path {path_id}"
            )
            
        item = LearningPathItem(
            learning_path_id=path_id,
            content_id=item_data.content_id,
            order=item_data.order,
            is_required=item_data.is_required
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        return item
    
    def remove_content_from_path(self, path_id: int, content_id: int) -> bool:
        """Remove content from a learning path."""
        item = self.db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path_id,
            LearningPathItem.content_id == content_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content {content_id} not found in path {path_id}"
            )
            
        self.db.delete(item)
        self.db.commit()
        
        return True
    
    def reorder_path_items(self, path_id: int, item_orders: Dict[int, int]) -> List[LearningPathItem]:
        """Reorder items in a learning path.
        
        Args:
            path_id: ID of the learning path
            item_orders: Dict mapping content_id to new order
        """
        path = self.get_learning_path_by_id(path_id)
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID {path_id} not found"
            )
            
        # Update orders
        for content_id, order in item_orders.items():
            item = self.db.query(LearningPathItem).filter(
                LearningPathItem.learning_path_id == path_id,
                LearningPathItem.content_id == content_id
            ).first()
            
            if item:
                item.order = order
                self.db.add(item)
                
        self.db.commit()
        
        # Refresh path to get updated items
        path = self.get_learning_path_by_id(path_id)
        return path.content_items
    
    # ===== User Progress Tracking =====
    
    def get_user_progress(self, user_id: int, content_id: Optional[int] = None) -> List[UserProgress]:
        """Get progress for a user, optionally filtered by content."""
        query = self.db.query(UserProgress).filter(UserProgress.user_id == user_id)
        
        if content_id:
            query = query.filter(UserProgress.content_id == content_id)
            
        return query.all()
    
    def get_single_progress(self, user_id: int, content_id: int) -> Optional[UserProgress]:
        """Get a user's progress for a specific content item."""
        return self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id
        ).first()
    
    def create_or_update_progress(
        self, 
        user_id: int, 
        content_id: int, 
        progress_data: Union[ProgressCreate, ProgressUpdate]
    ) -> UserProgress:
        """Create or update progress record for a user and content."""
        # Check if user and content exist
        user = self.db.query(User).get(user_id)
        content = self.get_content_by_id(content_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID {content_id} not found"
            )
            
        # Get existing progress or create new
        progress = self.get_single_progress(user_id, content_id)
        
        if not progress:
            # Create new progress
            if isinstance(progress_data, ProgressUpdate):
                # Convert update to create with defaults
                create_data = ProgressCreate(
                    user_id=user_id,
                    content_id=content_id,
                    is_started=progress_data.is_started or False,
                    is_completed=progress_data.is_completed or False,
                    progress_percent=progress_data.progress_percent or 0.0,
                    score=progress_data.score,
                    passed=progress_data.passed,
                    attempts=progress_data.attempts or 0,
                    time_spent_seconds=progress_data.time_spent_seconds or 0
                )
                progress = UserProgress(**create_data.dict())
            else:
                progress = UserProgress(**progress_data.dict())
                
            # Set started flag automatically
            progress.is_started = True
            progress.last_accessed = datetime.utcnow()
        else:
            # Update existing progress
            update_data = progress_data.dict(exclude_unset=True)
            
            for key, value in update_data.items():
                if value is not None:  # Only update non-None values
                    setattr(progress, key, value)
            
            # Update access time
            progress.last_accessed = datetime.utcnow()
            
            # Set completion time if newly completed
            if progress.is_completed and not progress.completed_at:
                progress.completed_at = datetime.utcnow()
                
                # If this is a quiz, check if we should update associated module progress
                if content.content_type == ContentType.QUIZ:
                    self._handle_quiz_completion(user_id, content_id, progress.passed)
        
        # Handle edge cases
        if progress.progress_percent >= 100:
            progress.progress_percent = 100
            
            # Don't mark as completed unless explicitly set or meets requirements
            if progress.is_completed is None:
                if content.completion_requirement == CompletionRequirement.NONE:
                    progress.is_completed = True
                    progress.completed_at = datetime.utcnow()
                elif content.completion_requirement == CompletionRequirement.TIME:
                    # Complete if minimum time spent
                    if progress.time_spent_seconds >= (content.estimated_minutes or 1) * 60:
                        progress.is_completed = True
                        progress.completed_at = datetime.utcnow()
        
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        
        # Check and update path progress
        self._update_learning_path_progress(user_id, content_id)
        
        # Check and update permissions
        if progress.is_completed:
            self._check_and_update_permissions(user_id)
        
        return progress
    
    def _handle_quiz_completion(self, user_id: int, quiz_id: int, passed: bool) -> None:
        """Handle completion of a quiz and update associated module progress."""
        quiz = self.get_content_by_id(quiz_id)
        if not quiz or quiz.content_type != ContentType.QUIZ:
            return
            
        # Find modules that have this quiz as completion requirement
        modules = self.db.query(EducationalContent).filter(
            EducationalContent.associated_quiz_id == quiz_id,
            EducationalContent.completion_requirement == CompletionRequirement.QUIZ
        ).all()
        
        for module in modules:
            module_progress = self.get_single_progress(user_id, module.id)
            
            if not module_progress:
                # Create module progress if it doesn't exist
                module_progress = UserProgress(
                    user_id=user_id,
                    content_id=module.id,
                    is_started=True,
                    progress_percent=100 if passed else 50,  # 50% if failed, 100% if passed
                    last_accessed=datetime.utcnow()
                )
            else:
                # Update existing progress
                module_progress.progress_percent = 100 if passed else max(module_progress.progress_percent, 50)
                module_progress.last_accessed = datetime.utcnow()
            
            # Mark as completed if quiz is passed
            if passed:
                module_progress.is_completed = True
                module_progress.completed_at = datetime.utcnow()
                
            self.db.add(module_progress)
        
        self.db.commit()
    
    def _update_learning_path_progress(self, user_id: int, content_id: int) -> None:
        """Update learning path progress when content progress changes."""
        # Find all learning paths containing this content
        paths = self.db.query(LearningPath).join(
            LearningPathItem, LearningPath.id == LearningPathItem.learning_path_id
        ).filter(
            LearningPathItem.content_id == content_id
        ).all()
        
        for path in paths:
            # Calculate path progress
            self.calculate_learning_path_progress(user_id, path.id)
    
    def calculate_learning_path_progress(self, user_id: int, path_id: int) -> float:
        """Calculate a user's progress percentage for a learning path."""
        path = self.get_learning_path_by_id(path_id)
        if not path:
            return 0.0
            
        # Get all required items in the path
        required_items = [item for item in path.content_items if item.is_required]
        if not required_items:
            return 0.0
            
        # Get progress for each required content
        completed_count = 0
        for item in required_items:
            progress = self.get_single_progress(user_id, item.content_id)
            if progress and progress.is_completed:
                completed_count += 1
                
        # Calculate percentage
        return (completed_count / len(required_items)) * 100 if required_items else 0.0
    
    def submit_quiz(self, user_id: int, submission: QuizSubmission) -> Dict[str, Any]:
        """Process a quiz submission and update progress."""
        # Get the quiz content
        quiz = self.get_content_by_id(submission.content_id)
        if not quiz or quiz.content_type != ContentType.QUIZ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid quiz content ID"
            )
            
        # Get or create progress
        progress = self.get_single_progress(user_id, submission.content_id)
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                content_id=submission.content_id,
                is_started=True,
                attempts=0,
                last_accessed=datetime.utcnow()
            )
            
        # Increment attempts
        progress.attempts += 1
        
        # In a real implementation, we would grade the quiz here
        # For now, we'll simulate with a random score for demonstration
        import random
        score = random.uniform(60, 100)
        
        # Check if passed
        passed = score >= (quiz.passing_score or 70)
        
        # Update progress
        progress.score = score
        progress.passed = passed
        progress.is_completed = True
        progress.progress_percent = 100
        progress.completed_at = datetime.utcnow()
        progress.time_spent_seconds += submission.time_spent_seconds
        
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        
        # Handle quiz completion
        self._handle_quiz_completion(user_id, submission.content_id, passed)
        
        return {
            "quiz_id": submission.content_id,
            "score": score,
            "passed": passed,
            "attempt": progress.attempts
        }
    
    def get_user_progress_summary(self, user_id: int) -> UserProgressSummary:
        """Get a summary of a user's educational progress."""
        # Get all content count
        total_content = self.db.query(func.count(EducationalContent.id)).scalar()
        
        # Get user progress stats
        progress_query = self.db.query(UserProgress).filter(UserProgress.user_id == user_id)
        
        # Get completed and started counts
        completed_count = progress_query.filter(UserProgress.is_completed == True).count()
        started_count = progress_query.filter(
            UserProgress.is_started == True, 
            UserProgress.is_completed == False
        ).count()
        
        # Get total time spent
        time_spent = self.db.query(func.sum(UserProgress.time_spent_seconds)).filter(
            UserProgress.user_id == user_id
        ).scalar() or 0
        
        # Calculate completion percentage
        completion_percentage = (completed_count / total_content) * 100 if total_content > 0 else 0
        
        # Get learning path progress
        learning_paths = self.get_all_learning_paths()
        path_progress = {}
        
        for path in learning_paths:
            progress = self.calculate_learning_path_progress(user_id, path.id)
            path_progress[path.slug] = progress
        
        # Get recent activities
        recent_activities = (self.db.query(UserProgress)
                            .filter(UserProgress.user_id == user_id)
                            .order_by(desc(UserProgress.last_accessed))
                            .limit(5)
                            .all())
        
        return UserProgressSummary(
            total_content_count=total_content,
            completed_count=completed_count,
            started_count=started_count,
            completion_percentage=completion_percentage,
            total_time_spent_minutes=time_spent // 60,
            learning_paths_progress=path_progress,
            recent_activities=recent_activities
        )
    
    # ===== Trading Permissions =====
    
    def get_all_trading_permissions(self, skip: int = 0, limit: int = 100) -> List[TradingPermission]:
        """Get all trading permissions with pagination."""
        return (self.db.query(TradingPermission)
                .order_by(TradingPermission.name)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_trading_permission_by_id(self, permission_id: int) -> Optional[TradingPermission]:
        """Get trading permission by ID."""
        return self.db.query(TradingPermission).filter(TradingPermission.id == permission_id).first()
    
    def get_trading_permission_by_type(self, permission_type: str) -> Optional[TradingPermission]:
        """Get trading permission by type."""
        return self.db.query(TradingPermission).filter(
            TradingPermission.permission_type == permission_type
        ).first()
    
    def create_trading_permission(self, permission_data: TradingPermissionCreate) -> TradingPermission:
        """Create new trading permission."""
        # Check if permission type already exists
        existing = self.db.query(TradingPermission).filter(
            TradingPermission.permission_type == permission_data.permission_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission with type '{permission_data.permission_type}' already exists"
            )
            
        # Validate references
        if permission_data.required_learning_path_id:
            path = self.get_learning_path_by_id(permission_data.required_learning_path_id)
            if not path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Learning path with ID {permission_data.required_learning_path_id} not found"
                )
                
        if permission_data.required_content_id:
            content = self.get_content_by_id(permission_data.required_content_id)
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Content with ID {permission_data.required_content_id} not found"
                )
                
        permission = TradingPermission(**permission_data.dict())
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def update_trading_permission(
        self, 
        permission_id: int, 
        permission_data: TradingPermissionUpdate
    ) -> TradingPermission:
        """Update existing trading permission."""
        permission = self.get_trading_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {permission_id} not found"
            )
            
        # Validate references
        if permission_data.required_learning_path_id:
            path = self.get_learning_path_by_id(permission_data.required_learning_path_id)
            if not path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Learning path with ID {permission_data.required_learning_path_id} not found"
                )
                
        if permission_data.required_content_id:
            content = self.get_content_by_id(permission_data.required_content_id)
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Content with ID {permission_data.required_content_id} not found"
                )
            
        # Update attributes
        for key, value in permission_data.dict(exclude_unset=True).items():
            setattr(permission, key, value)
            
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def delete_trading_permission(self, permission_id: int) -> bool:
        """Delete trading permission."""
        permission = self.get_trading_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {permission_id} not found"
            )
            
        # Check if any users have this permission
        user_count = self.db.query(func.count(UserPermission.id)).filter(
            UserPermission.permission_id == permission_id
        ).scalar()
        
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete permission assigned to {user_count} users"
            )
            
        self.db.delete(permission)
        self.db.commit()
        
        return True
    
    # ===== User Permissions =====
    
    def get_user_permissions(self, user_id: int) -> List[UserPermission]:
        """Get all permissions for a user."""
        return (self.db.query(UserPermission)
                .options(joinedload(UserPermission.permission))
                .filter(UserPermission.user_id == user_id)
                .all())
    
    def get_single_user_permission(self, user_id: int, permission_id: int) -> Optional[UserPermission]:
        """Get a specific permission for a user."""
        return (self.db.query(UserPermission)
                .filter(
                    UserPermission.user_id == user_id,
                    UserPermission.permission_id == permission_id
                )
                .first())
    
    def check_user_has_permission(self, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission type."""
        permission = self.get_trading_permission_by_type(permission_type)
        if not permission:
            return False
            
        user_permission = self.get_single_user_permission(user_id, permission.id)
        if not user_permission or not user_permission.is_granted:
            return False
            
        return True
    
    def grant_user_permission(
        self, 
        user_id: int, 
        permission_id: int, 
        granted_by_id: Optional[int] = None,
        override_reason: Optional[str] = None
    ) -> UserPermission:
        """Grant a permission to a user."""
        # Check if user and permission exist
        user = self.db.query(User).get(user_id)
        permission = self.get_trading_permission_by_id(permission_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {permission_id} not found"
            )
            
        # Check if user already has this permission
        user_permission = self.get_single_user_permission(user_id, permission_id)
        
        if user_permission:
            # Update existing permission
            user_permission.is_granted = True
            user_permission.granted_by_user_id = granted_by_id
            user_permission.override_reason = override_reason
            user_permission.granted_at = datetime.utcnow()
        else:
            # Create new permission
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                is_granted=True,
                granted_by_user_id=granted_by_id,
                override_reason=override_reason,
                granted_at=datetime.utcnow()
            )
            
        self.db.add(user_permission)
        self.db.commit()
        self.db.refresh(user_permission)
        
        return user_permission
    
    def revoke_user_permission(self, user_id: int, permission_id: int) -> bool:
        """Revoke a permission from a user."""
        user_permission = self.get_single_user_permission(user_id, permission_id)
        
        if not user_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} does not have permission {permission_id}"
            )
            
        user_permission.is_granted = False
        user_permission.granted_at = None
        
        self.db.add(user_permission)
        self.db.commit()
        
        return True
    
    def _check_and_update_permissions(self, user_id: int) -> Dict[str, bool]:
        """Check and update trading permissions based on educational progress."""
        user = self.db.query(User).get(user_id)
        if not user:
            return {}
            
        # Get all permissions
        permissions = self.get_all_trading_permissions()
        updated_permissions = {}
        
        for permission in permissions:
            # Skip if no educational requirements
            if not permission.required_content_id and not permission.required_learning_path_id:
                continue
                
            # Check if user meets requirements
            meets_requirements = self._check_if_user_meets_requirements(
                user_id, 
                permission.required_content_id,
                permission.required_learning_path_id,
                permission.required_score
            )
            
            if meets_requirements:
                # Get or create user permission
                user_permission = self.get_single_user_permission(user_id, permission.id)
                
                if not user_permission or not user_permission.is_granted:
                    # Grant permission (without override reason)
                    self.grant_user_permission(user_id, permission.id)
                    updated_permissions[permission.permission_type] = True
                    
        return updated_permissions
    
    def _check_if_user_meets_requirements(
        self, 
        user_id: int, 
        content_id: Optional[int], 
        path_id: Optional[int],
        required_score: Optional[float]
    ) -> bool:
        """Check if a user meets educational requirements for a permission."""
        # If no requirements, always meets them
        if not content_id and not path_id:
            return True
            
        # Check content requirement
        if content_id:
            progress = self.get_single_progress(user_id, content_id)
            if not progress or not progress.is_completed:
                return False
                
            # Check score requirement
            if required_score and (not progress.score or progress.score < required_score):
                return False
                
        # Check learning path requirement
        if path_id:
            path_progress = self.calculate_learning_path_progress(user_id, path_id)
            if path_progress < 100:
                return False
                
        return True