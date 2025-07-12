from typing import Dict, Optional, List
import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from app.models.trade import Trade, OrderType, OrderSide, OrderStatus
from app.models.portfolio import Portfolio, Position
from app.services.market_data import MarketDataService
from trading_engine.strategies.base import TradingStrategy
from .circuit_breaker import get_circuit_breaker, CircuitBreakerType
from .risk_config import get_risk_config, RiskProfile

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    The TradeExecutor handles the actual execution of trades based on strategy signals.
    It manages order placement, risk checks, and position tracking while ensuring
    proper interaction with the broker API.
    """
    
    def __init__(
        self,
        market_data_service: MarketDataService,
        strategy: TradingStrategy,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.market_data_service = market_data_service
        self.strategy = strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Track active orders and positions
        self.active_orders: Dict[str, Trade] = {}
        self.positions: Dict[str, Position] = {}
        
        # Performance tracking
        self.execution_metrics = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'average_slippage': 0.0
        }

    async def execute_strategy_signal(
        self,
        signal: Dict,
        portfolio: Portfolio
    ) -> Optional[Trade]:
        """
        Execute a trade based on the strategy signal while applying risk management
        and ensuring proper order execution.
        """
        try:
            # Validate signal and check risk parameters
            if not self._validate_signal(signal, portfolio):
                logger.warning("Signal validation failed - trade not executed")
                return None

            # Calculate position size based on risk parameters
            position_size = await self.strategy.calculate_position_size(
                portfolio_value=portfolio.total_value,
                current_price=signal['price'],
                confidence=signal['confidence']
            )

            # Create and execute the order
            order = await self._create_order(
                symbol=self.strategy.symbol,
                side=OrderSide(signal['action']),
                quantity=position_size,
                price=signal['price'],
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit'],
                portfolio=portfolio
            )

            if order:
                # Track the order and update positions
                self.active_orders[order.id] = order
                await self._monitor_order(order)
                return order

            return None

        except Exception as e:
            logger.error(f"Error executing strategy signal: {str(e)}")
            return None

    async def _create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        portfolio: Portfolio
    ) -> Optional[Trade]:
        """
        Create and submit a new order to the broker while handling various
        order types and conditions.
        """
        try:
            # Create main order
            order = Trade(
                symbol=symbol,
                order_type=OrderType.MARKET,
                side=side,
                quantity=quantity,
                price=price,
                status=OrderStatus.PENDING
            )

            # Submit order to broker
            for attempt in range(self.max_retries):
                try:
                    # Get fresh quote to check for slippage
                    quote = await self.market_data_service.get_quote(symbol)
                    current_price = quote['price']
                    
                    # Check for excessive slippage
                    slippage = abs(current_price - price) / price
                    if slippage > 0.01:  # 1% slippage threshold
                        logger.warning(f"Excessive slippage detected: {slippage:.2%}")
                        return None

                    # Submit the order
                    order.status = OrderStatus.FILLED
                    order.filled_at = datetime.utcnow()
                    
                    # Create stop loss order if specified
                    if stop_loss:
                        self._create_stop_loss_order(order, stop_loss)
                    
                    # Create take profit order if specified
                    if take_profit:
                        self._create_take_profit_order(order, take_profit)

                    # Update metrics
                    self._update_execution_metrics(order, slippage)
                    
                    return order

                except Exception as e:
                    logger.error(f"Order attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(self.retry_delay)

            return None

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None

    async def _monitor_order(self, order: Trade) -> None:
        """
        Monitor the status of an active order and handle its lifecycle,
        including updating positions and managing related orders.
        """
        try:
            while order.status == OrderStatus.PENDING:
                # Check order status with broker
                updated_status = await self._check_order_status(order.external_order_id)
                
                if updated_status == OrderStatus.FILLED:
                    await self._handle_order_filled(order)
                    break
                elif updated_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    await self._handle_order_cancelled(order)
                    break
                
                await asyncio.sleep(1)  # Polling interval

        except Exception as e:
            logger.error(f"Error monitoring order {order.id}: {str(e)}")

    def _validate_signal(self, signal: Dict, portfolio: Portfolio) -> bool:
        """
        Validate trading signal against risk parameters and trading rules.
        """
        try:
            # Check circuit breakers first
            circuit_breaker = get_circuit_breaker()
            
            # Check system-wide circuit breakers
            if not circuit_breaker.check():
                logger.warning("System-wide circuit breaker active - signal ignored")
                return False
                
            # Check strategy-specific circuit breakers
            strategy_name = self.strategy.__class__.__name__
            if not circuit_breaker.check(CircuitBreakerType.PER_STRATEGY, strategy_name):
                logger.warning(f"Strategy circuit breaker active for {strategy_name} - signal ignored")
                return False
                
            # Check symbol-specific circuit breakers
            symbol = signal.get('symbol', self.strategy.symbol)
            if not circuit_breaker.check(scope=symbol):
                logger.warning(f"Symbol circuit breaker active for {symbol} - signal ignored")
                return False

            # Check signal quality
            risk_config = get_risk_config()
            min_confidence = risk_config.get_param("position_sizing.min_signal_confidence") or 0.3
            if signal['action'] == 'hold' or signal['confidence'] < min_confidence:
                return False

            # Check trading hours
            if not self._is_market_open():
                logger.info("Market is closed - signal ignored")
                return False

            # Check portfolio risk limits
            if not self._check_risk_limits(signal, portfolio):
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False
            
    async def _check_order_status(self, external_order_id: str) -> OrderStatus:
        """
        Check the status of an order with the broker API.
        
        Args:
            external_order_id: The broker's order ID to check
            
        Returns:
            OrderStatus: Current status of the order
        """
        try:
            # In a real implementation, this would call the broker API to get the status
            # For now, we'll simulate a successful fill after a delay
            await asyncio.sleep(0.5)  # Simulate API call delay
            
            # Placeholder for real broker API call
            # Example:
            # order_status_response = await self.broker_client.get_order_status(external_order_id)
            # return OrderStatus(order_status_response['status'])
            
            # For simulation purposes, return FILLED status
            # In production, this would parse the actual response from the broker
            return OrderStatus.FILLED
            
        except Exception as e:
            logger.error(f"Error checking order status for order {external_order_id}: {str(e)}")
            # If we can't check the status, assume it's still pending
            return OrderStatus.PENDING
            
    def _create_stop_loss_order(self, order: Trade, stop_price: float) -> Optional[Trade]:
        """
        Create a stop loss order for an existing position.
        
        Args:
            order: The original order that this stop loss is protecting
            stop_price: The price at which to trigger the stop loss
            
        Returns:
            Trade: The created stop loss order, or None if creation failed
        """
        try:
            # Calculate the appropriate side (opposite of the original order)
            side = OrderSide.SELL if order.side == OrderSide.BUY else OrderSide.BUY
            
            # Create the stop loss order object
            stop_loss_order = Trade(
                symbol=order.symbol,
                order_type=OrderType.STOP,
                side=side,
                quantity=order.quantity,
                price=stop_price,
                status=OrderStatus.PENDING,
                parent_order_id=order.id
            )
            
            # In production, this would actually submit the order to the broker
            # For now, just log and return the order object
            logger.info(f"Stop loss order created for {order.symbol} at {stop_price}")
            
            # Track the stop loss order
            self.active_orders[stop_loss_order.id] = stop_loss_order
            
            return stop_loss_order
            
        except Exception as e:
            logger.error(f"Error creating stop loss order: {str(e)}")
            return None
            
    def _create_take_profit_order(self, order: Trade, take_profit_price: float) -> Optional[Trade]:
        """
        Create a take profit (limit) order for an existing position.
        
        Args:
            order: The original order that this take profit is for
            take_profit_price: The price at which to take profit
            
        Returns:
            Trade: The created take profit order, or None if creation failed
        """
        try:
            # Calculate the appropriate side (opposite of the original order)
            side = OrderSide.SELL if order.side == OrderSide.BUY else OrderSide.BUY
            
            # Create the take profit order object
            take_profit_order = Trade(
                symbol=order.symbol,
                order_type=OrderType.LIMIT,
                side=side,
                quantity=order.quantity,
                price=take_profit_price,
                status=OrderStatus.PENDING,
                parent_order_id=order.id
            )
            
            # In production, this would actually submit the order to the broker
            # For now, just log and return the order object
            logger.info(f"Take profit order created for {order.symbol} at {take_profit_price}")
            
            # Track the take profit order
            self.active_orders[take_profit_order.id] = take_profit_order
            
            return take_profit_order
            
        except Exception as e:
            logger.error(f"Error creating take profit order: {str(e)}")
            return None
            
    def _is_market_open(self) -> bool:
        """
        Check if the market is currently open for trading.
        
        Returns:
            bool: True if the market is open, False otherwise
        """
        try:
            # This is a simplified implementation
            # In production, this would check the actual market hours based on the asset class
            # and exchange, including pre/post market hours if applicable
            
            # Get current UTC time
            now = datetime.utcnow()
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                return False
                
            # Check if it's during market hours (simplified to 9:30am - 4:00pm ET)
            # This is a very simplified version - real implementation would:
            # 1. Account for holidays
            # 2. Handle different exchanges with different hours
            # 3. Consider pre/post market trading if applicable
            # 4. Properly convert from UTC to exchange local time
            
            # Assuming ET is UTC-4 (simplification - real code would use proper timezone conversion)
            et_hour = (now.hour - 4) % 24
            
            # Check if within regular trading hours (9:30am - 4:00pm ET)
            if et_hour < 9 or et_hour >= 16:
                return False
                
            if et_hour == 9 and now.minute < 30:
                return False
                
            # Market is open
            return True
            
        except Exception as e:
            logger.error(f"Error checking market hours: {str(e)}")
            # Default to closed if we can't determine
            return False
            
    async def _handle_order_filled(self, order: Trade) -> None:
        """
        Handle a successfully filled order by updating positions and related state.
        """
        try:
            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.utcnow()
            
            # Update position tracking
            if order.symbol in self.positions:
                # Update existing position
                position = self.positions[order.symbol]
                
                if order.side == OrderSide.BUY:
                    position.quantity += order.quantity
                    position.cost_basis = ((position.cost_basis * (position.quantity - order.quantity)) + 
                                          (order.price * order.quantity)) / position.quantity
                else:  # SELL
                    position.quantity -= order.quantity
                    
                    # Remove position if fully sold
                    if position.quantity <= 0:
                        del self.positions[order.symbol]
            else:
                # Create new position if buying
                if order.side == OrderSide.BUY:
                    self.positions[order.symbol] = Position(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        cost_basis=order.price
                    )
            
            # Remove from active orders
            if order.id in self.active_orders:
                del self.active_orders[order.id]
                
            logger.info(f"Order {order.id} for {order.symbol} filled successfully")
            
        except Exception as e:
            logger.error(f"Error handling filled order {order.id}: {str(e)}")
            
    async def _handle_order_cancelled(self, order: Trade) -> None:
        """
        Handle a cancelled or rejected order.
        """
        try:
            # Update order status
            if order.status != OrderStatus.REJECTED:
                order.status = OrderStatus.CANCELLED
                
            # Remove from active orders
            if order.id in self.active_orders:
                del self.active_orders[order.id]
                
            logger.warning(f"Order {order.id} for {order.symbol} was {order.status.name.lower()}")
            
        except Exception as e:
            logger.error(f"Error handling cancelled order {order.id}: {str(e)}")

    def _check_risk_limits(self, signal: Dict, portfolio: Portfolio) -> bool:
        """
        Check if the trade meets all risk management criteria.
        """
        try:
            # Get risk configuration
            risk_config = get_risk_config()
            
            # Calculate potential position value
            position_value = Decimal(str(signal['price'])) * Decimal(str(signal['quantity']))

            # Check maximum position size based on risk profile
            max_position_pct = Decimal(str(risk_config.get_param("position_sizing.max_position_size") or 0.1))
            max_position = portfolio.total_value * max_position_pct
            
            if position_value > max_position:
                logger.warning(f"Position size ({position_value}) exceeds maximum allowed ({max_position})")
                return False

            # Check daily loss limit based on risk profile
            max_daily_drawdown = Decimal(str(risk_config.get_param("drawdown_limits.max_daily_drawdown") or 0.02))
            daily_loss_pct = portfolio.get_daily_drawdown()
            
            if daily_loss_pct and daily_loss_pct > max_daily_drawdown:
                logger.warning(f"Daily loss limit reached: {daily_loss_pct:.2%} > {max_daily_drawdown:.2%}")
                
                # Trip a circuit breaker for daily loss
                circuit_breaker = get_circuit_breaker()
                circuit_breaker.trip(
                    CircuitBreakerType.DAILY_LOSS, 
                    f"Daily loss limit exceeded: {daily_loss_pct:.2%}",
                    reset_after=0  # Don't auto-reset until next trading day
                )
                
                return False

            # Check maximum trades per day
            max_trades_per_day = risk_config.get_param("trade_limitations.max_trades_per_day") or 10
            if portfolio.get_daily_trade_count() >= max_trades_per_day:
                logger.warning(f"Maximum trades per day reached: {max_trades_per_day}")
                return False

            # Check correlation with existing positions
            max_correlation = Decimal(str(risk_config.get_param("correlation_limits.max_correlation") or 0.8))
            if not self._check_portfolio_correlation(signal['symbol'], portfolio, max_correlation):
                return False

            # Check if symbol is in restricted assets list
            restricted_assets = risk_config.get_param("trade_limitations.restricted_assets") or []
            symbol = signal.get('symbol', self.strategy.symbol)
            
            # Simple check - would need more sophisticated mapping for actual asset classes
            if any(restricted in symbol.lower() for restricted in restricted_assets):
                logger.warning(f"Symbol {symbol} is in restricted assets list")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return False
            
    def _check_portfolio_correlation(
        self, 
        symbol: str, 
        portfolio: Portfolio,
        max_correlation: Decimal = Decimal('0.8')
    ) -> bool:
        """
        Check if adding this symbol would create high correlation in the portfolio
        """
        # This is a simplified implementation - in reality you would use
        # actual return data and correlation calculations
        
        # For now, just check if we already have too many positions of the same type
        # E.g., too many tech stocks, too many ETFs of the same sector, etc.
        
        # In a real implementation, this would use data from a sector/industry
        # classification service and actual correlation calculations
        
        # Just return True for now - placeholder for actual implementation
        return True

    def _update_execution_metrics(self, order: Trade, slippage: float) -> None:
        """
        Update execution quality metrics for monitoring and optimization.
        """
        try:
            self.execution_metrics['total_orders'] += 1
            
            if order.status == OrderStatus.FILLED:
                self.execution_metrics['successful_orders'] += 1
                
                # Update average slippage
                current_avg = self.execution_metrics['average_slippage']
                n = self.execution_metrics['successful_orders']
                self.execution_metrics['average_slippage'] = (
                    (current_avg * (n - 1) + slippage) / n
                )
            else:
                self.execution_metrics['failed_orders'] += 1

        except Exception as e:
            logger.error(f"Error updating execution metrics: {str(e)}")

    def get_execution_metrics(self) -> Dict:
        """
        Get current execution quality metrics.
        """
        return {
            **self.execution_metrics,
            'fill_rate': (
                self.execution_metrics['successful_orders'] /
                max(self.execution_metrics['total_orders'], 1)
            )
        }