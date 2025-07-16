from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import asyncio
import random
import uuid

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.trade import Trade, TradeType, OrderType, TradeStatus
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class FillQuality(str, Enum):
    """Quality of trade fill simulation."""
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


class SlippageModel(str, Enum):
    """Models for calculating price slippage."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLUME_BASED = "volume_based"
    MARKET_IMPACT = "market_impact"


class PaperTradingService:
    """
    Enhanced paper trading service with realistic fill simulation.
    
    Provides sophisticated order execution simulation including:
    - Realistic price slippage
    - Partial fills based on market conditions
    - Market impact modeling
    - Commission and fee simulation
    - Latency simulation
    """

    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService()
        
        # Paper trading configuration
        self.base_slippage_bps = getattr(settings, 'PAPER_TRADING_SLIPPAGE_BPS', 2)  # 2 basis points
        self.commission_per_share = getattr(settings, 'PAPER_TRADING_COMMISSION', 0.005)  # $0.005 per share
        self.min_commission = getattr(settings, 'PAPER_TRADING_MIN_COMMISSION', 1.0)  # $1 minimum
        self.max_commission = getattr(settings, 'PAPER_TRADING_MAX_COMMISSION', 10.0)  # $10 maximum
        
        # Execution simulation parameters
        self.fill_probability = 0.95  # 95% of trades fill
        self.partial_fill_probability = 0.15  # 15% chance of partial fill
        self.execution_delay_ms = 150  # 150ms average execution delay
        
        # Market condition modifiers
        self.volatility_slippage_multiplier = 2.0
        self.volume_impact_threshold = 10000  # Shares threshold for market impact

    async def execute_paper_trade(
        self, 
        trade: Trade,
        simulate_realistic_conditions: bool = True
    ) -> Dict[str, any]:
        """
        Execute a paper trade with realistic market simulation.
        
        Args:
            trade: Trade object to execute
            simulate_realistic_conditions: Whether to apply realistic market conditions
        
        Returns:
            Dictionary containing execution results
        """
        try:
            # Get current market data
            current_price = await self.market_data_service.get_current_price(trade.symbol)
            if not current_price:
                return self._create_rejection_result(
                    trade, "Unable to get current market price"
                )

            # Check market hours (simplified)
            if not self._is_market_open():
                return self._create_queued_result(trade, "Market closed - order queued")

            # Simulate execution delay
            if simulate_realistic_conditions:
                await asyncio.sleep(self.execution_delay_ms / 1000.0)

            # Calculate execution parameters
            execution_result = await self._simulate_order_execution(
                trade, current_price, simulate_realistic_conditions
            )

            if execution_result['status'] == 'filled':
                # Update trade record
                await self._update_trade_execution(trade, execution_result)
                
                # Update portfolio holdings
                await self._update_portfolio_holdings(trade, execution_result)
                
                logger.info(f"Paper trade executed: {trade.symbol} {trade.trade_type} {execution_result['filled_quantity']} @ {execution_result['execution_price']}")

            return execution_result

        except Exception as e:
            logger.error(f"Paper trade execution failed for {trade.id}: {e}")
            return self._create_error_result(trade, str(e))

    async def _simulate_order_execution(
        self, 
        trade: Trade, 
        current_price: float,
        realistic: bool
    ) -> Dict[str, any]:
        """Simulate realistic order execution."""
        
        # Market orders vs limit orders
        if trade.order_type == OrderType.MARKET:
            return await self._execute_market_order(trade, current_price, realistic)
        elif trade.order_type == OrderType.LIMIT:
            return await self._execute_limit_order(trade, current_price, realistic)
        elif trade.order_type in [OrderType.STOP, OrderType.STOP_LOSS]:
            return await self._execute_stop_order(trade, current_price, realistic)
        else:
            return self._create_rejection_result(trade, f"Unsupported order type: {trade.order_type}")

    async def _execute_market_order(
        self, 
        trade: Trade, 
        current_price: float, 
        realistic: bool
    ) -> Dict[str, any]:
        """Execute market order with realistic slippage."""
        
        if not realistic:
            # Simple execution at current price
            execution_price = current_price
            filled_quantity = trade.quantity
            commission = self._calculate_commission(filled_quantity, execution_price)
            
            return {
                'status': 'filled',
                'execution_price': execution_price,
                'filled_quantity': filled_quantity,
                'remaining_quantity': 0.0,
                'commission': commission,
                'fees': 0.0,
                'execution_time': datetime.utcnow(),
                'fill_quality': FillQuality.EXCELLENT,
                'slippage_bps': 0.0,
                'notes': 'Simplified paper execution'
            }

        # Realistic execution with slippage and market impact
        
        # 1. Check fill probability
        if random.random() > self.fill_probability:
            return self._create_rejection_result(trade, "Order not filled due to market conditions")

        # 2. Calculate slippage
        slippage_bps = await self._calculate_slippage(trade, current_price)
        slippage_factor = 1 + (slippage_bps / 10000.0)
        
        # Apply slippage direction based on trade type
        if trade.trade_type == TradeType.BUY:
            execution_price = current_price * slippage_factor
        else:  # SELL
            execution_price = current_price / slippage_factor

        # 3. Determine fill quantity (partial fills possible)
        filled_quantity = trade.quantity
        if random.random() < self.partial_fill_probability:
            # Partial fill: 60-95% of requested quantity
            fill_percentage = random.uniform(0.6, 0.95)
            filled_quantity = trade.quantity * fill_percentage
            filled_quantity = round(filled_quantity, 6)  # Round to avoid tiny fractions

        # 4. Calculate costs
        commission = self._calculate_commission(filled_quantity, execution_price)
        fees = self._calculate_fees(filled_quantity, execution_price)

        # 5. Determine fill quality
        fill_quality = self._assess_fill_quality(slippage_bps, filled_quantity / trade.quantity)

        return {
            'status': 'filled' if filled_quantity == trade.quantity else 'partially_filled',
            'execution_price': execution_price,
            'filled_quantity': filled_quantity,
            'remaining_quantity': trade.quantity - filled_quantity,
            'commission': commission,
            'fees': fees,
            'execution_time': datetime.utcnow(),
            'fill_quality': fill_quality,
            'slippage_bps': slippage_bps,
            'notes': f'Paper execution with {slippage_bps:.1f} bps slippage'
        }

    async def _execute_limit_order(
        self, 
        trade: Trade, 
        current_price: float, 
        realistic: bool
    ) -> Dict[str, any]:
        """Execute limit order with price checking."""
        
        limit_price = trade.limit_price or trade.price
        if not limit_price:
            return self._create_rejection_result(trade, "Limit price not specified")

        # Check if limit order can be filled
        can_fill = False
        if trade.trade_type == TradeType.BUY and current_price <= limit_price:
            can_fill = True
        elif trade.trade_type == TradeType.SELL and current_price >= limit_price:
            can_fill = True

        if not can_fill:
            return {
                'status': 'pending',
                'execution_price': None,
                'filled_quantity': 0.0,
                'remaining_quantity': trade.quantity,
                'commission': 0.0,
                'fees': 0.0,
                'execution_time': None,
                'fill_quality': None,
                'slippage_bps': 0.0,
                'notes': f'Limit order pending: current price {current_price} vs limit {limit_price}'
            }

        # Order can be filled - execute at limit price or better
        if realistic:
            # Add small probability of price improvement
            if random.random() < 0.2:  # 20% chance of price improvement
                price_improvement_bps = random.uniform(1, 5)
                improvement_factor = 1 + (price_improvement_bps / 10000.0)
                
                if trade.trade_type == TradeType.BUY:
                    execution_price = limit_price / improvement_factor
                else:
                    execution_price = limit_price * improvement_factor
            else:
                execution_price = limit_price
        else:
            execution_price = limit_price

        # Calculate fill quantity (limit orders less likely to partial fill)
        filled_quantity = trade.quantity
        if realistic and random.random() < 0.05:  # 5% chance of partial fill
            fill_percentage = random.uniform(0.8, 0.98)
            filled_quantity = trade.quantity * fill_percentage
            filled_quantity = round(filled_quantity, 6)

        commission = self._calculate_commission(filled_quantity, execution_price)
        fees = self._calculate_fees(filled_quantity, execution_price)
        
        slippage_bps = abs(execution_price - current_price) / current_price * 10000
        fill_quality = self._assess_fill_quality(slippage_bps, filled_quantity / trade.quantity)

        return {
            'status': 'filled' if filled_quantity == trade.quantity else 'partially_filled',
            'execution_price': execution_price,
            'filled_quantity': filled_quantity,
            'remaining_quantity': trade.quantity - filled_quantity,
            'commission': commission,
            'fees': fees,
            'execution_time': datetime.utcnow(),
            'fill_quality': fill_quality,
            'slippage_bps': slippage_bps,
            'notes': f'Limit order filled at {execution_price:.4f}'
        }

    async def _execute_stop_order(
        self, 
        trade: Trade, 
        current_price: float, 
        realistic: bool
    ) -> Dict[str, any]:
        """Execute stop order when triggered."""
        
        stop_price = trade.stop_price
        if not stop_price:
            return self._create_rejection_result(trade, "Stop price not specified")

        # Check if stop is triggered
        triggered = False
        if trade.trade_type == TradeType.SELL and current_price <= stop_price:
            triggered = True
        elif trade.trade_type == TradeType.BUY and current_price >= stop_price:
            triggered = True

        if not triggered:
            return {
                'status': 'pending',
                'execution_price': None,
                'filled_quantity': 0.0,
                'remaining_quantity': trade.quantity,
                'commission': 0.0,
                'fees': 0.0,
                'execution_time': None,
                'fill_quality': None,
                'slippage_bps': 0.0,
                'notes': f'Stop order pending: current price {current_price} vs stop {stop_price}'
            }

        # Stop triggered - execute as market order
        # Stop orders typically have worse slippage due to urgency
        if realistic:
            base_slippage = await self._calculate_slippage(trade, current_price)
            stop_slippage_multiplier = 1.5  # Stop orders get worse fills
            slippage_bps = base_slippage * stop_slippage_multiplier
        else:
            slippage_bps = 0.0

        slippage_factor = 1 + (slippage_bps / 10000.0)
        
        if trade.trade_type == TradeType.SELL:
            execution_price = current_price / slippage_factor
        else:
            execution_price = current_price * slippage_factor

        filled_quantity = trade.quantity
        commission = self._calculate_commission(filled_quantity, execution_price)
        fees = self._calculate_fees(filled_quantity, execution_price)
        fill_quality = self._assess_fill_quality(slippage_bps, 1.0)

        return {
            'status': 'filled',
            'execution_price': execution_price,
            'filled_quantity': filled_quantity,
            'remaining_quantity': 0.0,
            'commission': commission,
            'fees': fees,
            'execution_time': datetime.utcnow(),
            'fill_quality': fill_quality,
            'slippage_bps': slippage_bps,
            'notes': f'Stop order triggered and filled at {execution_price:.4f}'
        }

    async def _calculate_slippage(self, trade: Trade, current_price: float) -> float:
        """Calculate realistic slippage in basis points."""
        
        # Base slippage
        base_slippage = self.base_slippage_bps
        
        # Volume impact (larger orders = more slippage)
        volume_multiplier = 1.0
        if trade.quantity > self.volume_impact_threshold:
            volume_multiplier = 1 + (trade.quantity / self.volume_impact_threshold - 1) * 0.5
        
        # Market volatility impact (would use real volatility data in practice)
        volatility_multiplier = random.uniform(0.8, 2.0)  # Simulate varying market conditions
        
        # Time of day impact (market open/close typically have higher slippage)
        time_multiplier = self._get_time_of_day_multiplier()
        
        total_slippage = base_slippage * volume_multiplier * volatility_multiplier * time_multiplier
        
        # Add some randomness to simulate real market conditions
        randomness = random.uniform(0.5, 1.5)
        total_slippage *= randomness
        
        return min(total_slippage, 50.0)  # Cap at 50 bps

    def _calculate_commission(self, quantity: float, price: float) -> float:
        """Calculate trading commission."""
        commission = quantity * self.commission_per_share
        commission = max(commission, self.min_commission)
        commission = min(commission, self.max_commission)
        return round(commission, 2)

    def _calculate_fees(self, quantity: float, price: float) -> float:
        """Calculate additional trading fees."""
        trade_value = quantity * price
        
        # SEC fee (for sales only, typically 0.00008%)
        sec_fee = trade_value * 0.0000008 if trade_value > 0 else 0.0
        
        # TAF fee (for sales only, typically $0.000119 per share)
        taf_fee = quantity * 0.000119
        
        total_fees = sec_fee + taf_fee
        return round(total_fees, 4)

    def _assess_fill_quality(self, slippage_bps: float, fill_ratio: float) -> FillQuality:
        """Assess the quality of order fill."""
        
        # Consider both slippage and fill ratio
        if slippage_bps <= 1.0 and fill_ratio == 1.0:
            return FillQuality.EXCELLENT
        elif slippage_bps <= 3.0 and fill_ratio >= 0.95:
            return FillQuality.GOOD
        elif slippage_bps <= 8.0 and fill_ratio >= 0.8:
            return FillQuality.AVERAGE
        else:
            return FillQuality.POOR

    def _get_time_of_day_multiplier(self) -> float:
        """Get slippage multiplier based on time of day."""
        current_hour = datetime.utcnow().hour
        
        # Market open (9:30 AM EST = 14:30 UTC) and close (4:00 PM EST = 21:00 UTC) have higher slippage
        if current_hour in [14, 15, 20, 21]:  # Market open/close hours
            return 1.5
        elif current_hour in [16, 17, 18, 19]:  # Normal trading hours
            return 1.0
        else:  # After hours
            return 2.0

    def _is_market_open(self) -> bool:
        """Check if market is open (simplified)."""
        now = datetime.utcnow()
        weekday = now.weekday()
        hour = now.hour
        
        # Simple check: Monday-Friday, 14:30-21:00 UTC (9:30 AM - 4:00 PM EST)
        if weekday < 5 and 14 <= hour < 21:
            return True
        return False

    async def _update_trade_execution(self, trade: Trade, execution_result: Dict) -> None:
        """Update trade record with execution results."""
        try:
            trade.status = TradeStatus.FILLED if execution_result['status'] == 'filled' else TradeStatus.PARTIALLY_FILLED
            trade.filled_quantity = execution_result['filled_quantity']
            trade.filled_price = execution_result['execution_price']
            trade.commission = execution_result['commission']
            trade.fees = execution_result['fees']
            trade.executed_at = execution_result['execution_time']
            trade.filled_at = execution_result['execution_time']
            trade.total_cost = (execution_result['filled_quantity'] * execution_result['execution_price'] + 
                              execution_result['commission'] + execution_result['fees'])
            
            # Add execution notes
            if trade.notes:
                trade.notes += f"\n{execution_result['notes']}"
            else:
                trade.notes = execution_result['notes']
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update trade execution: {e}")
            self.db.rollback()

    async def _update_portfolio_holdings(self, trade: Trade, execution_result: Dict) -> None:
        """Update portfolio holdings after trade execution."""
        try:
            # Get or create holding
            holding = self.db.query(Holding).filter(
                Holding.portfolio_id == trade.portfolio_id,
                Holding.symbol == trade.symbol
            ).first()
            
            if not holding:
                holding = Holding(
                    portfolio_id=trade.portfolio_id,
                    symbol=trade.symbol,
                    asset_type="stock",  # Default to stock
                    quantity=0.0,
                    average_cost=0.0,
                    current_price=execution_result['execution_price'],
                    market_value=0.0
                )
                self.db.add(holding)
            
            # Update holding quantity and average cost
            filled_quantity = execution_result['filled_quantity']
            execution_price = execution_result['execution_price']
            
            if trade.trade_type == TradeType.BUY:
                # Add to position
                old_value = holding.quantity * holding.average_cost
                new_value = filled_quantity * execution_price
                new_quantity = holding.quantity + filled_quantity
                
                if new_quantity > 0:
                    holding.average_cost = (old_value + new_value) / new_quantity
                    holding.quantity = new_quantity
            else:  # SELL
                # Reduce position
                holding.quantity = max(0.0, holding.quantity - filled_quantity)
                # Average cost stays the same for sells
            
            # Update current price and market value
            holding.current_price = execution_price
            holding.market_value = holding.quantity * holding.current_price
            
            # Calculate unrealized P&L
            if holding.quantity > 0:
                holding.unrealized_gain_loss = holding.market_value - (holding.quantity * holding.average_cost)
                holding.unrealized_gain_loss_percentage = holding.unrealized_gain_loss / (holding.quantity * holding.average_cost) if holding.average_cost > 0 else 0.0
            else:
                holding.unrealized_gain_loss = 0.0
                holding.unrealized_gain_loss_percentage = 0.0
            
            # Update portfolio totals
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == trade.portfolio_id).first()
            if portfolio:
                # Update cash balance
                trade_value = filled_quantity * execution_price
                total_cost = trade_value + execution_result['commission'] + execution_result['fees']
                
                if trade.trade_type == TradeType.BUY:
                    portfolio.cash_balance = (portfolio.cash_balance or 0.0) - total_cost
                else:  # SELL
                    portfolio.cash_balance = (portfolio.cash_balance or 0.0) + trade_value - execution_result['commission'] - execution_result['fees']
                
                # Recalculate total portfolio value (would be done in a separate service)
                holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
                invested_value = sum(h.market_value for h in holdings if h.market_value)
                portfolio.total_value = (portfolio.cash_balance or 0.0) + invested_value
                portfolio.invested_amount = invested_value
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update portfolio holdings: {e}")
            self.db.rollback()

    def _create_rejection_result(self, trade: Trade, reason: str) -> Dict[str, any]:
        """Create rejection result."""
        return {
            'status': 'rejected',
            'execution_price': None,
            'filled_quantity': 0.0,
            'remaining_quantity': trade.quantity,
            'commission': 0.0,
            'fees': 0.0,
            'execution_time': None,
            'fill_quality': None,
            'slippage_bps': 0.0,
            'notes': f'Order rejected: {reason}'
        }

    def _create_queued_result(self, trade: Trade, reason: str) -> Dict[str, any]:
        """Create queued result."""
        return {
            'status': 'queued',
            'execution_price': None,
            'filled_quantity': 0.0,
            'remaining_quantity': trade.quantity,
            'commission': 0.0,
            'fees': 0.0,
            'execution_time': None,
            'fill_quality': None,
            'slippage_bps': 0.0,
            'notes': reason
        }

    def _create_error_result(self, trade: Trade, error: str) -> Dict[str, any]:
        """Create error result."""
        return {
            'status': 'error',
            'execution_price': None,
            'filled_quantity': 0.0,
            'remaining_quantity': trade.quantity,
            'commission': 0.0,
            'fees': 0.0,
            'execution_time': None,
            'fill_quality': None,
            'slippage_bps': 0.0,
            'notes': f'Execution error: {error}'
        }

    async def get_execution_statistics(self, user_id: int, days: int = 30) -> Dict[str, any]:
        """Get paper trading execution statistics for analysis."""
        try:
            # Get recent trades
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            trades = self.db.query(Trade).filter(
                Trade.portfolio_id.in_(
                    self.db.query(Portfolio.id).filter(Portfolio.owner_id == user_id)
                ),
                Trade.is_paper_trade == True,
                Trade.created_at >= cutoff_date,
                Trade.status.in_([TradeStatus.FILLED, TradeStatus.PARTIALLY_FILLED])
            ).all()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'message': 'No paper trades found in the specified period'
                }
            
            # Calculate statistics
            total_trades = len(trades)
            filled_trades = len([t for t in trades if t.status == TradeStatus.FILLED])
            partial_fills = len([t for t in trades if t.status == TradeStatus.PARTIALLY_FILLED])
            
            total_commissions = sum(t.commission or 0.0 for t in trades)
            total_fees = sum(t.fees or 0.0 for t in trades)
            
            # Calculate average fill metrics (would parse from notes in real implementation)
            avg_slippage = 2.5  # Placeholder
            avg_execution_time = 150  # Placeholder ms
            
            # Group by order type
            order_types = {}
            for trade in trades:
                ot = trade.order_type.value if trade.order_type else 'unknown'
                if ot not in order_types:
                    order_types[ot] = {'count': 0, 'volume': 0.0}
                order_types[ot]['count'] += 1
                order_types[ot]['volume'] += trade.filled_quantity or 0.0
            
            return {
                'period_days': days,
                'total_trades': total_trades,
                'filled_trades': filled_trades,
                'partial_fills': partial_fills,
                'fill_rate': filled_trades / total_trades if total_trades > 0 else 0.0,
                'total_volume': sum(t.filled_quantity or 0.0 for t in trades),
                'total_value': sum((t.filled_quantity or 0.0) * (t.filled_price or 0.0) for t in trades),
                'total_commissions': total_commissions,
                'total_fees': total_fees,
                'avg_slippage_bps': avg_slippage,
                'avg_execution_time_ms': avg_execution_time,
                'order_type_breakdown': order_types,
                'most_traded_symbols': self._get_top_symbols(trades, 5),
                'execution_quality': {
                    'excellent': '20%',  # Placeholder percentages
                    'good': '45%',
                    'average': '30%',
                    'poor': '5%'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution statistics: {e}")
            return {'error': str(e)}

    def _get_top_symbols(self, trades: List[Trade], limit: int = 5) -> List[Dict]:
        """Get most frequently traded symbols."""
        symbol_counts = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in symbol_counts:
                symbol_counts[symbol] = {'count': 0, 'volume': 0.0}
            symbol_counts[symbol]['count'] += 1
            symbol_counts[symbol]['volume'] += trade.filled_quantity or 0.0
        
        # Sort by trade count
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return [
            {
                'symbol': symbol,
                'trade_count': data['count'],
                'total_volume': data['volume']
            }
            for symbol, data in sorted_symbols[:limit]
        ]