# Regime-Specific Models for Elson Wealth Trading Platform

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from ..ai_model_engine.hybrid_models import (
    EnsembleVotingClassifier,
    HybridMachineLearningModel,
)
from ..ai_model_engine.quantum_models import (
    QuantumKernelClassifier,
    QuantumVariationalClassifier,
)
from .volatility_detector import VolatilityRegime

logger = logging.getLogger(__name__)


class RegimeSpecificModelSelector:
    """
    Model selector that provides appropriate model configuration
    based on the detected market volatility regime.

    This class implements the second component of Phase 2 in the
    Hybrid Model Improvement Plan, focusing on regime-specific models
    with improved transitions between different volatility regimes.
    """

    def __init__(self, enable_smooth_transitions: bool = True):
        """
        Initialize the regime-specific model selector.

        Args:
            enable_smooth_transitions: Whether to enable smooth transitions between regimes
        """
        self.models = {}
        self.trained_models = {}  # Storage for trained regime-specific models
        self.current_regime = None
        self.default_model = None
        self.previous_regime = None
        self.enable_smooth_transitions = enable_smooth_transitions

        # Model performance tracking by regime
        self.regime_performance = {
            VolatilityRegime.LOW: {"win_rate": 0.0, "samples": 0},
            VolatilityRegime.NORMAL: {"win_rate": 0.0, "samples": 0},
            VolatilityRegime.HIGH: {"win_rate": 0.0, "samples": 0},
            VolatilityRegime.EXTREME: {"win_rate": 0.0, "samples": 0},
        }

        # Enhanced transition parameters for smoother switching between regimes
        self.transition_state = {
            "in_transition": False,
            "from_regime": None,
            "to_regime": None,
            "transition_progress": 0.0,  # 0.0 to 1.0
            "transition_speed": 0.1,  # Reduced from 0.2 for more gradual transitions
            "stabilize_steps": 3,  # Number of consecutive identical regime detections before transition starts
            "current_stable_count": 0,  # Counter for stable regime detections
            "last_detected_regime": None,  # Keep track of most recently detected regime
        }

    def initialize_models(self, base_config: Dict[str, Any] = None):
        """
        Initialize regime-specific model variants.

        Args:
            base_config: Optional base configuration parameters
        """
        base_config = base_config or {}

        # Create models for each volatility regime
        for regime in VolatilityRegime:
            # Get regime-specific configuration
            regime_config = self._get_regime_config(regime, base_config)

            # Create a model for this regime
            regime_model = self._create_regime_model(regime, regime_config)

            # Store the model
            self.models[regime] = regime_model

            # Set the normal volatility model as default
            if regime == VolatilityRegime.NORMAL:
                self.default_model = regime_model

        logger.info(
            f"Initialized regime-specific models for {len(self.models)} volatility regimes"
        )

    def train_regime_specific_models(self, historical_data: pd.DataFrame):
        """
        Train separate models for each volatility regime using historical data.

        This is a key improvement for Phase 2, where we train specialized models
        for each regime rather than using a single model with different parameters.

        Args:
            historical_data: DataFrame with features and labels, must include 'volatility_regime'
        """
        if "volatility_regime" not in historical_data.columns:
            logger.error(
                "Cannot train regime-specific models: 'volatility_regime' column missing"
            )
            return

        # Group data by volatility regime
        regime_data = {}

        # Convert VolatilityRegime enum values to strings for comparison
        regime_mapping = {
            "low": VolatilityRegime.LOW,
            "normal": VolatilityRegime.NORMAL,
            "high": VolatilityRegime.HIGH,
            "extreme": VolatilityRegime.EXTREME,
        }

        # Split data by regime
        for regime_str, regime_enum in regime_mapping.items():
            regime_df = historical_data[
                historical_data["volatility_regime"] == regime_str
            ]

            if len(regime_df) == 0:
                logger.warning(f"No data available for {regime_str} volatility regime")
                continue

            regime_data[regime_enum] = regime_df
            logger.info(
                f"Extracted {len(regime_df)} samples for {regime_str} volatility regime"
            )

        # Train specialized models for each regime
        for regime, data in regime_data.items():
            if len(data) < 100:  # Minimum data requirement
                logger.warning(
                    f"Insufficient data for {regime.name} regime: {len(data)} samples"
                )
                continue

            try:
                # Get the base model configuration for this regime
                base_model = self.models.get(regime)
                if base_model is None:
                    logger.warning(f"No base model available for {regime.name} regime")
                    continue

                # Train a specialized model with optimal hyperparameters for this regime
                trained_model = self._train_specialized_model(regime, data, base_model)

                # Store the trained model
                self.trained_models[regime] = trained_model

                logger.info(
                    f"Successfully trained specialized model for {regime.name} volatility regime"
                )

            except Exception as e:
                logger.error(f"Error training model for {regime.name} regime: {str(e)}")

    def _train_specialized_model(
        self,
        regime: VolatilityRegime,
        data: pd.DataFrame,
        base_model: HybridMachineLearningModel,
    ) -> HybridMachineLearningModel:
        """
        Train a specialized model for a specific volatility regime with optimized hyperparameters.

        Args:
            regime: Volatility regime
            data: Training data for this regime
            base_model: Base model configuration

        Returns:
            Trained hybrid ML model
        """
        # Extract config from base model
        lookback = base_model.lookback_periods
        horizon = base_model.prediction_horizon
        ensemble_params = base_model.ensemble_params.copy()

        # Create a new model with the same configuration
        specialized_model = HybridMachineLearningModel(
            lookback_periods=lookback,
            prediction_horizon=horizon,
            feature_engineering_params={},  # Use defaults
            ensemble_params=ensemble_params,
        )

        # Feature selection specific to this regime
        if "return" in data.columns and "label" in data.columns:
            # Prepare features and target
            # In a real implementation, we would do more sophisticated feature selection
            # based on feature importance for each regime
            features = data.drop(
                ["return", "label", "volatility_regime"], axis=1, errors="ignore"
            )
            target = data["label"]

            # Train the specialized model on this regime's data
            specialized_model.train(features, target)

            logger.info(
                f"Trained {regime.name} model on {len(data)} samples with "
                f"{len(features.columns)} features"
            )
        else:
            logger.warning(
                f"Cannot train model for {regime.name}: missing required columns"
            )

        return specialized_model

    def update_regime_performance(
        self,
        regime: VolatilityRegime,
        new_predictions: List[bool],
        actual_outcomes: List[bool],
    ):
        """
        Update the performance metrics for a specific regime.

        Args:
            regime: Volatility regime
            new_predictions: List of predicted outcomes (True/False)
            actual_outcomes: List of actual outcomes (True/False)
        """
        if not new_predictions or not actual_outcomes:
            return

        if len(new_predictions) != len(actual_outcomes):
            logger.warning(
                f"Cannot update performance: prediction and outcome counts don't match"
            )
            return

        # Calculate correct predictions
        correct = sum(p == a for p, a in zip(new_predictions, actual_outcomes))
        total = len(new_predictions)

        # Get current performance
        current = self.regime_performance.get(regime, {"win_rate": 0.0, "samples": 0})

        # Calculate new win rate with weighted average
        current_samples = current["samples"]
        current_win_rate = current["win_rate"]

        if current_samples + total > 0:
            new_win_rate = (
                (current_win_rate * current_samples) + (correct / total * total)
            ) / (current_samples + total)
        else:
            new_win_rate = 0.0

        # Update performance metrics
        self.regime_performance[regime] = {
            "win_rate": new_win_rate,
            "samples": current_samples + total,
        }

        logger.info(
            f"Updated {regime.name} performance: Win rate {new_win_rate:.2%} ({current_samples + total} samples)"
        )

    def _get_regime_config(
        self, regime: VolatilityRegime, base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get configuration parameters for a specific volatility regime.

        Args:
            regime: Volatility regime
            base_config: Base configuration parameters

        Returns:
            Configuration dictionary for the specific regime
        """
        # Start with base configuration
        config = base_config.copy()

        # Apply regime-specific adjustments
        if regime == VolatilityRegime.LOW:
            # Low volatility: Longer prediction horizon, standard models
            config.update(
                {
                    "lookback_periods": 30,
                    "prediction_horizon": 5,
                    "ensemble_params": {
                        "voting": "soft",
                        "threshold": 0.55,
                        "weights": {
                            "random_forest": 1.0,
                            "gradient_boosting": 1.0,
                            "neural_network": 1.0,
                            "quantum_kernel": 1.2,
                            "quantum_variational": 1.2,
                        },
                    },
                }
            )

        elif regime == VolatilityRegime.NORMAL:
            # Normal volatility: Balanced approach
            config.update(
                {
                    "lookback_periods": 20,
                    "prediction_horizon": 3,
                    "ensemble_params": {
                        "voting": "soft",
                        "threshold": 0.60,
                        "weights": {
                            "random_forest": 1.1,
                            "gradient_boosting": 1.1,
                            "neural_network": 0.9,
                            "quantum_kernel": 1.0,
                            "quantum_variational": 0.9,
                        },
                    },
                }
            )

        elif regime == VolatilityRegime.HIGH:
            # High volatility: Very short prediction horizon, heavy emphasis on tree-based models
            config.update(
                {
                    "lookback_periods": 4,  # Further reduced from 8
                    "prediction_horizon": 1,
                    "ensemble_params": {
                        "voting": "soft",
                        "threshold": 0.92,  # Further increased from 0.82 for higher quality trades
                        "weights": {
                            "random_forest": 3.0,  # Further increased from 2.0
                            "gradient_boosting": 2.8,  # Further increased from 1.7
                            "neural_network": 0.0,  # Disabled (from 0.2)
                            "quantum_kernel": 0.1,  # Further reduced from 0.4
                            "quantum_variational": 0.0,  # Disabled (from 0.3)
                        },
                        "bypass_circuit_breaker": False,  # Circuit breaker active
                        "position_sizing_factor": 0.10,  # Further reduced position size
                    },
                }
            )

        elif regime == VolatilityRegime.EXTREME:
            # Extreme volatility: Minimal lookback, highest threshold, only tree-based models
            config.update(
                {
                    "lookback_periods": 2,  # Further reduced from 5
                    "prediction_horizon": 1,
                    "ensemble_params": {
                        "voting": "soft",
                        "threshold": 0.97,  # Further increased from 0.90
                        "weights": {
                            "random_forest": 4.0,  # Further increased from 2.5
                            "gradient_boosting": 3.5,  # Further increased from 2.0
                            "neural_network": 0.0,  # Disabled (from 0.1)
                            "quantum_kernel": 0.0,  # Disabled (from 0.1)
                            "quantum_variational": 0.0,  # Disabled (from 0.1)
                        },
                        "bypass_circuit_breaker": False,  # Circuit breaker active
                        "position_sizing_factor": 0.03,  # Further reduced position size from 0.10
                    },
                }
            )

        return config

    def _create_regime_model(
        self, regime: VolatilityRegime, config: Dict[str, Any]
    ) -> HybridMachineLearningModel:
        """
        Create a model optimized for the specific volatility regime.

        Args:
            regime: Volatility regime
            config: Configuration parameters

        Returns:
            Hybrid ML model configured for the specific regime
        """
        # Create hybrid model with regime-specific configuration
        model = HybridMachineLearningModel(
            lookback_periods=config.get("lookback_periods", 20),
            prediction_horizon=config.get("prediction_horizon", 3),
            feature_engineering_params=config.get("feature_engineering_params", {}),
            ensemble_params=config.get("ensemble_params", {}),
        )

        logger.info(
            f"Created model for {regime.name} volatility regime with "
            f"lookback={config.get('lookback_periods')}, "
            f"horizon={config.get('prediction_horizon')}"
        )

        return model

    def get_model_for_regime(
        self, regime: VolatilityRegime
    ) -> HybridMachineLearningModel:
        """
        Get the appropriate model for the given volatility regime.

        Args:
            regime: Detected volatility regime

        Returns:
            Hybrid ML model optimized for the regime
        """
        # Enhanced regime stabilization and transition handling
        if self.enable_smooth_transitions:
            # Check for potential regime change
            regime_changed = (
                self.current_regime != regime and self.current_regime is not None
            )

            # Stabilization logic - ensure regime is stable before transitioning
            if self.transition_state["last_detected_regime"] == regime:
                # Same regime detected consecutively
                self.transition_state["current_stable_count"] += 1
            else:
                # Different regime detected - reset counter
                self.transition_state["current_stable_count"] = 1
                self.transition_state["last_detected_regime"] = regime

            # Only handle actual regime transition after stabilization period
            if (
                regime_changed
                and self.transition_state["current_stable_count"]
                >= self.transition_state["stabilize_steps"]
            ):
                # Update regime tracking for transition
                self.previous_regime = self.current_regime
                self.current_regime = regime

                # Handle smooth transition
                return self._handle_regime_transition(self.previous_regime, regime)
            elif regime_changed:
                # Not stable enough to transition - stick with current regime model
                logger.info(
                    f"Detected potential change to {regime.name} regime, but waiting for stabilization "
                    f"({self.transition_state['current_stable_count']}/{self.transition_state['stabilize_steps']})"
                )

                # Use previous regime model
                temp_regime = self.current_regime
            else:
                # No change or already in transition
                if not self.transition_state["in_transition"]:
                    # Standard update without transition
                    self.previous_regime = self.current_regime
                    self.current_regime = regime
                    temp_regime = regime
                else:
                    # Already in transition, continue it
                    temp_regime = regime
        else:
            # Simple regime tracking without smooth transitions
            self.previous_regime = self.current_regime
            self.current_regime = regime
            temp_regime = regime

        # If not transitioning, use the appropriate model for the regime
        # First try to use a specialized trained model for the regime
        if temp_regime in self.trained_models:
            logger.info(
                f"Using trained specialized model for {temp_regime.name} volatility regime"
            )
            return self.trained_models[temp_regime]

        # If no trained model available, use the base configuration model
        if temp_regime in self.models:
            logger.info(
                f"Using configuration-based model for {temp_regime.name} volatility regime (no trained model available)"
            )
            return self.models[temp_regime]

        # Fall back to default model if not found
        logger.warning(
            f"No model available for {temp_regime.name} regime, using default model"
        )
        return self.default_model

    def _handle_regime_transition(
        self, from_regime: VolatilityRegime, to_regime: VolatilityRegime
    ) -> HybridMachineLearningModel:
        """
        Handle transitions between different volatility regimes smoothly.

        This prevents abrupt changes in model behavior when the regime changes,
        providing a more stable trading experience during regime transitions.

        Args:
            from_regime: The previous volatility regime
            to_regime: The new volatility regime

        Returns:
            A transitional model or the new regime's model
        """
        # Get the appropriate 'from' model (trained if available, otherwise base)
        from_model = self.trained_models.get(from_regime, self.models.get(from_regime))

        # Get the appropriate 'to' model (trained if available, otherwise base)
        to_model = self.trained_models.get(to_regime, self.models.get(to_regime))

        # If either regime doesn't have a model, just use the available one
        if from_model is None:
            return to_model or self.default_model
        if to_model is None:
            return from_model or self.default_model

        # Start transition if not already in one
        if not self.transition_state["in_transition"]:
            self.transition_state["in_transition"] = True
            self.transition_state["from_regime"] = from_regime
            self.transition_state["to_regime"] = to_regime
            self.transition_state["transition_progress"] = 0.0

            logger.info(
                f"Starting transition from {from_regime.name} to {to_regime.name} regime"
            )

            # Create an initial blended model with mostly 'from' regime characteristics
            return self.create_blended_model(
                from_model, to_model, blend_factor=0.1  # Start with 10% of target model
            )

        # Continue existing transition
        elif self.transition_state["in_transition"]:
            # Check if the target regime has changed
            if to_regime != self.transition_state["to_regime"]:
                # Update transition target
                previous_to_regime = self.transition_state["to_regime"]
                previous_to_model = self.trained_models.get(
                    previous_to_regime, self.models.get(previous_to_regime)
                )

                self.transition_state["from_regime"] = previous_to_regime
                self.transition_state["to_regime"] = to_regime
                self.transition_state["transition_progress"] = 0.0

                logger.info(f"Redirecting transition to {to_regime.name} regime")

                # Create a new blended model for this redirected transition
                return self.create_blended_model(
                    previous_to_model,
                    to_model,
                    blend_factor=0.1,  # Start with 10% of target model
                )

            # Update transition progress
            self.transition_state["transition_progress"] += self.transition_state[
                "transition_speed"
            ]

            # Check if transition is complete
            if self.transition_state["transition_progress"] >= 1.0:
                # Transition complete
                self.transition_state["in_transition"] = False

                logger.info(f"Completed transition to {to_regime.name} regime")

                # Return the target regime model
                return to_model

            # Create a smoothly blended model based on transition progress
            blend_factor = min(1.0, self.transition_state["transition_progress"])

            # Log transition progress
            if (
                round(blend_factor * 10) % 2 == 0
            ):  # Log every 20% progress to avoid too much logging
                logger.info(
                    f"Regime transition at {blend_factor*100:.1f}% from {from_regime.name} to {to_regime.name}"
                )

            # Get current from_regime model (which could be different from the original from_model)
            current_from_regime = self.transition_state["from_regime"]
            current_from_model = self.trained_models.get(
                current_from_regime, self.models.get(current_from_regime)
            )

            # Create properly blended model with current blend factor
            return self.create_blended_model(
                current_from_model, to_model, blend_factor=blend_factor
            )

    def get_current_regime_info(self) -> Dict[str, Any]:
        """
        Get information about the current regime and model.

        Returns:
            Dictionary with regime and model information
        """
        if self.current_regime is None:
            return {"status": "No regime detected yet"}

        # Get transition information if in transition
        transition_info = {}
        if self.enable_smooth_transitions and self.transition_state["in_transition"]:
            transition_info = {
                "in_transition": True,
                "from_regime": self.transition_state["from_regime"].name,
                "to_regime": self.transition_state["to_regime"].name,
                "transition_progress": f"{self.transition_state['transition_progress']*100:.1f}%",
            }

        current_model = self.models.get(self.current_regime)

        if current_model is None:
            info = {
                "regime": self.current_regime.name,
                "status": "No model configured for this regime",
            }
            if transition_info:
                info.update(transition_info)
            return info

        # Basic regime info
        info = {
            "regime": self.current_regime.name,
            "lookback_periods": current_model.lookback_periods,
            "prediction_horizon": current_model.prediction_horizon,
            "confidence_threshold": current_model.ensemble_params.get("threshold", 0.5),
            "position_sizing": current_model.ensemble_params.get(
                "position_sizing_factor", 1.0
            ),
        }

        # Add model weights if available
        weights = current_model.ensemble_params.get("weights")
        if weights:
            info["model_weights"] = weights

        # Add transition information if in transition
        if transition_info:
            info.update(transition_info)

        return info

    def create_blended_model(
        self,
        model1: Any,
        model2: Any,
        blend_ratio: float = 0.5,
        blend_factor: float = None,
    ) -> Any:
        """
        Create a blended model for smooth regime transitions.

        This enhanced implementation creates a more sophisticated ensemble that
        blends the actual predictions of two models, rather than just blending
        their parameters. This provides smoother transitions between volatility regimes.

        Args:
            model1: First model (could be from any regime)
            model2: Second model (could be from any regime)
            blend_ratio: Blending ratio from 0.0 (all model1) to 1.0 (all model2)

        Returns:
            A blended model object
        """
        # Ensure blend ratio is within range (handle both blend_ratio and blend_factor parameters)
        if blend_factor is not None:
            blend_ratio = blend_factor  # Support for the old parameter name
        blend_ratio = max(0.0, min(1.0, blend_ratio))

        # Create an ensemble with weighted predictions
        def blended_predict(X):
            pred1 = model1.predict(X)
            pred2 = model2.predict(X)
            # Blend predictions
            return pred1 * (1 - blend_ratio) + pred2 * blend_ratio

        # Create an ensemble with weighted probabilities
        def blended_predict_proba(X):
            proba1 = model1.predict_proba(X)
            proba2 = model2.predict_proba(X)
            # Blend probabilities
            return proba1 * (1 - blend_ratio) + proba2 * blend_ratio

        # Create blended model object
        blended_model = type("BlendedModel", (), {})()
        blended_model.predict = blended_predict
        blended_model.predict_proba = blended_predict_proba

        # Add parameter attributes for interfacing with other components
        if hasattr(model1, "lookback_periods") and hasattr(model2, "lookback_periods"):
            blended_model.lookback_periods = int(
                model1.lookback_periods * (1 - blend_ratio)
                + model2.lookback_periods * blend_ratio
            )

        if hasattr(model1, "prediction_horizon") and hasattr(
            model2, "prediction_horizon"
        ):
            blended_model.prediction_horizon = int(
                model1.prediction_horizon * (1 - blend_ratio)
                + model2.prediction_horizon * blend_ratio
            )

        # Blend ensemble parameters
        blended_model.ensemble_params = {}

        if hasattr(model1, "ensemble_params") and hasattr(model2, "ensemble_params"):
            # Get parameters from each model
            params1 = model1.ensemble_params
            params2 = model2.ensemble_params

            # Threshold blending
            threshold1 = params1.get("threshold", 0.5)
            threshold2 = params2.get("threshold", 0.5)
            blended_threshold = (
                threshold1 * (1 - blend_ratio) + threshold2 * blend_ratio
            )

            # Position sizing blending
            sizing1 = params1.get("position_sizing_factor", 1.0)
            sizing2 = params2.get("position_sizing_factor", 1.0)
            blended_sizing = sizing1 * (1 - blend_ratio) + sizing2 * blend_ratio

            # Weight blending
            blended_weights = {}
            weights1 = params1.get("weights", {})
            weights2 = params2.get("weights", {})

            # Combine all model types
            all_models = set(list(weights1.keys()) + list(weights2.keys()))

            for model_type in all_models:
                weight1 = weights1.get(model_type, 1.0)
                weight2 = weights2.get(model_type, 1.0)
                blended_weights[model_type] = (
                    weight1 * (1 - blend_ratio) + weight2 * blend_ratio
                )

            # Set final blended parameters
            blended_model.ensemble_params = {
                "voting": "soft",
                "threshold": blended_threshold,
                "weights": blended_weights,
                "position_sizing_factor": blended_sizing,
            }

        logger.info(f"Created enhanced blended model with ratio {blend_ratio:.2f}")

        return blended_model
