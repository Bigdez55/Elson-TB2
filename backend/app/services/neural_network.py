"""
Neural Network Service
Provides neural network functionality for trading AI models
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class NeuralNetworkService:
    """
    Neural Network and ML service for trading applications
    """

    def __init__(self, db: Session):
        self.db = db
        self.models = {}
        self.scalers = {}

    async def train_price_prediction_model(
        self,
        symbol: str,
        training_data: pd.DataFrame,
        features: List[str],
        target: str = "close",
        model_type: str = "random_forest",
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Train a price prediction model for a given symbol

        Args:
            symbol: Stock symbol
            training_data: DataFrame with training data
            features: List of feature column names
            target: Target variable column name
            model_type: Type of model ('random_forest', 'linear', 'ensemble')
            test_size: Proportion of data to use for testing

        Returns:
            Dictionary with training results and model metrics
        """
        try:
            # Prepare data
            X = training_data[features].dropna()
            y = training_data[target].loc[X.index]

            if len(X) < 50:
                logger.warning(f"Insufficient data for training model for {symbol}")
                return {"success": False, "error": "Insufficient training data"}

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            if model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
                )
            elif model_type == "linear":
                model = LinearRegression()
            else:
                # Default to random forest
                model = RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
                )

            model.fit(X_train_scaled, y_train)

            # Make predictions
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)

            # Calculate metrics
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

            # Store model and scaler
            model_key = f"{symbol}_{model_type}_price"
            self.models[model_key] = model
            self.scalers[model_key] = scaler

            # Feature importance (if available)
            feature_importance = {}
            if hasattr(model, "feature_importances_"):
                feature_importance = dict(zip(features, model.feature_importances_))

            return {
                "success": True,
                "model_key": model_key,
                "metrics": {
                    "train_mae": train_mae,
                    "test_mae": test_mae,
                    "train_rmse": train_rmse,
                    "test_rmse": test_rmse,
                    "train_samples": len(X_train),
                    "test_samples": len(X_test),
                },
                "feature_importance": feature_importance,
                "features": features,
                "model_type": model_type,
            }

        except Exception as e:
            logger.error(f"Error training model for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def predict_price(
        self,
        symbol: str,
        features: pd.DataFrame,
        model_type: str = "random_forest",
        confidence_interval: bool = True,
    ) -> Dict[str, Any]:
        """
        Predict price using trained model

        Args:
            symbol: Stock symbol
            features: DataFrame with feature values
            model_type: Type of model to use
            confidence_interval: Whether to calculate confidence intervals

        Returns:
            Dictionary with predictions and confidence metrics
        """
        try:
            model_key = f"{symbol}_{model_type}_price"

            if model_key not in self.models:
                return {"success": False, "error": f"Model not found: {model_key}"}

            model = self.models[model_key]
            scaler = self.scalers[model_key]

            # Scale features
            features_scaled = scaler.transform(features)

            # Make prediction
            prediction = model.predict(features_scaled)

            result = {
                "success": True,
                "prediction": (
                    prediction.tolist() if len(prediction) > 1 else prediction[0]
                ),
                "model_key": model_key,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add confidence interval for tree-based models
            if confidence_interval and hasattr(model, "estimators_"):
                predictions_all = np.array(
                    [tree.predict(features_scaled) for tree in model.estimators_]
                )

                # Calculate percentiles
                lower_bound = np.percentile(predictions_all, 5, axis=0)
                upper_bound = np.percentile(predictions_all, 95, axis=0)
                std_dev = np.std(predictions_all, axis=0)

                result["confidence"] = {
                    "lower_bound": (
                        lower_bound.tolist() if len(lower_bound) > 1 else lower_bound[0]
                    ),
                    "upper_bound": (
                        upper_bound.tolist() if len(upper_bound) > 1 else upper_bound[0]
                    ),
                    "std_dev": std_dev.tolist() if len(std_dev) > 1 else std_dev[0],
                }

            return result

        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def train_volatility_model(
        self, symbol: str, training_data: pd.DataFrame, lookback_window: int = 20
    ) -> Dict[str, Any]:
        """
        Train a volatility prediction model

        Args:
            symbol: Stock symbol
            training_data: DataFrame with price data
            lookback_window: Number of periods to look back for volatility calculation

        Returns:
            Dictionary with training results
        """
        try:
            # Calculate returns and volatility
            training_data = training_data.copy()
            training_data["returns"] = training_data["close"].pct_change()
            training_data["volatility"] = (
                training_data["returns"].rolling(window=lookback_window).std()
            )

            # Create features for volatility prediction
            features = []
            for lag in range(1, 6):  # Use 5 lags
                training_data[f"vol_lag_{lag}"] = training_data["volatility"].shift(lag)
                training_data[f"return_lag_{lag}"] = training_data["returns"].shift(lag)
                features.extend([f"vol_lag_{lag}", f"return_lag_{lag}"])

            # Add volume-based features if available
            if "volume" in training_data.columns:
                training_data["volume_change"] = training_data["volume"].pct_change()
                training_data["volume_ma"] = (
                    training_data["volume"].rolling(window=20).mean()
                )
                training_data["volume_ratio"] = (
                    training_data["volume"] / training_data["volume_ma"]
                )
                features.extend(["volume_change", "volume_ratio"])

            # Remove NaN values
            training_data = training_data.dropna()

            if len(training_data) < 100:
                return {
                    "success": False,
                    "error": "Insufficient data for volatility model",
                }

            # Train model similar to price prediction
            result = await self.train_price_prediction_model(
                f"{symbol}_vol",
                training_data,
                features,
                "volatility",
                "random_forest",
                0.2,
            )

            return result

        except Exception as e:
            logger.error(f"Error training volatility model for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def calculate_market_timing_signal(
        self,
        market_data: pd.DataFrame,
        features: List[str],
        signal_strength_threshold: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Calculate market timing signals using ML models

        Args:
            market_data: DataFrame with market data and features
            features: List of feature column names
            signal_strength_threshold: Minimum strength for signal generation

        Returns:
            Dictionary with market timing signals
        """
        try:
            # Simple signal generation based on feature analysis
            signals = {}

            # Calculate feature-based signals
            for feature in features:
                if feature in market_data.columns:
                    recent_values = market_data[feature].tail(5)
                    if len(recent_values) >= 2:
                        trend = recent_values.iloc[-1] - recent_values.iloc[-2]
                        signals[f"{feature}_trend"] = trend

            # Aggregate signals into overall market timing
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0

            for signal_name, signal_value in signals.items():
                if abs(signal_value) > signal_strength_threshold:
                    total_signals += 1
                    if signal_value > 0:
                        bullish_signals += 1
                    else:
                        bearish_signals += 1

            # Determine overall signal
            if total_signals == 0:
                signal_type = "hold"
                strength = 0.0
            else:
                bullish_ratio = bullish_signals / total_signals
                bearish_ratio = bearish_signals / total_signals

                if bullish_ratio > 0.6:
                    signal_type = "buy"
                    strength = bullish_ratio
                elif bearish_ratio > 0.6:
                    signal_type = "sell"
                    strength = bearish_ratio
                else:
                    signal_type = "hold"
                    strength = 0.5

            return {
                "signal_type": signal_type,
                "strength": strength,
                "confidence": min(strength, 1.0),
                "individual_signals": signals,
                "bullish_count": bullish_signals,
                "bearish_count": bearish_signals,
                "total_count": total_signals,
            }

        except Exception as e:
            logger.error(f"Error calculating market timing signal: {str(e)}")
            return {
                "signal_type": "hold",
                "strength": 0.0,
                "confidence": 0.0,
                "error": str(e),
            }

    async def get_model_performance(
        self, symbol: str, model_type: str = "random_forest"
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a trained model

        Args:
            symbol: Stock symbol
            model_type: Type of model

        Returns:
            Dictionary with model performance metrics
        """
        model_key = f"{symbol}_{model_type}_price"

        if model_key not in self.models:
            return {"success": False, "error": f"Model not found: {model_key}"}

        # For now, return basic model info
        # In a full implementation, this would include detailed performance tracking
        return {
            "success": True,
            "model_key": model_key,
            "model_type": model_type,
            "symbol": symbol,
            "status": "trained",
            "last_updated": datetime.utcnow().isoformat(),
        }

    def list_available_models(self) -> List[str]:
        """List all available trained models"""
        return list(self.models.keys())

    async def ensemble_predict(
        self,
        symbol: str,
        features: pd.DataFrame,
        model_types: List[str] = ["random_forest", "linear"],
    ) -> Dict[str, Any]:
        """
        Make ensemble predictions using multiple models

        Args:
            symbol: Stock symbol
            features: Feature DataFrame
            model_types: List of model types to ensemble

        Returns:
            Dictionary with ensemble prediction
        """
        predictions = []
        weights = []

        for model_type in model_types:
            result = await self.predict_price(symbol, features, model_type, False)
            if result["success"]:
                predictions.append(result["prediction"])
                weights.append(1.0)  # Equal weighting for now

        if not predictions:
            return {"success": False, "error": "No models available for ensemble"}

        # Calculate weighted average
        ensemble_prediction = np.average(predictions, weights=weights)

        return {
            "success": True,
            "prediction": ensemble_prediction,
            "individual_predictions": predictions,
            "model_types": model_types,
            "ensemble_method": "weighted_average",
        }
