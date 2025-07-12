"""
Temporary mock implementations of trading engine functions for risk.py
"""
import datetime
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskProfile(str, Enum):
    """Risk profile enum for the trading engine"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class CircuitBreakerType(str, Enum):
    """Circuit breaker types for the trading engine"""

    MARKET = "market"
    TECHNICAL = "technical"
    VOLATILITY = "volatility"
    ANOMALY = "anomaly"
    LIQUIDITY = "liquidity"
    EXCHANGE = "exchange"
    API_ERROR = "api_error"
    CUSTOM = "custom"


class MockRiskConfig:
    """Mock risk configuration for the trading engine"""

    def __init__(self):
        self.profile = RiskProfile.MODERATE
        self.audit_log_file = "/tmp/risk_audit.log"

    def get_profile_params(self, profile):
        """Get parameters for a risk profile"""
        # Return mock parameters based on profile
        if profile == RiskProfile.CONSERVATIVE:
            return {
                "position_sizing": {
                    "max_position_size": 0.05,
                    "max_sector_exposure": 0.20,
                    "base_quantity_percent": 0.02,
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.15,
                    "max_position_volatility": 0.30,
                },
                "drawdown_limits": {
                    "max_total_drawdown": 0.10,
                    "max_position_drawdown": 0.15,
                },
            }
        elif profile == RiskProfile.MODERATE:
            return {
                "position_sizing": {
                    "max_position_size": 0.10,
                    "max_sector_exposure": 0.30,
                    "base_quantity_percent": 0.05,
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.25,
                    "max_position_volatility": 0.40,
                },
                "drawdown_limits": {
                    "max_total_drawdown": 0.15,
                    "max_position_drawdown": 0.20,
                },
            }
        elif profile == RiskProfile.AGGRESSIVE:
            return {
                "position_sizing": {
                    "max_position_size": 0.20,
                    "max_sector_exposure": 0.40,
                    "base_quantity_percent": 0.10,
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.35,
                    "max_position_volatility": 0.50,
                },
                "drawdown_limits": {
                    "max_total_drawdown": 0.25,
                    "max_position_drawdown": 0.30,
                },
            }
        else:
            return {
                "position_sizing": {
                    "max_position_size": 0.15,
                    "max_sector_exposure": 0.35,
                    "base_quantity_percent": 0.075,
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.30,
                    "max_position_volatility": 0.45,
                },
                "drawdown_limits": {
                    "max_total_drawdown": 0.20,
                    "max_position_drawdown": 0.25,
                },
            }

    def set_param(self, param_path, value, profile, reason=None):
        """Set a parameter value"""
        logger.info(f"Setting {param_path} to {value} for profile {profile.value}")
        return True

    def set_profile(self, profile):
        """Set the active risk profile"""
        logger.info(f"Setting active profile to {profile.value}")
        self.profile = profile
        return True


class MockCircuitBreaker:
    """Mock circuit breaker for the trading engine"""

    def __init__(self):
        self.breakers = {}

    def get_status(self):
        """Get status of all circuit breakers"""
        return []

    def trip(self, breaker_type, reason, scope=None, reset_after=None):
        """Trip a circuit breaker"""
        logger.info(
            f"Tripping circuit breaker: {breaker_type.value}, scope: {scope}, reason: {reason}"
        )
        breaker_key = f"{breaker_type.value}:{scope}" if scope else breaker_type.value
        self.breakers[breaker_key] = {
            "type": breaker_type.value,
            "scope": scope,
            "reason": reason,
            "tripped_at": datetime.datetime.utcnow().isoformat(),
            "reset_after": reset_after,
            "active": True,
        }
        return True

    def reset(self, breaker_type, scope=None):
        """Reset a circuit breaker"""
        breaker_key = f"{breaker_type.value}:{scope}" if scope else breaker_type.value
        if breaker_key in self.breakers:
            self.breakers[breaker_key]["active"] = False
            return True
        return False

    def reset_all(self):
        """Reset all circuit breakers"""
        for key in self.breakers:
            self.breakers[key]["active"] = False
        return True


# Singleton instances
_risk_config = MockRiskConfig()
_circuit_breaker = MockCircuitBreaker()


def get_risk_config():
    """Get the risk configuration singleton"""
    return _risk_config


def get_circuit_breaker():
    """Get the circuit breaker singleton"""
    return _circuit_breaker
