"""
Integration tests for the adaptive parameters and enhanced circuit breaker modules.
"""

import unittest
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_adaptive_circuit_breaker_integration")

# Add the project path to the Python path
sys.path.append('/workspaces/Elson')

# Import components to test
from Elson.trading_engine.adaptive_parameters import (
    AdaptiveParameterOptimizer, 
    MarketCondition
)
from Elson.trading_engine.volatility_regime.volatility_detector import (
    VolatilityDetector,
    VolatilityRegime
)
from Elson.trading_engine.engine.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerType, 
    CircuitBreakerStatus, 
    VolatilityLevel
)


class TestAdaptiveCircuitBreakerIntegration(unittest.TestCase):
    """Integration tests for adaptive parameters and circuit breaker modules."""
    
    def setUp(self):
        """Set up test environment."""
        # Initialize the optimizer
        self.optimizer = AdaptiveParameterOptimizer(
            history_window=30,
            adaptation_speed=0.5,
            enable_online_learning=True
        )
        
        # Initialize the volatility detector
        self.volatility_detector = VolatilityDetector()
        
        # Initialize the circuit breaker
        self.circuit_breaker = CircuitBreaker()
        
        # Generate test market data for different volatility regimes
        self.low_volatility_data = self.generate_test_data("low")
        self.normal_volatility_data = self.generate_test_data("normal")
        self.high_volatility_data = self.generate_test_data("high")
        self.extreme_volatility_data = self.generate_test_data("extreme")
    
    def generate_test_data(self, volatility_type="normal", periods=100):
        """Generate synthetic market data with specified volatility."""
        # Set volatility based on type
        if volatility_type == "low":
            volatility = 0.005  # ~8% annualized
        elif volatility_type == "normal":
            volatility = 0.015  # ~24% annualized
        elif volatility_type == "high":
            volatility = 0.025  # ~40% annualized
        elif volatility_type == "extreme":
            volatility = 0.045  # ~71% annualized (significantly above the 40% threshold)
        else:
            volatility = 0.015  # default
        
        # Generate random returns
        np.random.seed(42)  # For reproducible tests
        returns = np.random.normal(0, volatility, periods)
        
        # Generate price series
        start_price = 100
        prices = start_price * np.cumprod(1 + returns)
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periods)
        dates = pd.date_range(start=start_date, end=end_date, periods=periods)
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.normal(0, 0.001, periods)),
            'high': prices * (1 + abs(np.random.normal(0, 0.002, periods))),
            'low': prices * (1 - abs(np.random.normal(0, 0.002, periods))),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, periods)
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def test_end_to_end_integration(self):
        """Test the entire integration flow from data to parameters to circuit breaker."""
        # For each volatility regime, test the integration flow
        
        test_regimes = [
            ("Low", self.low_volatility_data, VolatilityRegime.LOW, VolatilityLevel.LOW),
            ("Normal", self.normal_volatility_data, VolatilityRegime.NORMAL, VolatilityLevel.NORMAL),
            ("High", self.high_volatility_data, VolatilityRegime.HIGH, VolatilityLevel.HIGH),
            ("Extreme", self.extreme_volatility_data, VolatilityRegime.EXTREME, VolatilityLevel.EXTREME)
        ]
        
        for name, data, expected_regime, expected_level in test_regimes:
            logger.info(f"Testing {name} volatility regime integration")
            
            # Step 1: Detect volatility regime using volatility detector
            detected_regime, volatility_value = self.volatility_detector.detect_regime(data)
            self.assertEqual(detected_regime, expected_regime)
            
            # Step 2: Get optimized parameters from adaptive parameter optimizer
            optimized_params = self.optimizer.get_optimized_parameters(data)
            
            # Verify optimized parameters match the expected regime
            self.assertEqual(optimized_params['regime_info']['volatility_regime'], expected_regime.name)
            
            # Step 3: Process volatility with circuit breaker
            vol_level = expected_level  # Convert regime enum to circuit breaker level enum
            symbol = f"TEST_{name.upper()}"
            
            tripped, status, position_size = self.circuit_breaker.process_volatility(
                vol_level,
                volatility_value,
                symbol=symbol
            )
            
            # Verify circuit breaker status based on volatility level
            if expected_level == VolatilityLevel.EXTREME:
                self.assertTrue(tripped)
                self.assertEqual(status, CircuitBreakerStatus.OPEN)
                self.assertEqual(position_size, 0.25)
            elif expected_level == VolatilityLevel.HIGH:
                self.assertTrue(tripped)
                self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
                self.assertEqual(position_size, 0.5)
            elif expected_level == VolatilityLevel.NORMAL:
                self.assertTrue(tripped)
                self.assertEqual(status, CircuitBreakerStatus.CAUTIOUS)
                self.assertEqual(position_size, 1.0)
            else:  # LOW
                self.assertFalse(tripped)
                self.assertEqual(status, CircuitBreakerStatus.CLOSED)
                self.assertEqual(position_size, 1.0)
            
            # Step 4: Check if circuit breaker affects trading
            allowed, cb_status = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, symbol)
            
            # Verify trading allowed status
            if expected_level == VolatilityLevel.EXTREME:
                self.assertFalse(allowed)
            else:
                self.assertTrue(allowed)
            
            # Step 5: Get position sizing recommendation that considers circuit breaker
            position_sizing = self.optimizer.get_recommended_position_sizing(
                detected_regime,
                MarketCondition.BULL_TRENDING,
                cb_status
            )
            
            logger.info(f"{name} volatility: Regime={detected_regime.name}, Value={volatility_value:.2f}%, "
                       f"Circuit Breaker={status.name}, Position Sizing={position_sizing:.2f}")
            
            # Verify position sizing aligns with circuit breaker status
            if cb_status == CircuitBreakerStatus.OPEN:
                self.assertEqual(position_sizing, 0.0)
            elif cb_status == CircuitBreakerStatus.RESTRICTED:
                self.assertEqual(position_sizing, 0.5)
            elif cb_status == CircuitBreakerStatus.CAUTIOUS:
                self.assertEqual(position_sizing, 0.75)
    
    def test_volatility_regime_mapping(self):
        """Test that volatility regimes and circuit breaker levels map correctly."""
        # Create mapping of regimes to levels
        regime_to_level = {
            VolatilityRegime.LOW: VolatilityLevel.LOW,
            VolatilityRegime.NORMAL: VolatilityLevel.NORMAL,
            VolatilityRegime.HIGH: VolatilityLevel.HIGH,
            VolatilityRegime.EXTREME: VolatilityLevel.EXTREME
        }
        
        # Test each regime
        for regime_data, regime_name in [
            (self.low_volatility_data, VolatilityRegime.LOW),
            (self.normal_volatility_data, VolatilityRegime.NORMAL),
            (self.high_volatility_data, VolatilityRegime.HIGH),
            (self.extreme_volatility_data, VolatilityRegime.EXTREME)
        ]:
            # Detect regime
            detected_regime, _ = self.volatility_detector.detect_regime(regime_data)
            self.assertEqual(detected_regime, regime_name)
            
            # Map to level
            level = regime_to_level[detected_regime]
            
            # Verify level name matches regime name
            self.assertEqual(level.name, detected_regime.name)
    
    def test_parameter_propagation(self):
        """Test that parameters propagate correctly from optimizer to circuit breaker."""
        # Use extreme volatility data as a clear test case
        data = self.extreme_volatility_data
        
        # Step 1: Get optimized parameters
        optimized_params = self.optimizer.get_optimized_parameters(data)
        
        # Step 2: Extract confidence threshold
        confidence_threshold = optimized_params['confidence_threshold']
        
        # Verify confidence threshold is high for extreme volatility
        self.assertGreaterEqual(confidence_threshold, 0.7)
        
        # Step 3: Use the circuit breaker with these parameters
        regime, _, volatility_value = self.optimizer.detect_market_condition(data)
        level = VolatilityLevel.EXTREME if regime == VolatilityRegime.EXTREME else VolatilityLevel.NORMAL
        
        # Process volatility
        symbol = "TEST_PARAMETER_PROPAGATION"
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            level,
            volatility_value,
            symbol=symbol
        )
        
        # Verify circuit breaker was tripped
        self.assertTrue(tripped)
        
        # Step 4: Check what position sizing adaptations would be recommended
        allowed, cb_status = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, symbol)
        
        # Get position sizing recommendation
        position_sizing = self.optimizer.get_recommended_position_sizing(
            regime,
            MarketCondition.BEAR_VOLATILE,
            cb_status
        )
        
        # Verify position sizing is very conservative for extreme volatile bear market
        self.assertLessEqual(position_sizing, 0.25)
        
        logger.info(f"Parameter propagation test: confidence_threshold={confidence_threshold:.2f}, "
                  f"circuit_breaker_status={cb_status.name}, position_sizing={position_sizing:.2f}")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove any files created during testing
        if os.path.exists("performance_history.json"):
            os.remove("performance_history.json")
        if os.path.exists("circuit_breaker_status.json"):
            os.remove("circuit_breaker_status.json")


if __name__ == "__main__":
    unittest.main()