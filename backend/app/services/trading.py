from datetime import datetime
from typing import Any, Dict, List

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.portfolio import Holding, Portfolio
from app.models.trade import OrderType, Trade, TradeExecution, TradeStatus, TradeType
from app.models.user import User
from app.services.market_data import market_data_service

logger = structlog.get_logger()


class TradingService:
    """Trading service with paper trading and risk management"""

    def __init__(self):
        self.alpaca_api_key = settings.ALPACA_API_KEY
        self.alpaca_secret_key = settings.ALPACA_SECRET_KEY
        self.alpaca_base_url = settings.ALPACA_BASE_URL
        self.max_position_size = 0.1  # Max 10% of portfolio per position
        self.max_daily_loss = 0.05  # Max 5% daily loss

    async def validate_trade(self, trade_data: Dict[str, Any], portfolio: Portfolio) -> Dict[str, Any]:
        """Validate trade before execution"""
        errors = []

        # Basic validation
        if trade_data["quantity"] <= 0:
            errors.append("Quantity must be positive")

        if trade_data["trade_type"] == TradeType.SELL:
            # Check if we have enough shares to sell
            symbol = trade_data["symbol"]
            holding = None
            for h in portfolio.holdings:
                if h.symbol == symbol:
                    holding = h
                    break

            if not holding or holding.quantity < trade_data["quantity"]:
                errors.append(f"Insufficient shares of {symbol} to sell")

        # Get current market price for validation
        quote = await market_data_service.get_quote(trade_data["symbol"])
        if not quote:
            errors.append(f"Unable to get market data for {trade_data['symbol']}")
            return {"valid": False, "errors": errors}

        current_price = quote["price"]

        # Position size validation
        if trade_data["trade_type"] == TradeType.BUY:
            estimated_cost = trade_data["quantity"] * current_price
            position_percentage = estimated_cost / portfolio.total_value if portfolio.total_value > 0 else 1

            if position_percentage > self.max_position_size:
                errors.append(
                    f"Position size ({position_percentage:.1%}) exceeds "
                    f"maximum "
                    f"allowed ({self.max_position_size:.1%})"
                )

        # Price validation for limit orders
        if trade_data["order_type"] == OrderType.LIMIT:
            if not trade_data.get("limit_price"):
                errors.append("Limit price required for limit orders")
            else:
                limit_price = trade_data["limit_price"]
                # Check if limit price is reasonable (within 20% of
                # current price)
                if abs(limit_price - current_price) / current_price > 0.2:
                    errors.append("Limit price is too far from current market price")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "current_price": current_price,
            "estimated_cost": trade_data["quantity"] * current_price,
        }

    async def place_order(self, trade_data: Dict[str, Any], user: User, db: Session) -> Trade:
        """Place a trade order"""

        # Get user's portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.owner_id == user.id, Portfolio.is_active).first()

        if not portfolio:
            raise ValueError("No active portfolio found")

        # Validate trade
        validation = await self.validate_trade(trade_data, portfolio)
        if not validation["valid"]:
            raise ValueError(f"Trade validation failed: {', '.join(validation['errors'])}")

        # Create trade record
        trade = Trade(
            symbol=trade_data["symbol"].upper(),
            trade_type=trade_data["trade_type"],
            order_type=trade_data["order_type"],
            quantity=trade_data["quantity"],
            price=trade_data.get("limit_price"),
            limit_price=trade_data.get("limit_price"),
            stop_price=trade_data.get("stop_price"),
            portfolio_id=portfolio.id,
            strategy=trade_data.get("strategy", "manual"),
            notes=trade_data.get("notes"),
            is_paper_trade=True,  # Always start with paper trading for safety
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        # Execute the trade
        if trade_data["order_type"] == OrderType.MARKET:
            await self._execute_market_order(trade, validation["current_price"], db)
        else:
            # For limit orders, just mark as pending
            trade.status = TradeStatus.PENDING
            db.commit()

        return trade

    async def _execute_market_order(self, trade: Trade, current_price: float, db: Session):
        """Execute a market order immediately"""
        try:
            # Simulate execution with small random variation
            import random

            execution_price = current_price * (1 + random.uniform(-0.001, 0.001))  # ±0.1% variation

            # Create execution record
            execution = TradeExecution(
                trade_id=trade.id,
                executed_quantity=trade.quantity,
                executed_price=execution_price,
                execution_time=datetime.utcnow(),
                execution_id=(f"PAPER_{trade.id}_{datetime.utcnow().timestamp()}"),
            )

            # Update trade
            trade.status = TradeStatus.FILLED
            trade.filled_quantity = trade.quantity
            trade.filled_price = execution_price
            trade.total_cost = trade.quantity * execution_price
            trade.executed_at = datetime.utcnow()

            db.add(execution)
            db.commit()

            # Update portfolio holdings
            await self._update_portfolio_holdings(trade, db)

            logger.info(
                f"Executed paper trade: {trade.trade_type} {trade.quantity} " f"{trade.symbol} @ ${execution_price:.2f}"
            )

        except Exception as e:
            trade.status = TradeStatus.REJECTED
            trade.notes = f"Execution failed: {str(e)}"
            db.commit()
            logger.error(f"Failed to execute trade {trade.id}: {str(e)}")
            raise

    async def _update_portfolio_holdings(self, trade: Trade, db: Session):
        """Update portfolio holdings after trade execution"""
        portfolio = db.query(Portfolio).filter(Portfolio.id == trade.portfolio_id).first()

        # Find or create holding
        holding = None
        for h in portfolio.holdings:
            if h.symbol == trade.symbol:
                holding = h
                break

        if trade.trade_type == TradeType.BUY:
            if holding:
                # Update existing holding
                total_cost = (holding.quantity * holding.average_cost) + trade.total_cost
                holding.quantity += trade.quantity
                holding.average_cost = total_cost / holding.quantity
            else:
                # Create new holding
                holding = Holding(
                    symbol=trade.symbol,
                    asset_type="stock",  # Default, can be enhanced
                    quantity=trade.quantity,
                    average_cost=trade.filled_price,
                    current_price=trade.filled_price,
                    market_value=trade.total_cost,
                    portfolio_id=portfolio.id,
                )
                db.add(holding)

        elif trade.trade_type == TradeType.SELL and holding:
            holding.quantity -= trade.quantity
            if holding.quantity <= 0:
                # Remove holding if completely sold
                db.delete(holding)

        # Update portfolio totals
        await self._update_portfolio_totals(portfolio, db)

        db.commit()

    async def _update_portfolio_totals(self, portfolio: Portfolio, db: Session):
        """Update portfolio total values"""
        total_value = 0.0
        total_invested = 0.0

        for holding in portfolio.holdings:
            # Get current price
            quote = await market_data_service.get_quote(holding.symbol)
            if quote:
                holding.current_price = quote["price"]
                holding.market_value = holding.quantity * holding.current_price
                holding.unrealized_gain_loss = holding.market_value - (holding.quantity * holding.average_cost)
                holding.unrealized_gain_loss_percentage = (
                    holding.unrealized_gain_loss / (holding.quantity * holding.average_cost) * 100
                    if holding.average_cost > 0
                    else 0
                )

            total_value += holding.market_value
            total_invested += holding.quantity * holding.average_cost

        portfolio.total_value = total_value + portfolio.cash_balance
        portfolio.invested_amount = total_invested
        portfolio.total_return = total_value - total_invested
        portfolio.total_return_percentage = portfolio.total_return / total_invested * 100 if total_invested > 0 else 0

        db.commit()

    async def cancel_order(self, trade_id: int, user: User, db: Session) -> Trade:
        """Cancel a pending order"""
        trade = (
            db.query(Trade)
            .filter(
                Trade.id == trade_id,
                Trade.portfolio.has(Portfolio.owner_id == user.id),
            )
            .first()
        )

        if not trade:
            raise ValueError("Trade not found")

        if trade.status != TradeStatus.PENDING:
            raise ValueError("Only pending orders can be cancelled")

        trade.status = TradeStatus.CANCELLED
        db.commit()

        logger.info(f"Cancelled order {trade_id}")
        return trade

    async def get_trade_history(self, user: User, db: Session, limit: int = 100) -> List[Trade]:
        """Get user's trade history"""
        trades = (
            db.query(Trade)
            .join(Portfolio)
            .filter(Portfolio.owner_id == user.id)
            .order_by(Trade.created_at.desc())
            .limit(limit)
            .all()
        )

        return trades

    async def get_open_orders(self, user: User, db: Session) -> List[Trade]:
        """Get user's open orders"""
        orders = (
            db.query(Trade)
            .join(Portfolio)
            .filter(
                Portfolio.owner_id == user.id,
                Trade.status.in_([TradeStatus.PENDING, TradeStatus.PARTIALLY_FILLED]),
            )
            .order_by(Trade.created_at.desc())
            .all()
        )

        return orders


# Global instance
trading_service = TradingService()
