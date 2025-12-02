import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from ..engine.circuit_breaker import (
    CircuitBreaker, CircuitBreakerType, CircuitBreakerStatus, 
    VolatilityLevel, get_circuit_breaker
)

class TestEnhancedCircuitBreaker(unittest.TestCase):
    """Test the enhanced circuit breaker implementation for Phase 2."""
    
    def setUp(self):
        # Create a temporary status file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.status_file_path = os.path.join(self.temp_dir.name, "circuit_breaker_status.json")
        
        # Create a fresh circuit breaker instance for each test
        patcher = patch.object(CircuitBreaker, 'status_file', self.status_file_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.circuit_breaker = CircuitBreaker()
    
    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_volatility_processing(self):
        """Test processing different volatility levels."""
        # Test extreme volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.EXTREME, 42.5, symbol="AAPL"
        )
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.OPEN)
        self.assertEqual(position_size, 0.25)  # 25% position sizing
        
        # Test high volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.HIGH, 32.0, symbol="MSFT"
        )
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
        self.assertEqual(position_size, 0.50)  # 50% position sizing
        
        # Test normal volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.NORMAL, 18.0, symbol="GOOGL"
        )
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CAUTIOUS)
        self.assertEqual(position_size, 1.0)  # 100% position sizing
        
        # Test low volatility
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.LOW, 12.0, symbol="IBM"
        )
        self.assertFalse(tripped)
        self.assertEqual(status, CircuitBreakerStatus.CLOSED)
        self.assertEqual(position_size, 1.0)  # 100% position sizing
    
    def test_asset_class_modifier(self):
        """Test that asset class modifiers are applied correctly."""
        # Test cryptocurrency (1.5x modifier)
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.HIGH, 35.0, symbol="BTC-USD", asset_class="cryptocurrency"
        )
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
        
        # Test forex (0.8x modifier)
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.HIGH, 28.0, symbol="EUR/USD", asset_class="forex"
        )
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
    
    def test_hysteresis(self):
        """Test that hysteresis prevents rapid switching between regimes."""
        # Initialize history with multiple samples of high volatility
        self.circuit_breaker.volatility_history["TSLA"] = [
            VolatilityLevel.HIGH, VolatilityLevel.HIGH, VolatilityLevel.HIGH
        ]
        
        # Single reading of extreme should not immediately switch to extreme
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.EXTREME, 41.0, symbol="TSLA"
        )
        
        # Should still be in high regime due to hysteresis
        self.assertTrue(tripped)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)  # High regime status
        
        # Add more extreme readings to exceed threshold
        for _ in range(4):
            self.circuit_breaker.process_volatility(
                VolatilityLevel.EXTREME, 42.0, symbol="TSLA"
            )
        
        # Now it should switch to extreme
        tripped, status, position_size = self.circuit_breaker.process_volatility(
            VolatilityLevel.EXTREME, 43.0, symbol="TSLA"
        )
        self.assertEqual(status, CircuitBreakerStatus.OPEN)  # Extreme regime status
    
    def test_graduated_reset(self):
        """Test the graduated reset functionality."""
        # Trip a circuit breaker
        self.circuit_breaker.trip(
            CircuitBreakerType.VOLATILITY,
            "Test extreme volatility",
            scope="AMD",
            status=CircuitBreakerStatus.OPEN
        )
        
        # Verify initial status
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "AMD")
        key = next(iter(breaker_info))
        self.assertEqual(breaker_info[key]["status"], CircuitBreakerStatus.OPEN.value)
        
        # Reset one step
        reset_result = self.circuit_breaker.reset(CircuitBreakerType.VOLATILITY, "AMD")
        self.assertTrue(reset_result)
        
        # Check new status (should be RESTRICTED)
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "AMD")
        key = next(iter(breaker_info))
        self.assertEqual(breaker_info[key]["status"], CircuitBreakerStatus.RESTRICTED.value)
        
        # Reset one more step
        reset_result = self.circuit_breaker.reset(CircuitBreakerType.VOLATILITY, "AMD")
        self.assertTrue(reset_result)
        
        # Check new status (should be CAUTIOUS)
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "AMD")
        key = next(iter(breaker_info))
        self.assertEqual(breaker_info[key]["status"], CircuitBreakerStatus.CAUTIOUS.value)
        
        # Reset one final step
        reset_result = self.circuit_breaker.reset(CircuitBreakerType.VOLATILITY, "AMD")
        self.assertTrue(reset_result)
        
        # Check that the breaker is now fully removed
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "AMD")
        self.assertEqual(len(breaker_info), 0)
    
    def test_auto_reset(self):
        """Test automatic graduated reset based on cool-down periods."""
        # Create a circuit breaker with a past auto-reset time
        past_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        # Manually create circuit breaker entry with past reset time
        key = f"{CircuitBreakerType.VOLATILITY.value}:NVDA"
        self.circuit_breaker.circuit_breakers[key] = {
            "type": CircuitBreakerType.VOLATILITY.value,
            "scope": "NVDA",
            "status": CircuitBreakerStatus.OPEN.value,
            "reason": "Test auto-reset",
            "tripped_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            "auto_reset_at": past_time
        }
        
        # Save status
        self.circuit_breaker._save_status()
        
        # Check status - should trigger auto-reset
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "NVDA")
        key = next(iter(breaker_info))
        
        # Should have been auto-reset from OPEN to RESTRICTED
        self.assertEqual(breaker_info[key]["status"], CircuitBreakerStatus.RESTRICTED.value)
        
        # Set up the auto-reset time for the next level to be in the past
        self.circuit_breaker.circuit_breakers[key]["auto_reset_at"] = past_time
        self.circuit_breaker._save_status()
        
        # Check status again - should trigger another auto-reset
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "NVDA")
        key = next(iter(breaker_info))
        
        # Should have been auto-reset from RESTRICTED to CAUTIOUS
        self.assertEqual(breaker_info[key]["status"], CircuitBreakerStatus.CAUTIOUS.value)
        
        # Set up the auto-reset time for the next level to be in the past
        self.circuit_breaker.circuit_breakers[key]["auto_reset_at"] = past_time
        self.circuit_breaker._save_status()
        
        # Check status again - should trigger full removal
        breaker_info = self.circuit_breaker.get_status(CircuitBreakerType.VOLATILITY, "NVDA")
        
        # Should be completely removed now
        self.assertEqual(len(breaker_info), 0)
    
    def test_position_sizing(self):
        """Test position sizing based on circuit breaker status."""
        # Trip several breakers at different levels
        self.circuit_breaker.trip(
            CircuitBreakerType.VOLATILITY,
            "High volatility",
            scope="FB",
            status=CircuitBreakerStatus.RESTRICTED  # 50% position sizing
        )
        
        self.circuit_breaker.trip(
            CircuitBreakerType.DAILY_LOSS,
            "Warning level daily loss",
            scope="portfolio1",
            status=CircuitBreakerStatus.CAUTIOUS  # 75% position sizing
        )
        
        self.circuit_breaker.trip(
            CircuitBreakerType.SYSTEM,
            "System-wide warning",
            status=CircuitBreakerStatus.CAUTIOUS  # 75% position sizing
        )
        
        # Test symbol specific position sizing
        position_size = self.circuit_breaker.get_position_sizing(scope="FB")
        self.assertEqual(position_size, 0.5)  # Should use the 50% from RESTRICTED volatility
        
        # Test portfolio position sizing
        position_size = self.circuit_breaker.get_position_sizing(scope="portfolio1")
        self.assertEqual(position_size, 0.75)  # Should use the 75% from CAUTIOUS daily loss
        
        # Test system-wide position sizing
        position_size = self.circuit_breaker.get_position_sizing()
        self.assertEqual(position_size, 0.75)  # Should use the 75% from system CAUTIOUS status
        
        # Test combined position sizing (most restrictive should win)
        self.circuit_breaker.trip(
            CircuitBreakerType.VOLATILITY,
            "Extreme volatility",
            scope="portfolio1",
            status=CircuitBreakerStatus.OPEN  # 0% position sizing
        )
        
        position_size = self.circuit_breaker.get_position_sizing(scope="portfolio1")
        self.assertEqual(position_size, 0.0)  # Should use 0% from OPEN volatility
    
    def test_circuit_breaker_check(self):
        """Test the check method that determines if trading is allowed."""
        # Trip a breaker that halts trading
        self.circuit_breaker.trip(
            CircuitBreakerType.VOLATILITY,
            "Extreme volatility",
            scope="SPY",
            status=CircuitBreakerStatus.OPEN
        )
        
        # Trip a breaker that restricts but doesn't halt trading
        self.circuit_breaker.trip(
            CircuitBreakerType.VOLATILITY,
            "High volatility",
            scope="QQQ",
            status=CircuitBreakerStatus.RESTRICTED
        )
        
        # Check halted symbol
        allowed, status = self.circuit_breaker.check(scope="SPY")
        self.assertFalse(allowed)
        self.assertEqual(status, CircuitBreakerStatus.OPEN)
        
        # Check restricted symbol
        allowed, status = self.circuit_breaker.check(scope="QQQ")
        self.assertTrue(allowed)
        self.assertEqual(status, CircuitBreakerStatus.RESTRICTED)
        
        # Check unrestricted symbol
        allowed, status = self.circuit_breaker.check(scope="IWM")
        self.assertTrue(allowed)
        self.assertEqual(status, CircuitBreakerStatus.CLOSED)
    
    def test_singleton_instance(self):
        """Test that the singleton instance works correctly."""
        # Get two instances
        instance1 = get_circuit_breaker()
        instance2 = get_circuit_breaker()
        
        # They should be the same object
        self.assertIs(instance1, instance2)
        
        # Test that operations on one affect the other
        instance1.trip(
            CircuitBreakerType.MANUAL,
            "Test singleton",
            scope="SINGLETON"
        )
        
        # Check using the second instance
        breaker_info = instance2.get_status(CircuitBreakerType.MANUAL, "SINGLETON")
        self.assertEqual(len(breaker_info), 1)

if __name__ == "__main__":
    unittest.main()