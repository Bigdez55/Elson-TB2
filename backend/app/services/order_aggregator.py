"""Order aggregation service for batching and optimizing trades."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.trade import OrderSide, Trade, TradeStatus
from app.services.trading import TradingService

logger = logging.getLogger(__name__)


class OrderAggregator:
    """Service for aggregating and optimizing trade orders."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.trading_service = TradingService(db)

    def aggregate_orders(
        self, symbol: str, time_window: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Aggregate orders for a specific symbol within a time window.

        Args:
            symbol: The stock symbol to aggregate orders for
            time_window: Time window in minutes for aggregation

        Returns:
            List of aggregated orders
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window)

        # Get pending orders for this symbol within time window
        pending_orders = (
            self.db.query(Trade)
            .filter(
                Trade.symbol == symbol,
                Trade.status == TradeStatus.PENDING,
                Trade.created_at >= cutoff_time,
            )
            .all()
        )

        # Group by buy/sell
        buy_orders = [
            order for order in pending_orders if order.order_side == OrderSide.BUY
        ]
        sell_orders = [
            order for order in pending_orders if order.order_side == OrderSide.SELL
        ]

        # Calculate aggregated quantities
        total_buy_quantity = sum(order.quantity for order in buy_orders)
        total_sell_quantity = sum(order.quantity for order in sell_orders)

        # Calculate weighted average prices
        if buy_orders:
            buy_price = (
                sum(order.price * order.quantity for order in buy_orders)
                / total_buy_quantity
            )
        else:
            buy_price = 0

        if sell_orders:
            sell_price = (
                sum(order.price * order.quantity for order in sell_orders)
                / total_sell_quantity
            )
        else:
            sell_price = 0

        # Create aggregated order summaries
        aggregated_orders = []

        if total_buy_quantity > 0:
            aggregated_orders.append(
                {
                    "symbol": symbol,
                    "trade_type": "buy",
                    "quantity": total_buy_quantity,
                    "price": buy_price,
                    "order_count": len(buy_orders),
                    "order_ids": [order.id for order in buy_orders],
                }
            )

        if total_sell_quantity > 0:
            aggregated_orders.append(
                {
                    "symbol": symbol,
                    "trade_type": "sell",
                    "quantity": total_sell_quantity,
                    "price": sell_price,
                    "order_count": len(sell_orders),
                    "order_ids": [order.id for order in sell_orders],
                }
            )

        return aggregated_orders

    async def execute_aggregated_orders(self) -> Dict[str, Any]:
        """
        Execute all pending aggregated orders.

        Returns:
            Summary of executed orders
        """
        # Get all pending orders
        pending_orders = (
            self.db.query(Trade).filter(Trade.status == TradeStatus.PENDING).all()
        )

        # Group by symbol
        orders_by_symbol = {}
        for order in pending_orders:
            if order.symbol not in orders_by_symbol:
                orders_by_symbol[order.symbol] = []
            orders_by_symbol[order.symbol].append(order)

        # Process each symbol
        results = {
            "total_executed": 0,
            "total_failed": 0,
            "symbols_processed": 0,
            "details": [],
        }

        for symbol, orders in orders_by_symbol.items():
            # Aggregate orders
            aggregated = self.aggregate_orders(symbol)

            symbol_results = {
                "symbol": symbol,
                "orders_executed": 0,
                "orders_failed": 0,
            }

            # Execute each order
            for order in orders:
                success, error = await self.trading_service.execute_trade(order.id)
                if success:
                    symbol_results["orders_executed"] += 1
                    results["total_executed"] += 1
                else:
                    symbol_results["orders_failed"] += 1
                    results["total_failed"] += 1

            results["details"].append(symbol_results)
            results["symbols_processed"] += 1

        return results
