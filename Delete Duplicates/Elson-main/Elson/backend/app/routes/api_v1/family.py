from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path, status
from sqlalchemy.orm import Session
from datetime import datetime, date
import logging

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.models.trade import Trade, TradeStatus
from app.core.auth import get_current_active_user, get_current_user_with_permissions
from app.core.auth.two_factor import TwoFactorAuth, get_two_factor_auth
from app.core.auth.guardian_auth import check_guardian_authentication, get_guardian_stats
from app.services.notifications import NotificationService
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    UserTwoFactorStatus, 
    UserTwoFactorCreate, 
    UserTwoFactorResponse
)
from app.schemas.family import (
    MinorCreate,
    MinorResponse,
    GuardianMinorRelationship,
    ApproveTradeRequest,
    MinorTradeResponse,
    GuardianStatusResponse,
    GuardianNotificationResponse
)

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/family", tags=["family", "guardian"])

@router.post("/minor", response_model=MinorResponse)
async def create_minor_account(
    minor_data: MinorCreate,
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Create a new minor account as a guardian.
    Only adults can create minor accounts.
    """
    # Check that the current user is an adult
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only adult users can create minor accounts"
        )
    
    # Validate birthdate (must be under 18)
    today = date.today()
    birthdate = minor_data.birthdate
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    
    if age >= 18:
        raise HTTPException(
            status_code=400,
            detail="Minor must be under 18 years old"
        )
    
    # Create the minor user
    minor_user = User(
        email=minor_data.email,
        hashed_password="temporary",  # This would be hashed properly in a real system
        first_name=minor_data.first_name,
        last_name=minor_data.last_name,
        role=UserRole.MINOR,
        birthdate=minor_data.birthdate,
        is_active=True
    )
    
    # Sync the encrypted email and other PII
    minor_user.sync_encrypted_email()
    
    db.add(minor_user)
    db.commit()
    db.refresh(minor_user)
    
    # Create the custodial account linking the minor to the guardian
    custodial_account = Account(
        user_id=minor_user.id,
        guardian_id=current_user.id,
        account_type=AccountType.CUSTODIAL,
        account_number=f"CUST-{minor_user.id}-{datetime.utcnow().strftime('%Y%m%d')}",
        institution="Elson Wealth"
    )
    
    # Sync encrypted account number
    custodial_account.sync_encrypted_account_number()
    
    db.add(custodial_account)
    db.commit()
    
    # Return the minor user data
    return MinorResponse(
        id=minor_user.id,
        email=minor_user.email,
        first_name=minor_user.first_name,
        last_name=minor_user.last_name,
        birthdate=minor_user.birthdate,
        guardian_id=current_user.id,
        guardian_name=current_user.full_name,
        account_id=custodial_account.id
    )

@router.get("/minors", response_model=List[MinorResponse])
async def get_my_minors(
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Get all minors under the guardianship of the current user.
    """
    # Check that the current user is an adult
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only adult users can view their minor accounts"
        )
    
    # Query for accounts where the current user is the guardian
    custodial_accounts = db.query(Account).filter(
        Account.guardian_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).all()
    
    # Get the minor users
    minor_responses = []
    for account in custodial_accounts:
        minor = db.query(User).filter(User.id == account.user_id).first()
        if minor and minor.role == UserRole.MINOR:
            minor_responses.append(
                MinorResponse(
                    id=minor.id,
                    email=minor.email,
                    first_name=minor.first_name,
                    last_name=minor.last_name,
                    birthdate=minor.birthdate,
                    guardian_id=current_user.id,
                    guardian_name=current_user.full_name,
                    account_id=account.id
                )
            )
    
    return minor_responses

@router.get("/guardian", response_model=UserResponse)
async def get_my_guardian(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the guardian info for the current minor user.
    """
    # Check that the current user is a minor
    if current_user.role != UserRole.MINOR:
        raise HTTPException(
            status_code=403,
            detail="Only minor users can view their guardian"
        )
    
    # Query for the custodial account
    custodial_account = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).first()
    
    if not custodial_account:
        raise HTTPException(
            status_code=404,
            detail="No guardian found for this user"
        )
    
    # Get the guardian user
    guardian = db.query(User).filter(User.id == custodial_account.guardian_id).first()
    if not guardian:
        raise HTTPException(
            status_code=404,
            detail="Guardian not found"
        )
    
    return UserResponse(
        id=guardian.id,
        email=guardian.email,
        first_name=guardian.first_name,
        last_name=guardian.last_name,
        is_active=guardian.is_active,
        role=guardian.role.value
    )

@router.get("/trades/pending", response_model=List[MinorTradeResponse])
async def get_pending_trades(
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Get all pending trades from minors that need approval.
    Only for guardians.
    """
    # Check that the current user is an adult
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only adult users can view pending minor trades"
        )
    
    # Get all minor accounts under this guardian
    minor_accounts = db.query(Account).filter(
        Account.guardian_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).all()
    
    minor_user_ids = [account.user_id for account in minor_accounts]
    
    # Get all pending trades for these minors
    pending_trades = db.query(Trade).filter(
        Trade.user_id.in_(minor_user_ids),
        Trade.status == TradeStatus.PENDING_APPROVAL
    ).all()
    
    # Format the response
    trade_responses = []
    for trade in pending_trades:
        minor = db.query(User).filter(User.id == trade.user_id).first()
        if minor:
            trade_responses.append(
                MinorTradeResponse(
                    trade_id=trade.id,
                    minor_id=minor.id,
                    minor_name=f"{minor.first_name} {minor.last_name}",
                    symbol=trade.symbol,
                    quantity=trade.quantity,
                    price=trade.price,
                    trade_type=trade.trade_type,
                    created_at=trade.created_at,
                    status=trade.status.value
                )
            )
    
    return trade_responses

@router.post("/trade/{trade_id}/approve", response_model=MinorTradeResponse)
async def approve_minor_trade(
    trade_id: int = Path(...),
    approval_data: ApproveTradeRequest = Body(...),
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a minor's trade request.
    Only guardians can approve trades for their minors.
    """
    # Check that the current user is an adult
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only adult users can approve minor trades"
        )
    
    # Get the trade
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=404,
            detail="Trade not found"
        )
    
    # Verify that the trade is pending approval
    if trade.status != TradeStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Trade is not pending approval. Current status: {trade.status.value}"
        )
    
    # Get the minor user
    minor = db.query(User).filter(User.id == trade.user_id).first()
    if not minor or minor.role != UserRole.MINOR:
        raise HTTPException(
            status_code=400,
            detail="Trade is not from a minor user"
        )
    
    # Verify that the current user is the guardian for this minor
    custodial_account = db.query(Account).filter(
        Account.user_id == minor.id,
        Account.guardian_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).first()
    
    if not custodial_account:
        raise HTTPException(
            status_code=403,
            detail="You are not the guardian for this minor"
        )
    
    # Update the trade status based on the approval decision
    if approval_data.approved:
        trade.status = TradeStatus.PENDING  # Approved, now ready for execution
        trade.approved_by_user_id = current_user.id
        trade.approved_at = datetime.utcnow()
    else:
        trade.status = TradeStatus.REJECTED
        trade.rejection_reason = approval_data.rejection_reason
    
    db.commit()
    db.refresh(trade)
    
    # Send notification to the minor about the trade status
    notification_service = NotificationService(db)
    notification_service.send_trade_status_notification(trade)
    
    # Return the updated trade
    return MinorTradeResponse(
        trade_id=trade.id,
        minor_id=minor.id,
        minor_name=f"{minor.first_name} {minor.last_name}",
        symbol=trade.symbol,
        quantity=trade.quantity,
        price=trade.price,
        trade_type=trade.trade_type,
        created_at=trade.created_at,
        status=trade.status.value,
        approved_at=trade.approved_at,
        rejection_reason=trade.rejection_reason
    )
    
@router.get("/guardian/status", response_model=GuardianStatusResponse)
async def get_guardian_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get guardian status and statistics, including whether 2FA is required.
    """
    # Check if the user is a guardian
    stats = get_guardian_stats(current_user, db)
    
    return GuardianStatusResponse(
        is_guardian=stats["is_guardian"],
        minor_count=stats["minor_count"],
        total_trades=stats["total_trades"],
        pending_approvals=stats["pending_approvals"],
        two_factor_enabled=current_user.two_factor_enabled,
        requires_2fa_setup=stats["is_guardian"] and not current_user.two_factor_enabled
    )
    
@router.get("/notifications", response_model=List[GuardianNotificationResponse])
async def get_guardian_notifications(
    unread_only: bool = Query(False, description="Filter to only show unread notifications"),
    min_account_id: Optional[int] = Query(None, description="Filter by minor account ID"),
    limit: int = Query(50, description="Maximum number of notifications to return"),
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Get notifications for the guardian, optionally filtered by unread status or minor account.
    """
    # Check that the current user is an adult/guardian
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only guardian users can access this endpoint"
        )
    
    # Import here to avoid circular imports
    from app.models.notification import Notification
    
    # Base query for notifications
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    # Apply filters
    if unread_only:
        query = query.filter(Notification.is_read == False)
        
    if min_account_id:
        # Verify the minor account belongs to this guardian
        custodial_account = db.query(Account).filter(
            Account.id == min_account_id,
            Account.guardian_id == current_user.id,
            Account.account_type == AccountType.CUSTODIAL
        ).first()
        
        if not custodial_account:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this minor account's notifications"
            )
            
        query = query.filter(Notification.minor_account_id == min_account_id)
    
    # Order by timestamp descending (newest first) and limit results
    notifications = query.order_by(Notification.timestamp.desc()).limit(limit).all()
    
    # Format the notifications for the response
    response_notifications = []
    for notification in notifications:
        # Get minor name if we have a minor account ID
        minor_name = None
        if notification.minor_account_id:
            account = db.query(Account).filter(Account.id == notification.minor_account_id).first()
            if account:
                minor = db.query(User).filter(User.id == account.user_id).first()
                if minor:
                    minor_name = minor.full_name
        
        # Get trade details if we have a trade ID
        symbol = None
        quantity = None
        price = None
        trade_type = None
        if notification.trade_id:
            trade = db.query(Trade).filter(Trade.id == notification.trade_id).first()
            if trade:
                symbol = trade.symbol
                quantity = trade.quantity
                price = trade.price
                trade_type = trade.trade_type
        
        # Extract data from JSON if available
        data = notification.data or {}
        
        # Create the response object
        response_notifications.append(
            GuardianNotificationResponse(
                id=notification.id,
                minor_account_id=notification.minor_account_id,
                minor_name=minor_name or data.get("minor_name", "Unknown"),
                type=notification.type,
                message=notification.message,
                requires_action=notification.requires_action,
                timestamp=notification.timestamp,
                is_read=notification.is_read,
                trade_id=notification.trade_id,
                symbol=symbol or data.get("symbol"),
                quantity=quantity or data.get("quantity"),
                price=price or data.get("price"),
                trade_type=trade_type or data.get("trade_type")
            )
        )
    
    return response_notifications

@router.post("/notifications/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: str = Path(..., description="ID of the notification to mark as read"),
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Mark a guardian notification as read.
    """
    # Check that the current user is an adult/guardian
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only guardian users can access this endpoint"
        )
    
    # Import here to avoid circular imports
    from app.models.notification import Notification
    
    # Find the notification
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    # Mark as read
    notification.is_read = True
    db.commit()
    
    return {"success": True, "message": "Notification marked as read"}


# ===== Minor Account Permissions Endpoints =====

class MinorPermissionsResponse(BaseModel):
    """Schema for minor account permissions."""
    trading: bool = False
    withdrawals: bool = False
    learning: bool = True
    deposits: bool = True
    apiAccess: bool = False
    recurringInvestments: bool = False
    transferBetweenAccounts: bool = False
    advancedOrders: bool = False

class MinorPermissionsUpdate(BaseModel):
    """Schema for updating minor account permissions."""
    trading: Optional[bool] = None
    withdrawals: Optional[bool] = None
    learning: Optional[bool] = None
    deposits: Optional[bool] = None
    apiAccess: Optional[bool] = None
    recurringInvestments: Optional[bool] = None
    transferBetweenAccounts: Optional[bool] = None
    advancedOrders: Optional[bool] = None


@router.get("/minors/{minor_id}/permissions", response_model=MinorPermissionsResponse)
async def get_minor_permissions(
    minor_id: int = Path(..., description="ID of the minor account"),
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Get permission settings for a minor account.
    """
    # Check that the current user is an adult/guardian
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only guardian users can access this endpoint"
        )
    
    # Check if the current user is the guardian for this minor
    from app.models.account import Account, AccountType
    custodial_account = db.query(Account).filter(
        Account.user_id == minor_id,
        Account.guardian_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).first()
    
    if not custodial_account:
        raise HTTPException(
            status_code=403,
            detail="You are not the guardian for this minor"
        )
    
    # Get the minor user
    minor = db.query(User).filter(User.id == minor_id).first()
    if not minor or minor.role != UserRole.MINOR:
        raise HTTPException(
            status_code=404,
            detail="Minor account not found"
        )
    
    # Get permissions from EducationService
    from app.services.education_service import EducationService
    education_service = EducationService(db)
    
    # Check specific permission types
    has_trading = education_service.check_user_has_permission(minor_id, "trade_stocks")
    has_withdrawals = education_service.check_user_has_permission(minor_id, "withdrawals")
    has_api_access = education_service.check_user_has_permission(minor_id, "api_access")
    has_recurring = education_service.check_user_has_permission(minor_id, "recurring_investments")
    has_transfers = education_service.check_user_has_permission(minor_id, "transfer_between_accounts")
    has_advanced_orders = education_service.check_user_has_permission(minor_id, "advanced_orders")
    
    # Learning and deposits are enabled by default unless explicitly disabled
    has_learning = not education_service.check_user_has_permission(minor_id, "disable_learning")
    has_deposits = not education_service.check_user_has_permission(minor_id, "disable_deposits")
    
    return MinorPermissionsResponse(
        trading=has_trading,
        withdrawals=has_withdrawals,
        learning=has_learning,
        deposits=has_deposits,
        apiAccess=has_api_access,
        recurringInvestments=has_recurring,
        transferBetweenAccounts=has_transfers,
        advancedOrders=has_advanced_orders
    )


@router.put("/minors/{minor_id}/permissions", response_model=MinorPermissionsResponse)
async def update_minor_permissions(
    minor_id: int = Path(..., description="ID of the minor account"),
    permissions: MinorPermissionsUpdate = Body(...),
    current_user: User = Depends(check_guardian_authentication),
    db: Session = Depends(get_db)
):
    """
    Update permission settings for a minor account.
    """
    # Check that the current user is an adult/guardian
    if current_user.role != UserRole.ADULT:
        raise HTTPException(
            status_code=403,
            detail="Only guardian users can access this endpoint"
        )
    
    # Check if the current user is the guardian for this minor
    from app.models.account import Account, AccountType
    custodial_account = db.query(Account).filter(
        Account.user_id == minor_id,
        Account.guardian_id == current_user.id,
        Account.account_type == AccountType.CUSTODIAL
    ).first()
    
    if not custodial_account:
        raise HTTPException(
            status_code=403,
            detail="You are not the guardian for this minor"
        )
    
    # Get the minor user
    minor = db.query(User).filter(User.id == minor_id).first()
    if not minor or minor.role != UserRole.MINOR:
        raise HTTPException(
            status_code=404,
            detail="Minor account not found"
        )
    
    # Update permissions using EducationService
    from app.services.education_service import EducationService
    from app.models.education import TradingPermission
    service = EducationService(db)
    
    # Get or create permission IDs for each permission type
    permission_types = {
        "trade_stocks": permissions.trading,
        "withdrawals": permissions.withdrawals,
        "api_access": permissions.apiAccess,
        "recurring_investments": permissions.recurringInvestments,
        "transfer_between_accounts": permissions.transferBetweenAccounts,
        "advanced_orders": permissions.advancedOrders,
        "disable_learning": permissions.learning is not None and not permissions.learning,
        "disable_deposits": permissions.deposits is not None and not permissions.deposits
    }
    
    # For each permission type, grant or revoke as needed
    for permission_type, should_grant in permission_types.items():
        if should_grant is None:
            # Skip if not specified in the update
            continue
            
        # Get the permission by type
        permission = db.query(TradingPermission).filter(
            TradingPermission.permission_type == permission_type
        ).first()
        
        # Create the permission if it doesn't exist
        if not permission:
            permission = TradingPermission(
                name=permission_type.replace("_", " ").title(),
                description=f"Permission to {permission_type.replace('_', ' ')}",
                permission_type=permission_type,
                requires_guardian_approval=True
            )
            db.add(permission)
            db.commit()
            db.refresh(permission)
        
        # Grant or revoke permission
        if should_grant:
            service.grant_user_permission(
                minor_id, 
                permission.id, 
                granted_by_id=current_user.id
            )
        else:
            service.revoke_user_permission(minor_id, permission.id)
    
    # Return the updated permissions
    return await get_minor_permissions(minor_id, current_user, db)