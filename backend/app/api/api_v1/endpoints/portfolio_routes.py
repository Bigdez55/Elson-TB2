"""Portfolio management API routes with enhanced authentication."""

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth.trading_auth import TradingPermissionError
from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.holding import Position
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioPerformanceResponse,
    PortfolioResponse,
    PortfolioUpdate,
    PositionResponse,
    RiskAnalysisResponse,
)
from app.services.portfolio import PortfolioService

# Compatibility aliases
get_trading_user = get_current_active_user


def require_feature_access(feature: str):
    """Decorator for feature access - pass-through for now."""
    def decorator(func):
        func._required_feature = feature
        return func
    return decorator


async def get_user_with_portfolio(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user along with their portfolio."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.user_id == user.id
    ).first()
    if not portfolio:
        raise TradingPermissionError("No portfolio found for user")
    return (user, portfolio)

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    user_portfolio: tuple = Depends(get_user_with_portfolio),
):
    """Get user's portfolio with current positions and performance."""
    current_user, portfolio = user_portfolio

    # Update portfolio performance metrics
    portfolio.update_performance_metrics()

    return PortfolioResponse.from_orm(portfolio)


@router.put("/portfolio", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_update: PortfolioUpdate,
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Update portfolio settings and configuration."""
    current_user, portfolio = user_portfolio

    # Update allowed fields
    if portfolio_update.risk_profile:
        portfolio.risk_profile = portfolio_update.risk_profile

    if portfolio_update.max_position_concentration:
        if portfolio_update.max_position_concentration > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum position concentration cannot exceed 50%",
            )
        portfolio.max_position_concentration = (
            portfolio_update.max_position_concentration
        )

    if portfolio_update.rebalancing_threshold:
        portfolio.rebalancing_threshold = portfolio_update.rebalancing_threshold

    db.commit()
    db.refresh(portfolio)

    return PortfolioResponse.from_orm(portfolio)


@router.get("/portfolio/positions", response_model=List[PositionResponse])
async def get_positions(
    user_portfolio: tuple = Depends(get_user_with_portfolio),
):
    """Get all positions in user's portfolio."""
    current_user, portfolio = user_portfolio

    # Update all position calculations
    for position in portfolio.positions_detail:
        position.update_all_calculations()

    return [
        PositionResponse.from_orm(position) for position in portfolio.positions_detail
    ]


@router.get("/portfolio/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(
    period: str = Query("1M", regex="^(1D|1W|1M|3M|1Y|ALL)$"),
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Get portfolio performance metrics for specified period."""
    current_user, portfolio = user_portfolio

    portfolio_service = PortfolioService(db)
    performance_data = await portfolio_service.get_performance_metrics(
        portfolio.id, period
    )

    return PortfolioPerformanceResponse(**performance_data)


@router.get("/portfolio/risk-analysis", response_model=RiskAnalysisResponse)
async def get_risk_analysis(
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Get comprehensive risk analysis of portfolio."""
    current_user, portfolio = user_portfolio

    portfolio_service = PortfolioService(db)
    risk_analysis = await portfolio_service.analyze_portfolio_risk(portfolio.id)

    return RiskAnalysisResponse(**risk_analysis)


@router.post("/portfolio/rebalance")
@require_feature_access("advanced_trading")
async def rebalance_portfolio(
    dry_run: bool = Query(
        False, description="Perform dry run without executing trades"
    ),
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Rebalance portfolio to target allocation."""
    current_user, portfolio = user_portfolio

    # Check if rebalancing is needed
    if not portfolio.check_rebalancing_needed():
        return {
            "message": "Portfolio is within rebalancing thresholds",
            "rebalancing_needed": False,
        }

    portfolio_service = PortfolioService(db)

    if dry_run:
        rebalancing_plan = await portfolio_service.generate_rebalancing_plan(
            portfolio.id
        )
        return {
            "message": "Rebalancing plan generated",
            "dry_run": True,
            "plan": rebalancing_plan,
        }
    else:
        result = await portfolio_service.execute_rebalancing(
            portfolio.id, current_user.id
        )
        return {
            "message": "Rebalancing initiated",
            "trades_created": result["trades_created"],
            "estimated_completion": result["estimated_completion"],
        }


@router.get("/portfolio/diversification")
async def get_diversification_analysis(
    user_portfolio: tuple = Depends(get_user_with_portfolio),
):
    """Get portfolio diversification analysis."""
    current_user, portfolio = user_portfolio

    # Get sector exposure
    sector_exposure = portfolio.get_sector_exposure()

    # Calculate diversification metrics
    diversification_score = 100  # Simplified - would be more complex in reality
    if len(sector_exposure) < 3:
        diversification_score -= 30

    # Check for over-concentration
    max_sector_exposure = max(sector_exposure.values()) if sector_exposure else 0
    if max_sector_exposure > 0.4:  # 40%
        diversification_score -= 20

    return {
        "diversification_score": max(0, diversification_score),
        "sector_exposure": {
            sector: float(percentage * 100)
            for sector, percentage in sector_exposure.items()
        },
        "recommendations": [
            "Consider diversifying across more sectors"
            if len(sector_exposure) < 5
            else None,
            f"Reduce exposure to {max(sector_exposure, key=sector_exposure.get)} sector"
            if max_sector_exposure > 0.3
            else None,
        ],
    }


@router.get("/portfolio/positions/{symbol}", response_model=PositionResponse)
async def get_position_details(
    symbol: str,
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific position."""
    current_user, portfolio = user_portfolio

    position = (
        db.query(Position)
        .filter(
            Position.portfolio_id == portfolio.id, Position.symbol == symbol.upper()
        )
        .first()
    )

    if not position:
        raise HTTPException(
            status_code=404, detail=f"Position not found for symbol: {symbol}"
        )

    # Update position calculations
    position.update_all_calculations()

    return PositionResponse.from_orm(position)


@router.delete("/portfolio/positions/{symbol}")
async def close_position(
    symbol: str,
    user_portfolio: tuple = Depends(get_user_with_portfolio),
    db: Session = Depends(get_db),
):
    """Close entire position in a symbol (sell all shares)."""
    current_user, portfolio = user_portfolio

    position = (
        db.query(Position)
        .filter(
            Position.portfolio_id == portfolio.id, Position.symbol == symbol.upper()
        )
        .first()
    )

    if not position:
        raise HTTPException(
            status_code=404, detail=f"Position not found for symbol: {symbol}"
        )

    if position.quantity <= 0:
        raise HTTPException(status_code=400, detail="Position already closed")

    # This would typically create a sell order for the entire position
    # For now, we'll return a message indicating what would happen
    return {
        "message": f"Close position order would be created for {position.quantity} shares of {symbol}",
        "symbol": symbol,
        "quantity_to_sell": float(position.quantity),
        "estimated_proceeds": float(position.market_value)
        if position.market_value
        else 0,
    }
