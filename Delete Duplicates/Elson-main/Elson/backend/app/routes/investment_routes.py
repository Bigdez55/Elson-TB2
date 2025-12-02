"""Routes for dollar-based investments and fractional shares."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from app.db.database import get_db
from app.models.user import User, UserRole
from app.routes.deps import get_current_user, get_current_user_with_role
from app.schemas.trade import (
    DollarBasedInvestmentCreate,
    RecurringInvestmentCreate,
    RecurringInvestmentUpdate,
    RecurringInvestmentResponse,
    TradeResponse,
    TradeAggregationResponse
)
from app.services.investment_service import InvestmentService
from app.services.market_data import MarketDataService
from app.services.trading import TradingService
from app.services.order_aggregator import OrderAggregator
from app.core.config import settings

router = APIRouter(
    prefix="/api/v1/investments",
    tags=["investments"],
)


def get_investment_service(
    db: Session = Depends(get_db),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
    trading_service: TradingService = Depends(lambda: TradingService(db=db)),
    order_aggregator: OrderAggregator = Depends(lambda: OrderAggregator(db=db, market_data_service=market_data_service))
) -> InvestmentService:
    """Dependency to get the investment service."""
    return InvestmentService(
        db=db,
        market_data_service=market_data_service,
        trading_service=trading_service,
        order_aggregator=order_aggregator
    )


@router.post("/dollar-based", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_dollar_based_investment(
    investment: DollarBasedInvestmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Create a new dollar-based investment."""
    trade = investment_service.create_dollar_based_investment(
        user_id=current_user.id,
        investment_data=investment
    )
    
    # Trigger aggregation in the background if not auto-aggregated
    if not settings.AUTO_AGGREGATE_FRACTIONAL_ORDERS:
        background_tasks.add_task(investment_service.aggregate_investments)
    
    return trade


@router.post("/recurring", response_model=RecurringInvestmentResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_investment(
    investment: RecurringInvestmentCreate,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Create a new recurring investment plan."""
    recurring = investment_service.create_recurring_investment(
        user_id=current_user.id,
        investment_data=investment
    )
    
    if isinstance(recurring, dict) and "error" in recurring:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=recurring["error"]
        )
    
    return recurring


@router.get("/recurring", response_model=List[RecurringInvestmentResponse])
def get_recurring_investments(
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get all recurring investments for the current user."""
    return investment_service.get_recurring_investments(current_user.id)


@router.get("/recurring/{recurring_id}", response_model=RecurringInvestmentResponse)
def get_recurring_investment(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get a specific recurring investment."""
    recurring = investment_service.get_recurring_investment(recurring_id, current_user.id)
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring investment not found"
        )
    return recurring


@router.put("/recurring/{recurring_id}", response_model=RecurringInvestmentResponse)
def update_recurring_investment(
    recurring_id: int,
    update_data: RecurringInvestmentUpdate,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Update a recurring investment."""
    return investment_service.update_recurring_investment(
        recurring_id=recurring_id, 
        user_id=current_user.id, 
        update_data=update_data
    )


@router.delete("/recurring/{recurring_id}", response_model=Dict[str, str])
def cancel_recurring_investment(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Cancel a recurring investment."""
    return investment_service.cancel_recurring_investment(
        recurring_id=recurring_id, 
        user_id=current_user.id
    )


@router.get("/portfolio/{portfolio_id}/recurring", response_model=List[RecurringInvestmentResponse])
def get_portfolio_recurring_investments(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get all recurring investments for a specific portfolio."""
    return investment_service.get_recurring_investments_by_portfolio(portfolio_id)


@router.get("/pending", response_model=List[TradeResponse])
def get_pending_investments(
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get pending dollar-based investments for the current user."""
    return investment_service.get_pending_dollar_investments(user_id=current_user.id)


@router.get("/history", response_model=List[TradeResponse])
def get_investment_history(
    portfolio_id: Optional[int] = None,
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get investment history for the current user."""
    # Convert date to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    return investment_service.get_investment_history(
        user_id=current_user.id,
        portfolio_id=portfolio_id,
        symbol=symbol,
        start_date=start_datetime,
        end_date=end_datetime
    )


@router.get("/performance", response_model=Dict[str, Any])
def get_investment_performance(
    portfolio_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get performance metrics for dollar-based investments."""
    return investment_service.calculate_performance(
        user_id=current_user.id,
        portfolio_id=portfolio_id
    )


# Admin routes

@router.post("/admin/aggregate", response_model=TradeAggregationResponse)
def admin_aggregate_investments(
    current_user: User = Depends(get_current_user_with_role(UserRole.ADMIN)),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Manually trigger order aggregation (admin only)."""
    return investment_service.aggregate_investments()


@router.get("/admin/pending", response_model=List[TradeResponse])
def admin_get_all_pending_investments(
    current_user: User = Depends(get_current_user_with_role(UserRole.ADMIN)),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get all pending dollar-based investments (admin only)."""
    return investment_service.get_pending_dollar_investments()


@router.post("/admin/process-recurring", response_model=Dict[str, Any])
def admin_process_recurring_investments(
    current_user: User = Depends(get_current_user_with_role(UserRole.ADMIN)),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Manually process all due recurring investments (admin only)."""
    return investment_service.process_recurring_investments()


@router.get("/admin/due-recurring", response_model=List[RecurringInvestmentResponse])
def admin_get_due_recurring_investments(
    current_user: User = Depends(get_current_user_with_role(UserRole.ADMIN)),
    investment_service: InvestmentService = Depends(get_investment_service),
):
    """Get all recurring investments that are due to be processed (admin only)."""
    return investment_service.get_due_recurring_investments()