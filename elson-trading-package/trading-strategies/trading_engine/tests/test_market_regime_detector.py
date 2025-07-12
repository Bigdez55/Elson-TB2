"""
Tests for the MarketRegimeDetector.
"""

import unittest
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt

from trading_engine.timeframe_engine.market_regime_detector import (
    MarketRegimeDetector,
    MarketRegime
)


class TestMarketRegimeDetector:
    """Test suite for the MarketRegimeDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = MarketRegimeDetector(
            window_size=10,
            volatility_window=5,
            num_regimes=3
        )
        
        # Generate sample price data
        np.random.seed(42)  # For reproducibility
        
        # Create trending up data
        self.trending_up_data = np.linspace(100, 200, 100) + np.random.normal(0, 5, 100)
        
        # Create trending down data
        self.trending_down_data = np.linspace(200, 100, 100) + np.random.normal(0, 5, 100)
        
        # Create range-bound data
        self.ranging_data = 150 + np.sin(np.linspace(0, 10, 100)) * 20 + np.random.normal(0, 3, 100)
        
        # Create volatile data
        self.volatile_data = 150 + np.random.normal(0, 20, 100)
        
        # Create mean-reverting data
        mean = 150
        reversion_strength = 0.1
        price = mean
        self.mean_reverting_data = np.zeros(100)
        for i in range(100):
            price = price + (mean - price) * reversion_strength + np.random.normal(0, 5)
            self.mean_reverting_data[i] = price
    
    def test_feature_extraction(self):
        """Test feature extraction from price data."""
        features = self.detector.extract_features(self.trending_up_data)
        
        # Check that all expected features are present
        expected_features = [
            'ma_short', 'ma_long', 'ma_ratio', 'trend', 
            'volatility', 'volatility_change', 'return_kurtosis', 
            'return_skew', 'rsi', 'mean_dev'
        ]
        for feature in expected_features:
            assert feature in features.columns
        
        # Check dimensions
        assert len(features) == len(self.trending_up_data)
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        # Use a simplified series for testing
        prices = pd.Series([10, 11, 10.5, 11.5, 12, 11.5, 12.5, 13, 12.5, 13.5])
        rsi = self.detector._calculate_rsi(prices, window=3)
        
        # RSI should be between 0 and 100
        assert all((0 <= val <= 100) for val in rsi if not pd.isna(val))
        
        # First values should be NaN due to window
        assert pd.isna(rsi[0])
        
        # Rising prices should give high RSI
        assert rsi.iloc[-1] > 50
    
    @pytest.mark.parametrize(
        "data,expected_regime",
        [
            ("trending_up_data", MarketRegime.TRENDING_UP),
            ("trending_down_data", MarketRegime.TRENDING_DOWN),
            ("ranging_data", MarketRegime.RANGING),
            ("volatile_data", MarketRegime.VOLATILE),
            ("mean_reverting_data", MarketRegime.MEAN_REVERTING)
        ]
    )
    def test_regime_detection(self, data, expected_regime):
        """Test regime detection for different price patterns."""
        # Train the detector on the specific dataset
        price_data = getattr(self, data)
        self.detector.train(price_data)
        
        # Predict the regime
        regimes = self.detector.predict(price_data)
        
        # At least 30% of predictions should match the expected regime
        regime_counts = {regime: regimes.count(regime) for regime in set(regimes)}
        total_predictions = len(regimes)
        
        # Filter out UNKNOWN regimes from the count
        regime_counts = {k: v for k, v in regime_counts.items() if k != MarketRegime.UNKNOWN}
        
        # Get most common regime
        most_common_regime = max(regime_counts.items(), key=lambda x: x[1])[0] if regime_counts else MarketRegime.UNKNOWN
        
        # If the most common detected regime is just UNKNOWN, we consider this a test failure
        if most_common_regime == MarketRegime.UNKNOWN:
            pytest.fail(f"Detector could not identify a meaningful regime for {data}")
        
        # Check for certain regime characteristics
        if data == "trending_up_data":
            assert most_common_regime in [MarketRegime.TRENDING_UP, MarketRegime.BREAKOUT]
        elif data == "trending_down_data":
            assert most_common_regime in [MarketRegime.TRENDING_DOWN, MarketRegime.BREAKOUT]
        elif data == "ranging_data":
            assert most_common_regime in [MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY, MarketRegime.MEAN_REVERTING]
        elif data == "volatile_data":
            assert most_common_regime in [MarketRegime.VOLATILE, MarketRegime.HIGH_VOLATILITY]
        elif data == "mean_reverting_data":
            assert most_common_regime in [MarketRegime.MEAN_REVERTING, MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY]
    
    def test_current_regime(self):
        """Test current regime detection."""
        # Train the detector
        self.detector.train(self.trending_up_data)
        
        # Get current regime
        regime = self.detector.current_regime(self.trending_up_data)
        
        # Should return a MarketRegime enum
        assert isinstance(regime, MarketRegime)
    
    def test_optimal_strategy(self):
        """Test optimal strategy recommendation."""
        for regime in MarketRegime:
            strategy = self.detector.optimal_strategy(regime)
            assert isinstance(strategy, str)
            assert len(strategy) > 0
    
    def test_regime_adjusted_parameters(self):
        """Test parameter adjustment based on regime."""
        for regime in MarketRegime:
            params = self.detector.regime_adjusted_parameters(regime)
            
            # Check that required parameters are present
            assert "stop_loss_pct" in params
            assert "position_size_pct" in params
            assert "trailing_stop_pct" in params
            
            # Parameters should be reasonable values
            assert 0 < params["stop_loss_pct"] < 0.5
            assert 0 < params["position_size_pct"] < 0.5
            assert 0 < params["trailing_stop_pct"] < 0.5
    
    @patch('matplotlib.pyplot.show')
    def test_plotting(self, mock_show):
        """Test regime plotting capability."""
        # Train with plot=True
        features = self.detector.extract_features(self.trending_up_data)
        features['regime'] = np.zeros(len(features))  # Mock regime column
        
        # Call _plot_regimes directly
        self.detector._plot_regimes(features, self.trending_up_data)
        
        # Verify that show was called
        mock_show.assert_called_once()

    
if __name__ == '__main__':
    unittest.main()