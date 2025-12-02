from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging

from ...models.trade import OrderType, OrderSide
from ...services.market_data import MarketDataService

logger = logging.getLogger(__name__)

class TradingStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(
        self,
        symbol: str,
        market_data_service: MarketDataService,
        risk_percentage: float = 0.02,  # 2% risk per trade
        position_size_limit: float = 0.1,  # Max 10% of portfolio in one position
        stop_loss_pct: float = 0.02,  # 2% stop loss
        take_profit_pct: float = 0.06,  # 6% take profit
    ):
        self.symbol = symbol
        self.market_data_service = market_data_service
        self.risk_percentage = risk_percentage
        self.position_size_limit = position_size_limit
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Strategy state
        self.current_position = 0
        self.average_entry_price = 0
        self.unrealized_pnl = 0
        self.realized_pnl = 0
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0
        
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame) -> Dict:
        """Generate trading signals based on strategy logic
        
        Returns:
            Dict containing signal details:
            {
                'action': 'buy'/'sell'/'hold',
                'confidence': float,
                'price': float,
                'stop_loss': float,
                'take_profit': float
            }
        """
        pass
    
    async def calculate_position_size(
        self,
        portfolio_value: float,
        current_price: float,
        confidence: float
    ) -> float:
        """Calculate appropriate position size based on risk parameters"""
        try:
            # Base position size on risk percentage
            risk_amount = portfolio_value * self.risk_percentage
            
            # Adjust based on confidence
            position_value = risk_amount * confidence
            
            # Calculate shares/contracts
            position_size = position_value / current_price
            
            # Check against position size limit
            max_position = (portfolio_value * self.position_size_limit) / current_price
            position_size = min(position_size, max_position)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    async def validate_trade(
        self,
        action: str,
        price: float,
        size: float,
        portfolio_value: float
    ) -> bool:
        """Validate if a trade meets all strategy criteria"""
        try:
            # Check minimum position size
            if size * price < 100:  # Minimum $100 trade
                logger.warning("Trade rejected: Position size too small")
                return False
            
            # Check maximum position size
            if size * price > portfolio_value * self.position_size_limit:
                logger.warning("Trade rejected: Position size exceeds limit")
                return False
            
            # Check if adding to existing position
            if self.current_position != 0:
                if (action == 'buy' and self.current_position > 0) or \
                   (action == 'sell' and self.current_position < 0):
                    # Check if increasing position beyond limits
                    total_size = abs(self.current_position + size)
                    if total_size * price > portfolio_value * self.position_size_limit:
                        logger.warning("Trade rejected: Total position would exceed limit")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return False
    
    def update_position(self, trade_data: Dict) -> None:
        """Update strategy state after trade execution"""
        try:
            price = trade_data['price']
            quantity = trade_data['quantity']
            side = trade_data['side']
            
            if side == OrderSide.BUY:
                if self.current_position == 0:
                    # New long position
                    self.average_entry_price = price
                else:
                    # Adding to position
                    total_value = (self.current_position * self.average_entry_price) + (quantity * price)
                    total_quantity = self.current_position + quantity
                    self.average_entry_price = total_value / total_quantity
                    
                self.current_position += quantity
                
            else:  # SELL
                realized_pnl = (price - self.average_entry_price) * quantity
                self.realized_pnl += realized_pnl
                self.current_position -= quantity
                
                if self.current_position == 0:
                    self.average_entry_price = 0
                    
            # Update metrics
            self.total_trades += 1
            if realized_pnl > 0:
                self.winning_trades += 1
            elif realized_pnl < 0:
                self.losing_trades += 1
                
        except Exception as e:
            logger.error(f"Error updating position: {str(e)}")
    
    def get_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        try:
            win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
            
            return {
                'symbol': self.symbol,
                'current_position': self.current_position,
                'average_entry_price': self.average_entry_price,
                'unrealized_pnl': self.unrealized_pnl,
                'realized_pnl': self.realized_pnl,
                'total_trades': self.total_trades,
                'win_rate': win_rate,
                'max_drawdown': self.max_drawdown
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {}