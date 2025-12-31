"""Trade execution service for handling advanced order types and execution strategies.

This module provides functionality for executing trades with advanced order types,
handling partial fills, chunking large orders, and calculating execution metrics.
"""

import logging
import statistics
import time
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import record_metric
from app.models.trade import (
    InvestmentType,
    OrderSide,
    OrderType,
    Trade,
    TradeSource,
    TradeStatus,
)
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class TrailingStopType(Enum):
    """Types of trailing stops."""

    PERCENT = "percent"
    AMOUNT = "amount"


class ExecutionStrategy(Enum):
    """Available execution strategies for large orders."""

    SINGLE = "single"  # Execute as a single order
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price
    ICEBERG = "iceberg"  # Show only a portion of the order
    ADAPTIVE = "adaptive"  # Adapt to market conditions


class TradeExecutionService:
    """Service for advanced trade execution strategies."""

    def __init__(self, db: Session, market_data_service: MarketDataService):
        """Initialize with database session and market data service."""
        self.db = db
        self.market_data = market_data_service

        # Configuration
        self.max_order_chunk_size = Decimal(
            str(settings.MAX_ORDER_CHUNK_SIZE or "10000")
        )
        self.min_time_between_chunks = int(
            settings.MIN_TIME_BETWEEN_CHUNKS or 5
        )  # seconds
        self.max_partial_fill_attempts = int(settings.MAX_PARTIAL_FILL_ATTEMPTS or 5)
        self.execution_quality_threshold = Decimal(
            str(settings.EXECUTION_QUALITY_THRESHOLD or "0.001")
        )  # 0.1%

    async def execute_order(self, trade_id: int, broker_service=None) -> Dict[str, Any]:
        """Execute a trade with the specified order type and parameters.

        This is the main entry point for trade execution. It handles different
        order types and strategies based on the trade configuration.

        Args:
            trade_id: The ID of the trade to execute
            broker_service: Optional broker service for actual execution

        Returns:
            Dict containing execution results
        """
        # Get the trade from the database
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return {"success": False, "error": "Trade not found"}

        # Validate trade status
        if trade.status != TradeStatus.PENDING:
            logger.warning(
                f"Cannot execute trade {trade_id} with status {trade.status}"
            )
            return {
                "success": False,
                "error": f"Trade is not in PENDING state: {trade.status}",
            }

        # Handle different order types
        try:
            execution_start = time.time()

            # Handle large orders that need chunking
            if self._needs_chunking(trade):
                logger.info(f"Trade {trade_id} requires chunking due to large size")
                result = await self.chunk_and_execute_large_order(trade, broker_service)

            # Handle special order types
            elif (
                trade.order_type == OrderType.STOP
                or trade.order_type == OrderType.STOP_LIMIT
            ):
                result = await self._execute_stop_order(trade, broker_service)
            else:
                # Regular order execution
                result = await self._execute_regular_order(trade, broker_service)

            # Calculate and record execution metrics
            execution_time = time.time() - execution_start
            metrics = self.calculate_execution_metrics(trade, result, execution_time)

            # Record metrics for monitoring
            record_metric(
                "trade_execution_time",
                execution_time,
                {"symbol": trade.symbol, "order_type": trade.order_type.value},
            )

            if "slippage" in metrics:
                record_metric(
                    "trade_execution_slippage",
                    float(metrics["slippage"]),
                    {"symbol": trade.symbol, "order_type": trade.order_type.value},
                )

            # Update trade with execution results
            if result["success"]:
                self._update_trade_with_execution_results(trade, result)
                self.db.commit()

            return {**result, "metrics": metrics}

        except Exception as e:
            logger.error(f"Error executing trade {trade_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def handle_partial_fill(
        self, trade_id: int, fill_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a partial fill for a trade.

        Updates the trade with partial fill information and determines
        if additional execution attempts are needed.

        Args:
            trade_id: The ID of the trade that was partially filled
            fill_data: Dictionary containing fill information

        Returns:
            Dict containing updated trade status and remaining quantity
        """
        # Get the trade
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            logger.error(f"Trade {trade_id} not found for partial fill handling")
            return {"success": False, "error": "Trade not found"}

        # Extract fill information
        filled_quantity = Decimal(str(fill_data.get("filled_quantity", 0)))
        average_price = Decimal(str(fill_data.get("average_price", 0)))

        # Calculate previously filled quantity
        previously_filled = Decimal(str(trade.filled_quantity or 0))

        # Update trade with new fill information
        trade.filled_quantity = previously_filled + filled_quantity
        trade.average_price = self._calculate_average_price(
            previously_filled,
            Decimal(str(trade.average_price or 0)),
            filled_quantity,
            average_price,
        )

        # Determine if fully filled
        original_quantity = Decimal(str(trade.quantity))
        is_fully_filled = trade.filled_quantity >= original_quantity

        # Update trade status
        if is_fully_filled:
            trade.status = TradeStatus.FILLED
            trade.executed_at = datetime.utcnow()
        else:
            trade.status = TradeStatus.PARTIALLY_FILLED

        # Update broker information
        if "broker_order_id" in fill_data:
            trade.broker_order_id = fill_data["broker_order_id"]

        if "broker_status" in fill_data:
            trade.broker_status = fill_data["broker_status"]

        # Commit changes
        self.db.commit()

        # Calculate remaining quantity
        remaining_quantity = max(Decimal(0), original_quantity - trade.filled_quantity)

        return {
            "success": True,
            "trade_id": trade_id,
            "status": trade.status.value,
            "filled_quantity": float(trade.filled_quantity),
            "average_price": float(trade.average_price),
            "remaining_quantity": float(remaining_quantity),
            "is_complete": is_fully_filled,
        }

    async def create_trailing_stop_order(
        self,
        trade_id: int,
        trailing_type: TrailingStopType,
        trail_value: Decimal,
        broker_service=None,
    ) -> Dict[str, Any]:
        """Create a trailing stop order.

        Sets up a trailing stop order that adjusts the stop price as the
        market price moves in a favorable direction.

        Args:
            trade_id: The ID of the base trade
            trailing_type: PERCENT or AMOUNT
            trail_value: Value to trail by (percentage or fixed amount)
            broker_service: Optional broker service for actual execution

        Returns:
            Dict containing the created trailing stop order details
        """
        # Get the original trade
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            logger.error(f"Trade {trade_id} not found for trailing stop creation")
            return {"success": False, "error": "Trade not found"}

        # Get current market price
        try:
            market_price = Decimal(
                str(self.market_data.get_current_price(trade.symbol))
            )
        except Exception as e:
            logger.error(f"Failed to get current price for {trade.symbol}: {e}")
            return {"success": False, "error": f"Could not get market price: {e}"}

        # Calculate initial stop price
        if trade.trade_type == "buy":
            # For buy orders, trailing stop is below current price
            if trailing_type == TrailingStopType.PERCENT:
                stop_price = market_price * (1 - (trail_value / 100))
            else:  # AMOUNT
                stop_price = market_price - trail_value
        else:  # sell order
            # For sell orders, trailing stop is above current price
            if trailing_type == TrailingStopType.PERCENT:
                stop_price = market_price * (1 + (trail_value / 100))
            else:  # AMOUNT
                stop_price = market_price + trail_value

        # Create the trailing stop order
        trailing_stop = Trade(
            user_id=trade.user_id,
            portfolio_id=trade.portfolio_id,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=stop_price,  # Initial stop price
            trade_type="sell"
            if trade.trade_type == "buy"
            else "buy",  # Opposite of original
            order_type=OrderType.STOP,
            status=TradeStatus.PENDING,
            is_fractional=trade.is_fractional,
            trade_source=TradeSource.USER_INITIATED,
            created_at=datetime.utcnow(),
            # Store trailing stop metadata
            broker_status=f"trailing_stop:{trailing_type.value}:{trail_value}",
        )

        # Meta information for the trailing stop
        trailing_meta = {
            "parent_trade_id": trade_id,
            "trailing_type": trailing_type.value,
            "trail_value": float(trail_value),
            "initial_market_price": float(market_price),
            "initial_stop_price": float(stop_price),
        }

        # Save to database
        self.db.add(trailing_stop)
        self.db.flush()  # To get the ID

        # If broker service provided, register with broker
        if broker_service:
            try:
                broker_result = await broker_service.create_trailing_stop(
                    trade.symbol,
                    trailing_stop.trade_type,
                    float(trailing_stop.quantity),
                    trailing_type.value,
                    float(trail_value),
                )

                # Update with broker information
                trailing_stop.broker_order_id = broker_result.get("order_id")
                trailing_stop.broker_status = broker_result.get("status")

                # Include broker result in response
                trailing_meta["broker_result"] = broker_result
            except Exception as e:
                logger.error(f"Error creating trailing stop with broker: {e}")
                trailing_meta["broker_error"] = str(e)

        # Commit to database
        self.db.commit()

        return {
            "success": True,
            "trailing_stop_id": trailing_stop.id,
            "original_trade_id": trade_id,
            "stop_price": float(stop_price),
            "meta": trailing_meta,
        }

    async def create_oco_order(
        self,
        trade_id: int,
        take_profit_price: Decimal,
        stop_loss_price: Decimal,
        broker_service=None,
    ) -> Dict[str, Any]:
        """Create an OCO (One Cancels Other) order.

        Sets up a pair of orders: a take-profit limit order and a stop-loss order,
        where execution of one cancels the other.

        Args:
            trade_id: The ID of the base trade
            take_profit_price: Price for the take profit order
            stop_loss_price: Price for the stop loss order
            broker_service: Optional broker service for actual execution

        Returns:
            Dict containing the created OCO order details
        """
        # Get the original trade
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            logger.error(f"Trade {trade_id} not found for OCO creation")
            return {"success": False, "error": "Trade not found"}

        # Validate prices - ensure take profit and stop loss are on opposite sides of the market
        try:
            market_price = Decimal(
                str(self.market_data.get_current_price(trade.symbol))
            )

            if trade.trade_type == "buy":
                # For buy positions, take profit > market price > stop loss
                if not (take_profit_price > market_price > stop_loss_price):
                    return {
                        "success": False,
                        "error": "Invalid prices: for buy positions, take_profit must be above market and stop_loss below market",
                    }
            else:  # sell position
                # For sell positions, stop loss > market price > take profit
                if not (stop_loss_price > market_price > take_profit_price):
                    return {
                        "success": False,
                        "error": "Invalid prices: for sell positions, stop_loss must be above market and take_profit below market",
                    }
        except Exception as e:
            logger.error(f"Failed to validate OCO prices for {trade.symbol}: {e}")
            return {"success": False, "error": f"Could not validate prices: {e}"}

        # Create take profit order (limit order)
        take_profit = Trade(
            user_id=trade.user_id,
            portfolio_id=trade.portfolio_id,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=take_profit_price,
            trade_type="sell"
            if trade.trade_type == "buy"
            else "buy",  # Opposite of original
            order_type=OrderType.LIMIT,
            status=TradeStatus.PENDING,
            is_fractional=trade.is_fractional,
            trade_source=TradeSource.USER_INITIATED,
            created_at=datetime.utcnow(),
            broker_status="oco_take_profit",
        )

        # Create stop loss order
        stop_loss = Trade(
            user_id=trade.user_id,
            portfolio_id=trade.portfolio_id,
            symbol=trade.symbol,
            quantity=trade.quantity,
            price=stop_loss_price,
            trade_type="sell"
            if trade.trade_type == "buy"
            else "buy",  # Opposite of original
            order_type=OrderType.STOP,
            status=TradeStatus.PENDING,
            is_fractional=trade.is_fractional,
            trade_source=TradeSource.USER_INITIATED,
            created_at=datetime.utcnow(),
            broker_status="oco_stop_loss",
        )

        # Add to database to get IDs
        self.db.add(take_profit)
        self.db.add(stop_loss)
        self.db.flush()

        # Store OCO relationship
        take_profit.parent_order_id = trade_id
        stop_loss.parent_order_id = trade_id

        # Create metadata about the OCO relationship
        oco_meta = {
            "parent_trade_id": trade_id,
            "take_profit_id": take_profit.id,
            "stop_loss_id": stop_loss.id,
            "market_price_at_creation": float(market_price),
            "take_profit_price": float(take_profit_price),
            "stop_loss_price": float(stop_loss_price),
        }

        # If broker service provided, register with broker
        if broker_service:
            try:
                broker_result = await broker_service.create_oco_order(
                    trade.symbol,
                    "sell" if trade.trade_type == "buy" else "buy",
                    float(trade.quantity),
                    float(take_profit_price),
                    float(stop_loss_price),
                )

                # Update with broker information
                take_profit.broker_order_id = broker_result.get("take_profit_order_id")
                stop_loss.broker_order_id = broker_result.get("stop_loss_order_id")

                # Include broker result in response
                oco_meta["broker_result"] = broker_result
            except Exception as e:
                logger.error(f"Error creating OCO order with broker: {e}")
                oco_meta["broker_error"] = str(e)

        # Commit to database
        self.db.commit()

        return {
            "success": True,
            "take_profit_id": take_profit.id,
            "stop_loss_id": stop_loss.id,
            "original_trade_id": trade_id,
            "meta": oco_meta,
        }

    async def chunk_and_execute_large_order(
        self,
        trade: Trade,
        broker_service=None,
        strategy: ExecutionStrategy = ExecutionStrategy.TWAP,
    ) -> Dict[str, Any]:
        """Split a large order into smaller chunks and execute them.

        Implements different strategies for executing large orders to minimize
        market impact and achieve better execution prices.

        Args:
            trade: The trade to execute
            broker_service: Optional broker service for actual execution
            strategy: The execution strategy to use

        Returns:
            Dict containing the execution results
        """
        original_quantity = Decimal(str(trade.quantity))
        executed_quantity = Decimal("0")
        total_value = Decimal("0")
        chunks = []

        try:
            # Determine chunk sizes based on strategy
            if strategy == ExecutionStrategy.TWAP:
                chunk_sizes = self._calculate_twap_chunks(original_quantity)
            elif strategy == ExecutionStrategy.VWAP:
                chunk_sizes = await self._calculate_vwap_chunks(
                    trade.symbol, original_quantity
                )
            elif strategy == ExecutionStrategy.ICEBERG:
                chunk_sizes = self._calculate_iceberg_chunks(original_quantity)
            else:  # Default to even chunks
                chunk_sizes = self._calculate_even_chunks(original_quantity)

            logger.info(
                f"Executing {trade.id} in {len(chunk_sizes)} chunks using {strategy.value} strategy"
            )

            # Execute each chunk
            for i, chunk_size in enumerate(chunk_sizes):
                logger.info(
                    f"Executing chunk {i+1}/{len(chunk_sizes)} of size {chunk_size} for trade {trade.id}"
                )

                # Create child trade for this chunk
                chunk_trade = Trade(
                    user_id=trade.user_id,
                    portfolio_id=trade.portfolio_id,
                    symbol=trade.symbol,
                    quantity=chunk_size,
                    price=trade.price,
                    trade_type=trade.trade_type,
                    order_type=trade.order_type,
                    status=TradeStatus.PENDING,
                    is_fractional=trade.is_fractional,
                    trade_source=TradeSource.USER_INITIATED,
                    parent_order_id=trade.id,
                    broker_status=f"chunk_{i+1}_of_{len(chunk_sizes)}",
                    created_at=datetime.utcnow(),
                )

                self.db.add(chunk_trade)
                self.db.flush()  # To get the ID

                # Execute the chunk
                if broker_service:
                    # Execute with real broker
                    chunk_result = await broker_service.execute_order(
                        trade.symbol,
                        trade.trade_type,
                        float(chunk_size),
                        order_type=trade.order_type.value,
                        price=float(trade.price) if trade.price else None,
                    )
                else:
                    # Simulate execution
                    current_price = Decimal(
                        str(self.market_data.get_current_price(trade.symbol))
                    )
                    chunk_result = {
                        "success": True,
                        "filled_quantity": float(chunk_size),
                        "average_price": float(current_price),
                        "status": "filled",
                        "order_id": f"sim-{int(time.time())}-{i}",
                    }

                # Update chunk trade with execution results
                if chunk_result["success"]:
                    chunk_trade.status = TradeStatus.FILLED
                    chunk_trade.filled_quantity = Decimal(
                        str(chunk_result["filled_quantity"])
                    )
                    chunk_trade.average_price = Decimal(
                        str(chunk_result["average_price"])
                    )
                    chunk_trade.executed_at = datetime.utcnow()
                    chunk_trade.broker_order_id = chunk_result.get("order_id")

                    # Update totals
                    executed_quantity += chunk_trade.filled_quantity
                    total_value += (
                        chunk_trade.filled_quantity * chunk_trade.average_price
                    )

                    # Add to chunks result
                    chunks.append(
                        {
                            "chunk_id": chunk_trade.id,
                            "quantity": float(chunk_trade.filled_quantity),
                            "price": float(chunk_trade.average_price),
                            "broker_order_id": chunk_trade.broker_order_id,
                        }
                    )
                else:
                    chunk_trade.status = TradeStatus.REJECTED
                    chunk_trade.broker_status = (
                        f"Failed: {chunk_result.get('error', 'Unknown error')}"
                    )
                    logger.error(
                        f"Chunk {i+1} execution failed: {chunk_result.get('error')}"
                    )

                # Pause between chunks
                if i < len(chunk_sizes) - 1:
                    time.sleep(self.min_time_between_chunks)

            # Calculate average execution price if any chunks were executed
            average_price = (
                total_value / executed_quantity
                if executed_quantity > 0
                else Decimal("0")
            )

            # Update parent trade
            trade.filled_quantity = executed_quantity
            trade.average_price = average_price

            # Determine overall status
            if executed_quantity == 0:
                trade.status = TradeStatus.REJECTED
            elif executed_quantity < original_quantity:
                trade.status = TradeStatus.PARTIALLY_FILLED
            else:
                trade.status = TradeStatus.FILLED

            trade.executed_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "trade_id": trade.id,
                "status": trade.status.value,
                "original_quantity": float(original_quantity),
                "executed_quantity": float(executed_quantity),
                "average_price": float(average_price),
                "chunks": chunks,
                "strategy": strategy.value,
            }

        except Exception as e:
            logger.error(
                f"Error chunking and executing trade {trade.id}: {e}", exc_info=True
            )
            return {"success": False, "error": str(e)}

    def calculate_execution_metrics(
        self, trade: Trade, execution_result: Dict[str, Any], execution_time: float
    ) -> Dict[str, Any]:
        """Calculate execution quality metrics for a trade.

        Measures metrics like slippage, execution speed, and implementation shortfall
        to evaluate the quality of trade execution.

        Args:
            trade: The executed trade
            execution_result: The result from execution
            execution_time: Time taken for execution (seconds)

        Returns:
            Dict containing execution quality metrics
        """
        metrics = {"execution_time_seconds": execution_time}

        # Only calculate metrics for successful executions
        if execution_result.get("success") and trade.average_price:
            # Calculate slippage (difference between expected and actual price)
            if trade.price:
                expected_price = Decimal(str(trade.price))
                actual_price = Decimal(str(trade.average_price))

                # For buys, lower actual price is better; for sells, higher actual price is better
                if trade.trade_type == "buy":
                    price_difference = expected_price - actual_price
                else:  # sell
                    price_difference = actual_price - expected_price

                # Calculate slippage as a percentage
                slippage_percent = (price_difference / expected_price) * 100

                metrics["slippage"] = float(slippage_percent)
                metrics["price_improvement"] = True if price_difference > 0 else False

            # Calculate implementation shortfall if market price at time of execution is available
            if "market_price_at_execution" in execution_result:
                market_price = Decimal(
                    str(execution_result["market_price_at_execution"])
                )
                actual_price = Decimal(str(trade.average_price))

                # Calculate shortfall (difference between market price and execution price)
                if trade.trade_type == "buy":
                    shortfall = actual_price - market_price
                else:  # sell
                    shortfall = market_price - actual_price

                # Calculate as a percentage
                shortfall_percent = (shortfall / market_price) * 100

                metrics["implementation_shortfall"] = float(shortfall_percent)

            # Include fill rate for chunked orders
            if (
                "original_quantity" in execution_result
                and "executed_quantity" in execution_result
            ):
                original_quantity = Decimal(str(execution_result["original_quantity"]))
                executed_quantity = Decimal(str(execution_result["executed_quantity"]))

                if original_quantity > 0:
                    fill_rate = (executed_quantity / original_quantity) * 100
                    metrics["fill_rate"] = float(fill_rate)

            # Include strategy information for chunked orders
            if "strategy" in execution_result:
                metrics["strategy"] = execution_result["strategy"]

            # Calculate chunk metrics if present
            if "chunks" in execution_result and execution_result["chunks"]:
                chunks = execution_result["chunks"]
                chunk_prices = [Decimal(str(chunk["price"])) for chunk in chunks]

                # Calculate price dispersion (standard deviation)
                if len(chunk_prices) > 1:
                    price_dispersion = statistics.stdev(
                        [float(p) for p in chunk_prices]
                    )
                    metrics["price_dispersion"] = price_dispersion

                # Calculate pace of execution
                metrics["chunks_count"] = len(chunks)
                metrics["avg_time_per_chunk"] = execution_time / len(chunks)

        return metrics

    def _needs_chunking(self, trade: Trade) -> bool:
        """Determine if a trade needs to be split into chunks."""
        quantity = Decimal(str(trade.quantity))
        return quantity > self.max_order_chunk_size

    def _calculate_average_price(
        self,
        previous_quantity: Decimal,
        previous_avg_price: Decimal,
        new_quantity: Decimal,
        new_price: Decimal,
    ) -> Decimal:
        """Calculate the new average price after a partial fill."""
        if previous_quantity == 0:
            return new_price

        total_quantity = previous_quantity + new_quantity
        total_value = (previous_quantity * previous_avg_price) + (
            new_quantity * new_price
        )

        return total_value / total_quantity if total_quantity > 0 else Decimal("0")

    async def _execute_regular_order(
        self, trade: Trade, broker_service=None
    ) -> Dict[str, Any]:
        """Execute a regular market or limit order."""
        try:
            # Get current market price for reference
            market_price = Decimal(
                str(self.market_data.get_current_price(trade.symbol))
            )

            if broker_service:
                # Use broker service for actual execution
                result = await broker_service.execute_order(
                    trade.symbol,
                    trade.trade_type,
                    float(trade.quantity),
                    order_type=trade.order_type.value,
                    price=float(trade.price) if trade.price else None,
                )
            else:
                # Simulate execution
                # For paper trading, simulate market orders as executing at current price
                # and limit orders only if price conditions are met
                if trade.order_type == OrderType.LIMIT:
                    # Check if limit price conditions are met
                    if trade.trade_type == "buy" and market_price > trade.price:
                        return {
                            "success": False,
                            "error": f"Limit buy price {trade.price} is below market price {market_price}",
                        }
                    elif trade.trade_type == "sell" and market_price < trade.price:
                        return {
                            "success": False,
                            "error": f"Limit sell price {trade.price} is above market price {market_price}",
                        }

                # For simulation, use either the limit price or market price
                execution_price = (
                    trade.price if trade.order_type == OrderType.LIMIT else market_price
                )

                # Simulate successful execution
                result = {
                    "success": True,
                    "filled_quantity": float(trade.quantity),
                    "average_price": float(execution_price),
                    "status": "filled",
                    "order_id": f"sim-{int(time.time())}",
                    "market_price_at_execution": float(market_price),
                }

            return result

        except Exception as e:
            logger.error(f"Error executing regular order for trade {trade.id}: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_stop_order(
        self, trade: Trade, broker_service=None
    ) -> Dict[str, Any]:
        """Execute a stop or stop-limit order."""
        try:
            # Get current market price
            market_price = Decimal(
                str(self.market_data.get_current_price(trade.symbol))
            )

            # Check if stop price conditions are met
            stop_triggered = False
            if trade.trade_type == "buy" and market_price >= trade.price:
                stop_triggered = True
            elif trade.trade_type == "sell" and market_price <= trade.price:
                stop_triggered = True

            if not stop_triggered:
                return {
                    "success": False,
                    "error": "Stop price conditions not met",
                    "market_price": float(market_price),
                    "stop_price": float(trade.price),
                }

            # For real execution, use broker service
            if broker_service:
                result = await broker_service.execute_order(
                    trade.symbol,
                    trade.trade_type,
                    float(trade.quantity),
                    order_type=trade.order_type.value,
                    price=float(trade.price),
                )
            else:
                # For simulation, execute at stop price (or slightly worse)
                # Add a small slippage for realism in simulation
                slippage = market_price * Decimal("0.001")  # 0.1% slippage
                execution_price = trade.price

                if trade.trade_type == "buy":
                    execution_price = trade.price + slippage
                else:  # sell
                    execution_price = trade.price - slippage

                # Simulate successful execution
                result = {
                    "success": True,
                    "filled_quantity": float(trade.quantity),
                    "average_price": float(execution_price),
                    "status": "filled",
                    "order_id": f"sim-stop-{int(time.time())}",
                    "market_price_at_execution": float(market_price),
                }

            return result

        except Exception as e:
            logger.error(f"Error executing stop order for trade {trade.id}: {e}")
            return {"success": False, "error": str(e)}

    def _update_trade_with_execution_results(
        self, trade: Trade, result: Dict[str, Any]
    ) -> None:
        """Update a trade with execution results."""
        if not result.get("success"):
            trade.status = TradeStatus.REJECTED
            trade.broker_status = f"Failed: {result.get('error', 'Unknown error')}"
            return

        trade.status = TradeStatus.FILLED
        trade.filled_quantity = Decimal(
            str(result.get("filled_quantity", trade.quantity))
        )
        trade.average_price = Decimal(str(result.get("average_price", trade.price)))
        trade.broker_order_id = result.get("order_id")
        trade.broker_status = result.get("status", "filled")
        trade.executed_at = datetime.utcnow()

        # Set settlement date (typically T+2 for stocks)
        trade.settlement_date = datetime.utcnow() + timedelta(days=2)

        # Calculate total amount including commission
        commission = Decimal(str(result.get("commission", "0")))
        trade.commission = commission

        total = trade.filled_quantity * trade.average_price
        if trade.trade_type == "buy":
            total += commission
        else:  # sell
            total -= commission

        trade.total_amount = total

    def _calculate_even_chunks(self, quantity: Decimal) -> List[Decimal]:
        """Split quantity into even-sized chunks."""
        if quantity <= self.max_order_chunk_size:
            return [quantity]

        # Calculate number of chunks needed
        num_chunks = (quantity / self.max_order_chunk_size).to_integral_exact(
            rounding="ROUND_UP"
        )
        base_chunk_size = quantity / num_chunks

        # Create chunks (with slight adjustments to ensure total equals original quantity)
        chunks = [base_chunk_size for _ in range(int(num_chunks))]

        # Adjust last chunk to match the total
        total = sum(chunks)
        if total != quantity:
            chunks[-1] += quantity - total

        return chunks

    def _calculate_twap_chunks(self, quantity: Decimal) -> List[Decimal]:
        """Calculate Time-Weighted Average Price chunks.

        For simple TWAP, this is just equal-sized chunks over time.
        """
        return self._calculate_even_chunks(quantity)

    async def _calculate_vwap_chunks(
        self, symbol: str, quantity: Decimal
    ) -> List[Decimal]:
        """Calculate Volume-Weighted Average Price chunks.

        Distributes chunks based on historical volume profile.
        """
        try:
            # For simplicity, just use a basic approximation with 3 chunks weighted toward middle of day
            # In a real implementation, would use actual historical volume profiles
            chunks = []
            if quantity <= self.max_order_chunk_size:
                return [quantity]

            # Simple approximation of volume profile: 25% opening, 50% midday, 25% closing
            opening_chunk = quantity * Decimal("0.25")
            midday_chunk = quantity * Decimal("0.5")
            closing_chunk = quantity * Decimal("0.25")

            # Adjust any chunks exceeding max size
            if opening_chunk > self.max_order_chunk_size:
                num_opening_chunks = (
                    opening_chunk / self.max_order_chunk_size
                ).to_integral_exact(rounding="ROUND_UP")
                opening_chunks = [
                    opening_chunk / num_opening_chunks
                    for _ in range(int(num_opening_chunks))
                ]
                chunks.extend(opening_chunks)
            else:
                chunks.append(opening_chunk)

            if midday_chunk > self.max_order_chunk_size:
                num_midday_chunks = (
                    midday_chunk / self.max_order_chunk_size
                ).to_integral_exact(rounding="ROUND_UP")
                midday_chunks = [
                    midday_chunk / num_midday_chunks
                    for _ in range(int(num_midday_chunks))
                ]
                chunks.extend(midday_chunks)
            else:
                chunks.append(midday_chunk)

            if closing_chunk > self.max_order_chunk_size:
                num_closing_chunks = (
                    closing_chunk / self.max_order_chunk_size
                ).to_integral_exact(rounding="ROUND_UP")
                closing_chunks = [
                    closing_chunk / num_closing_chunks
                    for _ in range(int(num_closing_chunks))
                ]
                chunks.extend(closing_chunks)
            else:
                chunks.append(closing_chunk)

            # Ensure total matches original quantity
            total = sum(chunks)
            if total != quantity:
                chunks[-1] += quantity - total

            return chunks

        except Exception as e:
            logger.error(
                f"Error calculating VWAP chunks: {e}, falling back to even chunks"
            )
            return self._calculate_even_chunks(quantity)

    def _calculate_iceberg_chunks(self, quantity: Decimal) -> List[Decimal]:
        """Calculate Iceberg order chunks.

        Creates chunks with larger initial chunk and smaller subsequent chunks.
        """
        if quantity <= self.max_order_chunk_size:
            return [quantity]

        # For iceberg, show 20% initially, then distribute the rest
        visible_chunk = min(quantity * Decimal("0.2"), self.max_order_chunk_size)
        remaining = quantity - visible_chunk

        # Split remaining into equal chunks
        remaining_chunks = self._calculate_even_chunks(remaining)

        # Combine initial visible chunk with remaining chunks
        return [visible_chunk] + remaining_chunks
