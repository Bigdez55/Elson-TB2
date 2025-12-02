#!/usr/bin/env python3
"""
Unit tests for the adaptive parameter optimization component.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from Elson.trading_engine.adaptive_parameters import (
    AdaptiveParameterOptimizer,
    MarketCondition
)
from Elson.trading_engine.engine.circuit_breaker import CircuitBreakerStatus


class TestAdaptiveParameters(unittest.TestCase):
    """Test cases for adaptive parameter optimization."""

    def setUp(self):
        """Set up test environment."""
        self.optimizer = AdaptiveParameterOptimizer()
        
        # Create test data
        dates = [datetime.now() - timedelta(days=i) for i in range(100)]
        dates.reverse()  # Chronological order
        
        # Create synthetic price data with different volatility regimes
        np.random.seed(42)  # For reproducibility
        prices = []
        price = 100.0
        volatility = 0.01  # Start with low volatility
        
        for i in range(100):
            # Change volatility at different points
            if i == 25:
                volatility = 0.015  # Normal volatility
            elif i == 50:
                volatility = 0.025  # High volatility
            elif i == 75:
                volatility = 0.04   # Extreme volatility
                
            price *= (1 + np.random.normal(0, volatility))
            prices.append(price)
            
        # Create DataFrame
        self.data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, len(prices))),
            'high': prices * (1 + abs(np.random.normal(0, 0.002, len(prices)))),
            'low': prices * (1 - abs(np.random.normal(0, 0.002, len(prices)))),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, len(prices))
        }, index=dates)
        
        # Add returns
        self.data['returns'] = self.data['close'].pct_change()
        
        # Add volatility (annualized)
        self.data['volatility'] = self.data['returns'].rolling(window=20).std() * np.sqrt(252)

    def test_initialization(self):
        """Test initialization of adaptive parameter optimizer."""
        # Check default parameters
        self.assertIsInstance(self.optimizer.parameters, dict)
        self.assertIn('adaptation_frequency', self.optimizer.parameters)
        self.assertIn('stability_factor', self.optimizer.parameters)
        
        # Verify updated parameters
        self.assertEqual(self.optimizer.parameters['adaptation_frequency'], 24)  # Updated from 12
        self.assertEqual(self.optimizer.parameters['stability_factor'], 0.05)  # Added for smooth transitions
        
        # Check regime-specific parameters
        self.assertIn('regime_parameters', self.optimizer.parameters)
        regime_params = self.optimizer.parameters['regime_parameters']
        
        # Check high volatility parameters
        high_vol_params = regime_params.get('high_volatility', {})
        self.assertIn('lookback_periods', high_vol_params)
        self.assertIn('prediction_horizon', high_vol_params)
        self.assertIn('confidence_threshold', high_vol_params)
        self.assertIn('position_sizing', high_vol_params)
        
        # Verify updated high volatility parameters
        self.assertEqual(high_vol_params['lookback_periods'], 8)  # Updated from 15
        self.assertEqual(high_vol_params['prediction_horizon'], 1)  # Updated from 2
        self.assertEqual(high_vol_params['confidence_threshold'], 0.82)  # Updated from 0.65
        self.assertEqual(high_vol_params['position_sizing'], 0.25)  # Updated from 0.35
        
        # Check extreme volatility parameters
        extreme_vol_params = regime_params.get('extreme_volatility', {})
        
        # Verify updated extreme volatility parameters
        self.assertEqual(extreme_vol_params['lookback_periods'], 5)  # Updated from 10
        self.assertEqual(extreme_vol_params['prediction_horizon'], 1)
        self.assertEqual(extreme_vol_params['confidence_threshold'], 0.90)  # Updated from 0.75
        self.assertEqual(extreme_vol_params['position_sizing'], 0.10)  # Updated from 0.15

    def test_detect_market_condition(self):
        """Test detection of market conditions."""
        # Get the latest data
        latest_data = self.data.iloc[-20:]
        
        # Test detection with different volatility levels
        # Low volatility
        with patch.object(self.optimizer, '_detect_volatility_regime') as mock_detect_vol:
            mock_detect_vol.return_value = ('low_volatility', 10.0)
            
            condition = self.optimizer._detect_market_condition(latest_data)
            self.assertIsInstance(condition, dict)
            self.assertIn('volatility_regime', condition)
            self.assertEqual(condition['volatility_regime'], 'low_volatility')
        
        # High volatility
        with patch.object(self.optimizer, '_detect_volatility_regime') as mock_detect_vol:
            mock_detect_vol.return_value = ('high_volatility', 25.0)
            
            condition = self.optimizer._detect_market_condition(latest_data)
            self.assertEqual(condition['volatility_regime'], 'high_volatility')
        
        # Extreme volatility
        with patch.object(self.optimizer, '_detect_volatility_regime') as mock_detect_vol:
            mock_detect_vol.return_value = ('extreme_volatility', 40.0)
            
            condition = self.optimizer._detect_market_condition(latest_data)
            self.assertEqual(condition['volatility_regime'], 'extreme_volatility')
        
        # Check market direction detection
        # Add trend indicators
        latest_data = latest_data.copy()
        latest_data['sma_short'] = latest_data['close'].rolling(window=5).mean()
        latest_data['sma_long'] = latest_data['close'].rolling(window=20).mean()
        
        # Test bullish market
        latest_data.loc[:, 'sma_short'] = latest_data['sma_long'] * 1.05  # Short above long
        with patch.object(self.optimizer, '_detect_volatility_regime') as mock_detect_vol:
            mock_detect_vol.return_value = ('normal_volatility', 18.0)
            
            condition = self.optimizer._detect_market_condition(latest_data)
            self.assertIn('market_condition', condition)
            self.assertEqual(condition['market_condition'], MarketCondition.BULL)
        
        # Test bearish market
        latest_data.loc[:, 'sma_short'] = latest_data['sma_long'] * 0.95  # Short below long
        with patch.object(self.optimizer, '_detect_volatility_regime') as mock_detect_vol:
            mock_detect_vol.return_value = ('normal_volatility', 18.0)
            
            condition = self.optimizer._detect_market_condition(latest_data)
            self.assertEqual(condition['market_condition'], MarketCondition.BEAR)

    def test_get_optimized_parameters(self):
        """Test getting optimized parameters for different market conditions."""
        # Mock circuit breaker status
        cb_status = CircuitBreakerStatus.CLOSED
        
        # Test with low volatility
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'low_volatility',
                'market_condition': MarketCondition.BULL,
                'volatility_value': 10.0
            }
            
            params = self.optimizer.get_optimized_parameters(self.data, cb_status)
            
            # Verify parameters
            self.assertIsInstance(params, dict)
            self.assertIn('lookback_periods', params)
            self.assertIn('prediction_horizon', params)
            self.assertIn('confidence_threshold', params)
            self.assertIn('position_sizing', params)
            self.assertIn('regime_info', params)
            
            # Check that low volatility parameters were used
            regime_params = self.optimizer.parameters['regime_parameters']['low_volatility']
            self.assertEqual(params['lookback_periods'], regime_params['lookback_periods'])
            self.assertEqual(params['prediction_horizon'], regime_params['prediction_horizon'])
            self.assertEqual(params['confidence_threshold'], regime_params['confidence_threshold'])
            self.assertEqual(params['position_sizing'], regime_params['position_sizing'])
        
        # Test with high volatility
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'high_volatility',
                'market_condition': MarketCondition.BEAR,
                'volatility_value': 25.0
            }
            
            params = self.optimizer.get_optimized_parameters(self.data, cb_status)
            
            # Check that high volatility parameters were used
            regime_params = self.optimizer.parameters['regime_parameters']['high_volatility']
            self.assertEqual(params['lookback_periods'], regime_params['lookback_periods'])
            self.assertEqual(params['prediction_horizon'], regime_params['prediction_horizon'])
            self.assertEqual(params['confidence_threshold'], regime_params['confidence_threshold'])
            self.assertEqual(params['position_sizing'], regime_params['position_sizing'])
        
        # Test with extreme volatility
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'extreme_volatility',
                'market_condition': MarketCondition.BEAR_VOLATILE,
                'volatility_value': 40.0
            }
            
            params = self.optimizer.get_optimized_parameters(self.data, cb_status)
            
            # Check that extreme volatility parameters were used
            regime_params = self.optimizer.parameters['regime_parameters']['extreme_volatility']
            self.assertEqual(params['lookback_periods'], regime_params['lookback_periods'])
            self.assertEqual(params['prediction_horizon'], regime_params['prediction_horizon'])
            self.assertEqual(params['confidence_threshold'], regime_params['confidence_threshold'])
            self.assertEqual(params['position_sizing'], regime_params['position_sizing'])

    def test_circuit_breaker_override(self):
        """Test parameter adjustment based on circuit breaker status."""
        # Test with circuit breaker in CAUTIOUS state
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'normal_volatility',
                'market_condition': MarketCondition.BULL,
                'volatility_value': 18.0
            }
            
            # Normal parameters without circuit breaker
            params_normal = self.optimizer.get_optimized_parameters(self.data, CircuitBreakerStatus.CLOSED)
            
            # Parameters with circuit breaker CAUTIOUS
            params_cautious = self.optimizer.get_optimized_parameters(self.data, CircuitBreakerStatus.CAUTIOUS)
            
            # Verify that position sizing is reduced
            self.assertLess(params_cautious['position_sizing'], params_normal['position_sizing'])
            
            # Verify that confidence threshold is increased
            self.assertGreater(params_cautious['confidence_threshold'], params_normal['confidence_threshold'])
        
        # Test with circuit breaker in RESTRICTED state
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'normal_volatility',
                'market_condition': MarketCondition.BULL,
                'volatility_value': 18.0
            }
            
            # Parameters with circuit breaker RESTRICTED
            params_restricted = self.optimizer.get_optimized_parameters(self.data, CircuitBreakerStatus.RESTRICTED)
            
            # Verify that position sizing is further reduced
            self.assertLess(params_restricted['position_sizing'], params_cautious['position_sizing'])
            
            # Verify that confidence threshold is further increased
            self.assertGreater(params_restricted['confidence_threshold'], params_cautious['confidence_threshold'])
        
        # Test with circuit breaker in OPEN state (should not trade)
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'normal_volatility',
                'market_condition': MarketCondition.BULL,
                'volatility_value': 18.0
            }
            
            # Parameters with circuit breaker OPEN
            params_open = self.optimizer.get_optimized_parameters(self.data, CircuitBreakerStatus.OPEN)
            
            # Verify that position sizing is zero
            self.assertEqual(params_open['position_sizing'], 0.0)

    def test_update_performance_history(self):
        """Test updating and using performance history for optimization."""
        # Mock performance data
        performance_data = {
            'win_rate': 0.65,
            'return': 0.05,
            'drawdown': 0.02,
            'sharpe': 1.5
        }
        
        # Update performance history for a specific regime
        self.optimizer.update_performance_history('low_volatility', MarketCondition.BULL, performance_data)
        
        # Verify that history was updated
        self.assertIn('low_volatility', self.optimizer.performance_history)
        self.assertIn(MarketCondition.BULL, self.optimizer.performance_history['low_volatility'])
        
        # Verify that data was stored correctly
        stored_data = self.optimizer.performance_history['low_volatility'][MarketCondition.BULL]
        self.assertEqual(stored_data['win_rate'], 0.65)
        self.assertEqual(stored_data['return'], 0.05)
        
        # Update history for a different regime
        self.optimizer.update_performance_history('high_volatility', MarketCondition.BEAR, {
            'win_rate': 0.45,
            'return': -0.03,
            'drawdown': 0.05,
            'sharpe': 0.8
        })
        
        # Verify multiple regimes are tracked
        self.assertIn('high_volatility', self.optimizer.performance_history)
        
        # Test optimization with performance history
        with patch.object(self.optimizer, '_detect_market_condition') as mock_detect:
            mock_detect.return_value = {
                'volatility_regime': 'low_volatility',
                'market_condition': MarketCondition.BULL,
                'volatility_value': 10.0
            }
            
            # Get optimized parameters
            params = self.optimizer.get_optimized_parameters(self.data, CircuitBreakerStatus.CLOSED)
            
            # Performance history should be included in the regime info
            self.assertIn('performance_history', params['regime_info'])


if __name__ == '__main__':
    unittest.main()