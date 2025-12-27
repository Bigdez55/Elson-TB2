"""API endpoints for the education system."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services import education as education_service
from app.schemas.education import (
    EducationalContentResponse,
    EducationalContentCreate,
    EducationalContentUpdate,
    ContentWithProgress,
    UserProgressResponse,
    UserProgressUpdate,
    LearningPathResponse,
    LearningPathWithProgress,
    TradingPermissionResponse,
    UserPermissionResponse,
    PermissionCheckResponse,
)

router = APIRouter()


# ==================== Educational Content Endpoints ====================


@router.get("/content", response_model=List[EducationalContentResponse])
def list_educational_content(
    content_type: Optional[str] = None,
    level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List educational content with optional filters."""
    return education_service.list_content(
        db,
        content_type=content_type,
        level=level,
        min_age=None,  # Can add age filtering based on user if needed
        max_age=None,
        skip=skip,
        limit=limit,
    )


@router.get("/content/{content_id}", response_model=ContentWithProgress)
def get_educational_content(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get educational content by ID with user progress."""
    content = education_service.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get user progress for this content
    user_progress = education_service.get_user_progress(db, current_user.id, content_id)

    # Convert to response model
    response = ContentWithProgress.from_orm(content)
    if user_progress:
        response.user_progress = UserProgressResponse.from_orm(user_progress)

    return response


@router.post("/content", response_model=EducationalContentResponse)
def create_educational_content(
    content: EducationalContentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create new educational content (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if slug already exists
    existing = education_service.get_content_by_slug(db, content.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Content with this slug already exists")

    return education_service.create_content(db, content)


@router.put("/content/{content_id}", response_model=EducationalContentResponse)
def update_educational_content(
    content_id: int,
    content_update: EducationalContentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update educational content (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_content = education_service.update_content(db, content_id, content_update)
    if not updated_content:
        raise HTTPException(status_code=404, detail="Content not found")

    return updated_content


# ==================== User Progress Endpoints ====================


@router.get("/progress", response_model=List[UserProgressResponse])
def get_my_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all progress records for the current user."""
    return education_service.get_user_all_progress(db, current_user.id)


@router.get("/progress/{content_id}", response_model=UserProgressResponse)
def get_content_progress(
    content_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user's progress for specific content."""
    progress = education_service.get_user_progress(db, current_user.id, content_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return progress


@router.put("/progress/{content_id}", response_model=UserProgressResponse)
def update_content_progress(
    content_id: int,
    progress_update: UserProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user's progress for specific content."""
    # Verify content exists
    content = education_service.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Create or update progress
    progress = education_service.create_or_update_progress(
        db, current_user.id, content_id, progress_update
    )

    # Check if this completion unlocks any permissions
    if progress_update.is_completed:
        # Find permissions that require this content
        from app.models.education import TradingPermission
        permissions = db.query(TradingPermission).filter(
            TradingPermission.required_content_id == content_id
        ).all()

        for permission in permissions:
            education_service.grant_permission_if_eligible(
                db, current_user.id, permission.id
            )

    return progress


# ==================== Learning Path Endpoints ====================


@router.get("/paths", response_model=List[LearningPathResponse])
def list_learning_paths(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all learning paths."""
    return education_service.list_learning_paths(
        db,
        min_age=None,  # Can add age filtering based on user
        max_age=None,
        skip=skip,
        limit=limit,
    )


@router.get("/paths/{path_id}", response_model=LearningPathWithProgress)
def get_learning_path(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get learning path with user progress."""
    path = education_service.get_learning_path(db, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get progress
    progress = education_service.get_learning_path_progress(db, current_user.id, path_id)

    # Convert to response
    response = LearningPathWithProgress.from_orm(path)
    if progress:
        response.completion_percent = progress["completion_percent"]
        response.items_completed = progress["items_completed"]
        response.total_items = progress["total_items"]

    return response


# ==================== Trading Permission Endpoints ====================


@router.get("/permissions", response_model=List[TradingPermissionResponse])
def list_trading_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all available trading permissions."""
    return education_service.list_trading_permissions(db)


@router.get("/permissions/my", response_model=List[UserPermissionResponse])
def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all permissions granted to the current user."""
    return education_service.get_user_permissions(db, current_user.id)


@router.get("/permissions/{permission_id}/check", response_model=PermissionCheckResponse)
def check_permission(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if user has or is eligible for a permission."""
    permission = education_service.get_trading_permission(db, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    eligibility = education_service.check_permission_eligibility(
        db, current_user.id, permission_id
    )

    return PermissionCheckResponse(
        permission=TradingPermissionResponse.from_orm(permission),
        **eligibility
    )


@router.post("/permissions/{permission_id}/grant", response_model=UserPermissionResponse)
def grant_permission_to_self(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Attempt to grant permission to self (if eligible)."""
    permission = education_service.get_trading_permission(db, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # Check eligibility
    eligibility = education_service.check_permission_eligibility(
        db, current_user.id, permission_id
    )

    if not eligibility["is_eligible"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Not eligible for this permission",
                "missing_requirements": eligibility["missing_requirements"],
            },
        )

    # Check if already granted
    if eligibility["is_granted"]:
        user_permission = education_service.get_user_permission(
            db, current_user.id, permission_id
        )
        return user_permission

    # Check guardian approval requirement
    if eligibility["requires_guardian_approval"] and not current_user.is_adult:
        raise HTTPException(
            status_code=400,
            detail="Guardian approval required for this permission",
        )

    # Grant permission
    user_permission = education_service.grant_permission(
        db,
        current_user.id,
        permission_id,
        granted_by_user_id=None,  # Self-granted
        override_reason="Auto-granted upon completing requirements",
    )

    return user_permission
