from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy
from ...models.trade import OrderType, OrderSide, Trade
from ...services.market_data import MarketDataService

logger = logging.getLogger(__name__)

class MovingAverageStrategy(BaseStrategy):
    def __init__(
        self,
        market_data_service: MarketDataService,
        symbol: str,
        short_window: int = 20,
        long_window: int = 50,
        rsi_period: int = 14,
        rsi_overbought: int = 70,
        rsi_oversold: int = 30,
        volume_factor: float = 1.5
    ):
        super().__init__(market_data_service)
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_factor = volume_factor
        
        # Strategy state
        self.current_position = 0
        self.last_signal = None
        self.last_crossover = None

    async def generate_signals(self) -> Optional[Dict]:
        """Generate trading signals based on moving average crossover"""
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=100)  # Get enough data for indicators
            df = await self.market_data_service.get_historical_data(
                self.symbol,
                start_date,
                end_date
            )

            if df.empty:
                logger.warning(f"No data available for {self.symbol}")
                return None

            # Calculate indicators
            signals = self._calculate_indicators(df)
            
            # Generate trading decision
            return self._generate_trading_decision(signals)

        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # Calculate moving averages
        df['SMA_short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_long'] = df['Close'].rolling(window=self.long_window).mean()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate volume moving average
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Calculate MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Generate crossover signals
        df['Signal'] = 0
        df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1
        df.loc[df['SMA_short'] < df['SMA_long'], 'Signal'] = -1
        
        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict:
        """Generate trading decision based on signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        signal = None
        confidence = 0.0
        
        # Detect crossover
        if prev_row['Signal'] != last_row['Signal']:
            if last_row['Signal'] == 1:  # Bullish crossover
                signal = OrderSide.BUY
                self.last_crossover = 'bullish'
            elif last_row['Signal'] == -1:  # Bearish crossover
                signal = OrderSide.SELL
                self.last_crossover = 'bearish'
        
        # Confirm signal with other indicators
        if signal:
            confidence = self._calculate_signal_confidence(last_row)
            
            # Only generate signal if confidence is high enough
            if confidence >= 0.7:
                return {
                    'symbol': self.symbol,
                    'side': signal,
                    'confidence': confidence,
                    'price': last_row['Close'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'indicators': {
                        'rsi': last_row['RSI'],
                        'macd': last_row['MACD'],
                        'volume_ratio': last_row['Volume_Ratio'],
                        'short_ma': last_row['SMA_short'],
                        'long_ma': last_row['SMA_long']
                    }
                }
        
        return None

    def _calculate_signal_confidence(self, row: pd.Series) -> float:
        """Calculate confidence score for signal"""
        confidence = 0.0
        weights = {
            'crossover': 0.4,
            'rsi': 0.2,
            'volume': 0.2,
            'macd': 0.2
        }
        
        # Crossover confidence
        if self.last_crossover == 'bullish':
            confidence += weights['crossover']
        elif self.last_crossover == 'bearish':
            confidence += weights['crossover']
        
        # RSI confidence
        if self.last_crossover == 'bullish' and row['RSI'] < self.rsi_oversold:
            confidence += weights['rsi']
        elif self.last_crossover == 'bearish' and row['RSI'] > self.rsi_overbought:
            confidence += weights['rsi']
        
        # Volume confidence
        if row['Volume_Ratio'] > self.volume_factor:
            confidence += weights['volume']
        
        # MACD confidence
        if (self.last_crossover == 'bullish' and row['MACD'] > row['Signal_Line']) or \
           (self.last_crossover == 'bearish' and row['MACD'] < row['Signal_Line']):
            confidence += weights['macd']
        
        return confidence

    async def generate_trade(self, signal: Dict) -> Optional[Trade]:
        """Generate trade based on signal"""
        try:
            if not signal:
                return None

            # Get current quote
            quote = await self.market_data_service.get_quote(self.symbol)
            current_price = Decimal(str(quote['price']))

            # Calculate position size based on confidence
            position_size = self._calculate_position_size(
                current_price,
                signal['confidence']
            )

            return Trade(
                symbol=self.symbol,
                order_type=OrderType.MARKET,
                side=signal['side'],
                quantity=position_size,
                price=current_price,
                status='PENDING'
            )

        except Exception as e:
            logger.error(f"Error generating trade: {str(e)}")
            return None

    def _calculate_position_size(self, price: Decimal, confidence: float) -> Decimal:
        """Calculate position size based on confidence and risk parameters"""
        base_size = Decimal('100')  # Base position size
        confidence_factor = Decimal(str(confidence))
        return base_size * confidence_factor

    def update_position(self, quantity: Decimal):
        """Update current position"""
        self.current_position += quantity

    def get_strategy_state(self) -> Dict:
        """Get current strategy state"""
        return {
            'symbol': self.symbol,
            'current_position': self.current_position,
            'last_signal': self.last_signal,
            'last_crossover': self.last_crossover,
            'parameters': {
                'short_window': self.short_window,
                'long_window': self.long_window,
                'rsi_period': self.rsi_period,
                'rsi_overbought': self.rsi_overbought,
                'rsi_oversold': self.rsi_oversold,
                'volume_factor': self.volume_factor
            }
        }