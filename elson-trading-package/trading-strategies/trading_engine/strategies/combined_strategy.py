from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from .base import TradingStrategy
from ...services.neural_network import PredictionService
from ...services.market_data import MarketDataService

logger = logging.getLogger(__name__)

class CombinedStrategy(TradingStrategy):
    """Strategy combining technical indicators with ML predictions"""
    
    def __init__(
        self,
        symbol: str,
        market_data_service: MarketDataService,
        prediction_service: PredictionService,
        short_ma: int = 20,
        long_ma: int = 50,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        prediction_weight: float = 0.6,  # Weight given to ML predictions
        **kwargs
    ):
        super().__init__(symbol, market_data_service, **kwargs)
        self.prediction_service = prediction_service
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.prediction_weight = prediction_weight
        
    async def generate_signals(self, data: pd.DataFrame) -> Dict:
        """Generate trading signals using combined analysis"""
        try:
            # Calculate technical indicators
            signals = await self._calculate_technical_signals(data)
            
            # Get ML predictions
            prediction = await self.prediction_service.predict(self.symbol)
            
            # Combine signals
            technical_score = signals['signal_strength']  # -1 to 1
            prediction_score = self._normalize_prediction(prediction)  # -1 to 1
            
            # Weighted combination
            combined_score = (technical_score * (1 - self.prediction_weight) + 
                            prediction_score * self.prediction_weight)
            
            # Generate final signal
            current_price = data['Close'].iloc[-1]
            signal = self._generate_final_signal(
                combined_score,
                current_price,
                signals['volatility']
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return {'action': 'hold', 'confidence': 0}
    
    async def _calculate_technical_signals(self, data: pd.DataFrame) -> Dict:
        """Calculate technical analysis signals"""
        try:
            # Calculate moving averages
            data['SMA_short'] = data['Close'].rolling(window=self.short_ma).mean()
            data['SMA_long'] = data['Close'].rolling(window=self.long_ma).mean()
            
            # Calculate RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate volatility
            data['Volatility'] = data['Close'].pct_change().rolling(window=20).std()
            
            # Generate signal strength (-1 to 1)
            ma_signal = 1 if data['SMA_short'].iloc[-1] > data['SMA_long'].iloc[-1] else -1
            rsi_signal = self._get_rsi_signal(data['RSI'].iloc[-1])
            
            signal_strength = (ma_signal + rsi_signal) / 2
            
            return {
                'signal_strength': signal_strength,
                'volatility': data['Volatility'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical signals: {str(e)}")
            return {'signal_strength': 0, 'volatility': 0}
    
    def _get_rsi_signal(self, rsi: float) -> float:
        """Convert RSI to signal strength"""
        if rsi <= self.rsi_oversold:
            return 1  # Strong buy
        elif rsi >= self.rsi_overbought:
            return -1  # Strong sell
        else:
            # Linear scaling between oversold and overbought
            return 1 - (2 * (rsi - self.rsi_oversold) / 
                       (self.rsi_overbought - self.rsi_oversold))
    
    def _normalize_prediction(self, prediction: Dict) -> float:
        """Convert price prediction to signal strength"""
        try:
            current_price = prediction['current_price']
            predicted_price = prediction['predicted_price']
            confidence = prediction['confidence_score']
            
            # Calculate predicted return
            predicted_return = (predicted_price - current_price) / current_price
            
            # Scale to -1 to 1 range and adjust by confidence
            max_expected_return = 0.05  # 5% move
            signal_strength = (predicted_return / max_expected_return) * confidence
            
            return np.clip(signal_strength, -1, 1)
            
        except Exception as e:
            logger.error(f"Error normalizing prediction: {str(e)}")
            return 0
    
    def _generate_final_signal(
        self,
        combined_score: float,
        current_price: float,
        volatility: float
    ) -> Dict:
        """Generate final trading signal"""
        try:
            # Signal thresholds
            threshold = 0.3 + (volatility * 2)  # Increase threshold in high volatility
            
            if combined_score > threshold:
                action = 'buy'
                confidence = min((combined_score - threshold) / (1 - threshold), 1)
            elif combined_score < -threshold:
                action = 'sell'
                confidence = min((-combined_score - threshold) / (1 - threshold), 1)
            else:
                action = 'hold'
                confidence = 0
            
            # Calculate stop loss and take profit levels
            stop_loss = None
            take_profit = None
            
            if action != 'hold':
                volatility_factor = max(1, 1 + (volatility * 5))
                if action == 'buy':
                    stop_loss = current_price * (1 - self.stop_loss_pct * volatility_factor)
                    take_profit = current_price * (1 + self.take_profit_pct * volatility_factor)
                else:
                    stop_loss = current_price * (1 + self.stop_loss_pct * volatility_factor)
                    take_profit = current_price * (1 - self.take_profit_pct * volatility_factor)
            
            return {
                'action': action,
                'confidence': confidence,
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'signal_score': combined_score,
                'volatility': volatility
            }
            
        except Exception as e:
            logger.error(f"Error generating final signal: {str(e)}")
            return {
                'action': 'hold',
                'confidence': 0,
                'price': current_price
            }