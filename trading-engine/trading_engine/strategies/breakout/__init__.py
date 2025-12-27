"""
Breakout Trading Strategies

Contains strategies based on support/resistance breakouts,
opening range breakouts, and chart pattern breakouts.
"""

from .support_resistance import SupportResistanceBreakout
from .opening_range import OpeningRangeBreakout
from .donchian_breakout import DonchianBreakout

__all__ = [
    "SupportResistanceBreakout",
    "OpeningRangeBreakout",
    "DonchianBreakout",
]
