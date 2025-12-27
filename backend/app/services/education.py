"""Service layer for the education system."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.education import (
    EducationalContent,
    UserProgress,
    LearningPath,
    LearningPathItem,
    TradingPermission,
    UserPermission,
    ContentLevel,
    ContentType,
)
from app.models.user import User
from app.schemas.education import (
    EducationalContentCreate,
    EducationalContentUpdate,
    UserProgressCreate,
    UserProgressUpdate,
    LearningPathCreate,
    TradingPermissionCreate,
    UserPermissionCreate,
)


# ==================== Educational Content Services ====================


def get_content_by_id(db: Session, content_id: int) -> Optional[EducationalContent]:
    """Get educational content by ID."""
    return db.query(EducationalContent).filter(EducationalContent.id == content_id).first()


def get_content_by_slug(db: Session, slug: str) -> Optional[EducationalContent]:
    """Get educational content by slug."""
    return db.query(EducationalContent).filter(EducationalContent.slug == slug).first()


def list_content(
    db: Session,
    content_type: Optional[str] = None,
    level: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[EducationalContent]:
    """List educational content with optional filters."""
    query = db.query(EducationalContent)

    if content_type:
        query = query.filter(EducationalContent.content_type == ContentType[content_type.upper()])

    if level:
        query = query.filter(EducationalContent.level == ContentLevel[level.upper()])

    if min_age is not None:
        query = query.filter(
            or_(
                EducationalContent.min_age == None,
                EducationalContent.min_age <= min_age,
            )
        )

    if max_age is not None:
        query = query.filter(
            or_(
                EducationalContent.max_age == None,
                EducationalContent.max_age >= max_age,
            )
        )

    return query.order_by(EducationalContent.importance_level.desc()).offset(skip).limit(limit).all()


def create_content(db: Session, content: EducationalContentCreate) -> EducationalContent:
    """Create new educational content."""
    db_content = EducationalContent(
        **content.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


def update_content(
    db: Session, content_id: int, content_update: EducationalContentUpdate
) -> Optional[EducationalContent]:
    """Update educational content."""
    db_content = get_content_by_id(db, content_id)
    if not db_content:
        return None

    update_data = content_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_content, field, value)

    db_content.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_content)
    return db_content


# ==================== User Progress Services ====================


def get_user_progress(
    db: Session, user_id: int, content_id: int
) -> Optional[UserProgress]:
    """Get user's progress for specific content."""
    return (
        db.query(UserProgress)
        .filter(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.content_id == content_id,
            )
        )
        .first()
    )


def get_user_all_progress(db: Session, user_id: int) -> List[UserProgress]:
    """Get all progress records for a user."""
    return (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id)
        .options(joinedload(UserProgress.content))
        .all()
    )


def create_or_update_progress(
    db: Session, user_id: int, content_id: int, progress_update: UserProgressUpdate
) -> UserProgress:
    """Create or update user progress."""
    db_progress = get_user_progress(db, user_id, content_id)

    if not db_progress:
        # Create new progress record
        db_progress = UserProgress(
            user_id=user_id,
            content_id=content_id,
            is_started=True,
            created_at=datetime.utcnow(),
        )
        db.add(db_progress)

    # Update fields
    update_data = progress_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_progress, field, value)

    db_progress.last_accessed = datetime.utcnow()
    db_progress.updated_at = datetime.utcnow()

    # Set completed_at if marking as completed
    if progress_update.is_completed and not db_progress.completed_at:
        db_progress.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(db_progress)
    return db_progress


# ==================== Learning Path Services ====================


def get_learning_path(db: Session, path_id: int) -> Optional[LearningPath]:
    """Get learning path by ID with items."""
    return (
        db.query(LearningPath)
        .filter(LearningPath.id == path_id)
        .options(joinedload(LearningPath.items))
        .first()
    )


def get_learning_path_by_slug(db: Session, slug: str) -> Optional[LearningPath]:
    """Get learning path by slug."""
    return (
        db.query(LearningPath)
        .filter(LearningPath.slug == slug)
        .options(joinedload(LearningPath.items))
        .first()
    )


def list_learning_paths(
    db: Session,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[LearningPath]:
    """List all learning paths."""
    query = db.query(LearningPath).options(joinedload(LearningPath.items))

    if min_age is not None:
        query = query.filter(
            or_(
                LearningPath.min_age == None,
                LearningPath.min_age <= min_age,
            )
        )

    if max_age is not None:
        query = query.filter(
            or_(
                LearningPath.max_age == None,
                LearningPath.max_age >= max_age,
            )
        )

    return query.offset(skip).limit(limit).all()


def create_learning_path(db: Session, path: LearningPathCreate) -> LearningPath:
    """Create a new learning path with items."""
    db_path = LearningPath(
        title=path.title,
        slug=path.slug,
        description=path.description,
        min_age=path.min_age,
        max_age=path.max_age,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_path)
    db.flush()  # Get the ID without committing

    # Add items
    for item in path.items:
        db_item = LearningPathItem(
            learning_path_id=db_path.id,
            content_id=item.content_id,
            order=item.order,
            is_required=item.is_required,
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_path)
    return db_path


def get_learning_path_progress(
    db: Session, user_id: int, path_id: int
) -> dict:
    """Calculate user's progress through a learning path."""
    path = get_learning_path(db, path_id)
    if not path:
        return None

    total_items = len(path.items)
    if total_items == 0:
        return {
            "completion_percent": 0.0,
            "items_completed": 0,
            "total_items": 0,
        }

    # Get user progress for all content in the path
    content_ids = [item.content_id for item in path.items]
    completed_items = (
        db.query(UserProgress)
        .filter(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.content_id.in_(content_ids),
                UserProgress.is_completed == True,
            )
        )
        .count()
    )

    completion_percent = (completed_items / total_items) * 100

    return {
        "completion_percent": completion_percent,
        "items_completed": completed_items,
        "total_items": total_items,
    }


# ==================== Trading Permission Services ====================


def list_trading_permissions(db: Session) -> List[TradingPermission]:
    """List all trading permissions."""
    return db.query(TradingPermission).all()


def get_trading_permission(db: Session, permission_id: int) -> Optional[TradingPermission]:
    """Get trading permission by ID."""
    return (
        db.query(TradingPermission)
        .filter(TradingPermission.id == permission_id)
        .first()
    )


def create_trading_permission(
    db: Session, permission: TradingPermissionCreate
) -> TradingPermission:
    """Create a new trading permission."""
    db_permission = TradingPermission(
        **permission.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


# ==================== User Permission Services ====================


def get_user_permissions(db: Session, user_id: int) -> List[UserPermission]:
    """Get all permissions for a user."""
    return (
        db.query(UserPermission)
        .filter(UserPermission.user_id == user_id)
        .options(joinedload(UserPermission.permission))
        .all()
    )


def get_user_permission(
    db: Session, user_id: int, permission_id: int
) -> Optional[UserPermission]:
    """Get specific user permission."""
    return (
        db.query(UserPermission)
        .filter(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id,
            )
        )
        .first()
    )


def grant_permission(
    db: Session,
    user_id: int,
    permission_id: int,
    granted_by_user_id: Optional[int] = None,
    override_reason: Optional[str] = None,
) -> UserPermission:
    """Grant a permission to a user."""
    db_user_permission = get_user_permission(db, user_id, permission_id)

    if not db_user_permission:
        db_user_permission = UserPermission(
            user_id=user_id,
            permission_id=permission_id,
            created_at=datetime.utcnow(),
        )
        db.add(db_user_permission)

    db_user_permission.is_granted = True
    db_user_permission.granted_by_user_id = granted_by_user_id
    db_user_permission.override_reason = override_reason
    db_user_permission.granted_at = datetime.utcnow()
    db_user_permission.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_user_permission)
    return db_user_permission


def check_permission_eligibility(
    db: Session, user_id: int, permission_id: int
) -> dict:
    """Check if user is eligible for a permission."""
    permission = get_trading_permission(db, permission_id)
    if not permission:
        return {"is_eligible": False, "missing_requirements": ["Permission not found"]}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"is_eligible": False, "missing_requirements": ["User not found"]}

    missing_requirements = []
    completed_requirements = []

    # Check age requirement
    if permission.min_age is not None:
        # For now, we'll assume user.birthdate is a string or None
        # In production, you'd calculate age from birthdate
        if user.birthdate is None:
            missing_requirements.append("Birthdate verification required")
        # Add actual age check here when birthdate is implemented

    # Check learning path requirement
    if permission.required_learning_path_id:
        progress = get_learning_path_progress(
            db, user_id, permission.required_learning_path_id
        )
        if progress and progress["completion_percent"] >= 100:
            completed_requirements.append(
                f"Completed learning path (ID: {permission.required_learning_path_id})"
            )
        else:
            missing_requirements.append(
                f"Complete learning path (ID: {permission.required_learning_path_id})"
            )

    # Check content requirement
    if permission.required_content_id:
        user_progress = get_user_progress(db, user_id, permission.required_content_id)
        if user_progress and user_progress.is_completed:
            if permission.required_score:
                if user_progress.score and user_progress.score >= permission.required_score:
                    completed_requirements.append(
                        f"Passed content with required score ({user_progress.score}%)"
                    )
                else:
                    missing_requirements.append(
                        f"Score {permission.required_score}% or higher on content (ID: {permission.required_content_id})"
                    )
            else:
                completed_requirements.append(
                    f"Completed content (ID: {permission.required_content_id})"
                )
        else:
            missing_requirements.append(
                f"Complete content (ID: {permission.required_content_id})"
            )

    # Check if user permission already granted
    user_permission = get_user_permission(db, user_id, permission_id)
    is_granted = user_permission and user_permission.is_granted

    is_eligible = len(missing_requirements) == 0

    return {
        "is_granted": is_granted,
        "is_eligible": is_eligible,
        "missing_requirements": missing_requirements,
        "completed_requirements": completed_requirements,
        "requires_guardian_approval": permission.requires_guardian_approval,
    }


def grant_permission_if_eligible(
    db: Session, user_id: int, permission_id: int
) -> Optional[UserPermission]:
    """Automatically grant permission if user is eligible."""
    eligibility = check_permission_eligibility(db, user_id, permission_id)

    if eligibility["is_eligible"] and not eligibility["is_granted"]:
        # Auto-grant if no guardian approval required OR user is adult
        user = db.query(User).filter(User.id == user_id).first()
        if not eligibility["requires_guardian_approval"] or user.is_adult:
            return grant_permission(
                db,
                user_id,
                permission_id,
                granted_by_user_id=None,  # Auto-granted by system
                override_reason="Automatically granted upon completing requirements",
            )

    return None
