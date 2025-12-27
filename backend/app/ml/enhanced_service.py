"""
Enhanced Neural Network Service

Provides a unified interface for all ML capabilities including:
- Deep learning (LSTM, CNN) for price prediction
- Transformer-based sentiment analysis
- Quantum ML classification
- Ensemble methods
- Reinforcement learning integration

Automatically selects the best available models based on environment.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.ml.config import get_ml_config, MLConfig
from app.ml.model_factory import (
    MLModelFactory,
    BasePredictor,
    SklearnPredictor,
    EnsemblePredictor
)
from app.ml.sentiment import get_sentiment_analyzer, SentimentResult
from app.ml.quantum import get_quantum_classifier

logger = logging.getLogger(__name__)


class EnhancedNeuralNetworkService:
    """
    Enhanced ML service with deep learning, NLP, and quantum capabilities.

    This service automatically detects the environment and uses the best
    available models (deep learning on GCP, lightweight on Vercel).
    """

    def __init__(self, db: Session = None):
        self.db = db
        self.config = get_ml_config()
        self.factory = MLModelFactory(self.config)

        # Model caches
        self._price_predictors: Dict[str, BasePredictor] = {}
        self._volatility_predictors: Dict[str, BasePredictor] = {}
        self._sentiment_analyzer = None
        self._quantum_classifier = None

        # Feature engineering settings
        self.default_features = [
            'open', 'high', 'low', 'close', 'volume',
            'sma_10', 'sma_20', 'sma_50',
            'rsi', 'macd', 'macd_signal',
            'bb_upper', 'bb_lower', 'bb_middle',
            'volatility', 'returns'
        ]

        logger.info(f"EnhancedNeuralNetworkService initialized: {self.config.environment.value}")

    @property
    def sentiment_analyzer(self):
        """Lazy-load sentiment analyzer"""
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = get_sentiment_analyzer(financial=True)
        return self._sentiment_analyzer

    async def train_price_prediction_model(
        self,
        symbol: str,
        training_data: pd.DataFrame,
        features: Optional[List[str]] = None,
        target: str = "close",
        model_type: str = "auto",
        use_ensemble: bool = False,
        epochs: int = 50,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train a price prediction model with automatic model selection.

        Args:
            symbol: Stock symbol
            training_data: DataFrame with OHLCV and features
            features: Feature columns (uses defaults if None)
            target: Target column
            model_type: "auto", "lstm", "cnn", "sklearn", or "ensemble"
            use_ensemble: Whether to use ensemble of models
            epochs: Training epochs (for deep learning)
            validation_split: Validation split ratio

        Returns:
            Training results and metrics
        """
        try:
            features = features or self._get_available_features(training_data)

            # Prepare data
            X, y = self._prepare_training_data(training_data, features, target)

            if len(X) < 100:
                return {
                    "success": False,
                    "error": "Insufficient training data (need at least 100 samples)"
                }

            # Create predictor
            predictor = self.factory.create_price_predictor(
                model_type=model_type,
                use_ensemble=use_ensemble
            )

            # Train
            start_time = datetime.now()

            if hasattr(predictor, 'fit') and callable(predictor.fit):
                # Check if it's a deep learning model
                if model_type in ["lstm", "cnn"] or (
                    model_type == "auto" and self.config.can_use_deep_learning()
                ):
                    predictor.fit(X, y, epochs=epochs, validation_split=validation_split)
                else:
                    predictor.fit(X, y)

            training_time = (datetime.now() - start_time).total_seconds()

            # Store predictor
            model_key = f"{symbol}_{model_type}_price"
            self._price_predictors[model_key] = predictor

            # Calculate metrics on validation set
            split_idx = int(len(X) * (1 - validation_split))
            X_val, y_val = X[split_idx:], y[split_idx:]

            predictions = predictor.predict(X_val)

            # Handle sequence output for deep learning models
            if len(predictions) < len(y_val):
                y_val = y_val[-len(predictions):]

            mae = np.mean(np.abs(predictions - y_val))
            rmse = np.sqrt(np.mean((predictions - y_val) ** 2))

            # Get confidence intervals if available
            try:
                mean_pred, lower, upper = predictor.predict_with_confidence(X_val)
                confidence_coverage = np.mean(
                    (y_val[-len(mean_pred):] >= lower) &
                    (y_val[-len(mean_pred):] <= upper)
                )
            except Exception:
                confidence_coverage = None

            return {
                "success": True,
                "model_key": model_key,
                "model_type": type(predictor).__name__,
                "metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "training_samples": len(X),
                    "validation_samples": len(X_val),
                    "training_time_seconds": training_time,
                    "confidence_coverage": confidence_coverage
                },
                "features": features,
                "environment": self.config.environment.value,
                "deep_learning_used": model_type in ["lstm", "cnn"] or isinstance(
                    predictor, (type(None),)  # Placeholder for actual DL types
                )
            }

        except Exception as e:
            logger.error(f"Error training model for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    async def predict_price(
        self,
        symbol: str,
        features: pd.DataFrame,
        model_type: str = "auto",
        with_confidence: bool = True,
        forecast_horizon: int = 1
    ) -> Dict[str, Any]:
        """
        Predict price using trained model.

        Args:
            symbol: Stock symbol
            features: Feature DataFrame
            model_type: Model type to use
            with_confidence: Include confidence intervals
            forecast_horizon: Number of periods to forecast

        Returns:
            Prediction results with optional confidence intervals
        """
        try:
            model_key = f"{symbol}_{model_type}_price"

            if model_key not in self._price_predictors:
                # Try fallback
                for key in self._price_predictors:
                    if key.startswith(f"{symbol}_"):
                        model_key = key
                        break
                else:
                    return {"success": False, "error": f"No model found for {symbol}"}

            predictor = self._price_predictors[model_key]
            X = features.values if isinstance(features, pd.DataFrame) else features

            if with_confidence:
                mean_pred, lower, upper = predictor.predict_with_confidence(X)
                return {
                    "success": True,
                    "prediction": float(mean_pred[-1]) if len(mean_pred) > 0 else None,
                    "predictions": mean_pred.tolist() if forecast_horizon > 1 else None,
                    "confidence": {
                        "lower": float(lower[-1]) if len(lower) > 0 else None,
                        "upper": float(upper[-1]) if len(upper) > 0 else None,
                        "lower_all": lower.tolist() if forecast_horizon > 1 else None,
                        "upper_all": upper.tolist() if forecast_horizon > 1 else None
                    },
                    "model_key": model_key,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                predictions = predictor.predict(X)
                return {
                    "success": True,
                    "prediction": float(predictions[-1]) if len(predictions) > 0 else None,
                    "predictions": predictions.tolist() if forecast_horizon > 1 else None,
                    "model_key": model_key,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_sentiment(
        self,
        texts: Union[str, List[str]],
        aggregate: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of texts using best available NLP model.

        Args:
            texts: Single text or list of texts
            aggregate: Whether to return aggregated metrics

        Returns:
            Sentiment analysis results
        """
        try:
            if isinstance(texts, str):
                texts = [texts]

            results = self.sentiment_analyzer.analyze(texts)

            response = {
                "success": True,
                "results": [r.to_dict() for r in results],
                "count": len(results),
                "analyzer_type": type(self.sentiment_analyzer).__name__
            }

            if aggregate and len(results) > 1:
                scores = [r.score for r in results]
                confidences = [r.confidence for r in results]

                response["aggregate"] = {
                    "mean_score": float(np.mean(scores)),
                    "std_score": float(np.std(scores)),
                    "mean_confidence": float(np.mean(confidences)),
                    "bullish_ratio": sum(1 for s in scores if s > 0.1) / len(scores),
                    "bearish_ratio": sum(1 for s in scores if s < -0.1) / len(scores),
                    "overall_sentiment": "bullish" if np.mean(scores) > 0.1 else (
                        "bearish" if np.mean(scores) < -0.1 else "neutral"
                    )
                }

            return response

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"success": False, "error": str(e)}

    async def classify_market_regime(
        self,
        features: pd.DataFrame,
        use_quantum: bool = True
    ) -> Dict[str, Any]:
        """
        Classify market regime using quantum or classical classifier.

        Args:
            features: Market features DataFrame
            use_quantum: Whether to try quantum classifier

        Returns:
            Classification results
        """
        try:
            # Get or create classifier
            if self._quantum_classifier is None:
                self._quantum_classifier = get_quantum_classifier(
                    n_qubits=4,
                    use_quantum=use_quantum and self.config.can_use_quantum(),
                    fallback_to_inspired=True
                )

            X = features.values if isinstance(features, pd.DataFrame) else features

            # Make prediction
            prediction = self._quantum_classifier.predict(X)
            probabilities = self._quantum_classifier.predict_proba(X)

            # Map to regime labels
            regime_labels = ["bullish", "bearish", "neutral", "volatile"]
            predicted_regime = regime_labels[int(prediction[-1]) % len(regime_labels)]

            return {
                "success": True,
                "regime": predicted_regime,
                "confidence": float(np.max(probabilities[-1])),
                "probabilities": {
                    label: float(prob)
                    for label, prob in zip(regime_labels, probabilities[-1])
                },
                "classifier_info": self._quantum_classifier.get_info()
                if hasattr(self._quantum_classifier, 'get_info') else None
            }

        except Exception as e:
            logger.error(f"Error classifying market regime: {e}")
            return {"success": False, "error": str(e)}

    async def get_trading_signals(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        include_sentiment: bool = True,
        news_texts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trading signals using all available ML models.

        Args:
            symbol: Stock symbol
            market_data: OHLCV data with features
            include_sentiment: Include sentiment analysis
            news_texts: Optional news for sentiment

        Returns:
            Trading signals with confidence scores
        """
        try:
            signals = {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "signals": {}
            }

            # Price prediction signal
            if f"{symbol}_auto_price" in self._price_predictors:
                features = self._get_available_features(market_data)
                X = market_data[features].iloc[-30:].values

                pred_result = await self.predict_price(symbol, X, with_confidence=True)
                if pred_result["success"]:
                    current_price = market_data['close'].iloc[-1]
                    predicted_price = pred_result["prediction"]
                    change_pct = (predicted_price - current_price) / current_price

                    signals["signals"]["price_prediction"] = {
                        "signal": "buy" if change_pct > 0.02 else (
                            "sell" if change_pct < -0.02 else "hold"
                        ),
                        "predicted_change": float(change_pct),
                        "confidence": float(pred_result.get("confidence", {}).get(
                            "coverage", 0.5
                        ))
                    }

            # Sentiment signal
            if include_sentiment and news_texts:
                sentiment_result = await self.analyze_sentiment(news_texts)
                if sentiment_result["success"]:
                    agg = sentiment_result.get("aggregate", {})
                    mean_score = agg.get("mean_score", 0)

                    signals["signals"]["sentiment"] = {
                        "signal": "buy" if mean_score > 0.3 else (
                            "sell" if mean_score < -0.3 else "hold"
                        ),
                        "score": mean_score,
                        "confidence": agg.get("mean_confidence", 0.5)
                    }

            # Market regime signal
            regime_result = await self.classify_market_regime(
                market_data[self._get_available_features(market_data)].iloc[-10:]
            )
            if regime_result["success"]:
                regime = regime_result["regime"]
                signals["signals"]["market_regime"] = {
                    "regime": regime,
                    "signal": "buy" if regime == "bullish" else (
                        "sell" if regime == "bearish" else "hold"
                    ),
                    "confidence": regime_result["confidence"]
                }

            # Calculate overall signal
            buy_signals = sum(
                1 for s in signals["signals"].values()
                if s.get("signal") == "buy"
            )
            sell_signals = sum(
                1 for s in signals["signals"].values()
                if s.get("signal") == "sell"
            )
            total_signals = len(signals["signals"])

            if total_signals > 0:
                if buy_signals > sell_signals:
                    overall = "buy"
                    strength = buy_signals / total_signals
                elif sell_signals > buy_signals:
                    overall = "sell"
                    strength = sell_signals / total_signals
                else:
                    overall = "hold"
                    strength = 0.5
            else:
                overall = "hold"
                strength = 0.0

            signals["overall"] = {
                "signal": overall,
                "strength": float(strength),
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "total_signals": total_signals
            }

            return {"success": True, **signals}

        except Exception as e:
            logger.error(f"Error generating trading signals for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the ML service capabilities"""
        return {
            "environment": self.config.environment.value,
            "capabilities": self.factory.get_model_info(),
            "loaded_models": {
                "price_predictors": list(self._price_predictors.keys()),
                "volatility_predictors": list(self._volatility_predictors.keys()),
                "sentiment_analyzer": type(self._sentiment_analyzer).__name__
                if self._sentiment_analyzer else None,
                "quantum_classifier": "loaded" if self._quantum_classifier else None
            },
            "config": self.config.to_dict()
        }

    def _get_available_features(self, data: pd.DataFrame) -> List[str]:
        """Get list of available features from data"""
        available = []
        for feature in self.default_features:
            if feature in data.columns:
                available.append(feature)

        # Ensure we have at least some features
        if not available:
            available = [col for col in data.columns if col not in ['date', 'datetime', 'timestamp']]

        return available

    def _prepare_training_data(
        self,
        data: pd.DataFrame,
        features: List[str],
        target: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training"""
        # Handle missing values
        data = data.dropna(subset=features + [target])

        X = data[features].values
        y = data[target].values

        return X, y

    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to data"""
        df = data.copy()

        # Simple Moving Averages
        for window in [10, 20, 50]:
            df[f'sma_{window}'] = df['close'].rolling(window=window).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

        # Volatility and returns
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()

        return df


# Convenience function to get the service
def get_enhanced_ml_service(db: Session = None) -> EnhancedNeuralNetworkService:
    """Get an instance of the enhanced ML service"""
    return EnhancedNeuralNetworkService(db=db)
