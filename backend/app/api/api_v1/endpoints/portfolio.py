from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.portfolio import (
    HoldingResponse,
    PortfolioResponse,
    PortfolioSummaryResponse,
    PortfolioUpdateRequest,
)
from app.services.trading import trading_service

router = APIRouter()


@router.get("/", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get portfolio summary with holdings"""
    # Get user's active portfolio
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    # Update portfolio values with current market data
    await trading_service._update_portfolio_totals(portfolio, db)

    # Get holdings
    holdings = [
        HoldingResponse.from_orm(holding)
        for holding in portfolio.holdings
        if holding.quantity > 0
    ]

    # Calculate summary statistics
    total_positions = len(holdings)
    largest_position = (
        max(holdings, key=lambda h: h.market_value) if holdings else None
    )
    best_performer = (
        max(holdings, key=lambda h: h.unrealized_gain_loss_percentage)
        if holdings
        else None
    )
    worst_performer = (
        min(holdings, key=lambda h: h.unrealized_gain_loss_percentage)
        if holdings
        else None
    )

    return PortfolioSummaryResponse(
        portfolio=PortfolioResponse.from_orm(portfolio),
        holdings=holdings,
        total_positions=total_positions,
        largest_position=largest_position,
        best_performer=best_performer,
        worst_performer=worst_performer,
    )


@router.get("/details", response_model=PortfolioResponse)
async def get_portfolio_details(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get detailed portfolio information"""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    # Update portfolio values
    await trading_service._update_portfolio_totals(portfolio, db)

    return PortfolioResponse.from_orm(portfolio)


@router.get("/holdings", response_model=List[HoldingResponse])
async def get_holdings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all portfolio holdings"""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    # Update holdings with current prices
    await trading_service._update_portfolio_totals(portfolio, db)

    # Return only holdings with positive quantity
    holdings = [
        holding for holding in portfolio.holdings if holding.quantity > 0
    ]
    return [HoldingResponse.from_orm(holding) for holding in holdings]


@router.put("/", response_model=PortfolioResponse)
async def update_portfolio(
    update_request: PortfolioUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update portfolio settings"""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    # Update fields if provided
    update_data = update_request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(portfolio, field, value)

    db.commit()
    db.refresh(portfolio)

    return PortfolioResponse.from_orm(portfolio)


@router.get("/performance")
async def get_portfolio_performance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get portfolio performance metrics"""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    # Update portfolio values
    await trading_service._update_portfolio_totals(portfolio, db)

    # Calculate additional performance metrics
    holdings_count = len([h for h in portfolio.holdings if h.quantity > 0])

    # Asset allocation
    asset_allocation = {}
    for holding in portfolio.holdings:
        if holding.quantity > 0:
            asset_type = holding.asset_type
            if asset_type not in asset_allocation:
                asset_allocation[asset_type] = 0
            asset_allocation[asset_type] += holding.market_value

    # Convert to percentages
    total_invested = sum(asset_allocation.values())
    if total_invested > 0:
        asset_allocation = {
            asset_type: (value / total_invested) * 100
            for asset_type, value in asset_allocation.items()
        }

    return {
        "total_value": portfolio.total_value,
        "total_return": portfolio.total_return,
        "total_return_percentage": portfolio.total_return_percentage,
        "cash_balance": portfolio.cash_balance,
        "invested_amount": portfolio.invested_amount,
        "holdings_count": holdings_count,
        "asset_allocation": asset_allocation,
        "last_updated": portfolio.updated_at,
    }


@router.post("/refresh")
async def refresh_portfolio_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Manually refresh portfolio data with latest market prices"""
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="No active portfolio found"
        )

    try:
        # Force update of all holdings with current market data
        await trading_service._update_portfolio_totals(portfolio, db)

        return {
            "message": "Portfolio data refreshed successfully",
            "total_value": portfolio.total_value,
            "total_return": portfolio.total_return,
            "total_return_percentage": portfolio.total_return_percentage,
            "last_updated": portfolio.updated_at,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh portfolio data: {str(e)}",
        )
