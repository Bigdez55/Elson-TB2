"""
Momentum Trading Strategies

Contains strategies based on price momentum, factor investing,
and trend-following approaches.
"""

from .momentum_factor import MomentumFactorStrategy
from .trend_following import TrendFollowingStrategy

__all__ = [
    "MomentumFactorStrategy",
    "TrendFollowingStrategy",
]
