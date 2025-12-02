"""Guardian-specific authentication requirements.

This module implements enhanced security requirements for guardian accounts,
including mandatory two-factor authentication for accounts with minor dependents.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.account import Account
from app.core.auth.two_factor import TwoFactorAuth, get_two_factor_auth
from app.core.config import settings


async def require_guardian_2fa(
    user: User,
    db: Session,
    two_factor_auth: TwoFactorAuth,
) -> None:
    """Check if a user is a guardian and enforce 2FA requirements.
    
    Args:
        user: The user to check
        db: Database session
        two_factor_auth: TwoFactorAuth instance
        
    Raises:
        HTTPException: If the user is a guardian without 2FA enabled
    """
    # Skip check if 2FA is already enabled
    if user.two_factor_enabled:
        return
        
    # Check if user is a guardian for any minor accounts
    is_guardian = db.query(Account).filter(
        Account.guardian_id == user.id,
        Account.is_active == True
    ).first() is not None
    
    # Require 2FA for guardian accounts
    if is_guardian and not user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Two-factor authentication is required for guardian accounts. "
                  "Please enable 2FA to continue.",
            headers={"X-2FA-Required": "true"},
        )


async def check_guardian_authentication(
    user: User,
    db: Session = Depends(get_db),
    two_factor_auth: TwoFactorAuth = Depends(get_two_factor_auth),
) -> User:
    """Middleware-like dependency to enforce guardian authentication requirements.
    
    Args:
        user: The authenticated user
        db: Database session
        two_factor_auth: TwoFactorAuth instance
        
    Returns:
        The user if all requirements are met
        
    Raises:
        HTTPException: If the user doesn't meet guardian authentication requirements
    """
    await require_guardian_2fa(user, db, two_factor_auth)
    return user


def is_guardian(user: User, db: Session) -> bool:
    """Check if a user is a guardian for any minor accounts.
    
    Args:
        user: The user to check
        db: Database session
        
    Returns:
        True if the user is a guardian, False otherwise
    """
    return db.query(Account).filter(
        Account.guardian_id == user.id,
        Account.is_active == True
    ).first() is not None


def get_guardian_stats(user: User, db: Session) -> Dict[str, Any]:
    """Get statistics about a guardian's minor accounts.
    
    Args:
        user: The guardian user
        db: Database session
        
    Returns:
        Dictionary with guardian statistics
    """
    # Return empty stats if user is not a guardian
    if not is_guardian(user, db):
        return {
            "is_guardian": False,
            "minor_count": 0,
            "total_trades": 0,
            "pending_approvals": 0,
        }
    
    # Get counts of minor accounts
    minor_count = db.query(func.count(Account.id)).filter(
        Account.guardian_id == user.id,
        Account.is_active == True
    ).scalar() or 0
    
    # Get counts of trades across all minor accounts
    from app.models.trade import Trade, TradeStatus
    
    minor_user_ids = db.query(Account.user_id).filter(
        Account.guardian_id == user.id,
        Account.is_active == True
    ).all()
    minor_user_ids = [uid[0] for uid in minor_user_ids]
    
    total_trades = db.query(func.count(Trade.id)).filter(
        Trade.user_id.in_(minor_user_ids)
    ).scalar() or 0
    
    pending_approvals = db.query(func.count(Trade.id)).filter(
        Trade.user_id.in_(minor_user_ids),
        Trade.requires_guardian_approval == True,
        Trade.guardian_approved.is_(None)
    ).scalar() or 0
    
    return {
        "is_guardian": True,
        "minor_count": minor_count,
        "total_trades": total_trades,
        "pending_approvals": pending_approvals,
    }