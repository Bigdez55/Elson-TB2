"""Paper Trading Service.

This module provides a specialized implementation of the trading service
for paper trading, with additional functionality specific to simulated trading.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.portfolio import Portfolio, Position
from app.models.trade import (
    InvestmentType,
    OrderSide,
    OrderType,
    Trade,
    TradeSource,
    TradeStatus,
)
from app.models.user import User, UserRole
from app.services.broker.factory import BrokerType, get_broker
from app.services.market_data import MarketDataService
from app.services.market_simulation import MarketSimulationService
from app.services.risk_management import RiskManagementService
from app.services.trading_service import TradingService

logger = logging.getLogger(__name__)


class PaperTradingService(TradingService):
    """Specialized trading service for paper trading."""

    def __init__(
        self,
        db: Session,
        market_data_service: Optional[MarketDataService] = None,
        risk_service: Optional[RiskManagementService] = None,
        simulation_service: Optional[MarketSimulationService] = None,
    ):
        """Initialize the paper trading service with required dependencies."""
        # Initialize base class with paper broker type
        super().__init__(
            db=db,
            market_data_service=market_data_service,
            risk_service=risk_service,
            broker_type=BrokerType.PAPER,
        )

        # Initialize simulation service if not provided
        self.simulation_service = simulation_service or MarketSimulationService()

    async def create_paper_trade(
        self,
        user_id: int,
        portfolio_id: int,
        symbol: str,
        trade_type: str,
        order_type: str = "market",
        quantity: Optional[float] = None,
        investment_amount: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        is_fractional: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new paper trade with simplified parameters.
        """
        # Use base create_trade method with is_paper_trade=True
        investment_type = None
        if investment_amount is not None:
            investment_type = InvestmentType.DOLLAR_BASED
            is_fractional = True

        result = await self.create_trade(
            user_id=user_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            trade_type=trade_type,
            order_type=order_type,
            quantity=quantity,
            investment_amount=investment_amount,
            investment_type=investment_type,
            limit_price=limit_price,
            stop_price=stop_price,
            is_fractional=is_fractional,
            is_paper_trade=True,
            trade_source=TradeSource.USER_INITIATED.value,
        )

        return result

    async def create_paper_dollar_investment(
        self,
        user_id: int,
        portfolio_id: int,
        symbol: str,
        investment_amount: float,
        trade_type: str = "buy",
    ) -> Dict[str, Any]:
        """
        Create a dollar-based paper investment (fractional shares).
        """
        # Validate investment amount
        min_investment = float(settings.MIN_DOLLAR_INVESTMENT)
        if investment_amount < min_investment:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum investment amount is ${min_investment}",
            )

        # Create paper trade with dollar-based parameters
        result = await self.create_paper_trade(
            user_id=user_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            trade_type=trade_type,
            order_type="market",  # Dollar investments are always market orders
            investment_amount=investment_amount,
            is_fractional=True,
        )

        return result

    async def get_simulated_price_history(
        self, symbol: str, days: int = 30, interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """
        Get simulated price history for a symbol.
        """
        try:
            # Use market simulation service to generate price history
            history = self.simulation_service.get_price_history(
                symbol=symbol, days=days, interval=interval
            )

            return history

        except Exception as e:
            logger.error(f"Error getting simulated price history: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get price history: {str(e)}"
            )

    async def get_paper_portfolio_value(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Get current value of paper trading portfolio with positions.
        """
        try:
            # Get portfolio
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            )
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")

            # Get positions
            positions = (
                self.db.query(Position)
                .filter(Position.portfolio_id == portfolio_id)
                .all()
            )

            # Update portfolio value
            await self._update_portfolio_value(portfolio)

            # Format positions
            position_data = []
            for position in positions:
                # Calculate market value and gain/loss
                cost_basis = position.quantity * position.average_price
                market_value = position.quantity * position.current_price
                unrealized_gain = market_value - cost_basis

                # Only include non-zero positions
                if position.quantity > 0:
                    position_data.append(
                        {
                            "symbol": position.symbol,
                            "quantity": float(position.quantity),
                            "average_price": float(position.average_price),
                            "current_price": float(position.current_price),
                            "market_value": float(market_value),
                            "cost_basis": float(cost_basis),
                            "unrealized_gain": float(unrealized_gain),
                            "unrealized_gain_percent": float(
                                unrealized_gain / cost_basis * 100
                            )
                            if cost_basis > 0
                            else 0,
                            "is_fractional": position.is_fractional,
                        }
                    )

            # Return portfolio data
            return {
                "portfolio_id": portfolio.id,
                "total_value": float(portfolio.total_value),
                "cash_balance": float(portfolio.cash_balance),
                "invested_value": float(portfolio.total_value - portfolio.cash_balance),
                "positions": position_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting paper portfolio value: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get portfolio value: {str(e)}"
            )

    async def get_paper_trade_history(
        self, portfolio_id: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trade history for a paper trading portfolio.
        """
        try:
            # Get trades for the portfolio
            trades = (
                self.db.query(Trade)
                .filter(Trade.portfolio_id == portfolio_id)
                .order_by(Trade.created_at.desc())
                .limit(limit)
                .all()
            )

            # Format trades
            trade_history = []
            for trade in trades:
                # Calculate profit/loss for completed trades
                realized_pl = None
                if (
                    trade.status == TradeStatus.FILLED
                    and trade.filled_quantity
                    and trade.average_price
                ):
                    # For sells, calculate realized P/L
                    if trade.trade_type == "sell":
                        # This is simplified - in a real app we'd track cost basis per lot
                        # Get matching position or use current price as fallback
                        position = (
                            self.db.query(Position)
                            .filter(
                                Position.portfolio_id == portfolio_id,
                                Position.symbol == trade.symbol,
                            )
                            .first()
                        )

                        if position:
                            cost_basis = float(trade.filled_quantity) * float(
                                position.average_price
                            )
                            sale_proceeds = float(trade.filled_quantity) * float(
                                trade.average_price
                            )
                            realized_pl = sale_proceeds - cost_basis

                trade_history.append(
                    {
                        "id": trade.id,
                        "symbol": trade.symbol,
                        "quantity": float(trade.quantity) if trade.quantity else None,
                        "filled_quantity": float(trade.filled_quantity)
                        if trade.filled_quantity
                        else None,
                        "price": float(trade.price) if trade.price else None,
                        "average_price": float(trade.average_price)
                        if trade.average_price
                        else None,
                        "trade_type": trade.trade_type,
                        "order_type": trade.order_type.value,
                        "status": trade.status.value,
                        "created_at": trade.created_at.isoformat(),
                        "executed_at": trade.executed_at.isoformat()
                        if trade.executed_at
                        else None,
                        "commission": float(trade.commission)
                        if trade.commission
                        else None,
                        "total_amount": float(trade.total_amount)
                        if trade.total_amount
                        else None,
                        "realized_pl": realized_pl,
                        "is_fractional": trade.is_fractional,
                        "investment_type": trade.investment_type.value
                        if trade.investment_type
                        else None,
                        "investment_amount": float(trade.investment_amount)
                        if trade.investment_amount
                        else None,
                    }
                )

            return trade_history

        except Exception as e:
            logger.error(f"Error getting paper trade history: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get trade history: {str(e)}"
            )

    async def get_market_depth(self, symbol: str, levels: int = 5) -> Dict[str, Any]:
        """
        Get simulated market depth (order book) for a symbol.
        """
        try:
            # Use market simulation service to generate market depth
            depth = self.simulation_service.get_market_depth(
                symbol=symbol, levels=levels
            )

            return depth

        except Exception as e:
            logger.error(f"Error getting simulated market depth: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get market depth: {str(e)}"
            )
