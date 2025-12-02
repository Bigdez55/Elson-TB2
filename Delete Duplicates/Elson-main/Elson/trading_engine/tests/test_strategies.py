import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from strategies.base import BaseStrategy
from strategies.moving_average import MovingAverageStrategy
from strategies.combined_strategy import CombinedStrategy


class TestBaseStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = BaseStrategy()
        
        # Create sample historical data
        dates = pd.date_range(start='2020-01-01', periods=100)
        self.data = pd.DataFrame({
            'date': dates,
            'close': np.random.normal(100, 10, 100),
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        self.data.set_index('date', inplace=True)
    
    def test_base_strategy_generate_signals(self):
        # BaseStrategy.generate_signals should raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            self.strategy.generate_signals(self.data)
    
    def test_base_strategy_calculate_returns(self):
        # Create a simple signal series
        signals = pd.Series(index=self.data.index)
        signals.iloc[0:20] = 0
        signals.iloc[20:40] = 1
        signals.iloc[40:60] = 0
        signals.iloc[60:80] = -1
        signals.iloc[80:] = 0
        
        # Calculate returns
        returns = self.strategy.calculate_returns(self.data, signals)
        
        # Verify returns has the correct shape
        self.assertEqual(len(returns), len(self.data) - 1)
        
        # Verify returns is a pandas Series
        self.assertIsInstance(returns, pd.Series)


class TestMovingAverageStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = MovingAverageStrategy(short_window=10, long_window=30)
        
        # Generate sample price data with a clear trend
        dates = pd.date_range(start='2020-01-01', periods=100)
        
        # Create a price series with an uptrend followed by a downtrend
        prices = np.zeros(100)
        # Uptrend
        prices[0:50] = np.linspace(100, 150, 50)
        # Downtrend
        prices[50:] = np.linspace(150, 100, 50)
        # Add some noise
        prices += np.random.normal(0, 2, 100)
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        self.data.set_index('date', inplace=True)
    
    def test_moving_average_strategy_generate_signals(self):
        # Generate signals
        signals = self.strategy.generate_signals(self.data)
        
        # Verify signals is a pandas Series
        self.assertIsInstance(signals, pd.Series)
        
        # Verify signals has the correct length
        self.assertEqual(len(signals), len(self.data))
        
        # Verify the first long_window-1 values are NaN (not enough data for the long MA)
        self.assertTrue(signals.iloc[:self.strategy.long_window-1].isna().all())
        
        # Verify signals contain expected values: -1, 0, or 1
        valid_signals = signals.iloc[self.strategy.long_window-1:]
        self.assertTrue(set(valid_signals.unique()).issubset({-1, 0, 1}))
    
    def test_moving_average_strategy_trading_logic(self):
        # Generate signals
        signals = self.strategy.generate_signals(self.data)
        
        # Skip NaN values
        valid_signals = signals.dropna()
        
        # Verify we get at least one buy and one sell signal
        self.assertIn(1, valid_signals.values, "No buy signals generated")
        self.assertIn(-1, valid_signals.values, "No sell signals generated")
        
        # Calculate returns
        returns = self.strategy.calculate_returns(self.data, signals)
        
        # Verify returns has correct length
        self.assertEqual(len(returns), len(self.data) - 1)


class TestCombinedStrategy(unittest.TestCase):
    def setUp(self):
        # Create two simple strategies
        self.ma_strategy = MovingAverageStrategy(short_window=10, long_window=30)
        
        # Define a simple custom trend strategy
        class TrendStrategy(BaseStrategy):
            def generate_signals(self, data):
                signals = pd.Series(index=data.index)
                signals.iloc[:] = 0
                
                # Simple trend detection (naive implementation for testing)
                # If price > 5-day moving average, go long
                # If price < 5-day moving average, go short
                sma5 = data['close'].rolling(window=5).mean()
                
                # Long signal
                signals[data['close'] > sma5] = 1
                
                # Short signal
                signals[data['close'] < sma5] = -1
                
                # First few days don't have a moving average
                signals.iloc[:4] = 0
                
                return signals
        
        self.trend_strategy = TrendStrategy()
        
        # Create a combined strategy
        self.combined_strategy = CombinedStrategy(
            strategies=[self.ma_strategy, self.trend_strategy],
            weights=[0.7, 0.3]
        )
        
        # Sample data
        dates = pd.date_range(start='2020-01-01', periods=100)
        prices = np.zeros(100)
        # Uptrend, then downtrend, then uptrend again
        prices[0:33] = np.linspace(100, 130, 33)
        prices[33:66] = np.linspace(130, 110, 33)
        prices[66:] = np.linspace(110, 140, 34)
        # Add some noise
        prices += np.random.normal(0, 2, 100)
        
        self.data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        self.data.set_index('date', inplace=True)
    
    def test_combined_strategy_initialization(self):
        # Verify the strategy initializes correctly
        self.assertEqual(len(self.combined_strategy.strategies), 2)
        self.assertEqual(len(self.combined_strategy.weights), 2)
        self.assertEqual(sum(self.combined_strategy.weights), 1.0)
    
    def test_combined_strategy_generate_signals(self):
        # Generate signals for individual strategies
        ma_signals = self.ma_strategy.generate_signals(self.data)
        trend_signals = self.trend_strategy.generate_signals(self.data)
        
        # Generate signals for combined strategy
        combined_signals = self.combined_strategy.generate_signals(self.data)
        
        # Verify combined_signals is a pandas Series
        self.assertIsInstance(combined_signals, pd.Series)
        
        # Verify combined_signals has the correct length
        self.assertEqual(len(combined_signals), len(self.data))
        
        # Verify signals are properly weighted when both strategies agree
        # Find indices where both strategies have the same non-zero signal
        both_long = (ma_signals == 1) & (trend_signals == 1)
        both_short = (ma_signals == -1) & (trend_signals == -1)
        
        # When both are long, combined should be long
        self.assertTrue((combined_signals[both_long] > 0).all())
        
        # When both are short, combined should be short
        self.assertTrue((combined_signals[both_short] < 0).all())
    
    def test_combined_strategy_with_equal_weights(self):
        # Create a combined strategy with equal weights
        equal_weight_strategy = CombinedStrategy(
            strategies=[self.ma_strategy, self.trend_strategy],
            weights=[0.5, 0.5]
        )
        
        # Generate signals
        signals = equal_weight_strategy.generate_signals(self.data)
        
        # Calculate returns
        returns = equal_weight_strategy.calculate_returns(self.data, signals)
        
        # Verify returns has the correct length
        self.assertEqual(len(returns), len(self.data) - 1)


if __name__ == '__main__':
    unittest.main()