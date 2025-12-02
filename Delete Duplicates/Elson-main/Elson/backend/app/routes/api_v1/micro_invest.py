from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta

from ...db.database import get_db
from ...models.trade import Trade, TradeSource, InvestmentType, TradeStatus
from ...models.user_settings import UserSettings
from ...services.micro_invest_service import MicroInvestService
from ...services.investment_service import InvestmentService
from ...services.market_data import MarketDataService
from ...core.alerts import AlertService
from ...schemas.micro_invest import (
    RoundupTransactionCreate, UserSettingsCreate, 
    UserSettingsUpdate, RoundupTransactionResponse,
    UserSettingsResponse, MicroInvestmentCreate,
    MicroInvestStats, RoundupSummary
)
from ...core.auth import get_current_user, get_current_user_with_permissions
from ...models.user import User, UserRole
from ...core.config import settings

router = APIRouter()

# Helper function to initialize the MicroInvestService
def get_micro_invest_service(db: Session = Depends(get_db)):
    market_data_service = MarketDataService()
    alert_service = AlertService(db)
    investment_service = InvestmentService(
        db=db,
        market_data_service=market_data_service,
        trading_service=None,  # Will be lazy-loaded if needed
        order_aggregator=None  # Will be lazy-loaded if needed
    )
    return MicroInvestService(
        db=db,
        market_data_service=market_data_service,
        investment_service=investment_service,
        alert_service=alert_service
    )

# User Settings Endpoints

@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_micro_invest_settings(
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Get user's micro-investing settings."""
    settings = service.get_user_settings(current_user.id)
    if not settings:
        # Create default settings if none exist
        settings_data = UserSettingsCreate(
            user_id=current_user.id,
            micro_investing_enabled=False,
            roundup_enabled=False,
            roundup_multiplier=1.0,
            roundup_frequency="weekly",
            roundup_threshold=5.0,
            micro_invest_target_type="default_portfolio"
        )
        settings = service.create_user_settings(settings_data)
    
    return settings

@router.post("/settings", response_model=UserSettingsResponse)
async def create_micro_invest_settings(
    settings_data: UserSettingsCreate,
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service),
    db: Session = Depends(get_db)
):
    """Create or update micro-investing settings."""
    # Override user_id with current user's ID
    settings_data.user_id = current_user.id
    
    # Check if settings already exist
    existing_settings = service.get_user_settings(current_user.id)
    if existing_settings:
        # Convert to update data
        update_data = UserSettingsUpdate(**settings_data.dict(exclude={"user_id"}))
        return service.update_user_settings(current_user.id, update_data)
    
    return service.create_user_settings(settings_data)

@router.patch("/settings", response_model=UserSettingsResponse)
async def update_micro_invest_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Update micro-investing settings."""
    return service.update_user_settings(current_user.id, settings_data)

# Roundup Endpoints

@router.post("/roundups", response_model=RoundupTransactionResponse)
async def create_roundup_transaction(
    transaction_data: RoundupTransactionCreate,
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Create a new roundup transaction."""
    # Override user_id with current user's ID
    transaction_data.user_id = current_user.id
    return service.process_transaction_for_roundup(transaction_data)

@router.get("/roundups", response_model=Dict[str, Any])
async def get_roundup_transactions(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("transaction_date", 
                                  description="Field to sort by: 'transaction_date', 'transaction_amount', 'roundup_amount'"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's roundup transactions with filtering, pagination and sorting."""
    query = db.query(Trade.RoundupTransaction).filter(
        Trade.RoundupTransaction.user_id == current_user.id
    )
    
    # Apply filters
    if status:
        query = query.filter(Trade.RoundupTransaction.status == status)
    
    if start_date:
        query = query.filter(Trade.RoundupTransaction.transaction_date >= start_date)
        
    if end_date:
        query = query.filter(Trade.RoundupTransaction.transaction_date <= end_date)
    
    # Count total for pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Trade.RoundupTransaction, sort_by, Trade.RoundupTransaction.transaction_date)
    if sort_desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    return {
        "transactions": query.all(),
        "total": total
    }

@router.get("/roundups/summary", response_model=RoundupSummary)
async def get_roundups_summary(
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Get a summary of roundup activity."""
    return service.get_roundup_summary(current_user.id)

@router.post("/roundups/invest", response_model=Dict[str, Any])
async def invest_pending_roundups(
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Manually invest all pending roundups."""
    return service.invest_pending_roundups(current_user.id)

# Micro-investment Endpoints

@router.post("/micro-invest", response_model=Dict[str, Any])
async def create_micro_investment(
    investment_data: MicroInvestmentCreate,
    current_user: User = Depends(get_current_user_with_permissions(["fractional_shares"])),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Create a micro-investment (as small as $0.01)."""
    trade = service.create_micro_investment(current_user.id, investment_data)
    return {
        "trade_id": trade.id,
        "symbol": trade.symbol,
        "amount": float(trade.investment_amount),
        "status": trade.status.value,
        "created_at": trade.created_at
    }

@router.get("/micro-invest/stats", response_model=MicroInvestStats)
async def get_micro_invest_statistics(
    current_user: User = Depends(get_current_user),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Get statistics for micro-investing activity."""
    return service.get_micro_invest_statistics(current_user.id)

# Calculator endpoints

@router.get("/calculate-roundup", response_model=Dict[str, float])
async def calculate_roundup_amount(
    amount: float = Query(..., gt=0),
    multiplier: float = Query(1.0, ge=1.0, le=10.0),
    service: MicroInvestService = Depends(get_micro_invest_service)
):
    """Calculate the roundup amount for a transaction."""
    roundup = service.calculate_roundup(amount, multiplier)
    return {
        "original_amount": amount,
        "roundup_amount": roundup,
        "multiplier": multiplier,
        "total_amount": amount + roundup
    }

# Educational content integration

@router.post("/complete-education")
async def complete_micro_invest_education(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark micro-investing educational module as completed."""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )
    
    settings.completed_micro_invest_education = True
    db.commit()
    
    return {"status": "success", "message": "Educational module marked as completed"}