"""Portfolio service for managing user portfolios.

This module provides portfolio management functionality including
retrieving portfolio data, positions, and performance metrics.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.holding import Position
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service for portfolio operations."""

    def __init__(self, db: Session):
        self.db = db
        self.market_data = MarketDataService()

    def get_portfolio(self, user_id: int) -> Optional[Portfolio]:
        """Get portfolio for a user."""
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()

    def get_positions(self, portfolio_id: int) -> List[Position]:
        """Get all positions for a portfolio."""
        return (
            self.db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
        )

    async def get_portfolio_with_prices(self, portfolio_id: int) -> Dict[str, Any]:
        """Get portfolio with current prices for all positions."""
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not portfolio:
            return {}

        positions = self.get_positions(portfolio_id)
        position_data = []

        for position in positions:
            try:
                quote = await self.market_data.get_quote(position.symbol)
                current_price = quote.get("price", position.current_price)
                market_value = position.quantity * current_price
                cost_basis = position.quantity * position.average_cost
                unrealized_pnl = market_value - cost_basis

                position_data.append(
                    {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "average_cost": position.average_cost,
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_percent": (
                            (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting quote for {position.symbol}: {e}")
                position_data.append(
                    {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "average_cost": position.average_cost,
                        "current_price": position.current_price,
                        "market_value": position.quantity * position.current_price,
                        "unrealized_pnl": 0,
                        "unrealized_pnl_percent": 0,
                    }
                )

        total_value = sum(p["market_value"] for p in position_data)
        total_value += portfolio.cash_balance

        return {
            "portfolio": portfolio,
            "positions": position_data,
            "total_value": total_value,
            "cash_balance": portfolio.cash_balance,
        }

    def update_portfolio(self, portfolio_id: int, **kwargs) -> Optional[Portfolio]:
        """Update portfolio settings."""
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not portfolio:
            return None

        for key, value in kwargs.items():
            if hasattr(portfolio, key) and value is not None:
                setattr(portfolio, key, value)

        portfolio.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    async def get_performance(
        self, portfolio_id: int, period: str = "1M"
    ) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not portfolio:
            return {}

        # Basic performance calculation
        total_return = portfolio.total_value - portfolio.invested_amount
        total_return_percent = (
            (total_return / portfolio.invested_amount * 100)
            if portfolio.invested_amount > 0
            else 0
        )

        return {
            "portfolio_id": portfolio_id,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "invested_value": portfolio.invested_amount,
            "metrics": {
                "total_return": total_return,
                "total_return_percent": total_return_percent,
            },
            "updated_at": datetime.utcnow(),
        }

    async def get_risk_analysis(self, portfolio_id: int) -> Dict[str, Any]:
        """Get risk analysis for portfolio."""
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not portfolio:
            return {}

        positions = self.get_positions(portfolio_id)

        # Basic risk analysis
        position_count = len(positions)
        concentration_risk = (
            "low"
            if position_count >= 10
            else ("medium" if position_count >= 5 else "high")
        )

        return {
            "portfolio_id": portfolio_id,
            "risk_level": concentration_risk,
            "metrics": {
                "position_count": position_count,
            },
            "recommendations": [
                (
                    "Consider diversifying your portfolio"
                    if position_count < 10
                    else "Good diversification level"
                )
            ],
            "analyzed_at": datetime.utcnow(),
        }
