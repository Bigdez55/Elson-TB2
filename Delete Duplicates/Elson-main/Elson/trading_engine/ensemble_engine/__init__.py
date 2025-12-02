"""
Ensemble Engine for the trading bot.
Combines predictions from multiple models using ensemble methods.
"""

from .model_combiner import (
    ModelCombiner,
    ClassificationEnsemble,
    RegressionEnsemble,
    DynamicWeightEnsemble,
    RangePredictionEnsemble
)

__all__ = [
    'ModelCombiner',
    'ClassificationEnsemble',
    'RegressionEnsemble',
    'DynamicWeightEnsemble',
    'RangePredictionEnsemble'
]