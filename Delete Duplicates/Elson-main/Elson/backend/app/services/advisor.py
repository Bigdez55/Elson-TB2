from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging

from app.models.portfolio import Portfolio, Position
from app.models.user import User, UserRole
from app.models.trade import Trade, TradeStatus, OrderType

# Import services
from app.services.risk_management import RiskManager, calculate_portfolio_risk_metrics
from app.services.market_integration import get_market_integration_service, MarketIntegrationService

# Setup logger
logger = logging.getLogger(__name__)

class Recommendation:
    """
    Represents an investment recommendation from the AI advisor
    """
    def __init__(
        self,
        symbol: str,
        action: str,  # "buy" or "sell"
        quantity: float,
        price: float,
        confidence: float,  # 0.0 to 1.0
        strategy: str,
        reason: str
    ):
        self.symbol = symbol
        self.action = action
        self.quantity = quantity
        self.price = price
        self.confidence = confidence
        self.strategy = strategy
        self.reason = reason
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "price": self.price,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }


class AdvisorService:
    """
    High-level service that integrates the trading engine to provide
    AI-powered recommendations and portfolio management
    """
    
    def __init__(self, db: Session, market_data_service=None):
        self.db = db
        # Initialize market integration service
        self.market_integration = get_market_integration_service(db=db, market_data_service=market_data_service)
        self.risk_manager = RiskManager(db)
    
    async def get_recommendations_for_user(self, user_id: int, limit: int = 5) -> List[Recommendation]:
        """
        Get personalized investment recommendations for a user
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return []
            
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return []
        
        # Use the market integration service to generate recommendations
        try:
            # Get recommendations using the market integration service
            strategy_name = "combined"  # Default to combined strategy
            if portfolio.risk_profile in ["conservative", "moderate", "aggressive"]:
                strategy_name = "combined"  # We could use different strategies based on profile
                
            raw_recommendations = await self.market_integration.generate_recommendations(
                user_id=user_id,
                strategy_name=strategy_name,
                max_recommendations=limit * 2  # Get more so we can filter
            )
            
            # Convert to our Recommendation objects and filter based on user's role/restrictions
            recommendations = []
            for rec in raw_recommendations:
                # Skip if this recommendation isn't appropriate
                if user.role == UserRole.MINOR:
                    # Check if this symbol is allowed for minors
                    if rec["symbol"] not in self.risk_manager.ALLOWED_SYMBOLS_MINORS:
                        continue
                
                # Create a recommendation object
                recommendation = Recommendation(
                    symbol=rec["symbol"],
                    action=rec["action"],
                    quantity=rec["quantity"],
                    price=rec["price"],
                    confidence=rec["confidence"],
                    strategy=rec["strategy_name"],
                    reason=rec["reason"]
                )
                recommendations.append(recommendation)
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
    
    def rebalance_portfolio(self, user_id: int) -> List[Trade]:
        """
        Generate trades to rebalance a portfolio according to its target allocation
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return []
            
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return []
        
        # Get current positions
        positions = self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        
        # Get target allocation based on risk profile
        # In a real system, this would be configurable per portfolio
        target_allocation = self._get_target_allocation(portfolio.risk_profile)
        
        # Calculate trades needed to reach target allocation
        trades = []
        current_allocation = {p.symbol: p.quantity * p.current_price for p in positions}
        total_value = portfolio.total_value
        
        # Calculate trades for existing positions
        for position in positions:
            current_pct = (position.quantity * position.current_price) / total_value if total_value > 0 else 0
            target_pct = target_allocation.get(position.symbol, 0)
            
            if abs(current_pct - target_pct) < 0.02:  # 2% threshold to avoid unnecessary trades
                continue
                
            # Calculate target value and current value
            target_value = total_value * target_pct
            current_value = position.quantity * position.current_price
            
            # Calculate needed adjustment
            value_diff = target_value - current_value
            qty_diff = value_diff / position.current_price if position.current_price > 0 else 0
            
            # Create a trade
            if abs(qty_diff) > 0.01:  # Minimum quantity threshold
                trade = Trade(
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    symbol=position.symbol,
                    quantity=abs(qty_diff),
                    price=position.current_price,
                    trade_type="buy" if qty_diff > 0 else "sell",
                    order_type=OrderType.MARKET,
                    status=TradeStatus.PENDING,
                    total_amount=abs(qty_diff) * position.current_price,
                    requested_by_user_id=None,  # This is system-generated
                )
                trades.append(trade)
        
        # Calculate trades for new positions in target allocation
        for symbol, target_pct in target_allocation.items():
            if symbol in [p.symbol for p in positions]:
                continue  # Already handled above
                
            # This is a new position to add
            if target_pct > 0.01:  # Minimum allocation threshold
                # Get current price for the symbol (would come from market data service)
                current_price = 100.0  # Placeholder - this should come from market data
                
                target_value = total_value * target_pct
                qty = target_value / current_price if current_price > 0 else 0
                
                if qty > 0.01:  # Minimum quantity threshold
                    trade = Trade(
                        user_id=user_id,
                        portfolio_id=portfolio.id,
                        symbol=symbol,
                        quantity=qty,
                        price=current_price,
                        trade_type="buy",
                        order_type=OrderType.MARKET,
                        status=TradeStatus.PENDING,
                        total_amount=qty * current_price,
                        requested_by_user_id=None,  # This is system-generated
                    )
                    trades.append(trade)
        
        # Update the last_rebalanced_at timestamp
        portfolio.last_rebalanced_at = datetime.utcnow()
        self.db.commit()
        
        return trades
    
    def _get_target_allocation(self, risk_profile: str) -> Dict[str, float]:
        """
        Get target allocation based on risk profile
        This is a simplified version - in a real system this would be more sophisticated
        """
        if risk_profile == "conservative":
            return {
                "SPY": 0.30,
                "AGG": 0.30,
                "BND": 0.20,
                "VTI": 0.10,
                "VXUS": 0.10
            }
        elif risk_profile == "aggressive":
            return {
                "SPY": 0.40,
                "QQQ": 0.30,
                "VB": 0.15,
                "VXUS": 0.15
            }
        else:  # moderate is default
            return {
                "SPY": 0.35,
                "VTI": 0.20,
                "VXUS": 0.15,
                "BND": 0.15,
                "VB": 0.15
            }
    
    async def create_trade_from_recommendation(
        self, 
        user_id: int, 
        recommendation: Recommendation
    ) -> Tuple[Optional[Trade], Optional[str]]:
        """
        Create a trade from a recommendation, applying risk checks
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"
            
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            return None, "Portfolio not found"
        
        # Create a draft trade
        trade = Trade(
            user_id=user_id,
            portfolio_id=portfolio.id,
            symbol=recommendation.symbol,
            quantity=recommendation.quantity,
            price=recommendation.price,
            trade_type=recommendation.action.lower(),
            order_type=OrderType.MARKET,
            total_amount=recommendation.quantity * recommendation.price,
            requested_by_user_id=user_id
        )
        
        # Set status based on user role
        if user.role == UserRole.MINOR:
            trade.status = TradeStatus.PENDING_APPROVAL
        else:
            trade.status = TradeStatus.PENDING
        
        # Check if the trade passes risk checks
        risk_check = self.risk_manager.check_trade(user_id, trade)
        if not risk_check.approved:
            return None, risk_check.reason
            
        # Save the trade
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        
        # If user is not a minor and trade is ready to execute, use the market integration service
        if user.role != UserRole.MINOR:
            try:
                # Convert recommendation to format expected by market integration
                rec_dict = {
                    "symbol": recommendation.symbol,
                    "action": recommendation.action,
                    "quantity": recommendation.quantity,
                    "price": recommendation.price,
                    "confidence": recommendation.confidence,
                    "strategy_name": recommendation.strategy,
                    "reason": recommendation.reason
                }
                
                # Execute the trade using market integration service
                executed_trades = await self.market_integration.execute_trades_from_recommendations(
                    user_id=user_id,
                    recommendations=[rec_dict]
                )
                
                if executed_trades:
                    # Update our trade with execution details from the first executed trade
                    executed_trade = executed_trades[0]
                    trade.broker_order_id = executed_trade.broker_order_id
                    trade.status = executed_trade.status
                    trade.executed_at = executed_trade.executed_at
                    trade.filled_quantity = executed_trade.filled_quantity
                    trade.filled_price = executed_trade.filled_price
                    
                    # Save updates
                    self.db.commit()
                    self.db.refresh(trade)
            except Exception as e:
                logger.error(f"Error executing trade: {str(e)}")
                # Don't fail if execution fails - the trade is still created and can be executed later
        
        return trade, None
        
    async def update_portfolio_prices(self, user_id: int) -> bool:
        """
        Update current market prices for a user's portfolio.
        
        Args:
            user_id: User ID to update portfolio for
            
        Returns:
            True if successful, False otherwise
        """
        # Get portfolio
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return False
        
        try:
            # Use market integration service to update prices
            updated_count = await self.market_integration.update_market_prices(portfolio.id)
            
            logger.info(f"Updated {updated_count} position prices for user {user_id}")
            return updated_count > 0
        except Exception as e:
            logger.error(f"Error updating portfolio prices for user {user_id}: {str(e)}")
            return False
            
    async def get_market_prediction(
        self,
        symbol: str, 
        days_ahead: int = 5
    ) -> Dict[str, Any]:
        """
        Get market prediction for a symbol.
        
        Args:
            symbol: Symbol to predict
            days_ahead: Number of days ahead to predict
            
        Returns:
            Dictionary with prediction data
        """
        try:
            # Use market integration service to get prediction
            prediction = await self.market_integration.get_prediction(
                symbol=symbol,
                prediction_type="price",
                days_ahead=days_ahead
            )
            
            return prediction
        except Exception as e:
            logger.error(f"Error getting prediction for {symbol}: {str(e)}")
            return {"error": str(e)}