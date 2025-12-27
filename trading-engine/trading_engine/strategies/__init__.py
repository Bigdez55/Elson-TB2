"""
Trading Strategies Module

Contains base strategy framework and comprehensive trading strategy implementations
covering technical analysis, breakout, momentum, mean reversion, arbitrage,
grid trading, and execution algorithms.
"""

# Base classes and registry
from .base import TradingStrategy
from .registry import StrategyRegistry, StrategyCategory

# Technical Analysis Strategies
from .technical import (
    RSIStrategy,
    BollingerBandsStrategy,
    MACDStrategy,
    IchimokuCloudStrategy,
    ADXTrendStrategy,
    StochasticStrategy,
    CandlestickPatternStrategy,
)

# Breakout Strategies
from .breakout import (
    SupportResistanceBreakout,
    OpeningRangeBreakout,
    DonchianBreakout,
)

# Mean Reversion Strategies
from .mean_reversion import (
    StatisticalMeanReversion,
    RSIMeanReversion,
)

# Momentum Strategies
from .momentum import (
    MomentumFactorStrategy,
    TrendFollowingStrategy,
)

# Statistical Arbitrage Strategies
from .arbitrage import (
    PairsTradingStrategy,
)

# Grid and DCA Strategies
from .grid import (
    GridTradingStrategy,
    DCAStrategy,
)

# Execution Algorithms
from .execution import (
    VWAPExecutionStrategy,
    TWAPExecutionStrategy,
    IcebergExecutionStrategy,
)

__all__ = [
    # Base
    "TradingStrategy",
    "StrategyRegistry",
    "StrategyCategory",
    # Technical
    "RSIStrategy",
    "BollingerBandsStrategy",
    "MACDStrategy",
    "IchimokuCloudStrategy",
    "ADXTrendStrategy",
    "StochasticStrategy",
    "CandlestickPatternStrategy",
    # Breakout
    "SupportResistanceBreakout",
    "OpeningRangeBreakout",
    "DonchianBreakout",
    # Mean Reversion
    "StatisticalMeanReversion",
    "RSIMeanReversion",
    # Momentum
    "MomentumFactorStrategy",
    "TrendFollowingStrategy",
    # Arbitrage
    "PairsTradingStrategy",
    # Grid/DCA
    "GridTradingStrategy",
    "DCAStrategy",
    # Execution
    "VWAPExecutionStrategy",
    "TWAPExecutionStrategy",
    "IcebergExecutionStrategy",
]

# Strategy count for documentation
STRATEGY_COUNT = len(__all__) - 3  # Exclude base classes


def get_all_strategies():
    """Get a dictionary of all available strategies by category"""
    return {
        "technical": [
            "RSIStrategy",
            "BollingerBandsStrategy",
            "MACDStrategy",
            "IchimokuCloudStrategy",
            "ADXTrendStrategy",
            "StochasticStrategy",
            "CandlestickPatternStrategy",
        ],
        "breakout": [
            "SupportResistanceBreakout",
            "OpeningRangeBreakout",
            "DonchianBreakout",
        ],
        "mean_reversion": [
            "StatisticalMeanReversion",
            "RSIMeanReversion",
        ],
        "momentum": [
            "MomentumFactorStrategy",
            "TrendFollowingStrategy",
        ],
        "arbitrage": [
            "PairsTradingStrategy",
        ],
        "grid": [
            "GridTradingStrategy",
            "DCAStrategy",
        ],
        "execution": [
            "VWAPExecutionStrategy",
            "TWAPExecutionStrategy",
            "IcebergExecutionStrategy",
        ],
    }


def create_strategy(name: str, symbol: str, **kwargs):
    """
    Factory function to create a strategy by name.

    Args:
        name: Strategy name (registered in StrategyRegistry)
        symbol: Trading symbol
        **kwargs: Strategy-specific parameters

    Returns:
        Configured strategy instance
    """
    return StrategyRegistry.create(name, symbol=symbol, **kwargs)
