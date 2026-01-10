"""Paper trading broker implementation.

This module implements the BaseBroker interface for paper trading,
providing a simulated broker experience without real money.
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.trade import InvestmentType, OrderSide, OrderType, Trade, TradeStatus
from app.services.broker.base import BaseBroker, BrokerError

# Forward reference - will be imported at runtime to avoid circular imports
PaperTradingService = None
from app.core.config import settings
from app.services.market_simulation import MarketSimulationService

logger = logging.getLogger(__name__)


class PaperBroker(BaseBroker):
    """Paper trading broker implementation."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        global PaperTradingService

        self.db = db

        # Initialize related services
        self.market_simulation = MarketSimulationService()

        # Import PaperTradingService at runtime to avoid circular imports
        if PaperTradingService is None:
            from app.services.paper_trading_service import (
                PaperTradingService as PTService,
            )

            PaperTradingService = PTService

        # Now initialize PaperTradingService
        self.paper_trading = None  # Will be initialized lazily when needed

        # Dictionary to store paper trading positions by account
        self._positions = {}  # account_id -> List[Dict]

        # Dictionary to store paper trading orders
        self._orders = {}  # broker_order_id -> Dict

    def execute_trade(self, trade: Trade) -> Dict[str, Any]:
        """Execute a simulated trade and return execution details."""
        try:
            logger.info(
                f"Executing paper trade: {trade.id} {trade.symbol} {trade.trade_type}"
            )

            # Initialize paper_trading service lazily if not done yet
            if self.paper_trading is None:
                global PaperTradingService
                self.paper_trading = PaperTradingService(
                    self.db, simulation_service=self.market_simulation
                )

            # For this implementation, we'll simulate a successful trade execution
            # without actually calling the paper_trading service (to avoid circular dependencies)
            current_price = self.market_simulation.get_current_price(trade.symbol)

            # Generate a unique ID for the trade
            broker_order_id = str(uuid.uuid4())

            # Simulate trade details
            filled_quantity = trade.quantity
            commission = Decimal("0.00")  # No commission for paper trades
            timestamp = datetime.utcnow()
            settlement_date = timestamp + timedelta(days=2)  # T+2 settlement

            result = {
                "trade_id": broker_order_id,
                "filled_quantity": float(filled_quantity),
                "filled_price": float(current_price),
                "status": "filled",
                "commission": float(commission),
                "timestamp": timestamp,
                "settlement_date": settlement_date,
            }

            # Save the order in our internal tracking
            self._orders[broker_order_id] = {
                "trade_id": trade.id,
                "broker_order_id": broker_order_id,
                "symbol": trade.symbol,
                "quantity": filled_quantity,
                "price": current_price,
                "trade_type": trade.trade_type,
                "status": "filled",
                "commission": commission,
                "executed_at": timestamp,
                "settlement_date": settlement_date,
            }

            # Update positions
            self._update_positions(
                account_id=str(
                    trade.portfolio_id
                ),  # Use portfolio_id as account_id in paper trading
                symbol=trade.symbol,
                quantity=Decimal(str(filled_quantity)),
                price=Decimal(str(current_price)),
                trade_type=trade.trade_type,
            )

            return result

        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
            raise BrokerError(f"Paper trading error: {str(e)}")

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get simulated account information."""
        try:
            # In a real implementation, this would query the database for portfolio information
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.id == int(account_id)).first()
            )

            if not portfolio:
                raise BrokerError(f"Portfolio not found: {account_id}")

            # Get positions for this account
            positions = self.get_positions(account_id)
            positions_value = sum(pos["market_value"] for pos in positions)

            return {
                "account_id": account_id,
                "status": "active",
                "account_type": "paper",
                "cash_balance": float(portfolio.cash_balance),
                "positions_value": positions_value,
                "total_value": float(portfolio.cash_balance) + positions_value,
                "buying_power": float(portfolio.cash_balance),
                "created_at": portfolio.created_at.isoformat()
                if portfolio.created_at
                else None,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting paper account info: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get current simulated positions for an account."""
        try:
            # Get positions from our internal tracking
            account_positions = self._positions.get(account_id, [])

            # Update market values based on current prices
            updated_positions = []
            for position in account_positions:
                current_price = self.market_simulation.get_current_price(
                    position["symbol"]
                )
                market_value = position["quantity"] * Decimal(str(current_price))

                # Calculate unrealized profit/loss
                cost_basis = position["average_price"] * position["quantity"]
                unrealized_pl = market_value - cost_basis
                unrealized_pl_percent = (
                    (unrealized_pl / cost_basis * 100)
                    if cost_basis > 0
                    else Decimal("0")
                )

                updated_position = {
                    **position,
                    "current_price": float(current_price),
                    "market_value": float(market_value),
                    "unrealized_pl": float(unrealized_pl),
                    "unrealized_pl_percent": float(unrealized_pl_percent),
                    "last_updated": datetime.utcnow().isoformat(),
                }

                updated_positions.append(updated_position)

            return updated_positions

        except Exception as e:
            logger.error(f"Error getting paper positions: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def get_trade_status(self, broker_order_id: str) -> Dict[str, Any]:
        """Get the current status of a simulated trade."""
        try:
            # Get order from our internal tracking
            order = self._orders.get(broker_order_id)

            if not order:
                raise BrokerError(f"Order not found: {broker_order_id}")

            return {
                "broker_order_id": broker_order_id,
                "status": order["status"],
                "filled_quantity": order["quantity"],
                "filled_price": order["price"],
                "executed_at": order["executed_at"].isoformat()
                if isinstance(order["executed_at"], datetime)
                else order["executed_at"],
                "commission": order["commission"],
            }

        except Exception as e:
            logger.error(f"Error getting paper trade status: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def cancel_trade(self, broker_order_id: str) -> bool:
        """Cancel a pending simulated trade."""
        try:
            # Get order from our internal tracking
            order = self._orders.get(broker_order_id)

            if not order:
                raise BrokerError(f"Order not found: {broker_order_id}")

            # Check if order can be cancelled
            if order["status"] in ["filled", "cancelled"]:
                raise BrokerError(f"Cannot cancel order in status: {order['status']}")

            # Update order status
            order["status"] = "cancelled"
            self._orders[broker_order_id] = order

            return True

        except Exception as e:
            logger.error(f"Error cancelling paper trade: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def get_order_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get order history for a simulated account."""
        try:
            # Filter orders by account ID and date range
            orders = []

            for order_id, order in self._orders.items():
                # Parse executed_at if it's a string
                executed_at = order["executed_at"]
                if isinstance(executed_at, str):
                    executed_at = datetime.fromisoformat(
                        executed_at.replace("Z", "+00:00")
                    )

                # Check if order belongs to this account
                # In a real implementation, we would store the account_id in the order

                # Check date range if provided
                if start_date and executed_at < start_date:
                    continue

                if end_date and executed_at > end_date:
                    continue

                orders.append(order)

            return orders

        except Exception as e:
            logger.error(f"Error getting paper order history: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def get_trade_execution(self, broker_order_id: str) -> Dict[str, Any]:
        """Get detailed execution information for a completed simulated trade."""
        # For paper trading, this is the same as get_trade_status
        return self.get_trade_status(broker_order_id)

    def get_market_hours(self, market: str) -> Dict[str, Any]:
        """Get simulated market hours information."""
        # Simulate standard US market hours
        now = datetime.utcnow()

        # Calculate market open (9:30 AM ET) and close (4:00 PM ET) in UTC
        # ET is UTC-5 (standard time) or UTC-4 (daylight saving time)
        # Using UTC-4 for this example (assuming daylight saving time)
        utc_offset = -4

        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        market_open = today.replace(hour=9 + abs(utc_offset), minute=30)
        market_close = today.replace(hour=16 + abs(utc_offset), minute=0)

        # Check if today is a weekday (0 = Monday, 4 = Friday)
        is_weekday = now.weekday() < 5

        # Check if market is currently open
        is_open = is_weekday and now >= market_open and now < market_close

        return {
            "market": market,
            "is_open": is_open,
            "open_time": market_open.isoformat(),
            "close_time": market_close.isoformat(),
            "timezone": "America/New_York",
            "current_time": now.isoformat(),
            "next_open": self._calculate_next_market_open(now, market_open, is_weekday),
            "next_close": market_close.isoformat() if is_open else None,
        }

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a simulated quote for a symbol."""
        try:
            # Get price data from market simulation service
            price = self.market_simulation.get_current_price(symbol)
            bid, ask = self.market_simulation.get_bid_ask(symbol)

            return {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "last": price,
                "volume": random.randint(1000, 1000000),  # Random volume
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting paper quote: {e}")
            raise BrokerError(f"Paper broker error: {str(e)}")

    def _update_positions(
        self,
        account_id: str,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        trade_type: str,
    ) -> None:
        """Update internal positions tracking."""
        # Initialize positions for this account if needed
        if account_id not in self._positions:
            self._positions[account_id] = []

        # Find existing position for this symbol
        position = None
        for pos in self._positions[account_id]:
            if pos["symbol"] == symbol:
                position = pos
                break

        # If position doesn't exist, create it
        if not position and trade_type == "buy":
            position = {
                "symbol": symbol,
                "quantity": Decimal("0"),
                "average_price": Decimal("0"),
                "cost_basis": Decimal("0"),
            }
            self._positions[account_id].append(position)

        # Update position based on trade type
        if trade_type == "buy":
            # Calculate new average price and cost basis
            total_quantity = position["quantity"] + quantity
            total_cost = position["cost_basis"] + (quantity * price)

            position["quantity"] = total_quantity
            position["cost_basis"] = total_cost
            position["average_price"] = (
                total_cost / total_quantity if total_quantity > 0 else Decimal("0")
            )

        elif trade_type == "sell":
            # For sell, reduce position quantity
            if not position:
                raise ValueError(f"Cannot sell {symbol}: no position exists")

            # Validate sufficient quantity
            if position["quantity"] < quantity:
                raise ValueError(
                    f"Cannot sell {quantity} shares of {symbol}: only {position['quantity']} available"
                )

            # Reduce quantity
            position["quantity"] -= quantity

            # If quantity becomes zero or negative, remove the position
            if position["quantity"] <= 0:
                self._positions[account_id].remove(position)
            else:
                # Cost basis remains the same, only quantity changes
                pass

    def _calculate_next_market_open(
        self, now: datetime, market_open: datetime, is_weekday: bool
    ) -> str:
        """Calculate the next market open time."""
        if is_weekday and now < market_open:
            # Market opens later today
            return market_open.isoformat()

        # Find the next weekday
        days_to_add = 1
        if now.weekday() == 4:  # Friday
            days_to_add = 3  # Next Monday
        elif now.weekday() == 5:  # Saturday
            days_to_add = 2  # Next Monday

        next_open = market_open + timedelta(days=days_to_add)
        return next_open.isoformat()
