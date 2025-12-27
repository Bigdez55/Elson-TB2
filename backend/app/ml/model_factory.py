"""
ML Model Factory

Provides a unified interface for creating and using ML models.
Automatically selects the best available model based on environment.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

from app.ml.config import MLConfig, get_ml_config, MLBackend

logger = logging.getLogger(__name__)


class BasePredictor(ABC):
    """Abstract base class for all predictors"""

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BasePredictor":
        """Train the model"""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        pass

    @abstractmethod
    def predict_with_confidence(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with confidence intervals (mean, lower, upper)"""
        pass


class SklearnPredictor(BasePredictor):
    """Scikit-learn based predictor (always available)"""

    def __init__(self, model_type: str = "random_forest"):
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler

        self.model_type = model_type
        self.scaler = StandardScaler()
        self.model = None

        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100, max_depth=5, random_state=42
            )
        elif model_type == "linear":
            self.model = LinearRegression()
        else:
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
            )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnPredictor":
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_with_confidence(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)

        # For tree-based models, get predictions from all estimators
        if hasattr(self.model, "estimators_"):
            all_preds = np.array([
                tree.predict(X_scaled) for tree in self.model.estimators_
            ])
            lower = np.percentile(all_preds, 10, axis=0)
            upper = np.percentile(all_preds, 90, axis=0)
        else:
            # For non-ensemble models, use a simple uncertainty estimate
            std = np.std(predictions) * 0.1
            lower = predictions - 2 * std
            upper = predictions + 2 * std

        return predictions, lower, upper


class LSTMPredictor(BasePredictor):
    """TensorFlow LSTM-based predictor for time series"""

    def __init__(
        self,
        sequence_length: int = 30,
        lstm_units: List[int] = [64, 32],
        dense_units: List[int] = [16],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
    ):
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self._is_fitted = False

        # Check if TensorFlow is available
        try:
            import tensorflow as tf
            from sklearn.preprocessing import MinMaxScaler
            self.tf = tf
            self.scaler = MinMaxScaler()
        except ImportError:
            raise ImportError("TensorFlow is required for LSTMPredictor")

    def _build_model(self, input_shape: Tuple[int, int]):
        """Build the LSTM model"""
        from tensorflow.keras import layers, models, optimizers

        model = models.Sequential()

        # Add LSTM layers
        for i, units in enumerate(self.lstm_units):
            return_sequences = i < len(self.lstm_units) - 1
            if i == 0:
                model.add(layers.LSTM(
                    units,
                    return_sequences=return_sequences,
                    input_shape=input_shape
                ))
            else:
                model.add(layers.LSTM(units, return_sequences=return_sequences))
            model.add(layers.Dropout(self.dropout_rate))

        # Add dense layers
        for units in self.dense_units:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(self.dropout_rate))

        # Output layer
        model.add(layers.Dense(1))

        # Compile
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )

        return model

    def _create_sequences(
        self, X: np.ndarray, y: np.ndarray = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences for LSTM input"""
        sequences = []
        targets = []

        for i in range(len(X) - self.sequence_length):
            sequences.append(X[i:i + self.sequence_length])
            if y is not None:
                targets.append(y[i + self.sequence_length])

        X_seq = np.array(sequences)
        y_seq = np.array(targets) if y is not None else None

        return X_seq, y_seq

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 0
    ) -> "LSTMPredictor":
        # Scale the data
        X_scaled = self.scaler.fit_transform(X)

        # Create sequences
        X_seq, y_seq = self._create_sequences(X_scaled, y)

        if X_seq.shape[0] < 10:
            raise ValueError("Insufficient data for LSTM training")

        # Build model
        input_shape = (X_seq.shape[1], X_seq.shape[2])
        self.model = self._build_model(input_shape)

        # Train with early stopping
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.0001
            )
        ]

        self.model.fit(
            X_seq, y_seq,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=verbose
        )

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self._is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_seq, _ = self._create_sequences(X_scaled)

        predictions = self.model.predict(X_seq, verbose=0)
        return predictions.flatten()

    def predict_with_confidence(
        self, X: np.ndarray, n_samples: int = 100
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Use Monte Carlo dropout for uncertainty estimation"""
        if not self._is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_seq, _ = self._create_sequences(X_scaled)

        # Monte Carlo predictions with dropout
        predictions = []
        for _ in range(n_samples):
            pred = self.model(X_seq, training=True)  # Enable dropout
            predictions.append(pred.numpy().flatten())

        predictions = np.array(predictions)
        mean_pred = np.mean(predictions, axis=0)
        lower = np.percentile(predictions, 10, axis=0)
        upper = np.percentile(predictions, 90, axis=0)

        return mean_pred, lower, upper


class CNNPredictor(BasePredictor):
    """TensorFlow CNN-based predictor for pattern recognition"""

    def __init__(
        self,
        sequence_length: int = 30,
        filters: List[int] = [32, 64],
        kernel_sizes: List[int] = [3, 3],
        dense_units: List[int] = [64, 32],
        dropout_rate: float = 0.3,
        learning_rate: float = 0.001,
    ):
        self.sequence_length = sequence_length
        self.filters = filters
        self.kernel_sizes = kernel_sizes
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self._is_fitted = False

        try:
            import tensorflow as tf
            from sklearn.preprocessing import MinMaxScaler
            self.tf = tf
            self.scaler = MinMaxScaler()
        except ImportError:
            raise ImportError("TensorFlow is required for CNNPredictor")

    def _build_model(self, input_shape: Tuple[int, int]):
        """Build the CNN model"""
        from tensorflow.keras import layers, models, optimizers

        model = models.Sequential()

        # Add Conv1D layers
        for i, (filters, kernel_size) in enumerate(zip(self.filters, self.kernel_sizes)):
            if i == 0:
                model.add(layers.Conv1D(
                    filters, kernel_size,
                    activation='relu',
                    padding='same',
                    input_shape=input_shape
                ))
            else:
                model.add(layers.Conv1D(
                    filters, kernel_size,
                    activation='relu',
                    padding='same'
                ))
            model.add(layers.MaxPooling1D(2))
            model.add(layers.Dropout(self.dropout_rate))

        model.add(layers.Flatten())

        # Dense layers
        for units in self.dense_units:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(self.dropout_rate))

        model.add(layers.Dense(1))

        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )

        return model

    def _create_sequences(
        self, X: np.ndarray, y: np.ndarray = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences for CNN input"""
        sequences = []
        targets = []

        for i in range(len(X) - self.sequence_length):
            sequences.append(X[i:i + self.sequence_length])
            if y is not None:
                targets.append(y[i + self.sequence_length])

        X_seq = np.array(sequences)
        y_seq = np.array(targets) if y is not None else None

        return X_seq, y_seq

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 0
    ) -> "CNNPredictor":
        X_scaled = self.scaler.fit_transform(X)
        X_seq, y_seq = self._create_sequences(X_scaled, y)

        if X_seq.shape[0] < 10:
            raise ValueError("Insufficient data for CNN training")

        input_shape = (X_seq.shape[1], X_seq.shape[2])
        self.model = self._build_model(input_shape)

        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001)
        ]

        self.model.fit(
            X_seq, y_seq,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=verbose
        )

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self._is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_seq, _ = self._create_sequences(X_scaled)
        predictions = self.model.predict(X_seq, verbose=0)
        return predictions.flatten()

    def predict_with_confidence(
        self, X: np.ndarray, n_samples: int = 100
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self._is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        X_seq, _ = self._create_sequences(X_scaled)

        predictions = []
        for _ in range(n_samples):
            pred = self.model(X_seq, training=True)
            predictions.append(pred.numpy().flatten())

        predictions = np.array(predictions)
        mean_pred = np.mean(predictions, axis=0)
        lower = np.percentile(predictions, 10, axis=0)
        upper = np.percentile(predictions, 90, axis=0)

        return mean_pred, lower, upper


class EnsemblePredictor(BasePredictor):
    """Ensemble of multiple predictors"""

    def __init__(self, predictors: List[BasePredictor], weights: List[float] = None):
        self.predictors = predictors
        self.weights = weights or [1.0 / len(predictors)] * len(predictors)
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EnsemblePredictor":
        for predictor in self.predictors:
            predictor.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        predictions = []
        for predictor, weight in zip(self.predictors, self.weights):
            try:
                pred = predictor.predict(X)
                predictions.append(pred * weight)
            except Exception as e:
                logger.warning(f"Predictor {type(predictor).__name__} failed: {e}")

        if not predictions:
            raise ValueError("All predictors failed")

        return np.sum(predictions, axis=0)

    def predict_with_confidence(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        all_predictions = []

        for predictor in self.predictors:
            try:
                mean, lower, upper = predictor.predict_with_confidence(X)
                all_predictions.append(mean)
            except Exception as e:
                logger.warning(f"Predictor {type(predictor).__name__} failed: {e}")

        if not all_predictions:
            raise ValueError("All predictors failed")

        all_predictions = np.array(all_predictions)
        mean_pred = np.average(all_predictions, axis=0, weights=self.weights)
        lower = np.percentile(all_predictions, 10, axis=0)
        upper = np.percentile(all_predictions, 90, axis=0)

        return mean_pred, lower, upper


class MLModelFactory:
    """
    Factory for creating ML models based on configuration and availability.

    This factory automatically selects the best available model type
    based on the current environment and available libraries.
    """

    def __init__(self, config: MLConfig = None):
        self.config = config or get_ml_config()
        self._model_cache: Dict[str, BasePredictor] = {}

    def create_price_predictor(
        self,
        model_type: str = "auto",
        use_ensemble: bool = False,
        **kwargs
    ) -> BasePredictor:
        """
        Create a price prediction model.

        Args:
            model_type: Type of model ("auto", "lstm", "cnn", "sklearn", "ensemble")
            use_ensemble: Whether to create an ensemble of models
            **kwargs: Additional model parameters

        Returns:
            A predictor instance
        """
        if use_ensemble:
            return self._create_ensemble_predictor(**kwargs)

        if model_type == "auto":
            model_type = self._select_best_model_type()

        if model_type == "lstm" and self.config.lstm_enabled:
            return LSTMPredictor(**kwargs)
        elif model_type == "cnn" and self.config.cnn_enabled:
            return CNNPredictor(**kwargs)
        else:
            # Fallback to sklearn
            sklearn_type = kwargs.get("sklearn_model", "random_forest")
            return SklearnPredictor(model_type=sklearn_type)

    def create_volatility_predictor(self, **kwargs) -> BasePredictor:
        """Create a volatility prediction model"""
        # Use sklearn for volatility as it's generally sufficient
        return SklearnPredictor(model_type="gradient_boosting")

    def create_sentiment_analyzer(self, **kwargs):
        """Create a sentiment analysis model"""
        if self.config.can_use_transformers():
            return self._create_transformer_sentiment_analyzer(**kwargs)
        else:
            return self._create_simple_sentiment_analyzer(**kwargs)

    def create_quantum_classifier(self, **kwargs):
        """Create a quantum ML classifier"""
        if self.config.can_use_quantum():
            return self._create_qiskit_classifier(**kwargs)
        else:
            # Fallback to classical classifier
            logger.warning("Quantum not available, using classical classifier")
            return self._create_classical_classifier(**kwargs)

    def _select_best_model_type(self) -> str:
        """Select the best available model type"""
        if self.config.lstm_enabled:
            return "lstm"
        elif self.config.cnn_enabled:
            return "cnn"
        else:
            return "sklearn"

    def _create_ensemble_predictor(self, **kwargs) -> EnsemblePredictor:
        """Create an ensemble of available predictors"""
        predictors = []
        weights = []

        # Always add sklearn as baseline
        predictors.append(SklearnPredictor(model_type="random_forest"))
        weights.append(0.3)

        # Add deep learning models if available
        if self.config.lstm_enabled:
            try:
                predictors.append(LSTMPredictor(**kwargs))
                weights.append(0.4)
            except Exception as e:
                logger.warning(f"Could not create LSTM predictor: {e}")

        if self.config.cnn_enabled:
            try:
                predictors.append(CNNPredictor(**kwargs))
                weights.append(0.3)
            except Exception as e:
                logger.warning(f"Could not create CNN predictor: {e}")

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        return EnsemblePredictor(predictors, weights)

    def _create_transformer_sentiment_analyzer(self, **kwargs):
        """Create a transformer-based sentiment analyzer"""
        try:
            from transformers import pipeline

            model_name = kwargs.get(
                "model_name",
                self.config.sentiment_model
            )

            analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=-1  # CPU
            )

            return TransformerSentimentWrapper(analyzer)

        except Exception as e:
            logger.error(f"Failed to create transformer sentiment analyzer: {e}")
            return self._create_simple_sentiment_analyzer(**kwargs)

    def _create_simple_sentiment_analyzer(self, **kwargs):
        """Create a simple sentiment analyzer using VADER/TextBlob"""
        return SimpleSentimentAnalyzer()

    def _create_qiskit_classifier(self, **kwargs):
        """Create a Qiskit-based quantum classifier"""
        try:
            from app.ml.quantum import QuantumClassifier
            return QuantumClassifier(
                n_qubits=kwargs.get("n_qubits", self.config.num_qubits),
                backend=self.config.quantum_backend
            )
        except Exception as e:
            logger.error(f"Failed to create quantum classifier: {e}")
            return self._create_classical_classifier(**kwargs)

    def _create_classical_classifier(self, **kwargs):
        """Create a classical classifier as fallback"""
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        return {
            "environment": self.config.environment.value,
            "available_models": {
                "price_prediction": {
                    "lstm": self.config.lstm_enabled,
                    "cnn": self.config.cnn_enabled,
                    "sklearn": True,
                },
                "sentiment_analysis": {
                    "transformer": self.config.can_use_transformers(),
                    "simple": True,
                },
                "quantum_ml": {
                    "enabled": self.config.can_use_quantum(),
                },
                "reinforcement_learning": {
                    "enabled": self.config.can_use_rl(),
                },
            },
            "preferred_backend": self.config.get_preferred_backend().value,
            "gpu_available": self.config.use_gpu,
        }


class TransformerSentimentWrapper:
    """Wrapper for HuggingFace sentiment pipeline"""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def analyze(self, text: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """Analyze sentiment of text(s)"""
        if isinstance(text, str):
            text = [text]

        results = self.pipeline(text)

        formatted = []
        for result in results:
            label = result['label'].lower()
            score = result['score']

            # Normalize to -1 to 1 scale
            sentiment_score = score if 'positive' in label else -score

            formatted.append({
                'sentiment': 'positive' if sentiment_score > 0 else 'negative',
                'score': sentiment_score,
                'confidence': abs(score)
            })

        return formatted


class SimpleSentimentAnalyzer:
    """Simple sentiment analyzer using VADER or TextBlob"""

    def __init__(self):
        self._analyzer = None
        self._init_analyzer()

    def _init_analyzer(self):
        """Initialize the sentiment analyzer"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._analyzer = SentimentIntensityAnalyzer()
            self._analyzer_type = "vader"
        except ImportError:
            try:
                from textblob import TextBlob
                self._analyzer_type = "textblob"
            except ImportError:
                self._analyzer_type = "simple"
                logger.warning("No sentiment library available, using simple word matching")

    def analyze(self, text: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """Analyze sentiment of text(s)"""
        if isinstance(text, str):
            text = [text]

        results = []
        for t in text:
            if self._analyzer_type == "vader":
                scores = self._analyzer.polarity_scores(t)
                compound = scores['compound']
                results.append({
                    'sentiment': 'positive' if compound > 0 else 'negative',
                    'score': compound,
                    'confidence': abs(compound)
                })
            elif self._analyzer_type == "textblob":
                from textblob import TextBlob
                blob = TextBlob(t)
                polarity = blob.sentiment.polarity
                results.append({
                    'sentiment': 'positive' if polarity > 0 else 'negative',
                    'score': polarity,
                    'confidence': abs(polarity)
                })
            else:
                # Simple word matching fallback
                positive_words = ['good', 'great', 'excellent', 'up', 'gain', 'profit']
                negative_words = ['bad', 'terrible', 'down', 'loss', 'decline', 'crash']

                text_lower = t.lower()
                pos_count = sum(1 for w in positive_words if w in text_lower)
                neg_count = sum(1 for w in negative_words if w in text_lower)

                if pos_count > neg_count:
                    score = pos_count / (pos_count + neg_count + 1)
                elif neg_count > pos_count:
                    score = -neg_count / (pos_count + neg_count + 1)
                else:
                    score = 0

                results.append({
                    'sentiment': 'positive' if score > 0 else 'negative',
                    'score': score,
                    'confidence': abs(score)
                })

        return results
