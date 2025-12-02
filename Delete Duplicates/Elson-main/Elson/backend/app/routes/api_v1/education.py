"""API routes for educational content, progress tracking, and trading permissions."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.education_service import EducationService
from app.schemas.education import (
    ContentCreate, ContentUpdate, ContentResponse,
    ProgressCreate, ProgressUpdate, ProgressResponse,
    LearningPathCreate, LearningPathUpdate, LearningPathResponse,
    LearningPathItemCreate, LearningPathItemResponse,
    TradingPermissionCreate, TradingPermissionUpdate, TradingPermissionResponse,
    UserPermissionCreate, UserPermissionUpdate, UserPermissionResponse,
    QuizSubmission, UserProgressSummary
)
from app.routes.deps import get_current_user
from app.models.user import User, UserRole

router = APIRouter()


# ===== Educational Content Endpoints =====

@router.get("/content", response_model=List[ContentResponse])
async def get_educational_content(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all educational content."""
    service = EducationService(db)
    return service.get_all_content(skip, limit)


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content_by_id(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get educational content by ID."""
    service = EducationService(db)
    content = service.get_content_by_id(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )
    return content


@router.get("/content/slug/{slug}", response_model=ContentResponse)
async def get_content_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get educational content by slug."""
    service = EducationService(db)
    content = service.get_content_by_slug(slug)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with slug '{slug}' not found"
        )
    return content


@router.post("/content", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create educational content"
        )
        
    service = EducationService(db)
    return service.create_content(content_data)


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update educational content"
        )
        
    service = EducationService(db)
    return service.update_content(content_id, content_data)


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete educational content"
        )
        
    service = EducationService(db)
    service.delete_content(content_id)
    return {"message": f"Content with ID {content_id} deleted successfully"}


@router.post("/content/{content_id}/prerequisites/{prerequisite_id}", response_model=ContentResponse)
async def add_prerequisite(
    content_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a prerequisite to educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage prerequisites"
        )
        
    service = EducationService(db)
    return service.add_prerequisite(content_id, prerequisite_id)


@router.delete("/content/{content_id}/prerequisites/{prerequisite_id}", response_model=ContentResponse)
async def remove_prerequisite(
    content_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a prerequisite from educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage prerequisites"
        )
        
    service = EducationService(db)
    return service.remove_prerequisite(content_id, prerequisite_id)


@router.post("/content/{content_id}/quiz/{quiz_id}", response_model=ContentResponse)
async def associate_quiz(
    content_id: int,
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Associate a quiz with educational content (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can associate quizzes"
        )
        
    service = EducationService(db)
    return service.associate_quiz(content_id, quiz_id)


# ===== Learning Path Endpoints =====

@router.get("/learning-paths", response_model=List[LearningPathResponse])
async def get_learning_paths(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all learning paths."""
    service = EducationService(db)
    return service.get_all_learning_paths(skip, limit)


@router.get("/learning-paths/{path_id}", response_model=LearningPathResponse)
async def get_learning_path_by_id(
    path_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get learning path by ID."""
    service = EducationService(db)
    path = service.get_learning_path_by_id(path_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning path with ID {path_id} not found"
        )
    return path


@router.get("/learning-paths/slug/{slug}", response_model=LearningPathResponse)
async def get_learning_path_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get learning path by slug."""
    service = EducationService(db)
    path = service.get_learning_path_by_slug(slug)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning path with slug '{slug}' not found"
        )
    return path


@router.post("/learning-paths", response_model=LearningPathResponse, status_code=status.HTTP_201_CREATED)
async def create_learning_path(
    path_data: LearningPathCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create learning paths"
        )
        
    service = EducationService(db)
    return service.create_learning_path(path_data)


@router.put("/learning-paths/{path_id}", response_model=LearningPathResponse)
async def update_learning_path(
    path_id: int,
    path_data: LearningPathUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update learning paths"
        )
        
    service = EducationService(db)
    return service.update_learning_path(path_id, path_data)


@router.delete("/learning-paths/{path_id}")
async def delete_learning_path(
    path_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete learning paths"
        )
        
    service = EducationService(db)
    service.delete_learning_path(path_id)
    return {"message": f"Learning path with ID {path_id} deleted successfully"}


@router.post("/learning-paths/{path_id}/items", response_model=LearningPathItemResponse)
async def add_content_to_path(
    path_id: int,
    item_data: LearningPathItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add content to a learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify learning paths"
        )
        
    service = EducationService(db)
    return service.add_content_to_path(path_id, item_data)


@router.delete("/learning-paths/{path_id}/items/{content_id}")
async def remove_content_from_path(
    path_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove content from a learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify learning paths"
        )
        
    service = EducationService(db)
    service.remove_content_from_path(path_id, content_id)
    return {"message": f"Content {content_id} removed from path {path_id} successfully"}


@router.post("/learning-paths/{path_id}/reorder")
async def reorder_path_items(
    path_id: int,
    item_orders: Dict[str, int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder items in a learning path (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify learning paths"
        )
        
    service = EducationService(db)
    
    # Convert string content_ids to integers
    content_orders = {int(k): v for k, v in item_orders.items()}
    
    service.reorder_path_items(path_id, content_orders)
    return {"message": f"Learning path {path_id} items reordered successfully"}


# ===== User Progress Endpoints =====

@router.get("/progress", response_model=List[ProgressResponse])
async def get_user_progress(
    content_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress for the current user."""
    service = EducationService(db)
    return service.get_user_progress(current_user.id, content_id)


@router.get("/progress/summary", response_model=UserProgressSummary)
async def get_user_progress_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress summary for the current user."""
    service = EducationService(db)
    return service.get_user_progress_summary(current_user.id)


@router.get("/progress/{content_id}", response_model=ProgressResponse)
async def get_single_progress(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a user's progress for a specific content item."""
    service = EducationService(db)
    progress = service.get_single_progress(current_user.id, content_id)
    if not progress:
        # Return empty progress if not found
        return ProgressResponse(
            id=0,
            user_id=current_user.id,
            content_id=content_id,
            is_started=False,
            is_completed=False,
            progress_percent=0.0,
            attempts=0,
            time_spent_seconds=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    return progress


@router.post("/progress/{content_id}", response_model=ProgressResponse)
async def create_or_update_progress(
    content_id: int,
    progress_data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update progress for the current user."""
    service = EducationService(db)
    return service.create_or_update_progress(current_user.id, content_id, progress_data)


@router.post("/quiz/submit", response_model=Dict[str, Any])
async def submit_quiz(
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a quiz and update progress."""
    service = EducationService(db)
    return service.submit_quiz(current_user.id, submission)


# ===== Guardian Access to Minor Progress =====

@router.get("/minors/{minor_id}/progress", response_model=List[ProgressResponse])
async def get_minor_progress(
    minor_id: int,
    content_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get educational progress for a minor (guardian only)."""
    # Check if user is a guardian for this minor
    if not is_guardian_for_minor(db, current_user.id, minor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to view progress for this minor"
        )
        
    service = EducationService(db)
    return service.get_user_progress(minor_id, content_id)


@router.get("/minors/{minor_id}/progress/summary", response_model=UserProgressSummary)
async def get_minor_progress_summary(
    minor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get educational progress summary for a minor (guardian only)."""
    # Check if user is a guardian for this minor
    if not is_guardian_for_minor(db, current_user.id, minor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to view progress for this minor"
        )
        
    service = EducationService(db)
    return service.get_user_progress_summary(minor_id)


# ===== Trading Permissions Endpoints =====

@router.get("/permissions/trading", response_model=List[TradingPermissionResponse])
async def get_trading_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all trading permissions."""
    service = EducationService(db)
    return service.get_all_trading_permissions(skip, limit)


@router.get("/permissions/trading/{permission_id}", response_model=TradingPermissionResponse)
async def get_trading_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific trading permission."""
    service = EducationService(db)
    permission = service.get_trading_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    return permission


@router.post("/permissions/trading", response_model=TradingPermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_permission(
    permission_data: TradingPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trading permission (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create trading permissions"
        )
        
    service = EducationService(db)
    return service.create_trading_permission(permission_data)


@router.put("/permissions/trading/{permission_id}", response_model=TradingPermissionResponse)
async def update_trading_permission(
    permission_id: int,
    permission_data: TradingPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a trading permission (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update trading permissions"
        )
        
    service = EducationService(db)
    return service.update_trading_permission(permission_id, permission_data)


@router.delete("/permissions/trading/{permission_id}")
async def delete_trading_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a trading permission (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete trading permissions"
        )
        
    service = EducationService(db)
    service.delete_trading_permission(permission_id)
    return {"message": f"Permission with ID {permission_id} deleted successfully"}


# ===== User Permissions Endpoints =====

@router.get("/permissions/user", response_model=List[UserPermissionResponse])
async def get_user_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions for the current user."""
    service = EducationService(db)
    return service.get_user_permissions(current_user.id)


@router.get("/permissions/user/{permission_id}", response_model=UserPermissionResponse)
async def get_user_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific permission for the current user."""
    service = EducationService(db)
    permission = service.get_single_user_permission(current_user.id, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have permission with ID {permission_id}"
        )
    return permission


@router.post("/permissions/minors/{minor_id}/grant/{permission_id}", response_model=UserPermissionResponse)
async def grant_minor_permission(
    minor_id: int,
    permission_id: int,
    override_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grant a permission to a minor (guardian only)."""
    # Check if user is a guardian for this minor
    if not is_guardian_for_minor(db, current_user.id, minor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to grant permissions for this minor"
        )
        
    service = EducationService(db)
    return service.grant_user_permission(
        minor_id, 
        permission_id, 
        granted_by_id=current_user.id,
        override_reason=override_reason
    )


@router.post("/permissions/minors/{minor_id}/revoke/{permission_id}")
async def revoke_minor_permission(
    minor_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a permission from a minor (guardian only)."""
    # Check if user is a guardian for this minor
    if not is_guardian_for_minor(db, current_user.id, minor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to revoke permissions for this minor"
        )
        
    service = EducationService(db)
    service.revoke_user_permission(minor_id, permission_id)
    return {"message": f"Permission {permission_id} revoked from minor {minor_id}"}


@router.get("/permissions/check/{permission_type}")
async def check_permission(
    permission_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if the current user has a specific permission."""
    service = EducationService(db)
    has_permission = service.check_user_has_permission(current_user.id, permission_type)
    return {"permission_type": permission_type, "has_permission": has_permission}


# ===== Utility Functions =====

def is_guardian_for_minor(db: Session, guardian_id: int, minor_id: int) -> bool:
    """Check if a user is a guardian for a specific minor."""
    from app.models.account import Account
    
    account = db.query(Account).filter(
        Account.user_id == minor_id,
        Account.guardian_id == guardian_id
    ).first()
    
    return account is not None