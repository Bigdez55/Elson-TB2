#!/usr/bin/env python3
"""
Unit tests for the enhanced circuit breaker component.
"""

import unittest
from unittest.mock import patch, MagicMock

from Elson.trading_engine.engine.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerStatus,
    CircuitBreakerType
)
from Elson.trading_engine.volatility_regime.volatility_detector import VolatilityRegime


class TestCircuitBreaker(unittest.TestCase):
    """Test cases for the enhanced circuit breaker mechanism."""

    def setUp(self):
        """Set up test environment."""
        self.circuit_breaker = CircuitBreaker()
        
        # Configure test parameters
        self.test_symbol = "TEST"
        
        # Reset the circuit breaker's internal state
        self.circuit_breaker.circuit_status = {}
        self.circuit_breaker.volatility_history = {}
        self.circuit_breaker.cooldown_timers = {}

    def test_initialization(self):
        """Test circuit breaker initialization."""
        # Check default parameters
        self.assertIn('hysteresis_samples', self.circuit_breaker.config)
        self.assertIn('hysteresis_threshold', self.circuit_breaker.config)
        
        # Verify hysteresis settings from updated implementation
        self.assertEqual(self.circuit_breaker.config['hysteresis_samples'], 15)  # Updated from 10
        self.assertEqual(self.circuit_breaker.config['hysteresis_threshold'], 0.8)  # Updated from 0.75
        
        # Check volatility thresholds
        self.assertIn('volatility_thresholds', self.circuit_breaker.config)
        volatility_thresholds = self.circuit_breaker.config['volatility_thresholds']
        
        # Verify updated thresholds
        self.assertEqual(volatility_thresholds['high_volatility'], 20.0)  # Updated from 22.0
        self.assertEqual(volatility_thresholds['extreme_volatility'], 35.0)  # Updated from 38.0
        
        # Check position sizing
        self.assertIn('position_sizing', self.circuit_breaker.config)
        position_sizing = self.circuit_breaker.config['position_sizing']
        
        # Verify updated position sizing values
        self.assertEqual(position_sizing['high_volatility'], 0.25)  # Updated from 0.35
        self.assertEqual(position_sizing['extreme_volatility'], 0.10)  # Updated from 0.15

    def test_process_volatility(self):
        """Test processing volatility levels."""
        # Test low volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.LOW.value,
            volatility_value=10.0,
            symbol=self.test_symbol
        )
        
        self.assertFalse(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CLOSED)
        self.assertEqual(position_size, 1.0)
        
        # Test normal volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.NORMAL.value,
            volatility_value=18.0,
            symbol=self.test_symbol
        )
        
        self.assertFalse(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CLOSED)
        self.assertEqual(position_size, 1.0)
        
        # Test high volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.HIGH.value,
            volatility_value=25.0,
            symbol=self.test_symbol
        )
        
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CAUTIOUS)
        self.assertEqual(position_size, 0.25)  # Updated from 0.35
        
        # Test extreme volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.EXTREME.value,
            volatility_value=40.0,
            symbol=self.test_symbol
        )
        
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
        self.assertEqual(position_size, 0.10)  # Updated from 0.15

    def test_hysteresis_mechanism(self):
        """Test the hysteresis mechanism for preventing rapid switching."""
        # Add some volatility history
        self.circuit_breaker.volatility_history[self.test_symbol] = []
        
        # Add 14 high volatility samples (not enough to trip)
        for _ in range(14):
            self.circuit_breaker.process_volatility(
                volatility_level=VolatilityRegime.HIGH.value,
                volatility_value=25.0,
                symbol=self.test_symbol
            )
            
        # Circuit should not be tripped yet (need 15 samples with 80% above threshold)
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertFalse(tripped)
        
        # Add one more sample to reach the threshold
        self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.HIGH.value,
            volatility_value=25.0,
            symbol=self.test_symbol
        )
        
        # Now the circuit should be tripped
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertTrue(tripped)
        
        # Add some low volatility samples
        for _ in range(7):  # Not enough to reset
            self.circuit_breaker.process_volatility(
                volatility_level=VolatilityRegime.LOW.value,
                volatility_value=10.0,
                symbol=self.test_symbol
            )
        
        # Circuit should still be tripped (need more low samples)
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertTrue(tripped)
        
        # Add more low volatility samples to reach the threshold for resetting
        for _ in range(8):
            self.circuit_breaker.process_volatility(
                volatility_level=VolatilityRegime.LOW.value,
                volatility_value=10.0,
                symbol=self.test_symbol
            )
        
        # Now the circuit should be reset
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertFalse(tripped)

    @patch('Elson.trading_engine.engine.circuit_breaker.time')
    def test_cooldown_mechanism(self, mock_time):
        """Test the cooldown mechanism for circuit breakers."""
        # Set mock time
        mock_time.time.return_value = 1000.0
        
        # Trip circuit breaker with extreme volatility
        self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.EXTREME.value,
            volatility_value=40.0,
            symbol=self.test_symbol
        )
        
        # Circuit should be tripped
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertTrue(tripped)
        
        # Check cooldown timer
        self.assertIn(self.test_symbol, self.circuit_breaker.cooldown_timers)
        self.assertIn(CircuitBreakerType.VOLATILITY, self.circuit_breaker.cooldown_timers[self.test_symbol])
        
        # Time hasn't passed yet
        mock_time.time.return_value = 1001.0  # Just 1 second later
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertTrue(tripped)  # Still tripped due to cooldown
        
        # Advance time past cooldown period
        extreme_cooldown = self.circuit_breaker.config['cooldown_periods']['extreme_volatility']
        mock_time.time.return_value = 1000.0 + extreme_cooldown + 1
        
        # Process low volatility to reset
        for _ in range(15):  # Need enough samples to meet threshold
            self.circuit_breaker.process_volatility(
                volatility_level=VolatilityRegime.LOW.value,
                volatility_value=10.0,
                symbol=self.test_symbol
            )
        
        # Now the circuit should be reset
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertFalse(tripped)

    def test_reset(self):
        """Test manually resetting the circuit breaker."""
        # Trip the circuit breaker
        self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.HIGH.value,
            volatility_value=25.0,
            symbol=self.test_symbol
        )
        
        # Verify it's tripped
        self.assertIn(self.test_symbol, self.circuit_breaker.circuit_status)
        self.assertIn(CircuitBreakerType.VOLATILITY, self.circuit_breaker.circuit_status[self.test_symbol])
        
        # Reset it
        self.circuit_breaker.reset(CircuitBreakerType.VOLATILITY, self.test_symbol)
        
        # Verify it's reset
        tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, self.test_symbol)
        self.assertFalse(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CLOSED)

    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        # Trip multiple circuit breakers
        symbols = ["TEST1", "TEST2", "TEST3"]
        
        for symbol in symbols:
            self.circuit_breaker.process_volatility(
                volatility_level=VolatilityRegime.HIGH.value,
                volatility_value=25.0,
                symbol=symbol
            )
        
        # Verify they're all tripped
        for symbol in symbols:
            tripped, _, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, symbol)
            self.assertTrue(tripped)
        
        # Reset all
        self.circuit_breaker.reset_all()
        
        # Verify all are reset
        for symbol in symbols:
            tripped, status, _ = self.circuit_breaker.check(CircuitBreakerType.VOLATILITY, symbol)
            self.assertFalse(tripped)
            self.assertEqual(status, CircuitBreakerStatus.CLOSED)

    def test_different_position_sizing(self):
        """Test that position sizing is correctly applied for different volatility levels."""
        # Test high volatility
        _, _, position_size_high = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.HIGH.value,
            volatility_value=25.0,
            symbol=self.test_symbol
        )
        
        # Test extreme volatility
        _, _, position_size_extreme = self.circuit_breaker.process_volatility(
            volatility_level=VolatilityRegime.EXTREME.value,
            volatility_value=40.0,
            symbol=self.test_symbol
        )
        
        # Verify different position sizing
        self.assertGreater(position_size_high, position_size_extreme)
        self.assertEqual(position_size_high, 0.25)  # Updated from 0.35
        self.assertEqual(position_size_extreme, 0.10)  # Updated from 0.15


if __name__ == '__main__':
    unittest.main()