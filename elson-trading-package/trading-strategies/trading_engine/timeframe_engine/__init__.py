"""
Timeframe Estimation Engine for the trading bot.
Provides tools for detecting regime changes and estimating optimal timeframes for trading.
"""

from .change_point_detector import (
    ChangePointDetector,
    BinarySegmentation,
    PELT,
    WindowBasedDetector,
    BayesianChangePointDetector,
    detect_regime_changes,
    define_market_regimes
)

from .timeframe_estimator import (
    TimeframeEstimator,
    EventBasedTimeframeEstimator,
    detect_market_events
)

__all__ = [
    'ChangePointDetector',
    'BinarySegmentation',
    'PELT',
    'WindowBasedDetector',
    'BayesianChangePointDetector',
    'detect_regime_changes',
    'define_market_regimes',
    'TimeframeEstimator',
    'EventBasedTimeframeEstimator',
    'detect_market_events'
]