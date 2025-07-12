"""Unified Trading Service.

This module provides a unified interface for trading operations,
handling both paper trading and real broker trading through 
a clean abstraction layer with failover capabilities.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception_handlers import (
    BrokerError,
    MarketDataError,
    OrderExecutionError,
    ResourceNotFoundError,
    handle_errors,
)
from app.core.metrics import metrics
from app.models.account import Account, AccountType
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
from app.services.broker.base import BaseBroker
from app.services.broker.factory import BrokerType, get_broker, get_resilient_broker
from app.services.education_service import EducationService
from app.services.market_data import MarketDataService
from app.services.notifications import NotificationService
from app.services.risk_management import RiskManagementService

logger = logging.getLogger(__name__)


class TradingService:
    """Unified trading service for both paper and real trading."""

    def __init__(
        self,
        db: Session,
        market_data_service: Optional[MarketDataService] = None,
        risk_service: Optional[RiskManagementService] = None,
        notification_service: Optional[NotificationService] = None,
        education_service: Optional[EducationService] = None,
        broker_type: Optional[BrokerType] = None,
        use_resilient_broker: bool = True,
    ):
        """Initialize the trading service with required dependencies."""
        self.db = db
        self.market_data_service = market_data_service or MarketDataService()
        self.risk_service = risk_service or RiskManagementService(db)
        self.notification_service = notification_service or NotificationService(db)
        self.education_service = education_service or EducationService(db)

        # Record broker strategy in metrics
        if settings.ENVIRONMENT == "production":
            metrics.gauge(
                "trading_service.using_resilient_broker",
                1 if use_resilient_broker else 0,
            )

        # Configure broker - use resilient broker in production for failover
        if use_resilient_broker and settings.ENVIRONMENT == "production":
            self.broker = get_resilient_broker(db)
            logger.info("Trading service using resilient broker with failover")
        else:
            self.broker = get_broker(broker_type, db)
            logger.info(
                f"Trading service using single broker of type: {broker_type or settings.DEFAULT_BROKER}"
            )

        # Configuration
        self.commission_rate = Decimal(str(settings.DEFAULT_COMMISSION_RATE))

    async def create_trade(
        self,
        user_id: int,
        portfolio_id: int,
        symbol: str,
        trade_type: str,
        order_type: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        investment_amount: Optional[float] = None,
        investment_type: Optional[str] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        is_fractional: bool = False,
        is_paper_trade: bool = False,
        trade_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new trade order with flexible parameters supporting both
        quantity-based and dollar-based investments.
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get portfolio
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            )
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")

            # Validate the user owns this portfolio
            if portfolio.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Portfolio does not belong to user"
                )

            # Determine trade source
            if not trade_source:
                trade_source = TradeSource.USER_INITIATED
            else:
                trade_source = TradeSource(trade_source)

            # Determine investment type (traditional or dollar-based)
            if not investment_type:
                investment_type = InvestmentType.QUANTITY_BASED
            else:
                investment_type = InvestmentType(investment_type)

            # Determine order type
            order_type_enum = OrderType(order_type.lower())

            # Quote and execution price
            current_price = await self._get_market_price(symbol)
            execution_price = price if price else current_price

            # Create trade with common fields
            trade = Trade(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol.upper(),
                trade_type=trade_type.lower(),
                order_type=order_type_enum,
                status=TradeStatus.PENDING,
                price=execution_price,
                limit_price=limit_price,
                stop_price=stop_price,
                is_fractional=is_fractional,
                created_at=datetime.utcnow(),
                trade_source=trade_source,
                investment_type=investment_type,
            )

            # Handle quantity vs. dollar-based investments
            if investment_type == InvestmentType.DOLLAR_BASED:
                if not investment_amount:
                    raise ValueError(
                        "Investment amount is required for dollar-based investments"
                    )

                # Set investment amount and calculate approx quantity for reference
                trade.investment_amount = investment_amount
                approx_quantity = Decimal(str(investment_amount)) / Decimal(
                    str(execution_price)
                )
                trade.quantity = approx_quantity
            else:
                if not quantity:
                    raise ValueError(
                        "Quantity is required for quantity-based investments"
                    )

                # Set quantity and calculate total amount
                trade.quantity = quantity

            # Validate trade against risk limits and restrictions
            self._validate_trade(trade, user, portfolio)

            # Check if this requires guardian approval (for minors)
            requires_approval = self._check_if_requires_approval(trade, user)
            if requires_approval:
                trade.status = TradeStatus.PENDING_APPROVAL
                trade.requested_by_user_id = user_id

            # Calculate approximate commission and total
            trade.commission = self._calculate_commission(trade)

            # For a market order not requiring approval, we could execute immediately
            # But instead we'll save it first for consistency and execute separately

            # Save the trade
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)

            # Return trade info with additional details
            result = {
                "id": trade.id,
                "symbol": trade.symbol,
                "quantity": float(trade.quantity) if trade.quantity else None,
                "price": float(trade.price) if trade.price else None,
                "investment_amount": float(trade.investment_amount)
                if trade.investment_amount
                else None,
                "trade_type": trade.trade_type,
                "order_type": trade.order_type.value,
                "status": trade.status.value,
                "created_at": trade.created_at.isoformat(),
                "is_fractional": trade.is_fractional,
                "requires_approval": trade.status == TradeStatus.PENDING_APPROVAL,
                "investment_type": trade.investment_type.value,
                "is_paper_trade": is_paper_trade,
            }

            return result

        except ValueError as e:
            self.db.rollback()
            logger.error(f"Validation error creating trade: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating trade: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create trade: {str(e)}"
            )

    async def execute_trade(self, trade_id: int, user_id: int) -> Dict[str, Any]:
        """
        Execute a previously created trade that is in PENDING status.
        This handles both paper trading and real broker trading through the broker abstraction.
        """
        try:
            # Get the trade
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")

            # Check permissions
            if trade.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Trade does not belong to user"
                )

            # Check if trade is in executable state
            if trade.status != TradeStatus.PENDING:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot execute trade in status: {trade.status.value}",
                )

            # Get portfolio
            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == trade.portfolio_id)
                .first()
            )
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")

            # Check sufficient funds for buy orders
            if trade.trade_type == "buy":
                # Get fresh quote for last-minute price check
                current_price = await self._get_market_price(trade.symbol)

                # For market orders, update to current price
                if trade.order_type == OrderType.MARKET:
                    trade.price = current_price

                # Calculate total cost at current price
                quantity = (
                    Decimal(str(trade.quantity)) if trade.quantity else Decimal("0")
                )
                price = Decimal(str(trade.price)) if trade.price else Decimal("0")

                if trade.investment_type == InvestmentType.DOLLAR_BASED:
                    # Dollar-based investments have a fixed cost
                    total_cost = Decimal(str(trade.investment_amount))
                else:
                    # Calculate cost including commission
                    total_cost = quantity * price + self._calculate_commission(trade)

                # Check if enough cash is available
                if total_cost > portfolio.cash_balance:
                    raise HTTPException(
                        status_code=400, detail="Insufficient funds for trade"
                    )

            # Execute the trade through the broker
            try:
                result = self.broker.execute_trade(trade)

                # Update trade status and details
                trade.status = TradeStatus.FILLED
                trade.executed_at = datetime.utcnow()
                trade.filled_quantity = Decimal(str(result.get("filled_quantity", 0)))
                trade.average_price = Decimal(str(result.get("filled_price", 0)))
                trade.broker_order_id = result.get("trade_id")
                trade.broker_status = result.get("status")
                trade.commission = Decimal(str(result.get("commission", 0)))
                trade.total_amount = Decimal(str(result.get("total_amount", 0)))
                trade.settlement_date = result.get("settlement_date")

                # Update portfolio cash and positions
                await self._update_portfolio_after_trade(trade, portfolio)

                # Save changes
                self.db.commit()
                self.db.refresh(trade)

                # Return the updated trade info
                return {
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
                    "commission": float(trade.commission) if trade.commission else None,
                    "total_amount": float(trade.total_amount)
                    if trade.total_amount
                    else None,
                    "is_fractional": trade.is_fractional,
                    "broker_order_id": trade.broker_order_id,
                    "settlement_date": trade.settlement_date.isoformat()
                    if trade.settlement_date
                    else None,
                }

            except BrokerError as e:
                logger.error(f"Broker error executing trade: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Broker error: {str(e)}")

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error executing trade: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to execute trade: {str(e)}"
            )

    async def approve_trade(
        self,
        trade_id: int,
        guardian_id: int,
        approved: bool,
        rejection_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve or reject a trade that requires guardian approval.
        """
        try:
            # Get the trade
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")

            # Check if trade requires approval
            if trade.status != TradeStatus.PENDING_APPROVAL:
                raise HTTPException(
                    status_code=400,
                    detail=f"Trade is not pending approval. Current status: {trade.status.value}",
                )

            # Get the minor user
            minor = self.db.query(User).filter(User.id == trade.user_id).first()
            if not minor or minor.role != UserRole.MINOR:
                raise HTTPException(
                    status_code=400, detail="Trade is not from a minor user"
                )

            # Verify guardian relationship
            custodial_account = (
                self.db.query(Account)
                .filter(
                    Account.user_id == minor.id,
                    Account.guardian_id == guardian_id,
                    Account.account_type == AccountType.CUSTODIAL,
                )
                .first()
            )

            if not custodial_account:
                raise HTTPException(
                    status_code=403, detail="You are not the guardian for this minor"
                )

            # Update trade based on approval decision
            if approved:
                trade.status = TradeStatus.PENDING  # Approved, now ready for execution
                trade.approved_by_user_id = guardian_id
                trade.approved_at = datetime.utcnow()

                # Notify minor of approval
                self.notification_service.send_trade_approved_notification(trade)

                result = {
                    "trade_id": trade.id,
                    "status": trade.status.value,
                    "approved_at": trade.approved_at.isoformat(),
                    "message": "Trade approved successfully",
                }
            else:
                # Ensure rejection reason is provided
                if not rejection_reason:
                    raise HTTPException(
                        status_code=400,
                        detail="Rejection reason is required when rejecting a trade",
                    )

                trade.status = TradeStatus.REJECTED
                trade.rejection_reason = rejection_reason

                # Notify minor of rejection
                self.notification_service.send_trade_rejected_notification(trade)

                result = {
                    "trade_id": trade.id,
                    "status": trade.status.value,
                    "rejection_reason": trade.rejection_reason,
                    "message": "Trade rejected",
                }

            # Save changes
            self.db.commit()

            return result

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving trade: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to approve trade: {str(e)}"
            )

    async def cancel_trade(self, trade_id: int, user_id: int) -> Dict[str, Any]:
        """
        Cancel a pending trade.
        """
        try:
            # Get the trade
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")

            # Check permissions
            if trade.user_id != user_id:
                raise HTTPException(
                    status_code=403, detail="Trade does not belong to user"
                )

            # Check if trade can be cancelled
            if trade.status not in [TradeStatus.PENDING, TradeStatus.PENDING_APPROVAL]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel trade in status: {trade.status.value}",
                )

            # If trade has a broker order ID, cancel it with the broker
            if trade.broker_order_id:
                try:
                    success = self.broker.cancel_trade(trade.broker_order_id)
                    if not success:
                        raise HTTPException(
                            status_code=400, detail="Failed to cancel trade with broker"
                        )
                except BrokerError as e:
                    logger.error(f"Broker error cancelling trade: {str(e)}")
                    raise HTTPException(
                        status_code=400, detail=f"Broker error: {str(e)}"
                    )

            # Update trade status
            trade.status = TradeStatus.CANCELLED
            trade.updated_at = datetime.utcnow()

            # Save changes
            self.db.commit()

            return {
                "trade_id": trade.id,
                "status": trade.status.value,
                "message": "Trade cancelled successfully",
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling trade: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to cancel trade: {str(e)}"
            )

    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current order book for a symbol.
        """
        try:
            symbol = symbol.upper()

            # Get pending buy orders
            buy_orders = (
                self.db.query(Trade)
                .filter(
                    Trade.symbol == symbol,
                    Trade.status == TradeStatus.PENDING,
                    Trade.trade_type == "buy",
                )
                .all()
            )

            # Get pending sell orders
            sell_orders = (
                self.db.query(Trade)
                .filter(
                    Trade.symbol == symbol,
                    Trade.status == TradeStatus.PENDING,
                    Trade.trade_type == "sell",
                )
                .all()
            )

            # Format the orders
            buy_orders_data = []
            for order in buy_orders:
                buy_orders_data.append(
                    {
                        "id": order.id,
                        "quantity": float(order.quantity) if order.quantity else None,
                        "price": float(order.price) if order.price else None,
                        "order_type": order.order_type.value,
                        "created_at": order.created_at.isoformat(),
                    }
                )

            sell_orders_data = []
            for order in sell_orders:
                sell_orders_data.append(
                    {
                        "id": order.id,
                        "quantity": float(order.quantity) if order.quantity else None,
                        "price": float(order.price) if order.price else None,
                        "order_type": order.order_type.value,
                        "created_at": order.created_at.isoformat(),
                    }
                )

            return {
                "symbol": symbol,
                "buy_orders": buy_orders_data,
                "sell_orders": sell_orders_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting order book: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get order book: {str(e)}"
            )

    @handle_errors()
    async def _get_market_price(self, symbol: str) -> float:
        """
        Get the current market price for a symbol.

        Args:
            symbol: The stock symbol to get the price for

        Returns:
            The current market price

        Raises:
            MarketDataError: If there's an error getting the market data
        """
        # Normalize symbol
        symbol = symbol.upper()

        # Get quote from market data service
        quote = await self.market_data_service.get_quote(symbol)

        if not quote or "price" not in quote:
            # Use our standard exception type
            raise MarketDataError(
                message=f"Failed to get quote for {symbol}",
                source="market_data_service",
            )

        return float(quote["price"])

    def _calculate_commission(self, trade: Trade) -> Decimal:
        """
        Calculate commission for a trade.
        """
        # Determine base amount
        if trade.investment_type == InvestmentType.DOLLAR_BASED:
            # For dollar-based investments, use the investment amount
            base_amount = Decimal(str(trade.investment_amount or 0))
        else:
            # For quantity-based investments, calculate from quantity and price
            quantity = Decimal(str(trade.quantity or 0))
            price = Decimal(str(trade.price or 0))
            base_amount = quantity * price

        # Calculate commission
        commission = base_amount * self.commission_rate

        # Ensure minimum commission
        min_commission = Decimal("0.50")
        if commission < min_commission and base_amount > 0:
            commission = min_commission

        return commission.quantize(Decimal("0.01"))

    def _validate_trade(self, trade: Trade, user: User, portfolio: Portfolio) -> None:
        """
        Validate a trade against various rules and restrictions.
        """
        # Check basic validation
        if trade.trade_type not in ["buy", "sell"]:
            raise ValueError("Trade type must be 'buy' or 'sell'")

        if trade.order_type not in [o for o in OrderType]:
            raise ValueError(f"Invalid order type: {trade.order_type}")

        # For limit orders, check limit price
        if trade.order_type == OrderType.LIMIT and not trade.limit_price:
            raise ValueError("Limit price is required for limit orders")

        # For stop orders, check stop price
        if (
            trade.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]
            and not trade.stop_price
        ):
            raise ValueError("Stop price is required for stop orders")

        # Additional validation for sell orders
        if trade.trade_type == "sell":
            # Check if user has the position
            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == portfolio.id,
                    Position.symbol == trade.symbol,
                )
                .first()
            )

            if not position:
                raise ValueError(f"No position found for {trade.symbol}")

            # Check sufficient quantity
            if trade.quantity and position.quantity < trade.quantity:
                raise ValueError(
                    f"Insufficient position: have {position.quantity}, attempted to sell {trade.quantity}"
                )

        # Check risk limits using risk service
        risk_result = self.risk_service.validate_trade(trade, user, portfolio)
        if not risk_result["allowed"]:
            raise ValueError(f"Trade violates risk limits: {risk_result['reason']}")

        # Check educational requirements for minors
        if user.role == UserRole.MINOR:
            self._validate_educational_requirements(user.id, trade)

    def _validate_educational_requirements(self, user_id: int, trade: Trade) -> None:
        """
        Validate that the user has completed the required educational requirements for this trade.

        Args:
            user_id: The user ID
            trade: The trade to validate

        Raises:
            ValueError: If the user has not completed the required educational requirements
        """
        # Determine which permission type to check based on trade details
        permission_types = []

        # Basic trading permission
        basic_permission = "trade_stocks"

        # Add additional permission checks based on order type
        if trade.order_type == OrderType.MARKET:
            permission_types.append("market_orders")
        elif trade.order_type == OrderType.LIMIT:
            permission_types.append("limit_orders")
        elif trade.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            permission_types.append("stop_orders")

        # Check if this is a fractional trade
        if trade.is_fractional or trade.investment_type.value == "dollar_based":
            permission_types.append("fractional_trading")

        # Always check the basic permission
        if not self.education_service.check_user_has_permission(
            user_id, basic_permission
        ):
            raise ValueError(
                "You need to complete the basic trading education before you can trade stocks"
            )

        # Check additional permissions
        for permission_type in permission_types:
            if not self.education_service.check_user_has_permission(
                user_id, permission_type
            ):
                permission_name = permission_type.replace("_", " ").title()
                raise ValueError(
                    f"You need to complete the education for {permission_name} before you can use this order type"
                )

    def _check_if_requires_approval(self, trade: Trade, user: User) -> bool:
        """
        Check if a trade requires guardian approval.
        """
        # Check if user is a minor
        if user.role != UserRole.MINOR:
            return False

        # Get the minor's guardian relationship
        custodial_account = (
            self.db.query(Account)
            .filter(
                Account.user_id == user.id,
                Account.account_type == AccountType.CUSTODIAL,
            )
            .first()
        )

        # If there's no custodial account, something is wrong
        if not custodial_account:
            logger.warning(f"Minor user {user.id} has no custodial account")
            # We'll still require approval to be safe
            return True

        # All trades from minors require guardian approval
        return True

    async def _update_portfolio_after_trade(
        self, trade: Trade, portfolio: Portfolio
    ) -> None:
        """
        Update portfolio cash balance and positions after a trade is executed.
        """
        # Get trade details
        quantity = (
            Decimal(str(trade.filled_quantity))
            if trade.filled_quantity
            else Decimal("0")
        )
        price = (
            Decimal(str(trade.average_price)) if trade.average_price else Decimal("0")
        )
        commission = (
            Decimal(str(trade.commission)) if trade.commission else Decimal("0")
        )
        total_amount = quantity * price

        # Update cash balance
        if trade.trade_type == "buy":
            total_cost = total_amount + commission
            portfolio.cash_balance -= total_cost
        else:  # sell
            total_proceeds = total_amount - commission
            portfolio.cash_balance += total_proceeds

        # Get or create position
        position = (
            self.db.query(Position)
            .filter(
                Position.portfolio_id == portfolio.id, Position.symbol == trade.symbol
            )
            .first()
        )

        # Update position
        if trade.trade_type == "buy":
            if not position:
                # Create new position
                position = Position(
                    portfolio_id=portfolio.id,
                    symbol=trade.symbol,
                    quantity=quantity,
                    average_price=price,
                    current_price=price,
                    is_fractional=trade.is_fractional,
                )
                self.db.add(position)
            else:
                # Update existing position
                old_value = position.quantity * position.average_price
                new_value = quantity * price
                position.quantity += quantity

                # Recalculate average price
                if position.quantity > 0:
                    position.average_price = (old_value + new_value) / position.quantity

                position.current_price = price
                position.is_fractional = position.is_fractional or trade.is_fractional
        else:  # sell
            if position:
                position.quantity -= quantity
                position.current_price = price

                # Remove position if quantity is 0 or negative
                if position.quantity <= 0:
                    self.db.delete(position)

        # Update portfolio total value with latest market prices
        await self._update_portfolio_value(portfolio)

    async def _update_portfolio_value(self, portfolio: Portfolio) -> None:
        """
        Update the total value of a portfolio based on current market prices.
        """
        try:
            # Start with cash balance
            total_value = portfolio.cash_balance

            # Get all positions
            positions = (
                self.db.query(Position)
                .filter(Position.portfolio_id == portfolio.id)
                .all()
            )

            if positions:
                # Get symbols
                symbols = [position.symbol for position in positions]

                # Get current prices
                quotes = {}
                for symbol in symbols:
                    try:
                        quote = await self.market_data_service.get_quote(symbol)
                        quotes[symbol] = quote["price"]
                    except Exception as e:
                        logger.error(f"Error getting quote for {symbol}: {str(e)}")
                        # Use existing price as fallback
                        for position in positions:
                            if position.symbol == symbol:
                                quotes[symbol] = position.current_price

                # Update positions and calculate total value
                for position in positions:
                    if position.symbol in quotes:
                        current_price = Decimal(str(quotes[position.symbol]))
                        position.current_price = current_price
                        position_value = position.quantity * current_price
                        total_value += position_value

            # Update portfolio value
            portfolio.total_value = total_value
            self.db.commit()

        except Exception as e:
            logger.error(f"Error updating portfolio value: {str(e)}")
            # Don't raise exception to avoid affecting the main operation
