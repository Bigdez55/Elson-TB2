"""
Adaptive Parameter Optimization Module for Elson Wealth Trading Platform

This module implements dynamic parameter optimization for the hybrid machine learning models
based on current market volatility and other conditions. It adapts model parameters and 
trading settings to optimize performance across different market regimes.

Part of Phase 2 of the Hybrid Model Improvement Plan focusing on volatility robustness.
"""

import datetime
import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..engine.circuit_breaker import CircuitBreakerStatus, VolatilityLevel
from ..ml_models.volatility_regime.volatility_detector import (
    VolatilityDetector,
    VolatilityRegime,
)

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market condition classification beyond just volatility."""

    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS = "sideways"
    BULL_VOLATILE = "bull_volatile"
    BEAR_VOLATILE = "bear_volatile"
    REGIME_CHANGE = "regime_change"


class AdaptiveParameterOptimizer:
    """
    Dynamic parameter optimizer that adapts model parameters and trading settings
    based on current market conditions and volatility regimes.

    This class implements the third component of Phase 2 in the
    Hybrid Model Improvement Plan.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        history_window: int = 120,  # Increased from 90 to 120 days for more stable history
        adaptation_speed: float = 0.05,  # Reduced from 0.1 to 0.05 for more gradual adaptation
        enable_online_learning: bool = True,
    ):
        """
        Initialize the adaptive parameter optimizer.

        Args:
            config_path: Path to configuration file
            history_window: Number of days of historical performance to consider
            adaptation_speed: How quickly to adapt parameters (0-1)
            enable_online_learning: Whether to enable online parameter learning
        """
        self.history_window = history_window
        self.adaptation_speed = adaptation_speed
        self.enable_online_learning = enable_online_learning
        # Additional stability factor to prevent rapid parameter changes
        self.stability_factor = (
            0.03  # Further reduced from 0.05 for even more gradual adaptation
        )

        # Performance history
        self.performance_history = {
            VolatilityRegime.LOW: [],
            VolatilityRegime.NORMAL: [],
            VolatilityRegime.HIGH: [],
            VolatilityRegime.EXTREME: [],
        }

        # Parameter history
        self.parameter_history = []

        # Default parameter ranges
        self.parameter_ranges = {
            "lookback_periods": {
                "min": 3,  # Reduced min from 5 to 3
                "max": 50,
                "step": 5,
            },
            "prediction_horizon": {"min": 1, "max": 10, "step": 1},
            "confidence_threshold": {
                "min": 0.5,
                "max": 0.95,  # Increased max threshold
                "step": 0.05,
            },
        }

        # Default parameters by volatility regime
        self.default_parameters = {
            VolatilityRegime.LOW: {
                "lookback_periods": 30,
                "prediction_horizon": 5,
                "confidence_threshold": 0.55,
                "model_weights": {
                    "random_forest": 1.0,
                    "gradient_boosting": 1.0,
                    "neural_network": 1.0,
                    "quantum_kernel": 1.2,
                    "quantum_variational": 1.2,
                },
                "position_sizing": 1.0,
            },
            VolatilityRegime.NORMAL: {
                "lookback_periods": 20,
                "prediction_horizon": 3,
                "confidence_threshold": 0.65,  # Increased from 0.60 for better quality trades
                "model_weights": {
                    "random_forest": 1.2,  # Increased from 1.1
                    "gradient_boosting": 1.2,  # Increased from 1.1
                    "neural_network": 0.8,  # Reduced from 0.9
                    "quantum_kernel": 0.9,  # Reduced from 1.0
                    "quantum_variational": 0.8,  # Reduced from 0.9
                },
                "position_sizing": 0.90,  # Reduced from 1.0 for slightly more conservative approach
            },
            VolatilityRegime.HIGH: {
                "lookback_periods": 4,  # Further reduced from 6 for faster adaptation
                "prediction_horizon": 1,
                "confidence_threshold": 0.92,  # Increased from 0.88 for higher quality trades
                "model_weights": {
                    "random_forest": 3.0,  # Increased from 2.5
                    "gradient_boosting": 2.8,  # Increased from 2.2
                    "neural_network": 0.0,  # Disabled (from 0.1)
                    "quantum_kernel": 0.1,  # Reduced from 0.2
                    "quantum_variational": 0.0,  # Disabled (from 0.1)
                },
                "position_sizing": 0.10,  # Further reduced from 0.15 for risk management
            },
            VolatilityRegime.EXTREME: {
                "lookback_periods": 2,  # Further reduced from 3 for faster response
                "prediction_horizon": 1,
                "confidence_threshold": 0.97,  # Increased from 0.95 for only highest-conviction trades
                "model_weights": {
                    "random_forest": 4.0,  # Increased from 3.0
                    "gradient_boosting": 3.5,  # Increased from 2.5
                    "neural_network": 0.0,  # Disabled
                    "quantum_kernel": 0.0,  # Disabled
                    "quantum_variational": 0.0,  # Disabled
                },
                "position_sizing": 0.03,  # Further reduced from 0.05 for minimal risk
            },
        }

        # Current optimized parameters
        self.optimized_parameters = self.default_parameters.copy()

        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

        # Initialize volatility detector
        self.volatility_detector = VolatilityDetector()

        # Parameter adaptation tracking
        self.last_adaptation_time = None
        self.adaptation_frequency = datetime.timedelta(
            hours=36
        )  # Increased from 24 to 36 hours for more stability

        # Load historical performance data if available
        self._load_performance_history()

    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # Update parameters from config
            if "parameter_ranges" in config:
                self.parameter_ranges.update(config["parameter_ranges"])

            if "default_parameters" in config:
                for regime_str, params in config["default_parameters"].items():
                    try:
                        regime = VolatilityRegime[regime_str.upper()]
                        self.default_parameters[regime].update(params)
                    except KeyError:
                        logger.warning(
                            f"Unknown volatility regime in config: {regime_str}"
                        )

            # Reset optimized parameters to defaults
            self.optimized_parameters = self.default_parameters.copy()

            logger.info(f"Loaded adaptive parameter configuration from {config_path}")

        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")

    def _load_performance_history(self) -> None:
        """Load historical performance data if available."""
        history_path = "performance_history.json"

        if os.path.exists(history_path):
            try:
                with open(history_path, "r") as f:
                    history_data = json.load(f)

                for regime_str, entries in history_data.get(
                    "performance_history", {}
                ).items():
                    try:
                        regime = VolatilityRegime[regime_str.upper()]
                        self.performance_history[regime] = entries
                    except KeyError:
                        logger.warning(
                            f"Unknown volatility regime in history: {regime_str}"
                        )

                self.parameter_history = history_data.get("parameter_history", [])

                logger.info(
                    f"Loaded performance history with {sum(len(h) for h in self.performance_history.values())} entries"
                )

            except Exception as e:
                logger.error(f"Error loading performance history: {str(e)}")

    def _save_performance_history(self) -> None:
        """Save historical performance data."""
        history_path = "performance_history.json"

        try:
            # Convert enum keys to strings
            performance_history_serializable = {
                regime.name: entries
                for regime, entries in self.performance_history.items()
            }

            history_data = {
                "performance_history": performance_history_serializable,
                "parameter_history": self.parameter_history,
            }

            with open(history_path, "w") as f:
                json.dump(history_data, f, indent=2)

            logger.info(f"Saved performance history to {history_path}")

        except Exception as e:
            logger.error(f"Error saving performance history: {str(e)}")

    def detect_market_condition(
        self, data: pd.DataFrame, vix_data: Optional[pd.DataFrame] = None
    ) -> Tuple[VolatilityRegime, MarketCondition, float]:
        """
        Detect current market condition beyond just volatility.

        Args:
            data: DataFrame with market data
            vix_data: Optional VIX index data

        Returns:
            Tuple of (volatility_regime, market_condition, volatility_value)
        """
        # Detect volatility regime
        volatility_regime, volatility_value = self.volatility_detector.detect_regime(
            data, vix_data
        )

        # Determine market trending condition
        if "close" in data.columns and len(data) >= 50:
            # Calculate moving averages
            ma20 = data["close"].rolling(window=20).mean()
            ma50 = data["close"].rolling(window=50).mean()

            # Determine trend based on price vs moving averages
            latest_close = data["close"].iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_ma50 = ma50.iloc[-1]

            # Check for regime change - substantial difference in volatility recently
            if len(data) >= 30:
                recent_volatility = (
                    data["close"].pct_change().iloc[-10:].std() * np.sqrt(252) * 100
                )
                older_volatility = (
                    data["close"].pct_change().iloc[-30:-10].std() * np.sqrt(252) * 100
                )

                regime_change = (
                    abs(recent_volatility - older_volatility) > 10
                )  # 10% difference threshold
            else:
                regime_change = False

            # Determine market condition
            if regime_change:
                market_condition = MarketCondition.REGIME_CHANGE
            elif latest_close > latest_ma20 and latest_ma20 > latest_ma50:
                # Bull market
                if volatility_regime in [
                    VolatilityRegime.HIGH,
                    VolatilityRegime.EXTREME,
                ]:
                    market_condition = MarketCondition.BULL_VOLATILE
                else:
                    market_condition = MarketCondition.BULL_TRENDING
            elif latest_close < latest_ma20 and latest_ma20 < latest_ma50:
                # Bear market
                if volatility_regime in [
                    VolatilityRegime.HIGH,
                    VolatilityRegime.EXTREME,
                ]:
                    market_condition = MarketCondition.BEAR_VOLATILE
                else:
                    market_condition = MarketCondition.BEAR_TRENDING
            else:
                # Sideways market
                market_condition = MarketCondition.SIDEWAYS
        else:
            # Default to sideways if insufficient data
            market_condition = MarketCondition.SIDEWAYS

        logger.info(
            f"Detected market condition: Volatility={volatility_regime.name}, "
            f"Market={market_condition.value}, Value={volatility_value:.2f}%"
        )

        return volatility_regime, market_condition, volatility_value

    def adapt_lookback_period(
        self, volatility_regime: VolatilityRegime, market_condition: MarketCondition
    ) -> int:
        """
        Adapt the lookback period based on market conditions.

        Args:
            volatility_regime: Current volatility regime
            market_condition: Current market condition

        Returns:
            Adapted lookback period
        """
        # Start with the default for this volatility regime
        base_lookback = self.optimized_parameters[volatility_regime]["lookback_periods"]

        # Adjust based on market condition
        if market_condition == MarketCondition.REGIME_CHANGE:
            # Even shorter lookback during regime changes for high volatility regimes
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = -2
            else:
                adjustment = -5
        elif (
            market_condition == MarketCondition.BULL_TRENDING
            or market_condition == MarketCondition.BEAR_TRENDING
        ):
            # Longer lookback for trending markets, but only slightly for high volatility
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = 1
            else:
                adjustment = 5
        elif (
            market_condition == MarketCondition.BULL_VOLATILE
            or market_condition == MarketCondition.BEAR_VOLATILE
        ):
            # Even shorter lookback for volatile markets
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = -2
            else:
                adjustment = -5
        else:  # SIDEWAYS
            # Default for sideways markets
            adjustment = 0

        # Apply adjustment with constraints
        adjusted_lookback = base_lookback + adjustment
        min_lookback = self.parameter_ranges["lookback_periods"]["min"]
        max_lookback = self.parameter_ranges["lookback_periods"]["max"]

        return max(min_lookback, min(adjusted_lookback, max_lookback))

    def adapt_confidence_threshold(
        self, volatility_regime: VolatilityRegime, market_condition: MarketCondition
    ) -> float:
        """
        Adapt confidence threshold based on market conditions.

        Args:
            volatility_regime: Current volatility regime
            market_condition: Current market condition

        Returns:
            Adapted confidence threshold
        """
        # Start with the default for this volatility regime
        base_threshold = self.optimized_parameters[volatility_regime][
            "confidence_threshold"
        ]

        # Adjust based on market condition - more aggressive adjustments for high volatility
        if market_condition == MarketCondition.REGIME_CHANGE:
            # Higher threshold during regime changes (more conservative)
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = 0.03
            else:
                adjustment = 0.05
        elif market_condition == MarketCondition.BULL_TRENDING:
            # Lower threshold for bullish trends (slightly more aggressive)
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = -0.02
            else:
                adjustment = -0.05
        elif market_condition == MarketCondition.BEAR_TRENDING:
            # Higher threshold for bearish trends (more conservative)
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                adjustment = 0.03
            else:
                adjustment = 0.05
        elif market_condition == MarketCondition.BULL_VOLATILE:
            # Higher threshold for volatile bull markets
            adjustment = 0.03
        elif market_condition == MarketCondition.BEAR_VOLATILE:
            # Even higher threshold for volatile bear markets
            adjustment = 0.05
        else:  # SIDEWAYS
            # Default for sideways markets
            adjustment = 0

        # Apply adjustment with constraints
        adjusted_threshold = base_threshold + adjustment
        min_threshold = self.parameter_ranges["confidence_threshold"]["min"]
        max_threshold = self.parameter_ranges["confidence_threshold"]["max"]

        return max(min_threshold, min(adjusted_threshold, max_threshold))

    def adapt_prediction_horizon(
        self, volatility_regime: VolatilityRegime, market_condition: MarketCondition
    ) -> int:
        """
        Adapt prediction horizon based on market conditions.

        Args:
            volatility_regime: Current volatility regime
            market_condition: Current market condition

        Returns:
            Adapted prediction horizon
        """
        # Start with the default for this volatility regime
        base_horizon = self.optimized_parameters[volatility_regime][
            "prediction_horizon"
        ]

        # For HIGH and EXTREME volatility, always use horizon of 1 (very short-term focus)
        if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
            return 1

        # For other regimes, adjust based on market condition
        if market_condition == MarketCondition.REGIME_CHANGE:
            # Shorter horizon during regime changes
            adjustment = -1
        elif market_condition == MarketCondition.BULL_TRENDING:
            # Longer horizon for bullish trends
            adjustment = 1
        elif market_condition == MarketCondition.BEAR_TRENDING:
            # Shorter horizon for bearish trends
            adjustment = -1
        elif (
            market_condition == MarketCondition.BULL_VOLATILE
            or market_condition == MarketCondition.BEAR_VOLATILE
        ):
            # Shorter horizon for volatile markets
            adjustment = -1
        else:  # SIDEWAYS
            # Default for sideways markets
            adjustment = 0

        # Apply adjustment with constraints
        adjusted_horizon = base_horizon + adjustment
        min_horizon = self.parameter_ranges["prediction_horizon"]["min"]
        max_horizon = self.parameter_ranges["prediction_horizon"]["max"]

        return max(min_horizon, min(adjusted_horizon, max_horizon))

    def adapt_model_weights(
        self, volatility_regime: VolatilityRegime, market_condition: MarketCondition
    ) -> Dict[str, float]:
        """
        Adapt model weights based on market conditions.

        Args:
            volatility_regime: Current volatility regime
            market_condition: Current market condition

        Returns:
            Dictionary of adapted model weights
        """
        # Start with the default weights for this volatility regime
        base_weights = self.optimized_parameters[volatility_regime][
            "model_weights"
        ].copy()

        # For HIGH and EXTREME volatility, force disable unstable models
        if volatility_regime == VolatilityRegime.HIGH:
            # Heavily favor tree-based models, minimal weights for others
            base_weights["neural_network"] = 0.0
            base_weights["quantum_variational"] = 0.0
            base_weights["quantum_kernel"] = 0.1
        elif volatility_regime == VolatilityRegime.EXTREME:
            # Only use tree-based models for extreme volatility
            base_weights["neural_network"] = 0.0
            base_weights["quantum_variational"] = 0.0
            base_weights["quantum_kernel"] = 0.0

            # Further increase random forest for extreme conditions
            base_weights["random_forest"] = max(
                base_weights.get("random_forest", 3.0), 4.0
            )

        # Apply market condition specific adjustments (but only for LOW and NORMAL regimes)
        if volatility_regime in [VolatilityRegime.LOW, VolatilityRegime.NORMAL]:
            if market_condition == MarketCondition.REGIME_CHANGE:
                # During regime changes, favor robust traditional models
                adjustments = {
                    "random_forest": 0.2,
                    "gradient_boosting": 0.2,
                    "neural_network": -0.2,
                    "quantum_kernel": -0.1,
                    "quantum_variational": -0.1,
                }
            elif market_condition == MarketCondition.BULL_TRENDING:
                # In bull trends, favor neural networks and quantum models
                adjustments = {
                    "random_forest": -0.1,
                    "gradient_boosting": 0.0,
                    "neural_network": 0.1,
                    "quantum_kernel": 0.1,
                    "quantum_variational": 0.1,
                }
            elif market_condition == MarketCondition.BEAR_TRENDING:
                # In bear trends, favor traditional models
                adjustments = {
                    "random_forest": 0.1,
                    "gradient_boosting": 0.1,
                    "neural_network": -0.1,
                    "quantum_kernel": -0.05,
                    "quantum_variational": -0.05,
                }
            elif market_condition == MarketCondition.BULL_VOLATILE:
                # In volatile bull markets, balanced approach
                adjustments = {
                    "random_forest": 0.0,
                    "gradient_boosting": 0.1,
                    "neural_network": 0.0,
                    "quantum_kernel": 0.0,
                    "quantum_variational": -0.1,
                }
            elif market_condition == MarketCondition.BEAR_VOLATILE:
                # In volatile bear markets, heavily favor very robust models
                adjustments = {
                    "random_forest": 0.3,
                    "gradient_boosting": 0.3,
                    "neural_network": -0.3,
                    "quantum_kernel": -0.2,
                    "quantum_variational": -0.2,
                }
            else:  # SIDEWAYS
                # No adjustments for sideways markets
                adjustments = {
                    "random_forest": 0.0,
                    "gradient_boosting": 0.0,
                    "neural_network": 0.0,
                    "quantum_kernel": 0.0,
                    "quantum_variational": 0.0,
                }

            # Apply adjustments
            for model, adjustment in adjustments.items():
                if model in base_weights:
                    base_weights[model] += adjustment

        # Ensure weights are positive or zero (we want to fully disable some models)
        for model in base_weights:
            if base_weights[model] < 0.1 and base_weights[model] > 0:
                base_weights[model] = 0.1
            elif base_weights[model] < 0:
                base_weights[model] = 0.0

        return base_weights

    def get_recommended_position_sizing(
        self,
        volatility_regime: VolatilityRegime,
        market_condition: MarketCondition,
        circuit_breaker_status: Optional[CircuitBreakerStatus] = None,
    ) -> float:
        """
        Get recommended position sizing based on current conditions.

        Args:
            volatility_regime: Current volatility regime
            market_condition: Current market condition
            circuit_breaker_status: Optional circuit breaker status

        Returns:
            Position sizing multiplier (0.0-1.0)
        """
        # If circuit breaker is active, it takes precedence
        if circuit_breaker_status is not None:
            if circuit_breaker_status == CircuitBreakerStatus.OPEN:
                return 0.0
            elif circuit_breaker_status == CircuitBreakerStatus.RESTRICTED:
                # Further reduce position size when circuit breaker is restricted
                if volatility_regime == VolatilityRegime.EXTREME:
                    return 0.03  # Further reduced from 0.05
                elif volatility_regime == VolatilityRegime.HIGH:
                    return 0.10  # Further reduced from 0.15
                else:
                    return 0.5
            elif circuit_breaker_status == CircuitBreakerStatus.CAUTIOUS:
                # Apply more conservative sizing when cautious
                if volatility_regime == VolatilityRegime.EXTREME:
                    return 0.05  # Further reduced
                elif volatility_regime == VolatilityRegime.HIGH:
                    return 0.15  # Further reduced
                else:
                    return 0.75

        # Start with the default for this volatility regime
        base_sizing = self.optimized_parameters[volatility_regime]["position_sizing"]

        # Adjust based on market condition
        if market_condition == MarketCondition.REGIME_CHANGE:
            # Reduce position size during regime changes (high uncertainty)
            multiplier = 0.4  # Further reduced from 0.5
        elif market_condition == MarketCondition.BULL_TRENDING:
            # Slightly reduced position sizing even for bullish trends (from 1.0)
            multiplier = 0.9
        elif market_condition == MarketCondition.BEAR_TRENDING:
            # Further reduced position sizing for bearish trends
            multiplier = 0.6  # Reduced from 0.75
        elif market_condition == MarketCondition.BULL_VOLATILE:
            # More conservative for volatile bull markets
            multiplier = 0.7  # Reduced from 0.8
        elif market_condition == MarketCondition.BEAR_VOLATILE:
            # Even more reduced for volatile bear markets
            multiplier = 0.3  # Reduced from 0.4
        else:  # SIDEWAYS
            # More conservative for sideways markets
            multiplier = 0.8  # Reduced from 0.9

        return base_sizing * multiplier

    def update_performance_metrics(
        self,
        volatility_regime: VolatilityRegime,
        win_rate: float,
        avg_return: float,
        sharpe_ratio: float,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Update performance metrics for the current regime.

        Args:
            volatility_regime: Current volatility regime
            win_rate: Win rate achieved
            avg_return: Average return achieved
            sharpe_ratio: Sharpe ratio achieved
            parameters: Parameters used
        """
        # Create performance entry
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "sharpe_ratio": sharpe_ratio,
            "parameters": parameters,
        }

        # Add to performance history
        self.performance_history[volatility_regime].append(entry)

        # Trim history if it gets too long
        if len(self.performance_history[volatility_regime]) > self.history_window:
            self.performance_history[volatility_regime] = self.performance_history[
                volatility_regime
            ][-self.history_window :]

        # Add to parameter history
        parameter_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "regime": volatility_regime.name,
            "parameters": parameters,
            "performance": {
                "win_rate": win_rate,
                "avg_return": avg_return,
                "sharpe_ratio": sharpe_ratio,
            },
        }
        self.parameter_history.append(parameter_entry)

        # Trim parameter history
        if len(self.parameter_history) > 100:
            self.parameter_history = self.parameter_history[-100:]

        # Save updated history
        self._save_performance_history()

        logger.info(
            f"Updated performance metrics for {volatility_regime.name} regime: "
            f"Win Rate={win_rate:.2f}, Avg Return={avg_return:.2f}%, Sharpe={sharpe_ratio:.2f}"
        )

    def optimize_parameters(
        self, volatility_regime: VolatilityRegime, force_update: bool = False
    ) -> None:
        """
        Optimize parameters for the given volatility regime based on historical performance.

        Args:
            volatility_regime: Volatility regime to optimize for
            force_update: Whether to force an update even if recently updated
        """
        # Check if enough time has passed since last adaptation
        now = datetime.datetime.now()
        if not force_update and self.last_adaptation_time is not None:
            time_since_adaptation = now - self.last_adaptation_time
            if time_since_adaptation < self.adaptation_frequency:
                logger.info(
                    f"Skipping parameter optimization, last adaptation was {time_since_adaptation} ago"
                )
                return

        # Check if we have enough performance history
        if len(self.performance_history[volatility_regime]) < 5:
            logger.info(
                f"Not enough performance history for {volatility_regime.name} regime to optimize parameters"
            )
            return

        logger.info(
            f"Optimizing parameters for {volatility_regime.name} volatility regime"
        )

        # Get current parameters for this regime
        current_params = self.optimized_parameters[volatility_regime]

        # Extract recent performance entries
        recent_entries = self.performance_history[volatility_regime][
            -min(20, len(self.performance_history[volatility_regime])) :
        ]

        # Group by parameters and calculate average performance
        parameter_performance = {}

        for entry in recent_entries:
            # Create a key based on key parameters
            param_key = (
                entry["parameters"].get("lookback_periods"),
                entry["parameters"].get("prediction_horizon"),
                entry["parameters"].get("confidence_threshold"),
            )

            # Skip if any parameter is missing
            if None in param_key:
                continue

            # Initialize if needed
            if param_key not in parameter_performance:
                parameter_performance[param_key] = {
                    "win_rates": [],
                    "avg_returns": [],
                    "sharpe_ratios": [],
                    "count": 0,
                }

            # Add performance metrics
            parameter_performance[param_key]["win_rates"].append(entry["win_rate"])
            parameter_performance[param_key]["avg_returns"].append(entry["avg_return"])
            parameter_performance[param_key]["sharpe_ratios"].append(
                entry["sharpe_ratio"]
            )
            parameter_performance[param_key]["count"] += 1

        # Find best performing parameters
        best_param_key = None
        best_performance = -float("inf")

        for param_key, perf in parameter_performance.items():
            # Only consider parameter sets with enough samples
            if perf["count"] < 3:
                continue

            # Calculate average performance metrics
            avg_win_rate = np.mean(perf["win_rates"])
            avg_return = np.mean(perf["avg_returns"])
            avg_sharpe = np.mean(perf["sharpe_ratios"])

            # Combined performance score (weighted sum)
            # Higher weight on win rate for HIGH and EXTREME regimes
            if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                performance_score = (
                    (0.6 * avg_win_rate)
                    + (0.3 * avg_sharpe)
                    + (0.1 * (avg_return / 5.0))
                )
            else:
                performance_score = (
                    (0.4 * avg_win_rate)
                    + (0.4 * avg_sharpe)
                    + (0.2 * (avg_return / 5.0))
                )

            if performance_score > best_performance:
                best_performance = performance_score
                best_param_key = param_key

        # Update parameters if we found a better set
        if best_param_key is not None:
            lookback, horizon, threshold = best_param_key

            # Update parameters with adaptation_speed factor for smooth transitions
            self.optimized_parameters[volatility_regime]["lookback_periods"] = int(
                (1 - self.adaptation_speed * self.stability_factor)
                * current_params["lookback_periods"]
                + self.adaptation_speed * self.stability_factor * lookback
            )

            self.optimized_parameters[volatility_regime]["prediction_horizon"] = int(
                (1 - self.adaptation_speed * self.stability_factor)
                * current_params["prediction_horizon"]
                + self.adaptation_speed * self.stability_factor * horizon
            )

            self.optimized_parameters[volatility_regime]["confidence_threshold"] = (
                1 - self.adaptation_speed * self.stability_factor
            ) * current_params[
                "confidence_threshold"
            ] + self.adaptation_speed * self.stability_factor * threshold

            logger.info(
                f"Updated parameters for {volatility_regime.name} regime: "
                f"Lookback={self.optimized_parameters[volatility_regime]['lookback_periods']}, "
                f"Horizon={self.optimized_parameters[volatility_regime]['prediction_horizon']}, "
                f"Threshold={self.optimized_parameters[volatility_regime]['confidence_threshold']:.2f}"
            )
        else:
            logger.info(
                f"No optimal parameter set found for {volatility_regime.name} regime, keeping current parameters"
            )

        # Update adaptation timestamp
        self.last_adaptation_time = now

    def get_optimized_parameters(
        self,
        data: pd.DataFrame,
        vix_data: Optional[pd.DataFrame] = None,
        circuit_breaker_status: Optional[CircuitBreakerStatus] = None,
    ) -> Dict[str, Any]:
        """
        Get optimized parameters for the current market conditions.

        Args:
            data: Market data for volatility detection
            vix_data: Optional VIX data
            circuit_breaker_status: Optional circuit breaker status

        Returns:
            Dictionary of optimized parameters
        """
        # Detect market conditions
        volatility_regime, market_condition, volatility_value = (
            self.detect_market_condition(data, vix_data)
        )

        # Optimize parameters for this regime if online learning is enabled
        if self.enable_online_learning:
            self.optimize_parameters(volatility_regime)

        # Get base parameters for this regime
        base_params = self.optimized_parameters[volatility_regime].copy()

        # Adapt parameters based on current market conditions
        lookback_periods = self.adapt_lookback_period(
            volatility_regime, market_condition
        )
        prediction_horizon = self.adapt_prediction_horizon(
            volatility_regime, market_condition
        )
        confidence_threshold = self.adapt_confidence_threshold(
            volatility_regime, market_condition
        )
        model_weights = self.adapt_model_weights(volatility_regime, market_condition)
        position_sizing = self.get_recommended_position_sizing(
            volatility_regime, market_condition, circuit_breaker_status
        )

        # Create final parameter set
        optimized_params = {
            "lookback_periods": lookback_periods,
            "prediction_horizon": prediction_horizon,
            "confidence_threshold": confidence_threshold,
            "model_weights": model_weights,
            "position_sizing": position_sizing,
            "regime_info": {
                "volatility_regime": volatility_regime.name,
                "market_condition": market_condition.value,
                "volatility_value": volatility_value,
                "timestamp": datetime.datetime.now().isoformat(),
            },
        }

        # Log the optimized parameters
        logger.info(
            f"Optimized parameters for {volatility_regime.name}/{market_condition.value}: "
            f"Lookback={lookback_periods}, Horizon={prediction_horizon}, "
            f"Threshold={confidence_threshold:.2f}, Position={position_sizing:.2f}"
        )

        return optimized_params

    def backtest_parameter_optimization(
        self,
        historical_data: pd.DataFrame,
        performance_evaluator: callable,
        initial_parameters: Dict[str, Any],
        parameter_ranges: Dict[str, Dict[str, Any]],
        iterations: int = 10,
    ) -> Dict[str, Any]:
        """
        Backtest parameter optimization to find optimal parameters.

        Args:
            historical_data: Historical market data
            performance_evaluator: Function that evaluates performance given parameters
            initial_parameters: Starting parameter set
            parameter_ranges: Ranges for each parameter to explore
            iterations: Number of optimization iterations

        Returns:
            Dictionary of optimized parameters
        """
        logger.info("Running parameter optimization backtesting")

        # Start with initial parameters
        best_parameters = initial_parameters.copy()
        best_performance = performance_evaluator(historical_data, best_parameters)

        logger.info(f"Initial performance: {best_performance}")

        # Gradient-based optimization
        for iteration in range(iterations):
            improved = False

            # Try adjusting each parameter
            for param_name, param_range in parameter_ranges.items():
                # Skip parameters not in our initial set
                if param_name not in best_parameters:
                    continue

                # Get current value
                current_value = best_parameters[param_name]

                # Try increasing and decreasing
                for direction in [-1, 1]:
                    # Calculate step size based on parameter type
                    if isinstance(current_value, int):
                        step = param_range.get("step", 1)
                    elif isinstance(current_value, float):
                        step = param_range.get("step", 0.05)
                    else:
                        # Skip non-numeric parameters
                        continue

                    # Apply change
                    test_parameters = best_parameters.copy()
                    test_parameters[param_name] = current_value + (direction * step)

                    # Ensure parameter stays within range
                    min_value = param_range.get("min")
                    max_value = param_range.get("max")

                    if min_value is not None:
                        test_parameters[param_name] = max(
                            min_value, test_parameters[param_name]
                        )
                    if max_value is not None:
                        test_parameters[param_name] = min(
                            max_value, test_parameters[param_name]
                        )

                    # Skip if no change
                    if test_parameters[param_name] == current_value:
                        continue

                    # Evaluate performance
                    performance = performance_evaluator(
                        historical_data, test_parameters
                    )

                    # Update if better
                    if performance > best_performance:
                        best_parameters = test_parameters
                        best_performance = performance
                        improved = True
                        logger.info(
                            f"Iteration {iteration+1}: Improved performance to {best_performance} "
                            f"by changing {param_name} to {test_parameters[param_name]}"
                        )

            # Stop if no improvement in this iteration
            if not improved:
                logger.info(
                    f"No improvement in iteration {iteration+1}, stopping early"
                )
                break

        logger.info(f"Optimization complete. Final performance: {best_performance}")
        logger.info(f"Optimized parameters: {best_parameters}")

        return best_parameters
