"""
Ensemble Engine for the trading bot.
Combines predictions from multiple models using ensemble methods.
"""

from .model_combiner import (
    ClassificationEnsemble,
    DynamicWeightEnsemble,
    ModelCombiner,
    RangePredictionEnsemble,
    RegressionEnsemble,
)

__all__ = [
    "ModelCombiner",
    "ClassificationEnsemble",
    "RegressionEnsemble",
    "DynamicWeightEnsemble",
    "RangePredictionEnsemble",
]
