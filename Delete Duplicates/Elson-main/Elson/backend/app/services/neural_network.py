import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TradingModel(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64):
        super(TradingModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])

class NeuralNetworkService:
    def __init__(self, market_data_service=None):
        self.market_data_service = market_data_service
        self.models = {}  # Store models by symbol
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Default input size for technical features
        self.input_size = 10  # Extended feature set for better predictions
        
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for the model"""
        features = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Calculate technical indicators
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['RSI'] = self.calculate_rsi(df['Close'])
        df['MACD'] = self.calculate_macd(df['Close'])
        
        # Create sequences
        sequence_length = 20
        sequences = []
        targets = []
        
        for i in range(len(df) - sequence_length):
            sequence = df[features].iloc[i:i + sequence_length].values
            target = df['Close'].iloc[i + sequence_length]
            sequences.append(sequence)
            targets.append(target)
            
        return np.array(sequences), np.array(targets)

    @staticmethod
    def calculate_rsi(prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(prices: pd.Series) -> pd.Series:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        return exp1 - exp2

    async def train(self, symbol: str, days: int = 365):
        """Train the model on historical data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch historical data
            df = await self.market_data_service.get_historical_data(
                symbol, start_date, end_date
            )
            
            # Prepare data
            X, y = self.preprocess_data(df)
            X = torch.FloatTensor(X).to(self.device)
            y = torch.FloatTensor(y).to(self.device)
            
            # Training parameters
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            # Training loop
            self.model.train()
            for epoch in range(100):
                optimizer.zero_grad()
                outputs = self.model(X)
                loss = criterion(outputs.squeeze(), y)
                loss.backward()
                optimizer.step()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f'Epoch [{epoch+1}/100], Loss: {loss.item():.4f}')
                    
        except Exception as e:
            logger.error(f"Error training model for {symbol}: {str(e)}")
            raise

    def predict(self, symbol: str, features: Dict[str, List[float]], horizon: int = 7) -> Dict:
        """
        Generate price predictions using technical features
        
        Args:
            symbol: The symbol to predict
            features: Dictionary of technical features
            horizon: Prediction horizon in days
            
        Returns:
            Prediction dictionary with price direction and confidence
        """
        try:
            # For now, we'll implement a simplified prediction method
            # In a real implementation, this would use the pre-trained model
            
            # Extract key technical indicators from features
            rsi = 50.0  # Default neutral
            macd = 0.0  # Default neutral
            bb_position = 0.5  # Default middle of bands
            volatility = 0.01  # Default low volatility
            momentum = 0.0  # Default no momentum
            
            # Try to extract actual values if available
            if 'rsi' in features and len(features['rsi']) > 0:
                rsi = features['rsi'][-1]
                
            if 'macd_line' in features and len(features['macd_line']) > 0:
                macd = features['macd_line'][-1]
                
            if 'bb_position' in features and len(features['bb_position']) > 0:
                bb_position = features['bb_position'][-1]
                
            if 'volatility_20' in features and len(features['volatility_20']) > 0:
                volatility = features['volatility_20'][-1]
                
            if 'returns' in features and len(features['returns']) > 10:
                # Calculate recent momentum (last 10 periods)
                momentum = sum(features['returns'][-10:])
            
            # Combined prediction score
            # Positive = bullish, Negative = bearish
            prediction_score = 0.0
            
            # RSI factor (oversold = bullish, overbought = bearish)
            if rsi < 30:
                prediction_score += 0.3
            elif rsi > 70:
                prediction_score -= 0.3
                
            # MACD factor
            prediction_score += macd * 5.0  # Scale MACD contribution
            
            # Bollinger Band position factor
            if bb_position < 0.2:
                prediction_score += 0.25  # Near lower band = bullish
            elif bb_position > 0.8:
                prediction_score -= 0.25  # Near upper band = bearish
                
            # Momentum factor
            prediction_score += momentum * 10.0  # Scale momentum contribution
            
            # Scale prediction based on horizon
            # Longer horizons tend toward mean reversion for extreme values
            if horizon > 14:
                prediction_score *= max(0.5, 1.0 - (horizon - 14) / 60)
                
            # Convert score to direction and confidence
            direction = 1 if prediction_score > 0 else -1
            confidence = min(0.9, 0.5 + abs(prediction_score))
            
            # Calculate expected return
            expected_return = prediction_score * (0.01 * horizon)  # rough estimate
            
            # Create prediction result
            return {
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'prediction_horizon': horizon,
                'expected_return': expected_return,
                'prediction_score': prediction_score,
                'volatility': volatility,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {str(e)}")
            # Return a default neutral prediction
            return {
                'symbol': symbol,
                'direction': 0,
                'confidence': 0.5,
                'prediction_horizon': horizon,
                'expected_return': 0.0,
                'prediction_score': 0.0,
                'volatility': 0.02,
                'timestamp': datetime.now().isoformat()
            }

    def calculate_confidence_score(self, df: pd.DataFrame, prediction: float) -> float:
        """Calculate a confidence score for the prediction"""
        try:
            # Calculate volatility
            volatility = df['Close'].pct_change().std()
            
            # Calculate trend strength
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            trend_strength = abs((ma20 - ma50) / ma50)
            
            # Combine factors for confidence score
            confidence = (1 - volatility) * (1 + trend_strength)
            return min(max(confidence, 0), 1)  # Normalize between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5  # Return neutral confidence on error