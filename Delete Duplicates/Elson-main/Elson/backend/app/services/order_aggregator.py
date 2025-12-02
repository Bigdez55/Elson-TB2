"""Order aggregation service for handling fractional share orders.

This module provides functionality for aggregating multiple small orders
(especially fractional share orders) into larger orders for more efficient
execution and to meet minimum order size requirements.
"""

import logging
from decimal import Decimal
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.trade import Trade, TradeStatus, TradeSource, InvestmentType, OrderType
from app.services.market_data import MarketDataService
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrderAggregator:
    """Aggregates small orders (especially fractional shares) into larger orders."""
    
    def __init__(
        self, 
        db: Session,
        market_data_service: MarketDataService
    ):
        """Initialize with database session and market data service."""
        self.db = db
        self.market_data = market_data_service
        
        # Configuration - load from settings with defaults
        self.min_order_amount = Decimal(str(getattr(settings, "MIN_ORDER_AMOUNT", 10.00)))
        self.min_fractional_amount = Decimal(str(getattr(settings, "MIN_FRACTIONAL_AMOUNT", 1.00)))
        self.max_aggregation_delay = timedelta(minutes=int(getattr(settings, "MAX_AGGREGATION_DELAY_MINUTES", 15)))
        self.aggregation_threshold = Decimal(str(getattr(settings, "AGGREGATION_THRESHOLD", 100.00)))
        
        # System account settings
        self.system_user_id = getattr(settings, "SYSTEM_USER_ID", 1)
        self.system_portfolio_id = getattr(settings, "SYSTEM_PORTFOLIO_ID", 1)
        
        logger.info(f"OrderAggregator initialized with min_fractional={self.min_fractional_amount}, "
                   f"threshold={self.aggregation_threshold}, "
                   f"max_delay={self.max_aggregation_delay}")
    
    def get_pending_dollar_based_orders(self, symbol: Optional[str] = None) -> List[Trade]:
        """Get pending dollar-based orders ready for aggregation."""
        query = self.db.query(Trade).filter(
            and_(
                Trade.status == TradeStatus.PENDING,
                Trade.investment_type == InvestmentType.DOLLAR_BASED,
                Trade.parent_order_id.is_(None)  # Not already aggregated
            )
        )
        
        # Filter by symbol if provided
        if symbol:
            query = query.filter(Trade.symbol == symbol)
            
        # Orders older than the max delay should be processed immediately
        max_age = datetime.utcnow() - self.max_aggregation_delay
        
        # Get orders either older than max delay or where we have enough volume
        result = query.filter(
            or_(
                Trade.created_at <= max_age,
                Trade.investment_amount >= self.aggregation_threshold
            )
        ).all()
        
        return result
    
    def aggregate_orders_by_symbol(self) -> Dict[str, List[Trade]]:
        """Aggregate pending dollar-based orders by symbol."""
        # Get all symbols with pending dollar-based orders
        symbols = self.db.query(Trade.symbol).filter(
            and_(
                Trade.status == TradeStatus.PENDING,
                Trade.investment_type == InvestmentType.DOLLAR_BASED,
                Trade.parent_order_id.is_(None)
            )
        ).distinct().all()
        
        # Extract symbols from query result
        symbols = [symbol[0] for symbol in symbols]
        
        aggregated_orders = {}
        for symbol in symbols:
            orders = self.get_pending_dollar_based_orders(symbol)
            if orders:
                aggregated_orders[symbol] = orders
                
        return aggregated_orders
    
    def create_parent_order(self, symbol: str, child_orders: List[Trade]) -> Optional[Trade]:
        """Create a parent order to represent the aggregated child orders.
        
        Args:
            symbol: Stock symbol to aggregate orders for
            child_orders: List of child orders to aggregate
            
        Returns:
            Parent trade object if successful, None otherwise
        """
        if not child_orders:
            return None
            
        # Verify all orders are for the same symbol and trade type (buy/sell)
        if any(order.symbol != symbol for order in child_orders):
            logger.error(f"Attempted to aggregate orders with different symbols: {symbol}")
            return None
            
        # Only aggregate orders of the same side (buy/sell)
        trade_type = child_orders[0].trade_type
        if any(order.trade_type != trade_type for order in child_orders):
            logger.error(f"Attempted to aggregate orders with different sides for {symbol}")
            return None
            
        # Sum up the total investment amount
        total_investment = sum(
            Decimal(str(order.investment_amount)) for order in child_orders
            if order.investment_amount is not None
        )
        
        # Validate minimum investment amount
        if total_investment < self.min_order_amount:
            logger.warning(
                f"Aggregated investment amount ${total_investment} for {symbol} "
                f"below minimum order amount ${self.min_order_amount}"
            )
            # We'll still continue as this might be necessary for small orders
        
        # Get current price
        try:
            current_price = Decimal(str(self.market_data.get_current_price(symbol)))
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
            
        # Calculate the total quantity based on investment amount and current price
        total_quantity = (total_investment / current_price).quantize(Decimal('0.00000001'))
        
        # Create the parent order
        parent_order = Trade(
            user_id=self.system_user_id,  # Use system user for parent orders
            portfolio_id=self.system_portfolio_id,  # System portfolio for aggregation
            symbol=symbol,
            quantity=total_quantity,
            price=current_price,
            investment_amount=total_investment,
            investment_type=InvestmentType.DOLLAR_BASED,  # Keep as dollar-based
            trade_type=trade_type,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
            is_fractional=True,  # Parent is now fractional for consistency
            trade_source=TradeSource.AGGREGATED,
            total_amount=total_investment,
            created_at=datetime.utcnow()
        )
        
        # Add additional metadata to track child orders
        child_ids = [order.id for order in child_orders]
        
        self.db.add(parent_order)
        self.db.flush()  # Need to flush to get the ID
        
        # Update child orders to reference the parent
        for order in child_orders:
            order.parent_order_id = parent_order.id
            
            # Don't change the original trade source, we want to preserve that information
            # Instead, update the status to indicate it's part of an aggregated order
            order.status = TradeStatus.PENDING
            
        self.db.commit()
        
        logger.info(
            f"Created parent order {parent_order.id} for {len(child_orders)} "
            f"child orders of {symbol} with total investment ${total_investment}"
        )
        
        return parent_order
    
    def process_completed_parent_order(self, parent_order_id: int) -> bool:
        """Process a completed parent order and update child orders.
        
        This method distributes the executed shares from a parent order to its
        child orders proportionally based on their investment amounts.
        
        Args:
            parent_order_id: ID of the parent order to process
            
        Returns:
            True if successful, False otherwise
        """
        parent_order = self.db.query(Trade).filter(Trade.id == parent_order_id).first()
        if not parent_order:
            logger.error(f"Parent order {parent_order_id} not found")
            return False
            
        # Process both filled and partially filled orders
        if parent_order.status not in [TradeStatus.FILLED, TradeStatus.PARTIALLY_FILLED]:
            logger.warning(
                f"Cannot process parent order {parent_order_id} with status {parent_order.status}"
            )
            return False
            
        # Get all child orders
        child_orders = self.db.query(Trade).filter(
            Trade.parent_order_id == parent_order_id
        ).all()
        
        if not child_orders:
            logger.warning(f"No child orders found for parent order {parent_order_id}")
            return False
            
        # Update child orders
        total_investment = sum(
            Decimal(str(order.investment_amount)) for order in child_orders 
            if order.investment_amount is not None
        )
        
        # Get execution details with fallbacks for safety
        filled_quantity = parent_order.filled_quantity
        if filled_quantity is None or filled_quantity == 0:
            filled_quantity = parent_order.quantity or Decimal('0')
            
        # Use average price if available, fall back to trade price if needed
        executed_price = (
            parent_order.average_price if parent_order.average_price 
            else parent_order.price or Decimal('0')
        )
        
        # Calculate total filled amount to check investment ratio
        total_filled_amount = filled_quantity * executed_price
        
        # Check if we didn't get full execution (could happen in partially filled orders)
        execution_ratio = Decimal('1.0')
        if total_filled_amount > 0 and total_investment > 0:
            execution_ratio = min(Decimal('1.0'), total_filled_amount / total_investment)
            
        for child_order in child_orders:
            if child_order.investment_amount is None or child_order.investment_amount == 0:
                continue
                
            # Calculate proportional allocation
            child_ratio = Decimal(str(child_order.investment_amount)) / total_investment
            
            # Quantity distributed to this child order
            child_quantity = (filled_quantity * child_ratio).quantize(Decimal('0.00000001'))
            
            # Actual invested amount (could be less than requested if order partially filled)
            actual_investment = child_order.investment_amount * execution_ratio
            
            # Update child order to mark as filled
            child_order.status = TradeStatus.FILLED
            child_order.filled_quantity = child_quantity
            child_order.quantity = child_quantity  # Set quantity based on actual fill
            child_order.average_price = executed_price
            child_order.price = executed_price
            child_order.executed_at = parent_order.executed_at or datetime.utcnow()
            child_order.settlement_date = parent_order.settlement_date
            child_order.broker_status = "filled_via_aggregation"
            child_order.total_amount = actual_investment
            
            # No commission on child orders as it's paid at parent level
            child_order.commission = Decimal('0.00')
            
            # Explicitly mark as fractional because the child_quantity will almost 
            # certainly be a fractional amount
            child_order.is_fractional = True
            
        self.db.commit()
        
        logger.info(
            f"Updated {len(child_orders)} child orders for completed parent order {parent_order_id}"
            f" with execution price ${executed_price} and total quantity {filled_quantity}"
        )
        
        return True
    
    def validate_min_investment(self, investment_amount: Decimal) -> bool:
        """Validate that an investment meets minimum requirements.
        
        Args:
            investment_amount: The dollar amount of the investment
            
        Returns:
            True if valid, False if too small
        """
        if investment_amount < self.min_fractional_amount:
            logger.warning(
                f"Investment amount ${investment_amount} below minimum ${self.min_fractional_amount}"
            )
            return False
        return True
    
    def get_aggregatable_pending_orders(self) -> List[Trade]:
        """Get all pending orders that could be aggregated but haven't been yet.
        
        Returns:
            List of trades eligible for aggregation
        """
        return self.db.query(Trade).filter(
            and_(
                Trade.status == TradeStatus.PENDING,
                Trade.is_fractional == True,
                Trade.investment_type == InvestmentType.DOLLAR_BASED,
                Trade.parent_order_id.is_(None),
                Trade.investment_amount < self.aggregation_threshold
            )
        ).all()
        
    def get_pending_parent_orders(self) -> List[Trade]:
        """Get all pending parent orders ready for execution.
        
        Returns:
            List of parent trades ready to be executed
        """
        return self.db.query(Trade).filter(
            and_(
                Trade.status == TradeStatus.PENDING,
                Trade.trade_source == TradeSource.AGGREGATED,
                # Parent orders don't have parent_order_id
                Trade.parent_order_id.is_(None)
            )
        ).all()
    
    def get_completed_parent_orders(self) -> List[Trade]:
        """Get completed parent orders that need to update their child orders.
        
        Returns:
            List of completed parent trades
        """
        return self.db.query(Trade).filter(
            and_(
                Trade.status.in_([TradeStatus.FILLED, TradeStatus.PARTIALLY_FILLED]),
                Trade.trade_source == TradeSource.AGGREGATED,
                # Parent orders don't have parent_order_id
                Trade.parent_order_id.is_(None)
            )
        ).all()
            
    def run_aggregation_cycle(self) -> Dict[str, Any]:
        """Run a complete aggregation cycle.
        
        This method:
        1. Finds all pending fractional orders that can be aggregated
        2. Groups them by symbol and trade type
        3. Creates parent orders for each group
        4. Returns statistics about the aggregation process
        
        Returns:
            Dictionary with aggregation statistics
        """
        result = {
            "orders_aggregated": 0,
            "parent_orders_created": 0,
            "symbols_processed": 0,
            "errors": 0,
            "completed_parent_orders": 0
        }
        
        try:
            # Process completed parent orders first
            completed_parents = self.get_completed_parent_orders()
            for parent in completed_parents:
                try:
                    if self.process_completed_parent_order(parent.id):
                        result["completed_parent_orders"] += 1
                except Exception as e:
                    logger.error(f"Error processing completed parent order {parent.id}: {e}")
                    result["errors"] += 1
            
            # Get orders aggregated by symbol
            aggregated_by_symbol = self.aggregate_orders_by_symbol()
            result["symbols_processed"] = len(aggregated_by_symbol)
            
            # Process each symbol
            for symbol, orders in aggregated_by_symbol.items():
                try:
                    # Skip if no orders
                    if not orders:
                        continue
                        
                    # Create parent order
                    parent_order = self.create_parent_order(symbol, orders)
                    if parent_order:
                        result["orders_aggregated"] += len(orders)
                        result["parent_orders_created"] += 1
                except Exception as e:
                    logger.error(f"Error processing orders for {symbol}: {e}")
                    result["errors"] += 1
            
            # Log statistics
            logger.info(
                f"Aggregation cycle: processed {result['symbols_processed']} symbols, "
                f"aggregated {result['orders_aggregated']} orders into {result['parent_orders_created']} "
                f"parent orders, processed {result['completed_parent_orders']} completed parents, "
                f"encountered {result['errors']} errors"
            )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error running aggregation cycle: {e}")
            result["errors"] += 1
            return result