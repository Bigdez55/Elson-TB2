"""
Trading Engine Module

Advanced trading engine with AI/ML integration, risk management,
and quantum-enhanced portfolio optimization for personal trading.

This package provides standalone trading functionality. Some modules
require the backend app to be installed for full functionality.
"""

# Core engine components (standalone - no app dependencies)
from .engine.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerType,
    CircuitBreakerStatus,
    VolatilityLevel,
    get_circuit_breaker,
)
from .engine.risk_config import RiskProfile, get_risk_config

# Optional imports - these may require backend app
try:
    from .engine.trade_executor import TradeExecutor
except ImportError:
    TradeExecutor = None  # Available when app is installed

try:
    from .engine.risk_manager import RiskManager
    from .engine.performance_monitor import PerformanceMonitor
    from .engine.strategy_optimizer import StrategyOptimizer
except ImportError:
    RiskManager = None
    PerformanceMonitor = None
    StrategyOptimizer = None

# Strategies (standalone)
from .strategies.base import TradingStrategy
from .strategies.registry import StrategyRegistry, StrategyCategory

# Optional strategy imports
try:
    from .strategies.moving_average import MovingAverageStrategy
except ImportError:
    MovingAverageStrategy = None

__version__ = "1.0.0"

# Export list - only include what's successfully imported
__all__ = [
    # Engine (always available)
    "CircuitBreaker",
    "CircuitBreakerType",
    "CircuitBreakerStatus",
    "VolatilityLevel",
    "get_circuit_breaker",
    "RiskProfile",
    "get_risk_config",
    # Strategies (always available)
    "TradingStrategy",
    "StrategyRegistry",
    "StrategyCategory",
]

# Add optional exports if available
if TradeExecutor is not None:
    __all__.append("TradeExecutor")
if RiskManager is not None:
    __all__.extend(["RiskManager", "PerformanceMonitor", "StrategyOptimizer"])
if MovingAverageStrategy is not None:
    __all__.append("MovingAverageStrategy")
