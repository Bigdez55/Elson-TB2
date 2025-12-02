"""Authentication routes for two-factor authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_two_factor_auth
from app.core.auth.two_factor import TwoFactorAuth
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserTwoFactorCreate,
    UserTwoFactorVerify,
    UserTwoFactorResponse,
    UserTwoFactorStatus,
)

# Dependencies
from app.routes.deps import get_current_user, get_current_user_with_role

router = APIRouter(
    prefix="/auth/2fa",
    tags=["auth", "two-factor"],
)


@router.get("/status", response_model=UserTwoFactorStatus)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
):
    """Get the 2FA status for the current user."""
    return {"enabled": current_user.two_factor_enabled}


@router.post("/generate", response_model=UserTwoFactorResponse)
async def generate_2fa_secret(
    current_user: User = Depends(get_current_user),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Generate a new 2FA secret for the current user."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled",
        )

    # Generate a new secret
    secret = two_factor_auth.generate_totp_secret()
    
    # Generate QR code URI
    qr_uri = two_factor_auth.get_totp_uri(secret, current_user.email)
    
    # Generate backup codes
    backup_codes = two_factor_auth.generate_backup_codes()
    
    return {
        "secret": secret,
        "qr_uri": qr_uri,
        "backup_codes": backup_codes,
    }


@router.post("/enable", status_code=status.HTTP_200_OK)
async def enable_2fa(
    two_factor_data: UserTwoFactorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Enable 2FA for the current user."""
    result = two_factor_auth.setup_2fa(db, current_user.id, two_factor_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to enable two-factor authentication",
        )
    return {"status": "Two-factor authentication enabled successfully"}


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    verify_data: UserTwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Disable 2FA for the current user."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )
    
    # Verify the TOTP code before disabling
    if not two_factor_auth.verify_totp(current_user.two_factor_secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )
    
    result = two_factor_auth.disable_2fa(db, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disable two-factor authentication",
        )
    return {"status": "Two-factor authentication disabled successfully"}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_2fa(
    verify_data: UserTwoFactorVerify,
    current_user: User = Depends(get_current_user),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Verify a 2FA code for the current user."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )
    
    if not two_factor_auth.verify_totp(current_user.two_factor_secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )
    
    return {"status": "Two-factor authentication verified successfully"}


@router.post("/backup", status_code=status.HTTP_200_OK)
async def verify_backup_code(
    verify_data: UserTwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Verify a backup code for 2FA recovery."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )
    
    if not two_factor_auth.verify_backup_code(db, current_user.id, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup code",
        )
    
    return {"status": "Backup code verified successfully"}


# Admin-only endpoints for managing 2FA
@router.post("/admin/disable/{user_id}", status_code=status.HTTP_200_OK)
async def admin_disable_2fa(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role(UserRole.ADMIN)),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
):
    """Admin endpoint to disable 2FA for a user."""
    result = two_factor_auth.disable_2fa(db, user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disable two-factor authentication",
        )
    return {"status": "Two-factor authentication disabled successfully"}

@router.get("/guardian-requirement")
async def check_guardian_2fa_requirement(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if 2FA is required for the current user based on guardian status."""
    # Check if the user is a guardian (has minor accounts)
    from app.models.account import Account
    is_guardian = db.query(Account).filter(
        Account.guardian_id == current_user.id,
        Account.is_active == True
    ).first() is not None
    
    requires_2fa = is_guardian and not current_user.two_factor_enabled
    
    return {
        "is_guardian": is_guardian,
        "requires_2fa": requires_2fa,
        "two_factor_enabled": current_user.two_factor_enabled
    }