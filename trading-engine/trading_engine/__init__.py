"""
Trading Engine Module

Advanced trading engine with AI/ML integration, risk management,
and quantum-enhanced portfolio optimization for personal trading.
"""

from .engine.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerType,
    CircuitBreakerStatus,
    VolatilityLevel,
    get_circuit_breaker,
)

__version__ = "1.0.0"

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerType",
    "CircuitBreakerStatus",
    "VolatilityLevel",
    "get_circuit_breaker",
]
