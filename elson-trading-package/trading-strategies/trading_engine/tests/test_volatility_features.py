#!/usr/bin/env python3
"""
Unit tests for the volatility feature engineering component.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from Elson.trading_engine.feature_engineering.volatility_features import (
    VolatilityFeatureEngineer,
    create_volatility_adjusted_features,
    get_current_volatility_regime,
    get_volatility_recommendations
)


class TestVolatilityFeatures(unittest.TestCase):
    """Test cases for volatility feature engineering."""

    def setUp(self):
        """Set up test data."""
        # Create a simple synthetic price dataset
        dates = [datetime.now() - timedelta(days=i) for i in range(100)]
        dates.reverse()  # Chronological order
        
        # Create a price series with increasing volatility
        np.random.seed(42)  # For reproducibility
        prices = []
        price = 100.0
        
        # Low volatility region
        for _ in range(25):
            price *= (1 + np.random.normal(0, 0.005))  # 0.5% daily volatility
            prices.append(price)
            
        # Normal volatility region
        for _ in range(25):
            price *= (1 + np.random.normal(0, 0.01))  # 1% daily volatility
            prices.append(price)
            
        # High volatility region
        for _ in range(25):
            price *= (1 + np.random.normal(0, 0.02))  # 2% daily volatility
            prices.append(price)
            
        # Extreme volatility region
        for _ in range(25):
            price *= (1 + np.random.normal(0, 0.03))  # 3% daily volatility
            prices.append(price)
        
        # Create DataFrame
        self.data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, len(prices))),
            'high': prices * (1 + abs(np.random.normal(0, 0.002, len(prices)))),
            'low': prices * (1 - abs(np.random.normal(0, 0.002, len(prices)))),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, len(prices))
        }, index=dates)
        
        # Create engineer instance
        self.engineer = VolatilityFeatureEngineer()

    def test_calculate_returns(self):
        """Test calculation of return series."""
        returns = self.engineer.calculate_returns(self.data['close'])
        
        # Check that returns are calculated correctly
        self.assertEqual(len(returns), len(self.data))
        self.assertTrue(np.isnan(returns.iloc[0]))  # First value should be NaN
        
        # Check log returns calculation
        manual_log_returns = np.log(self.data['close'] / self.data['close'].shift(1))
        pd.testing.assert_series_equal(returns.iloc[1:], manual_log_returns.iloc[1:], check_less_precise=True)
        
        # Test with simple returns
        self.engineer.use_log_returns = False
        simple_returns = self.engineer.calculate_returns(self.data['close'])
        
        manual_simple_returns = self.data['close'].pct_change()
        pd.testing.assert_series_equal(simple_returns.iloc[1:], manual_simple_returns.iloc[1:], check_less_precise=True)

    def test_calculate_volatility(self):
        """Test volatility calculation methods."""
        returns = self.engineer.calculate_returns(self.data['close'])
        
        # Test standard volatility calculation
        volatility = self.engineer.calculate_volatility(returns, window=20, method='standard')
        self.assertEqual(len(volatility), len(returns))
        self.assertTrue(np.isnan(volatility.iloc[0]))  # First value should be NaN
        
        # Check annualization
        daily_vol = self.engineer.calculate_volatility(returns, window=20, method='standard', annualize=False)
        annualized_manual = daily_vol * np.sqrt(252)
        pd.testing.assert_series_equal(volatility, annualized_manual, check_less_precise=True)
        
        # Test EWMA volatility
        ewma_vol = self.engineer.calculate_volatility(returns, window=20, method='ewma')
        self.assertEqual(len(ewma_vol), len(returns))
        
        # Test with invalid method
        fallback_vol = self.engineer.calculate_volatility(returns, window=20, method='invalid_method')
        # Should fall back to standard
        pd.testing.assert_series_equal(fallback_vol, volatility, check_exact=False)

    def test_calculate_garch_volatility_proxy(self):
        """Test GARCH-like volatility proxy implementation."""
        returns = self.engineer.calculate_returns(self.data['close'])
        
        garch_vol = self.engineer.calculate_garch_volatility_proxy(returns, window=20)
        
        # Basic validation
        self.assertEqual(len(garch_vol), len(returns))
        self.assertTrue(np.isnan(garch_vol.iloc[0]))  # First value should be NaN
        self.assertTrue(all(garch_vol.iloc[1:] >= 0))  # All volatilities should be non-negative

    def test_calculate_jump_robust_volatility(self):
        """Test jump-robust volatility calculation."""
        returns = self.engineer.calculate_returns(self.data['close'])
        
        jump_vol = self.engineer.calculate_jump_robust_volatility(returns, window=20)
        
        # Basic validation
        self.assertEqual(len(jump_vol), len(returns))
        self.assertTrue(np.isnan(jump_vol.iloc[0]))  # First value should be NaN
        self.assertTrue(all(jump_vol.iloc[20:] >= 0))  # All volatilities from window onwards should be non-negative

    def test_engineer_volatility_features(self):
        """Test full feature engineering pipeline."""
        # Process the data
        result = self.engineer.engineer_volatility_features(self.data)
        
        # Basic validation
        self.assertEqual(len(result), len(self.data))
        
        # Check that all expected columns are present
        expected_columns = [
            'volatility_short', 'volatility_medium', 'volatility_long',
            'volatility_short_ewma', 'volatility_short_jump_robust',
            'volatility_short_garch', 'volatility_short_blended',
            'volatility_regime', 'volatility_ratio_short_long',
            'volatility_zscore', 'returns_vol_adjusted'
        ]
        
        for col in expected_columns:
            self.assertIn(col, result.columns)
        
        # Verify regime columns
        regime_columns = ['regime_low', 'regime_normal', 'regime_high', 'regime_extreme']
        for col in regime_columns:
            self.assertIn(col, result.columns)
            self.assertTrue(set(result[col].unique()).issubset({0, 1}))  # Should be binary indicators
            
        # Check that the volatility regimes are classified correctly
        self.assertTrue('volatility_regime' in result.columns)
        regimes = set(result['volatility_regime'].unique())
        expected_regimes = {'low', 'normal', 'high', 'extreme', 'unknown'}
        self.assertTrue(regimes.issubset(expected_regimes))
        
        # Verify that the metrics are stored
        self.assertTrue(hasattr(self.engineer, 'rolling_metrics'))
        self.assertTrue(hasattr(self.engineer, 'relative_metrics'))
        self.assertTrue(hasattr(self.engineer, 'market_regime_features'))

    def test_convenience_functions(self):
        """Test the module's convenience functions."""
        # Test create_volatility_adjusted_features
        adjusted = create_volatility_adjusted_features(self.data)
        self.assertEqual(len(adjusted), len(self.data))
        self.assertIn('volatility_short', adjusted.columns)
        
        # Test get_current_volatility_regime
        regime = get_current_volatility_regime(self.data)
        self.assertIn(regime, ['low', 'normal', 'high', 'extreme', 'unknown'])
        
        # Test get_volatility_recommendations
        recommendations = get_volatility_recommendations(self.data)
        self.assertIsInstance(recommendations, dict)
        self.assertIn('confidence_threshold', recommendations)
        self.assertIn('prediction_horizon', recommendations)
        self.assertIn('lookback_periods', recommendations)
        self.assertIn('position_sizing', recommendations)

    def test_get_regime_recommendations(self):
        """Test getting regime-specific recommendations."""
        # Process the data first to populate internal state
        self.engineer.engineer_volatility_features(self.data)
        
        # Test recommendations for each regime
        for regime in ['low', 'normal', 'high', 'extreme']:
            recommendations = self.engineer.get_regime_recommendations(regime)
            
            # Check recommendation structure
            self.assertIsInstance(recommendations, dict)
            self.assertIn('confidence_threshold', recommendations)
            self.assertIn('prediction_horizon', recommendations)
            self.assertIn('lookback_periods', recommendations)
            self.assertIn('circuit_breaker', recommendations)
            self.assertIn('position_sizing', recommendations)
            
            # Verify model weights
            self.assertIn('model_weights', recommendations)
            weights = recommendations['model_weights']
            self.assertIn('random_forest', weights)
            self.assertIn('gradient_boosting', weights)
            self.assertIn('neural_network', weights)
            self.assertIn('quantum_kernel', weights)
            self.assertIn('quantum_variational', weights)
            
        # Test with unknown regime
        default_rec = self.engineer.get_regime_recommendations('unknown')
        self.assertIsInstance(default_rec, dict)
        self.assertIn('confidence_threshold', default_rec)


if __name__ == '__main__':
    unittest.main()