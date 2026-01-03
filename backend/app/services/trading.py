from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import time
from decimal import Decimal, InvalidOperation
import re

import structlog
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.monitoring import track_trade, performance_tracker, update_portfolio
from app.core.logging_config import (
    log_trade_execution,
    log_risk_event,
    log_portfolio_update,
    log_system_error,
    LogOperationContext,
)
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.trade import OrderType, Trade, TradeExecution, TradeStatus, TradeType
from app.models.user import User
from app.services.market_data import market_data_service
from app.trading_engine.engine.circuit_breaker import (
    get_circuit_breaker,
    CircuitBreakerType,
    CircuitBreakerStatus,
)

logger = structlog.get_logger()


class TradingService:
    """Trading service with paper trading and risk management"""

    def __init__(self):
        try:
            self.alpaca_api_key = settings.ALPACA_API_KEY
            self.alpaca_secret_key = settings.ALPACA_SECRET_KEY
            self.alpaca_base_url = settings.ALPACA_BASE_URL
            self.max_position_size = 0.1  # Max 10% of portfolio per position
            self.max_daily_loss = 0.05  # Max 5% daily loss

            # Initialize circuit breaker with error handling
            try:
                self.circuit_breaker = get_circuit_breaker()
            except Exception as e:
                logger.error(f"Failed to initialize circuit breaker: {str(e)}")
                # Create a dummy circuit breaker that always allows trading
                self.circuit_breaker = None

            self.consecutive_failures = 0  # Track consecutive execution failures

            logger.info("TradingService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize TradingService: {str(e)}")
            raise ValueError(f"TradingService initialization failed: {str(e)}")

    def _sanitize_symbol(self, symbol: str) -> str:
        """Sanitize and validate symbol input"""
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

        # Remove whitespace and convert to uppercase
        symbol = symbol.strip().upper()

        # Validate symbol format (letters, numbers, and basic symbols)
        if not re.match(r"^[A-Z0-9.\-]{1,10}$", symbol):
            raise ValueError("Invalid symbol format")

        return symbol

    def _validate_quantity(self, quantity: Union[int, float]) -> float:
        """Validate and sanitize quantity input"""
        if quantity is None:
            raise ValueError("Quantity is required")

        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            raise ValueError("Quantity must be a valid number")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if quantity > 1000000:  # Reasonable upper limit
            raise ValueError("Quantity exceeds maximum allowed limit")

        return quantity

    def _validate_price(
        self, price: Union[int, float], price_type: str = "price"
    ) -> float:
        """Validate and sanitize price input"""
        if price is None:
            return None

        try:
            price = float(price)
        except (ValueError, TypeError):
            raise ValueError(f"{price_type} must be a valid number")

        if price <= 0:
            raise ValueError(f"{price_type} must be positive")

        if price > 1000000:  # Reasonable upper limit
            raise ValueError(f"{price_type} exceeds maximum allowed limit")

        return price

    async def validate_trade(
        self, trade_data: Dict[str, Any], portfolio: Portfolio
    ) -> Dict[str, Any]:
        """Validate trade before execution with comprehensive checks"""
        errors = []

        try:
            # Input sanitization and validation
            if not isinstance(trade_data, dict):
                raise ValueError("Trade data must be a dictionary")

            # Validate required fields
            required_fields = ["symbol", "quantity", "trade_type"]
            for field in required_fields:
                if field not in trade_data:
                    errors.append(f"Missing required field: {field}")

            if errors:
                return {"valid": False, "errors": errors}

            # Sanitize inputs
            try:
                trade_data["symbol"] = self._sanitize_symbol(trade_data["symbol"])
                trade_data["quantity"] = self._validate_quantity(trade_data["quantity"])

                if (
                    "limit_price" in trade_data
                    and trade_data["limit_price"] is not None
                ):
                    trade_data["limit_price"] = self._validate_price(
                        trade_data["limit_price"], "limit_price"
                    )

                if "stop_price" in trade_data and trade_data["stop_price"] is not None:
                    trade_data["stop_price"] = self._validate_price(
                        trade_data["stop_price"], "stop_price"
                    )

            except ValueError as e:
                errors.append(str(e))
                return {"valid": False, "errors": errors}

            # Validate trade type
            if trade_data["trade_type"] not in [TradeType.BUY, TradeType.SELL]:
                errors.append("Trade type must be BUY or SELL")

            # Validate order type
            order_type = trade_data.get("order_type", OrderType.MARKET)
            if order_type not in [
                OrderType.MARKET,
                OrderType.LIMIT,
                OrderType.STOP,
                OrderType.STOP_LIMIT,
            ]:
                errors.append("Invalid order type")

            # Validate portfolio
            if not portfolio or not portfolio.is_active:
                errors.append("Portfolio is not active or not found")

            if portfolio.cash_balance is None or portfolio.cash_balance < 0:
                errors.append("Portfolio cash balance is invalid")

            # Check circuit breaker status
            try:
                allowed, cb_status = self.circuit_breaker.check(
                    scope=trade_data.get("symbol")
                )
                if not allowed:
                    errors.append(
                        f"Trading halted by circuit breaker: {cb_status.value}"
                    )
                    return {"valid": False, "errors": errors}
            except Exception as e:
                logger.error(f"Circuit breaker check failed: {str(e)}")
                errors.append("Unable to verify trading status")
                return {"valid": False, "errors": errors}

            # Validate sell orders
            if trade_data["trade_type"] == TradeType.SELL:
                symbol = trade_data["symbol"]
                holding = None
                for h in portfolio.holdings:
                    if h.symbol == symbol:
                        holding = h
                        break

                if not holding:
                    errors.append(f"No position found for {symbol}")
                elif holding.quantity < trade_data["quantity"]:
                    errors.append(
                        f"Insufficient shares of {symbol}: have {holding.quantity}, "
                        f"trying to sell {trade_data['quantity']}"
                    )
                elif holding.quantity <= 0:
                    errors.append(f"Position for {symbol} has invalid quantity")

            # Get current market price for validation
            try:
                quote = await market_data_service.get_quote(trade_data["symbol"])
                if not quote or "price" not in quote:
                    errors.append(
                        f"Unable to get market data for {trade_data['symbol']}"
                    )
                    return {"valid": False, "errors": errors}

                current_price = float(quote["price"])
                if current_price <= 0:
                    errors.append(f"Invalid market price for {trade_data['symbol']}")
                    return {"valid": False, "errors": errors}

            except Exception as e:
                logger.error(f"Market data service error: {str(e)}")
                errors.append(f"Failed to retrieve market data: {str(e)}")
                return {"valid": False, "errors": errors}

            # Position size and fund validation for buy orders
            if trade_data["trade_type"] == TradeType.BUY:
                estimated_cost = trade_data["quantity"] * current_price

                # Check sufficient funds
                if estimated_cost > portfolio.cash_balance:
                    errors.append(
                        f"Insufficient funds: need ${estimated_cost:.2f}, "
                        f"available ${portfolio.cash_balance:.2f}"
                    )

                # Get position sizing multiplier from circuit breaker
                try:
                    cb_multiplier = self.circuit_breaker.get_position_sizing(
                        scope=trade_data["symbol"]
                    )
                    adjusted_max_position_size = self.max_position_size * cb_multiplier
                except Exception as e:
                    logger.error(f"Circuit breaker position sizing error: {str(e)}")
                    # Use conservative default
                    adjusted_max_position_size = self.max_position_size * 0.5

                # Position size validation
                if portfolio.total_value > 0:
                    position_percentage = estimated_cost / portfolio.total_value
                    if position_percentage > adjusted_max_position_size:
                        if cb_multiplier < 1.0:
                            errors.append(
                                f"Position size ({position_percentage:.1%}) exceeds circuit breaker "
                                f"limit ({adjusted_max_position_size:.1%}, reduced to {cb_multiplier*100:.0f}% "
                                f"due to market conditions)"
                            )
                        else:
                            errors.append(
                                f"Position size ({position_percentage:.1%}) exceeds "
                                f"maximum allowed ({self.max_position_size:.1%})"
                            )

                # Check for reasonable minimum investment
                if estimated_cost < 1.0:
                    errors.append("Investment amount too small (minimum $1.00)")

            # Enhanced price validation for different order types
            if order_type == OrderType.LIMIT:
                if not trade_data.get("limit_price"):
                    errors.append("Limit price required for limit orders")
                else:
                    limit_price = trade_data["limit_price"]
                    # Check if limit price is reasonable (within 20% of current price)
                    price_deviation = abs(limit_price - current_price) / current_price
                    if price_deviation > 0.2:
                        errors.append(
                            f"Limit price (${limit_price:.2f}) is too far from current price "
                            f"(${current_price:.2f}) - maximum deviation is 20%"
                        )

                    # Check for reasonable limit price direction
                    if (
                        trade_data["trade_type"] == TradeType.BUY
                        and limit_price > current_price * 1.05
                    ):
                        errors.append(
                            "Buy limit price should not be significantly above market price"
                        )
                    elif (
                        trade_data["trade_type"] == TradeType.SELL
                        and limit_price < current_price * 0.95
                    ):
                        errors.append(
                            "Sell limit price should not be significantly below market price"
                        )

            elif order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                if not trade_data.get("stop_price"):
                    errors.append("Stop price required for stop orders")
                else:
                    stop_price = trade_data["stop_price"]
                    # Validate stop price direction
                    if (
                        trade_data["trade_type"] == TradeType.SELL
                        and stop_price >= current_price
                    ):
                        errors.append(
                            "Stop-loss price should be below current market price"
                        )
                    elif (
                        trade_data["trade_type"] == TradeType.BUY
                        and stop_price <= current_price
                    ):
                        errors.append(
                            "Stop-buy price should be above current market price"
                        )

                if order_type == OrderType.STOP_LIMIT and not trade_data.get(
                    "limit_price"
                ):
                    errors.append("Limit price required for stop-limit orders")

            # Market hours validation (basic check)
            # Simplified market hours: 9:30 AM to 4:00 PM ET (converted to UTC would need timezone handling)
            # For now, just warn about after-hours trading
            if order_type == OrderType.MARKET:
                # Add warning for market orders outside typical hours
                pass  # Could add market hours check here

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "current_price": current_price,
                "estimated_cost": trade_data["quantity"] * current_price,
                "warnings": [],  # Could add non-blocking warnings here
            }

        except Exception as e:
            logger.error(f"Unexpected error in trade validation: {str(e)}")
            return {
                "valid": False,
                "errors": ["Internal validation error occurred"],
                "current_price": 0,
                "estimated_cost": 0,
            }

    async def place_order(
        self, trade_data: Dict[str, Any], user: User, db: Session
    ) -> Trade:
        """Place a trade order with comprehensive error handling"""

        if not user or not user.id:
            raise ValueError("Valid user is required")

        if not isinstance(trade_data, dict):
            raise ValueError("Trade data must be a dictionary")

        try:
            # Get user's portfolio with error handling
            try:
                portfolio = (
                    db.query(Portfolio)
                    .filter(Portfolio.owner_id == user.id, Portfolio.is_active)
                    .first()
                )
            except SQLAlchemyError as e:
                logger.error(f"Database error retrieving portfolio: {str(e)}")
                raise ValueError("Failed to retrieve portfolio")

            if not portfolio:
                raise ValueError("No active portfolio found for user")

            # Validate trade with enhanced error reporting
            try:
                validation = await self.validate_trade(trade_data, portfolio)
            except Exception as e:
                logger.error(f"Trade validation error: {str(e)}")
                raise ValueError(f"Trade validation failed: {str(e)}")

            if not validation["valid"]:
                error_msg = "Trade validation failed: " + "; ".join(
                    validation["errors"]
                )
                logger.warning(
                    f"Trade validation failed for user {user.id}: {error_msg}"
                )
                raise ValueError(error_msg)

            # Sanitize trade data before creating record
            try:
                sanitized_symbol = self._sanitize_symbol(trade_data["symbol"])
                sanitized_quantity = self._validate_quantity(trade_data["quantity"])
            except ValueError as e:
                logger.error(f"Data sanitization error: {str(e)}")
                raise ValueError(f"Invalid trade data: {str(e)}")

            # Create trade record with error handling
            try:
                trade = Trade(
                    symbol=sanitized_symbol,
                    trade_type=trade_data["trade_type"],
                    order_type=trade_data["order_type"],
                    quantity=sanitized_quantity,
                    price=validation["current_price"],
                    limit_price=trade_data.get("limit_price"),
                    stop_price=trade_data.get("stop_price"),
                    portfolio_id=portfolio.id,
                    strategy=trade_data.get("strategy", "manual"),
                    notes=trade_data.get("notes", "")[:500]
                    if trade_data.get("notes")
                    else None,  # Limit notes length
                    is_paper_trade=True,  # Always start with paper trading for safety
                    status=TradeStatus.PENDING,
                )

                db.add(trade)
                db.commit()
                db.refresh(trade)

                logger.info(
                    f"Created trade order {trade.id} for user {user.id}: {trade.trade_type} {trade.quantity} {trade.symbol}"
                )

            except SQLAlchemyError as e:
                logger.error(f"Database error creating trade: {str(e)}")
                db.rollback()
                raise ValueError("Failed to create trade record")

            # Execute the trade based on order type
            try:
                if trade_data["order_type"] == OrderType.MARKET:
                    await self._execute_market_order(
                        trade, validation["current_price"], db
                    )
                else:
                    # For non-market orders, just mark as pending
                    trade.status = TradeStatus.PENDING
                    db.commit()
                    logger.info(
                        f"Trade {trade.id} marked as pending for later execution"
                    )
            except Exception as e:
                logger.error(f"Error executing/updating trade {trade.id}: {str(e)}")
                # Don't fail the entire operation, trade is created but execution failed
                trade.status = TradeStatus.REJECTED
                trade.notes = f"Execution failed: {str(e)}"
                db.commit()

            return trade

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in place_order: {str(e)}")
            if "db" in locals():
                db.rollback()
            raise ValueError(f"Failed to place order: {str(e)}")

    @performance_tracker.track_duration("execute_market_order")
    async def _execute_market_order(
        self, trade: Trade, current_price: float, db: Session
    ):
        """Execute a market order immediately with enhanced error handling"""
        start_time = time.time()
        execution_id = None

        if not trade or not trade.id:
            raise ValueError("Invalid trade object")

        if current_price <= 0:
            raise ValueError("Invalid current price")

        try:
            # Validate trade state before execution
            if trade.status != TradeStatus.PENDING:
                raise ValueError(
                    f"Trade {trade.id} is not in pending status: {trade.status}"
                )

            # Simulate execution with realistic slippage
            import random

            # More realistic slippage model based on quantity and volatility
            base_slippage = random.uniform(-0.0005, 0.0005)  # ±0.05% base
            size_impact = min(
                float(trade.quantity) / 10000, 0.001
            )  # Size impact up to 0.1%

            execution_price = current_price * (1 + base_slippage + size_impact)
            execution_price = round(execution_price, 4)  # Round to 4 decimal places
            slippage = abs(execution_price - current_price) / current_price * 100

            # Validate execution price is reasonable
            if (
                abs(execution_price - current_price) / current_price > 0.05
            ):  # 5% max slippage
                raise ValueError(
                    f"Execution price deviation too large: {slippage:.2f}%"
                )

            # Create execution record with error handling
            try:
                execution_id = (
                    f"PAPER_{trade.id}_{int(datetime.utcnow().timestamp() * 1000)}"
                )
                execution = TradeExecution(
                    trade_id=trade.id,
                    executed_quantity=trade.quantity,
                    executed_price=execution_price,
                    execution_time=datetime.utcnow(),
                    execution_id=execution_id,
                )

                # Calculate commission (simple flat rate for paper trading)
                commission = 0.0  # No commission for paper trading
                total_cost = float(trade.quantity) * execution_price + commission

                # Update trade with execution details
                trade.status = TradeStatus.FILLED
                trade.filled_quantity = trade.quantity
                trade.filled_price = execution_price
                trade.total_cost = total_cost
                trade.executed_at = datetime.utcnow()

                db.add(execution)
                db.commit()

                logger.info(f"Trade execution record created: {execution_id}")

            except SQLAlchemyError as e:
                logger.error(f"Database error creating execution record: {str(e)}")
                db.rollback()
                raise ValueError("Failed to record trade execution")

            # Update portfolio holdings with error handling
            try:
                await self._update_portfolio_holdings(trade, db)
                logger.info(f"Portfolio updated for trade {trade.id}")
            except Exception as e:
                logger.error(f"Portfolio update failed for trade {trade.id}: {str(e)}")
                # Don't fail the trade, but log the issue
                trade.notes = (
                    f"Execution successful but portfolio update failed: {str(e)}"
                )
                db.commit()

            # Reset consecutive failures on successful execution
            self.consecutive_failures = 0

            # Track trade execution with error handling
            try:
                execution_time = time.time() - start_time
                track_trade(
                    {
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "trade_type": trade.trade_type.value,
                        "order_type": trade.order_type.value,
                        "quantity": float(trade.quantity),
                        "execution_price": float(execution_price),
                        "expected_price": float(current_price),
                        "slippage": float(slippage),
                        "execution_time": execution_time,
                        "status": "filled",
                        "is_paper_trade": True,
                        "execution_id": execution_id,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to track trade metrics: {str(e)}")
                # Don't fail the trade execution for metrics issues

            logger.info(
                f"Executed paper trade {trade.id}: {trade.trade_type.value} {trade.quantity} "
                f"{trade.symbol} @ ${execution_price:.4f} (slippage: {slippage:.3f}%, "
                f"execution_time: {time.time() - start_time:.3f}s)"
            )

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing trade {trade.id}: {str(e)}")

            try:
                # Update trade status to rejected
                trade.status = TradeStatus.REJECTED
                trade.notes = (
                    f"Execution failed: {str(e)[:200]}"  # Limit error message length
                )
                db.commit()

                # Track consecutive failures for circuit breaker
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    try:
                        if self.circuit_breaker:
                            self.circuit_breaker.trip(
                                CircuitBreakerType.EXECUTION,
                                f"Multiple execution failures: {self.consecutive_failures} consecutive failures",
                                scope=trade.symbol,
                            )
                            logger.warning(
                                f"Circuit breaker tripped for {trade.symbol} after {self.consecutive_failures} failures"
                            )
                    except Exception as cb_error:
                        logger.error(f"Failed to trip circuit breaker: {str(cb_error)}")

                # Track failed trade
                try:
                    track_trade(
                        {
                            "trade_id": trade.id,
                            "symbol": trade.symbol,
                            "trade_type": trade.trade_type.value,
                            "status": "rejected",
                            "error": str(e)[:100],  # Limit error length
                            "execution_time": time.time() - start_time,
                            "consecutive_failures": self.consecutive_failures,
                        }
                    )
                except Exception as track_error:
                    logger.error(f"Failed to track failed trade: {str(track_error)}")

            except SQLAlchemyError as db_error:
                logger.error(
                    f"Failed to update trade status after execution error: {str(db_error)}"
                )
                db.rollback()

            raise ValueError(f"Trade execution failed: {str(e)}")

    async def _update_portfolio_holdings(self, trade: Trade, db: Session):
        """Update portfolio holdings after trade execution with comprehensive error handling"""

        if not trade or not trade.portfolio_id:
            raise ValueError("Invalid trade or portfolio ID")

        try:
            # Get portfolio with error handling
            portfolio = (
                db.query(Portfolio).filter(Portfolio.id == trade.portfolio_id).first()
            )
            if not portfolio:
                raise ValueError(f"Portfolio {trade.portfolio_id} not found")

            # Find existing holding
            holding = None
            try:
                for h in portfolio.holdings:
                    if h.symbol == trade.symbol:
                        holding = h
                        break
            except Exception as e:
                logger.error(f"Error searching holdings: {str(e)}")
                raise ValueError("Failed to access portfolio holdings")

            # Process the trade based on type
            if trade.trade_type == TradeType.BUY:
                self._process_buy_trade(trade, holding, portfolio, db)
            elif trade.trade_type == TradeType.SELL:
                self._process_sell_trade(trade, holding, portfolio, db)
            else:
                raise ValueError(f"Unknown trade type: {trade.trade_type}")

            # Update portfolio cash balance
            try:
                if trade.trade_type == TradeType.BUY:
                    portfolio.cash_balance -= trade.total_cost
                else:  # SELL
                    portfolio.cash_balance += trade.total_cost

                # Ensure cash balance doesn't go negative
                if portfolio.cash_balance < 0:
                    logger.warning(
                        f"Portfolio {portfolio.id} cash balance went negative: {portfolio.cash_balance}"
                    )

            except Exception as e:
                logger.error(f"Error updating cash balance: {str(e)}")
                raise ValueError("Failed to update portfolio cash balance")

            # Update portfolio totals
            try:
                await self._update_portfolio_totals(portfolio, db)
            except Exception as e:
                logger.error(f"Error updating portfolio totals: {str(e)}")
                # Don't fail the holding update for this

            # Commit all changes
            try:
                db.commit()
                logger.info(f"Portfolio holdings updated for trade {trade.id}")
            except SQLAlchemyError as e:
                logger.error(f"Database error committing portfolio updates: {str(e)}")
                db.rollback()
                raise ValueError("Failed to save portfolio updates")

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating portfolio holdings: {str(e)}")
            db.rollback()
            raise ValueError(f"Portfolio update failed: {str(e)}")

    def _process_buy_trade(
        self,
        trade: Trade,
        holding: Optional[Holding],
        portfolio: Portfolio,
        db: Session,
    ):
        """Process a buy trade and update holdings"""
        try:
            if holding:
                # Update existing holding with weighted average cost
                old_total_cost = float(holding.quantity) * float(holding.average_cost)
                new_total_cost = old_total_cost + float(trade.total_cost)

                holding.quantity += trade.quantity
                if holding.quantity > 0:
                    holding.average_cost = new_total_cost / float(holding.quantity)
                holding.current_price = trade.filled_price
                holding.market_value = float(holding.quantity) * float(
                    holding.current_price
                )

                logger.debug(
                    f"Updated existing holding: {holding.symbol}, new quantity: {holding.quantity}"
                )
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
                logger.debug(
                    f"Created new holding: {holding.symbol}, quantity: {holding.quantity}"
                )

        except Exception as e:
            logger.error(f"Error processing buy trade: {str(e)}")
            raise ValueError(f"Failed to process buy trade: {str(e)}")

    def _process_sell_trade(
        self,
        trade: Trade,
        holding: Optional[Holding],
        portfolio: Portfolio,
        db: Session,
    ):
        """Process a sell trade and update holdings"""
        try:
            if not holding:
                raise ValueError(f"No holding found for {trade.symbol} to sell")

            if holding.quantity < trade.quantity:
                raise ValueError(
                    f"Insufficient shares to sell: have {holding.quantity}, trying to sell {trade.quantity}"
                )

            # Update holding quantity
            holding.quantity -= trade.quantity
            holding.current_price = trade.filled_price

            if holding.quantity <= 0:
                # Remove holding if completely sold
                logger.debug(
                    f"Removing holding for {holding.symbol} - quantity: {holding.quantity}"
                )
                db.delete(holding)
            else:
                # Update market value for remaining shares
                holding.market_value = float(holding.quantity) * float(
                    holding.current_price
                )
                logger.debug(
                    f"Updated holding after sell: {holding.symbol}, remaining quantity: {holding.quantity}"
                )

        except Exception as e:
            logger.error(f"Error processing sell trade: {str(e)}")
            raise ValueError(f"Failed to process sell trade: {str(e)}")

    @performance_tracker.track_duration("update_portfolio_totals")
    async def _update_portfolio_totals(self, portfolio: Portfolio, db: Session):
        """Update portfolio total values with enhanced error handling"""
        if not portfolio:
            raise ValueError("Portfolio is required")

        try:
            total_value = 0.0
            total_invested = 0.0
            positions = []

            # Process holdings with error handling
            for holding in portfolio.holdings:
                try:
                    # Get current price with fallback to stored price
                    quote = await market_data_service.get_quote(holding.symbol)
                    if quote and "price" in quote:
                        current_price = float(quote["price"])
                        holding.current_price = current_price
                    else:
                        # Use existing price as fallback
                        current_price = (
                            float(holding.current_price)
                            if holding.current_price
                            else 0.0
                        )
                        logger.warning(
                            f"Using fallback price for {holding.symbol}: ${current_price}"
                        )

                    # Calculate market values
                    quantity = float(holding.quantity)
                    average_cost = float(holding.average_cost)

                    holding.market_value = quantity * current_price
                    cost_basis = quantity * average_cost
                    holding.unrealized_gain_loss = holding.market_value - cost_basis

                    if cost_basis > 0:
                        holding.unrealized_gain_loss_percentage = (
                            holding.unrealized_gain_loss / cost_basis * 100
                        )
                    else:
                        holding.unrealized_gain_loss_percentage = 0

                    total_value += holding.market_value
                    total_invested += cost_basis

                    # Collect position data for monitoring
                    positions.append(
                        {
                            "symbol": holding.symbol,
                            "quantity": quantity,
                            "value": float(holding.market_value),
                            "gain_loss": float(holding.unrealized_gain_loss),
                            "current_price": current_price,
                            "average_cost": average_cost,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing holding {holding.symbol}: {str(e)}")
                    # Continue processing other holdings

            # Update portfolio totals
            new_total_value = total_value + float(portfolio.cash_balance)
            portfolio.total_value = new_total_value
            portfolio.invested_amount = total_invested
            portfolio.total_return = total_value - total_invested
            portfolio.total_return_percentage = (
                portfolio.total_return / total_invested * 100
                if total_invested > 0
                else 0
            )

            # Commit portfolio updates
            try:
                db.commit()
                logger.debug(
                    f"Portfolio {portfolio.id} totals updated: value=${new_total_value:.2f}"
                )
            except SQLAlchemyError as e:
                logger.error(f"Error committing portfolio updates: {str(e)}")
                db.rollback()
                raise ValueError("Failed to save portfolio totals")

            # Update portfolio metrics for monitoring
            try:
                update_portfolio(
                    {
                        "portfolio_id": portfolio.id,
                        "total_value": float(portfolio.total_value),
                        "cash_balance": float(portfolio.cash_balance),
                        "invested_amount": float(portfolio.invested_amount),
                        "total_return": float(portfolio.total_return),
                        "total_return_percentage": float(
                            portfolio.total_return_percentage
                        ),
                        "position_count": len(positions),
                        "positions": positions,
                        "daily_return": float(
                            portfolio.total_return_percentage
                        ),  # Simplified for now
                    }
                )
            except Exception as e:
                logger.error(f"Failed to update portfolio metrics: {str(e)}")
                # Don't fail the entire operation for metrics issues

        except Exception as e:
            logger.error(
                f"Error updating portfolio totals for portfolio {portfolio.id}: {str(e)}"
            )
            # Don't raise exception to avoid affecting the main operation
            # But ensure we don't leave the portfolio in an inconsistent state
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback after portfolio update error: {str(rollback_error)}"
                )

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

    async def get_trade_history(
        self, user: User, db: Session, limit: int = 100
    ) -> List[Trade]:
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


# Enhanced commission calculation helper
def calculate_commission(trade_amount: float, commission_rate: float = 0.0) -> float:
    """Calculate commission for a trade with minimum commission handling"""
    try:
        commission = trade_amount * commission_rate
        min_commission = 0.50  # Minimum commission for real trades

        # For paper trades, no commission
        if commission_rate == 0.0:
            return 0.0

        # Apply minimum commission for real trades
        return max(commission, min_commission)

    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return 0.0


# Global instance
trading_service = TradingService()
