"""
Model combiner module for ensemble prediction.
Combines multiple model predictions using various methods like voting, stacking, etc.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    VotingClassifier,
    VotingRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression

logger = logging.getLogger(__name__)


class ModelCombiner:
    """
    Base class for model combiners
    """

    def __init__(self, name: str = "base_model_combiner"):
        self.name = name
        self.models = []
        self.weights = []

    def add_model(self, model: Any, weight: float = 1.0) -> None:
        """
        Add a model to the ensemble

        Args:
            model: Model instance
            weight: Weight for this model
        """
        self.models.append(model)
        self.weights.append(weight)

    def combine(self, predictions: List[np.ndarray]) -> np.ndarray:
        """
        Combine predictions from multiple models

        Args:
            predictions: List of model predictions

        Returns:
            Combined prediction
        """
        raise NotImplementedError("Subclasses must implement combine method")


class ClassificationEnsemble(ModelCombiner):
    """
    Ensemble for classification models
    """

    def __init__(
        self, method: str = "weighted_voting", name: str = "classification_ensemble"
    ):
        """
        Initialize the classification ensemble

        Args:
            method: Combination method ("weighted_voting", "probability_mean", "stacking")
            name: Name of the ensemble
        """
        super().__init__(name=name)
        self.method = method
        self.meta_model = None

    def combine(
        self,
        predictions: List[np.ndarray],
        probabilities: Optional[List[np.ndarray]] = None,
    ) -> np.ndarray:
        """
        Combine predictions from multiple classification models

        Args:
            predictions: List of model predictions (class indices)
            probabilities: List of model probabilities (optional)

        Returns:
            Combined prediction
        """
        if not self.models:
            raise ValueError("No models in the ensemble")

        if len(predictions) != len(self.models):
            raise ValueError(
                f"Number of predictions ({len(predictions)}) "
                f"doesn't match number of models ({len(self.models)})"
            )

        if self.method == "weighted_voting":
            # Weighted majority voting
            unique_classes = np.unique(np.concatenate(predictions))
            vote_counts = np.zeros((predictions[0].shape[0], len(unique_classes)))

            for i, pred in enumerate(predictions):
                weight = self.weights[i]
                for j, cls in enumerate(unique_classes):
                    vote_counts[:, j] += weight * (pred == cls)

            # Return the class with the highest weighted vote count
            return unique_classes[np.argmax(vote_counts, axis=1)]

        elif self.method == "probability_mean":
            # Average of class probabilities
            if probabilities is None:
                raise ValueError("Probability averaging requires model probabilities")

            if len(probabilities) != len(self.models):
                raise ValueError(
                    f"Number of probability arrays ({len(probabilities)}) "
                    f"doesn't match number of models ({len(self.models)})"
                )

            # Calculate weighted average of probabilities
            avg_proba = np.zeros_like(probabilities[0])
            weight_sum = sum(self.weights)

            for i, proba in enumerate(probabilities):
                avg_proba += self.weights[i] * proba

            avg_proba /= weight_sum

            # Return the class with the highest probability
            return np.argmax(avg_proba, axis=1)

        elif self.method == "stacking":
            # Stacking requires a meta-model to be trained
            if self.meta_model is None:
                raise ValueError("Stacking method requires a trained meta-model")

            # Use the meta-model to make predictions
            if isinstance(self.meta_model, (VotingClassifier, VotingRegressor)):
                # For voting ensembles, we need to restructure the input
                return self.meta_model.predict(np.column_stack(predictions))
            else:
                # For other meta-models
                return self.meta_model.predict(np.column_stack(predictions))

        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def fit_meta_model(
        self, X_meta: np.ndarray, y_meta: np.ndarray, meta_model: Optional[Any] = None
    ) -> None:
        """
        Fit the meta-model for stacking

        Args:
            X_meta: Meta-features (predictions from base models)
            y_meta: Target labels
            meta_model: Meta-model instance (default: LogisticRegression)
        """
        if self.method != "stacking":
            logger.warning(f"Fitting meta-model for non-stacking method: {self.method}")

        if meta_model is None:
            # Default meta-model for classification
            meta_model = LogisticRegression(max_iter=1000)

        self.meta_model = meta_model
        self.meta_model.fit(X_meta, y_meta)

        logger.info(f"Meta-model fitted with shape: {X_meta.shape}")


class RegressionEnsemble(ModelCombiner):
    """
    Ensemble for regression models
    """

    def __init__(
        self, method: str = "weighted_average", name: str = "regression_ensemble"
    ):
        """
        Initialize the regression ensemble

        Args:
            method: Combination method ("weighted_average", "median", "stacking")
            name: Name of the ensemble
        """
        super().__init__(name=name)
        self.method = method
        self.meta_model = None

    def combine(
        self,
        predictions: List[np.ndarray],
        confidence_intervals: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Combine predictions from multiple regression models

        Args:
            predictions: List of model predictions
            confidence_intervals: List of tuples with (lower, upper) bounds

        Returns:
            Combined prediction, or tuple of (prediction, lower, upper) if confidence_intervals is provided
        """
        if not self.models:
            raise ValueError("No models in the ensemble")

        if len(predictions) != len(self.models):
            raise ValueError(
                f"Number of predictions ({len(predictions)}) "
                f"doesn't match number of models ({len(self.models)})"
            )

        if self.method == "weighted_average":
            # Weighted average of predictions
            combined = np.zeros_like(predictions[0])
            weight_sum = sum(self.weights)

            for i, pred in enumerate(predictions):
                combined += self.weights[i] * pred

            combined /= weight_sum

            # Handle confidence intervals if provided
            if confidence_intervals is not None:
                # Combine lower and upper bounds using the same weights
                lower = np.zeros_like(predictions[0])
                upper = np.zeros_like(predictions[0])

                for i, (low, high) in enumerate(confidence_intervals):
                    lower += self.weights[i] * low
                    upper += self.weights[i] * high

                lower /= weight_sum
                upper /= weight_sum

                return combined, lower, upper

            return combined

        elif self.method == "median":
            # Median of predictions
            combined = np.median(np.array(predictions), axis=0)

            # Handle confidence intervals if provided
            if confidence_intervals is not None:
                lower = np.median(
                    np.array([low for low, _ in confidence_intervals]), axis=0
                )
                upper = np.median(
                    np.array([high for _, high in confidence_intervals]), axis=0
                )

                return combined, lower, upper

            return combined

        elif self.method == "stacking":
            # Stacking requires a meta-model to be trained
            if self.meta_model is None:
                raise ValueError("Stacking method requires a trained meta-model")

            # Use the meta-model to make predictions
            if isinstance(self.meta_model, (VotingClassifier, VotingRegressor)):
                # For voting ensembles, we need to restructure the input
                combined = self.meta_model.predict(np.column_stack(predictions))
            else:
                # For other meta-models
                combined = self.meta_model.predict(np.column_stack(predictions))

            # For stacking, we don't have a standard way to combine confidence intervals
            # We could potentially fit a separate meta-model for variance prediction
            if confidence_intervals is not None:
                logger.warning(
                    "Confidence intervals are not supported with stacking method"
                )

            return combined

        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def fit_meta_model(
        self, X_meta: np.ndarray, y_meta: np.ndarray, meta_model: Optional[Any] = None
    ) -> None:
        """
        Fit the meta-model for stacking

        Args:
            X_meta: Meta-features (predictions from base models)
            y_meta: Target values
            meta_model: Meta-model instance (default: LinearRegression)
        """
        if self.method != "stacking":
            logger.warning(f"Fitting meta-model for non-stacking method: {self.method}")

        if meta_model is None:
            # Default meta-model for regression
            meta_model = LinearRegression()

        self.meta_model = meta_model
        self.meta_model.fit(X_meta, y_meta)

        logger.info(f"Meta-model fitted with shape: {X_meta.shape}")


class DynamicWeightEnsemble(ModelCombiner):
    """
    Ensemble with dynamically adjusted weights based on recent performance
    """

    def __init__(
        self,
        is_classification: bool = False,
        window_size: int = 20,
        decay_factor: float = 0.95,
        name: str = "dynamic_weight_ensemble",
    ):
        """
        Initialize the dynamic weight ensemble

        Args:
            is_classification: Whether this is a classification ensemble
            window_size: Window size for performance tracking
            decay_factor: Decay factor for older performance
            name: Name of the ensemble
        """
        super().__init__(name=name)
        self.is_classification = is_classification
        self.window_size = window_size
        self.decay_factor = decay_factor
        self.performance_history = []
        self.dynamic_weights = []

    def update_weights(
        self,
        predictions: List[np.ndarray],
        true_values: np.ndarray,
        performance_metric: Optional[Callable] = None,
    ) -> None:
        """
        Update model weights based on recent performance

        Args:
            predictions: List of model predictions
            true_values: True target values
            performance_metric: Function to calculate performance
        """
        if not self.models:
            raise ValueError("No models in the ensemble")

        if len(predictions) != len(self.models):
            raise ValueError(
                f"Number of predictions ({len(predictions)}) "
                f"doesn't match number of models ({len(self.models)})"
            )

        # Default performance metrics
        if performance_metric is None:
            if self.is_classification:
                # Accuracy for classification
                performance_metric = lambda y_true, y_pred: np.mean(y_true == y_pred)
            else:
                # Negative MSE for regression
                performance_metric = lambda y_true, y_pred: -np.mean(
                    (y_true - y_pred) ** 2
                )

        # Calculate performance for each model
        model_performances = []
        for i, pred in enumerate(predictions):
            perf = performance_metric(true_values, pred)
            model_performances.append(perf)

        # Update performance history
        self.performance_history.append(model_performances)

        # Keep only the most recent window_size performances
        if len(self.performance_history) > self.window_size:
            self.performance_history = self.performance_history[-self.window_size :]

        # Calculate dynamic weights based on recent performance
        dynamic_weights = np.zeros(len(self.models))

        for i, performances in enumerate(self.performance_history):
            # Apply decay factor (older performances have less influence)
            age = len(self.performance_history) - i - 1
            decay = self.decay_factor**age

            for j, perf in enumerate(performances):
                # Skip negative performances for weighting
                if perf > 0:
                    dynamic_weights[j] += perf * decay

        # Normalize weights to sum to 1
        weight_sum = np.sum(dynamic_weights)
        if weight_sum > 0:
            dynamic_weights = dynamic_weights / weight_sum
        else:
            # Fallback to equal weights if all performances are negative
            dynamic_weights = np.ones(len(self.models)) / len(self.models)

        self.dynamic_weights = dynamic_weights

        logger.info(f"Updated dynamic weights: {dynamic_weights}")

    def combine(
        self, predictions: List[np.ndarray], use_dynamic_weights: bool = True
    ) -> np.ndarray:
        """
        Combine predictions using dynamic weights

        Args:
            predictions: List of model predictions
            use_dynamic_weights: Whether to use dynamic weights

        Returns:
            Combined prediction
        """
        if not self.models:
            raise ValueError("No models in the ensemble")

        if len(predictions) != len(self.models):
            raise ValueError(
                f"Number of predictions ({len(predictions)}) "
                f"doesn't match number of models ({len(self.models)})"
            )

        # Use dynamic weights if available, otherwise use static weights
        weights = (
            self.dynamic_weights
            if use_dynamic_weights and len(self.dynamic_weights) == len(self.models)
            else self.weights
        )

        if len(weights) != len(self.models):
            # Fallback to equal weights
            weights = np.ones(len(self.models)) / len(self.models)

        # Weighted combination of predictions
        combined = np.zeros_like(predictions[0])
        weight_sum = sum(weights)

        for i, pred in enumerate(predictions):
            combined += weights[i] * pred

        combined /= weight_sum

        if self.is_classification:
            # For classification, return the class with the highest probability
            return np.argmax(combined, axis=1) if combined.ndim > 1 else combined
        else:
            # For regression, return the weighted average
            return combined


class RangePredictionEnsemble(ModelCombiner):
    """
    Ensemble for range-based predictions
    """

    def __init__(
        self, method: str = "weighted_average", name: str = "range_prediction_ensemble"
    ):
        """
        Initialize the range prediction ensemble

        Args:
            method: Combination method ("weighted_average", "envelope", "quantile")
            name: Name of the ensemble
        """
        super().__init__(name=name)
        self.method = method

    def combine(
        self, predictions: List[Dict[str, np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """
        Combine range-based predictions from multiple models

        Args:
            predictions: List of dictionaries, each with 'mean', 'lower', 'upper' keys

        Returns:
            Dictionary with combined 'mean', 'lower', 'upper' predictions
        """
        if not self.models:
            raise ValueError("No models in the ensemble")

        if len(predictions) != len(self.models):
            raise ValueError(
                f"Number of predictions ({len(predictions)}) "
                f"doesn't match number of models ({len(self.models)})"
            )

        # Extract mean, lower, and upper predictions
        mean_preds = [pred["mean"] for pred in predictions]
        lower_preds = [pred["lower"] for pred in predictions if "lower" in pred]
        upper_preds = [pred["upper"] for pred in predictions if "upper" in pred]

        # Check if all models provide confidence intervals
        has_intervals = len(lower_preds) == len(self.models) and len(
            upper_preds
        ) == len(self.models)

        if self.method == "weighted_average":
            # Weighted average of predictions
            mean_combined = np.zeros_like(mean_preds[0])
            weight_sum = sum(self.weights)

            for i, pred in enumerate(mean_preds):
                mean_combined += self.weights[i] * pred

            mean_combined /= weight_sum

            # Combine intervals if available
            result = {"mean": mean_combined}

            if has_intervals:
                lower_combined = np.zeros_like(lower_preds[0])
                upper_combined = np.zeros_like(upper_preds[0])

                for i in range(len(lower_preds)):
                    lower_combined += self.weights[i] * lower_preds[i]
                    upper_combined += self.weights[i] * upper_preds[i]

                lower_combined /= weight_sum
                upper_combined /= weight_sum

                result["lower"] = lower_combined
                result["upper"] = upper_combined

            return result

        elif self.method == "envelope":
            # Weighted average for mean, min/max for bounds
            mean_combined = np.zeros_like(mean_preds[0])
            weight_sum = sum(self.weights)

            for i, pred in enumerate(mean_preds):
                mean_combined += self.weights[i] * pred

            mean_combined /= weight_sum

            # Combine intervals using outer envelope
            result = {"mean": mean_combined}

            if has_intervals:
                lower_combined = np.min(np.array(lower_preds), axis=0)
                upper_combined = np.max(np.array(upper_preds), axis=0)

                result["lower"] = lower_combined
                result["upper"] = upper_combined

            return result

        elif self.method == "quantile":
            # Weighted quantiles for mean and bounds
            # Stack predictions with repeats based on weights
            weight_sum = sum(self.weights)
            normalized_weights = [w / weight_sum for w in self.weights]

            # Use 1000 as a multiplier for weights
            rep_counts = [max(1, int(w * 1000)) for w in normalized_weights]

            # Repeat predictions based on weights
            mean_stacked = np.concatenate(
                [
                    np.repeat(pred.reshape(-1, 1), count, axis=1)
                    for pred, count in zip(mean_preds, rep_counts)
                ],
                axis=1,
            )

            # Compute the median (50th percentile) for the mean prediction
            mean_combined = np.median(mean_stacked, axis=1)

            # Combine intervals using quantiles
            result = {"mean": mean_combined}

            if has_intervals:
                lower_stacked = np.concatenate(
                    [
                        np.repeat(pred.reshape(-1, 1), count, axis=1)
                        for pred, count in zip(lower_preds, rep_counts)
                    ],
                    axis=1,
                )

                upper_stacked = np.concatenate(
                    [
                        np.repeat(pred.reshape(-1, 1), count, axis=1)
                        for pred, count in zip(upper_preds, rep_counts)
                    ],
                    axis=1,
                )

                # Use 10th percentile for lower bound and 90th percentile for upper bound
                lower_combined = np.percentile(lower_stacked, 10, axis=1)
                upper_combined = np.percentile(upper_stacked, 90, axis=1)

                result["lower"] = lower_combined
                result["upper"] = upper_combined

            return result

        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def plot_ensemble_prediction(
        self,
        predictions: List[Dict[str, np.ndarray]],
        combined_pred: Dict[str, np.ndarray],
        x_values: Optional[np.ndarray] = None,
        figsize: Tuple[int, int] = (12, 6),
    ) -> plt.Figure:
        """
        Plot individual and ensemble predictions with confidence intervals

        Args:
            predictions: List of model predictions
            combined_pred: Combined prediction
            x_values: X-axis values (default: range(len(prediction)))
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Set x-values if not provided
        if x_values is None:
            x_values = np.arange(len(combined_pred["mean"]))

        # Plot individual model predictions
        for i, pred in enumerate(predictions):
            label = f"Model {i+1}" if i < len(self.models) else f"Model {i+1}"
            alpha = 0.3

            # Plot mean prediction
            ax.plot(x_values, pred["mean"], alpha=alpha, label=label)

            # Plot confidence intervals if available
            if "lower" in pred and "upper" in pred:
                ax.fill_between(x_values, pred["lower"], pred["upper"], alpha=0.1)

        # Plot ensemble prediction
        ax.plot(x_values, combined_pred["mean"], "k-", linewidth=2, label="Ensemble")

        # Plot ensemble confidence intervals if available
        if "lower" in combined_pred and "upper" in combined_pred:
            ax.fill_between(
                x_values,
                combined_pred["lower"],
                combined_pred["upper"],
                color="k",
                alpha=0.2,
                label="Ensemble CI",
            )

        # Add labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.set_title(f"Ensemble Prediction ({self.method})")
        ax.legend()

        # Add grid
        ax.grid(True, alpha=0.3)

        return fig
