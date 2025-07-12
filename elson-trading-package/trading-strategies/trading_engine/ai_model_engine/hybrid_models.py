"""
Hybrid Machine Learning models combining classical and quantum approaches
to achieve 70%+ win rate in market predictions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
import os
import joblib
import json
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Import quantum models
from .quantum_models import QuantumKernelClassifier, QuantumVariationalClassifier

logger = logging.getLogger(__name__)


class EnsembleVotingClassifier:
    """
    Ensemble voting classifier that combines multiple classical and quantum models
    to make more accurate predictions.
    """
    
    def __init__(
        self,
        models: Dict[str, Any] = None,
        voting: str = 'soft',
        weights: Dict[str, float] = None,
        threshold: float = 0.5
    ):
        """
        Initialize the ensemble voting classifier
        
        Args:
            models: Dictionary of model instances with their names
            voting: Voting strategy ('hard' or 'soft')
            weights: Dictionary of model weights for weighted voting
            threshold: Decision threshold for binary classification
        """
        self.models = models or {}
        self.voting = voting
        self.weights = weights or {}
        self.threshold = threshold
        self.fitted_models = {}
        self.model_metadata = {}
        
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """
        Add a model to the ensemble
        
        Args:
            name: Name of the model
            model: Model instance
            weight: Weight of the model in the ensemble
        """
        self.models[name] = model
        self.weights[name] = weight
        
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs):
        """
        Fit all models in the ensemble
        
        Args:
            X: Training features
            y: Target values
            **kwargs: Additional arguments to pass to individual model fit methods
        
        Returns:
            Self
        """
        for name, model in self.models.items():
            logger.info(f"Fitting model: {name}")
            start_time = datetime.now()
            
            try:
                # Different models might have different fit signatures
                if hasattr(model, 'validation_split') and 'validation_split' in kwargs:
                    model.fit(X, y, validation_split=kwargs.get('validation_split', 0.2))
                else:
                    model.fit(X, y)
                
                self.fitted_models[name] = model
                
                # Store metadata
                end_time = datetime.now()
                self.model_metadata[name] = {
                    'training_time': (end_time - start_time).total_seconds(),
                    'training_samples': len(X),
                    'training_date': start_time.isoformat()
                }
                
                # Get model-specific metadata if available
                if hasattr(model, 'get_metadata'):
                    model_specific_metadata = model.get_metadata()
                    self.model_metadata[name].update(model_specific_metadata)
                    
                logger.info(f"Model {name} fitted successfully.")
            except Exception as e:
                logger.error(f"Error fitting model {name}: {str(e)}")
                # Continue with other models even if one fails
                
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the ensemble
        
        Args:
            X: Input features
            
        Returns:
            Predicted class labels
        """
        if not self.fitted_models:
            raise ValueError("No models have been fitted yet")
        
        if self.voting == 'hard':
            # Hard voting (majority vote)
            predictions = {}
            for name, model in self.fitted_models.items():
                predictions[name] = model.predict(X)
                
            # Stack predictions and take majority vote
            stacked_predictions = np.column_stack([predictions[name] for name in self.fitted_models])
            majority_votes = np.apply_along_axis(
                lambda x: np.argmax(np.bincount(x, weights=[self.weights.get(name, 1.0) for name in self.fitted_models])),
                axis=1,
                arr=stacked_predictions.astype(int)
            )
            
            return majority_votes
        
        else:  # soft voting
            # Get probabilities from each model
            probabilities = {}
            for name, model in self.fitted_models.items():
                if hasattr(model, 'predict_proba'):
                    probabilities[name] = model.predict_proba(X)
                else:
                    # Convert binary predictions to probabilities
                    preds = model.predict(X)
                    probs = np.zeros((len(X), 2))
                    probs[:, 1] = preds
                    probs[:, 0] = 1 - preds
                    probabilities[name] = probs
            
            # Combine probabilities with weights
            weighted_probas = np.zeros((X.shape[0], 2))
            for name, proba in probabilities.items():
                weight = self.weights.get(name, 1.0)
                weighted_probas += proba * weight
                
            # Normalize
            total_weight = sum(self.weights.get(name, 1.0) for name in self.fitted_models)
            weighted_probas /= total_weight
            
            # Apply threshold for binary classification
            return (weighted_probas[:, 1] >= self.threshold).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities
        
        Args:
            X: Input features
            
        Returns:
            Class probabilities
        """
        if not self.fitted_models:
            raise ValueError("No models have been fitted yet")
        
        # Get probabilities from each model
        probabilities = {}
        for name, model in self.fitted_models.items():
            if hasattr(model, 'predict_proba'):
                probabilities[name] = model.predict_proba(X)
            else:
                # Convert binary predictions to probabilities
                preds = model.predict(X)
                probs = np.zeros((len(X), 2))
                probs[:, 1] = preds
                probs[:, 0] = 1 - preds
                probabilities[name] = probs
        
        # Combine probabilities with weights
        weighted_probas = np.zeros((X.shape[0], 2))
        for name, proba in probabilities.items():
            weight = self.weights.get(name, 1.0)
            weighted_probas += proba * weight
            
        # Normalize
        total_weight = sum(self.weights.get(name, 1.0) for name in self.fitted_models)
        weighted_probas /= total_weight
        
        return weighted_probas
    
    def score(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Calculate performance metrics for the ensemble
        
        Args:
            X: Input features
            y: True labels
            
        Returns:
            Dictionary of performance metrics
        """
        y_pred = self.predict(X)
        
        # Determine if binary or multiclass
        classes = np.unique(y)
        is_binary = len(classes) == 2
        
        if is_binary:
            average = 'binary'
        else:
            average = 'weighted'
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average=average, zero_division=0),
            'recall': recall_score(y, y_pred, average=average, zero_division=0),
            'f1': f1_score(y, y_pred, average=average, zero_division=0)
        }
        
        # Individual model scores
        model_scores = {}
        for name, model in self.fitted_models.items():
            try:
                if hasattr(model, 'score') and callable(model.score):
                    if isinstance(model, (QuantumKernelClassifier, QuantumVariationalClassifier)):
                        # Quantum models return a dict of metrics
                        model_scores[name] = model.score(X, y)
                    else:
                        # Classical models typically return accuracy
                        model_scores[name] = {'accuracy': model.score(X, y)}
            except Exception as e:
                logger.error(f"Error scoring model {name}: {str(e)}")
                model_scores[name] = {'error': str(e)}
        
        metrics['model_scores'] = model_scores
        
        return metrics
    
    def save(self, filepath: str):
        """
        Save the ensemble model to disk
        
        Args:
            filepath: Path to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save classical models and metadata
        save_data = {
            'voting': self.voting,
            'weights': self.weights,
            'threshold': self.threshold,
            'model_metadata': self.model_metadata,
            'classical_models': {},
            'quantum_model_paths': {}
        }
        
        # Save each model
        for name, model in self.fitted_models.items():
            # Special handling for quantum models
            if isinstance(model, (QuantumKernelClassifier, QuantumVariationalClassifier)):
                quantum_dir = os.path.join(os.path.dirname(filepath), "quantum_models")
                os.makedirs(quantum_dir, exist_ok=True)
                quantum_path = os.path.join(quantum_dir, f"{name}.pkl")
                model.save(model_name=name, model_dir=quantum_dir)
                save_data['quantum_model_paths'][name] = quantum_path
            else:
                # Save classical models directly
                save_data['classical_models'][name] = model
        
        # Save to disk
        joblib.dump(save_data, filepath)
        logger.info(f"Ensemble model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'EnsembleVotingClassifier':
        """
        Load an ensemble model from disk
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded ensemble model
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        # Load saved data
        save_data = joblib.load(filepath)
        
        # Create new instance
        ensemble = cls(
            voting=save_data['voting'],
            weights=save_data['weights'],
            threshold=save_data['threshold']
        )
        
        # Load classical models
        ensemble.fitted_models = save_data['classical_models'].copy()
        
        # Load quantum models
        for name, path in save_data['quantum_model_paths'].items():
            try:
                if 'Kernel' in name:
                    model = QuantumKernelClassifier.load(path)
                else:
                    model = QuantumVariationalClassifier.load(path)
                ensemble.fitted_models[name] = model
            except Exception as e:
                logger.error(f"Failed to load quantum model {name}: {str(e)}")
        
        # Load metadata
        ensemble.model_metadata = save_data['model_metadata']
        
        return ensemble


class HybridMachineLearningModel:
    """
    Hybrid model combining classical ML, deep learning, and quantum ML
    to achieve 70%+ win rate in market predictions.
    """
    
    def __init__(
        self,
        lookback_periods: int = 20,
        prediction_horizon: int = 5,
        feature_engineering_params: Dict[str, Any] = None,
        ensemble_params: Dict[str, Any] = None
    ):
        """
        Initialize the hybrid ML model
        
        Args:
            lookback_periods: Number of periods to use for feature engineering
            prediction_horizon: Number of periods ahead to predict
            feature_engineering_params: Parameters for feature engineering
            ensemble_params: Parameters for the ensemble model
        """
        self.lookback_periods = lookback_periods
        self.prediction_horizon = prediction_horizon
        self.feature_engineering_params = feature_engineering_params or {}
        self.ensemble_params = ensemble_params or {}
        
        # Feature preprocessing
        self.scaler = StandardScaler()
        
        # Create ensemble model
        self.model = self._create_ensemble_model()
        
        # Track feature importance
        self.feature_importance = {}
        self.feature_names = []
        
    def _create_ensemble_model(self) -> EnsembleVotingClassifier:
        """
        Create the ensemble model with classical and quantum components
        
        Returns:
            Ensemble model
        """
        # Get parameters from ensemble_params or use defaults
        voting = self.ensemble_params.get('voting', 'soft')
        threshold = self.ensemble_params.get('threshold', 0.5)
        
        # Default weights give slightly more weight to quantum models
        default_weights = {
            'random_forest': 1.0,
            'gradient_boosting': 1.0,
            'neural_network': 1.0,
            'quantum_kernel': 1.2,
            'quantum_variational': 1.2
        }
        weights = self.ensemble_params.get('weights', default_weights)
        
        # Create ensemble
        ensemble = EnsembleVotingClassifier(voting=voting, weights=weights, threshold=threshold)
        
        # Add classical models
        if self.ensemble_params.get('use_random_forest', True):
            random_forest = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            ensemble.add_model('random_forest', random_forest, weights.get('random_forest', 1.0))
        
        if self.ensemble_params.get('use_gradient_boosting', True):
            gradient_boosting = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            ensemble.add_model('gradient_boosting', gradient_boosting, weights.get('gradient_boosting', 1.0))
        
        if self.ensemble_params.get('use_neural_network', True):
            neural_network = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size='auto',
                learning_rate='adaptive',
                learning_rate_init=0.001,
                max_iter=200,
                random_state=42
            )
            ensemble.add_model('neural_network', neural_network, weights.get('neural_network', 1.0))
        
        # Add quantum models
        if self.ensemble_params.get('use_quantum_kernel', True):
            quantum_kernel = QuantumKernelClassifier(
                n_qubits=4,
                feature_map_reps=2,
                backend_name='statevector',
                feature_selection='pca',
                regularization=1.0
            )
            ensemble.add_model('quantum_kernel', quantum_kernel, weights.get('quantum_kernel', 1.2))
        
        if self.ensemble_params.get('use_quantum_variational', True):
            quantum_variational = QuantumVariationalClassifier(
                n_qubits=4,
                feature_map_reps=2,
                variational_form_reps=2,
                backend_name='statevector',
                shots=1024,
                feature_selection='pca',
                regularization_strength=0.01
            )
            ensemble.add_model('quantum_variational', quantum_variational, weights.get('quantum_variational', 1.2))
        
        return ensemble
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from raw market data with enhanced volatility handling
        and error handling for improved robustness.
        
        Args:
            data: DataFrame with market data (OHLCV)
            
        Returns:
            DataFrame with engineered features
        """
        try:
            # Input validation
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    logger.error(f"Required column {col} not found in input data")
                    raise ValueError(f"Required column {col} not found in input data")
                
            if len(data) < self.lookback_periods:
                logger.warning(f"Input data has fewer rows ({len(data)}) than lookback periods ({self.lookback_periods}). "
                               f"Results may be unreliable.")
            
            # Check for NaN values
            if data.isna().any().any():
                logger.warning("Input data contains NaN values. These will be forward-filled.")
                data = data.ffill()
                
            # Make a copy to avoid modifying the original
            df = data.copy()
            
            # Price features
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Moving averages
            for window in [5, 10, 20, 50]:
                df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
                df[f'ema_{window}'] = df['close'].ewm(span=window, adjust=False).mean()
                
                # Relative to price
                df[f'close_to_sma_{window}'] = df['close'] / df[f'sma_{window}'].replace(0, np.nan)
                df[f'close_to_ema_{window}'] = df['close'] / df[f'ema_{window}'].replace(0, np.nan)
                
                # Volatility
                df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
                
            # Enhanced volatility features
            # This addresses one of the key limitations identified in testing
            df['volatility_ratio_5_20'] = df['volatility_5'] / df['volatility_20'].replace(0, np.nan) 
            df['volatility_ratio_10_50'] = df['volatility_10'] / df['volatility_50'].replace(0, np.nan)
            
            # Volatility regime features - help model adjust to different market conditions
            # Annualized volatility (assuming daily data)
            df['annualized_volatility'] = df['volatility_20'] * np.sqrt(252) 
            
            # Volatility regime flags - binary features to help model learn regime-specific patterns
            df['low_vol_regime'] = (df['annualized_volatility'] < 0.15).astype(int)
            df['normal_vol_regime'] = ((df['annualized_volatility'] >= 0.15) & 
                                       (df['annualized_volatility'] < 0.25)).astype(int)
            df['high_vol_regime'] = ((df['annualized_volatility'] >= 0.25) & 
                                       (df['annualized_volatility'] < 0.40)).astype(int)
            df['extreme_vol_regime'] = (df['annualized_volatility'] >= 0.40).astype(int)
            
            # Volatility trend
            df['vol_trend_10d'] = (df['volatility_10'] - df['volatility_10'].shift(10)) / df['volatility_10'].shift(10).replace(0, np.nan)
            
            # Volume features
            df['volume_change'] = df['volume'].pct_change()
            df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
            df['relative_volume'] = df['volume'] / df['volume_ma_5'].replace(0, np.nan)
            
            # Price patterns
            df['body_size'] = abs(df['close'] - df['open']) / df['open'].replace(0, np.nan)
            df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['open'].replace(0, np.nan)
            df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['open'].replace(0, np.nan)
            
            # Trend features
            df['trend_5_1'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5).replace(0, np.nan)
            df['trend_10_5'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10).replace(0, np.nan)
            df['trend_20_10'] = (df['close'] - df['close'].shift(20)) / df['close'].shift(20).replace(0, np.nan)
            
            # Calculate market regime features
            # Trend strength based on SMA relationships
            df['bull_market'] = ((df['close'] > df['sma_50']) & (df['sma_20'] > df['sma_50'])).astype(int)
            df['bear_market'] = ((df['close'] < df['sma_50']) & (df['sma_20'] < df['sma_50'])).astype(int)
            df['sideways_market'] = 1 - df['bull_market'] - df['bear_market']
            
            # Technical indicators
            try:
                # RSI
                def calculate_rsi(series, window=14):
                    delta = series.diff()
                    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
                    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
                    # Avoid division by zero
                    rs = gain / loss.replace(0, 1e-9)
                    return 100 - (100 / (1 + rs))
                
                df['rsi_14'] = calculate_rsi(df['close'], window=14)
                
                # MACD
                df['macd_line'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
                df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
                df['macd_histogram'] = df['macd_line'] - df['macd_signal']
                
                # Bollinger Bands
                df['bb_middle'] = df['close'].rolling(window=20).mean()
                bb_std = df['close'].rolling(window=20).std()
                df['bb_upper'] = df['bb_middle'] + 2 * bb_std
                df['bb_lower'] = df['bb_middle'] - 2 * bb_std
                df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'].replace(0, np.nan)
                
                # Handle division by zero in bb_relative calculation
                bb_range = df['bb_upper'] - df['bb_lower']
                df['bb_relative'] = (df['close'] - df['bb_lower']) / bb_range.replace(0, np.nan)
                
                # ATR (Average True Range)
                def calculate_atr(df, window=14):
                    high_low = df['high'] - df['low']
                    high_close = np.abs(df['high'] - df['close'].shift())
                    low_close = np.abs(df['low'] - df['close'].shift())
                    try:
                        tr = pd.concat([high_low, high_close, low_close], axis=1)
                        return tr.max(axis=1).rolling(window=window).mean()
                    except Exception as e:
                        logger.error(f"Error calculating ATR: {str(e)}")
                        # Fallback to simpler calculation if concat fails
                        return high_low.rolling(window=window).mean()
                
                df['atr_14'] = calculate_atr(df, window=14)
                df['atr_percent'] = df['atr_14'] / df['close'].replace(0, np.nan)
            
            except Exception as e:
                logger.error(f"Error calculating technical indicators: {str(e)}")
                logger.warning("Using simplified feature set due to calculation errors")
            
            # Replace infinite values with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            
            # Handle remaining NaNs
            if df.isna().any().any():
                logger.warning("Generated features contain NaN values. These will be forward-filled then backfilled.")
                df = df.ffill().bfill()
                
                # If we still have NaNs after filling, replace with zeros
                if df.isna().any().any():
                    logger.warning("NaN values persist after forward/back filling. Replacing with zeros.")
                    df.fillna(0, inplace=True)
            
            # Store feature names, excluding non-feature columns
            self.feature_names = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'date']]
            
            return df
            
        except Exception as e:
            logger.critical(f"Critical error in feature engineering: {str(e)}")
            # If all else fails, return a minimal viable feature set
            if 'df' in locals() and isinstance(df, pd.DataFrame) and len(df) > 0:
                # Create minimal features from whatever data we have
                logger.warning("Generating minimal emergency features due to error")
                df['returns'] = df['close'].pct_change().fillna(0)
                df['sma_20'] = df['close'].rolling(window=min(20, len(df))).mean().fillna(df['close'])
                df['volatility_20'] = df['returns'].rolling(window=min(20, len(df))).std().fillna(0)
                self.feature_names = ['returns', 'sma_20', 'volatility_20']
                return df[['open', 'high', 'low', 'close', 'volume'] + self.feature_names]
            else:
                # We don't even have a valid DataFrame to work with
                raise RuntimeError(f"Fatal error in feature engineering: {str(e)}")
    
    def _prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for model training/prediction with enhanced volatility awareness
        and robust error handling.
        
        Args:
            data: DataFrame with market data
            
        Returns:
            Tuple of (features, targets)
        """
        try:
            # Engineer features
            df = self._engineer_features(data)
            
            if len(df) == 0:
                raise ValueError("No data available after feature engineering")
                
            # Check for sufficient data after engineering
            if len(df) < max(self.prediction_horizon * 2, 30):
                logger.warning(f"Limited data ({len(df)} rows) available after feature engineering. "
                              f"Predictions may be unreliable.")
            
            # Create X (features)
            try:
                X = df[self.feature_names].values
            except KeyError as e:
                missing_features = [f for f in self.feature_names if f not in df.columns]
                logger.error(f"Missing features in data: {missing_features}")
                # Use only available features
                available_features = [f for f in self.feature_names if f in df.columns]
                if not available_features:
                    raise ValueError(f"No usable features available: {str(e)}")
                logger.warning(f"Proceeding with limited feature set: {available_features}")
                X = df[available_features].values
                self.feature_names = available_features
            
            # Create y (target)
            try:
                # Target is 1 if price increases by prediction_horizon periods ahead, 0 otherwise
                future_returns = df['close'].pct_change(self.prediction_horizon).shift(-self.prediction_horizon)
                
                # For data with limited points at the end (can't see full prediction_horizon ahead)
                if future_returns.isna().any():
                    logger.warning(f"Data contains {future_returns.isna().sum()} NaN values in target calculation. "
                                 f"These will be excluded from the analysis.")
                
                # Create binary target
                y = (future_returns > 0).astype(int).values
                
                # Enhanced target for higher volatility regimes
                # When annualized_volatility > 25%, adjust prediction horizon to be more conservative
                if 'annualized_volatility' in df.columns:
                    high_vol_mask = (df['annualized_volatility'] >= 0.25).values
                    if high_vol_mask.any():
                        # For high volatility periods, we might want to be more cautious with predictions
                        logger.info(f"Detected {high_vol_mask.sum()} high volatility data points")
                        
                        # Store volatility information for later use
                        self.current_volatility = df['annualized_volatility'].mean()
                        self.high_volatility_present = high_vol_mask.any()
                        
                        # Track volatility regime distribution
                        if 'low_vol_regime' in df.columns:
                            self.volatility_regime_stats = {
                                'low': df['low_vol_regime'].mean(),
                                'normal': df['normal_vol_regime'].mean() if 'normal_vol_regime' in df.columns else 0,
                                'high': df['high_vol_regime'].mean() if 'high_vol_regime' in df.columns else 0,
                                'extreme': df['extreme_vol_regime'].mean() if 'extreme_vol_regime' in df.columns else 0
                            }
                
            except Exception as e:
                logger.error(f"Error creating target variable: {str(e)}")
                if len(df) > self.prediction_horizon:
                    # Fallback to simple future returns calculation
                    logger.warning("Falling back to simple future returns calculation")
                    future_price = df['close'].shift(-self.prediction_horizon)
                    current_price = df['close']
                    future_returns = (future_price - current_price) / current_price
                    y = (future_returns > 0).astype(int).values
                else:
                    raise ValueError(f"Insufficient data for target calculation: {str(e)}")
            
            # Remove rows with NaN in the target
            valid_indices = ~np.isnan(y)
            if not valid_indices.all():
                logger.warning(f"Removing {(~valid_indices).sum()} rows with NaN targets")
                X = X[valid_indices]
                y = y[valid_indices]
            
            # Final validation
            if len(X) == 0 or len(y) == 0:
                raise ValueError("No valid data points after preparing data")
                
            if len(X) != len(y):
                raise ValueError(f"Feature and target length mismatch: X={len(X)}, y={len(y)}")
                
            # Check for NaN/inf in features
            if np.isnan(X).any() or np.isinf(X).any():
                logger.warning("NaN or Inf values detected in features. Replacing with zeros.")
                X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
                
            return X, y
            
        except Exception as e:
            logger.critical(f"Critical error preparing data: {str(e)}")
            raise RuntimeError(f"Failed to prepare data: {str(e)}")
    
    def fit(self, data: pd.DataFrame) -> 'HybridMachineLearningModel':
        """
        Fit the hybrid ML model to market data with enhanced volatility handling
        
        Args:
            data: DataFrame with market data (must have 'open', 'high', 'low', 'close', 'volume' columns)
            
        Returns:
            Self
        """
        try:
            logger.info(f"Fitting hybrid model with lookback={self.lookback_periods}, horizon={self.prediction_horizon}")
            
            # Initialize volatility tracking attributes
            self.current_volatility = None
            self.high_volatility_present = False
            self.volatility_regime_stats = {}
            
            # Prepare data
            X, y = self._prepare_data(data)
            
            if len(X) < 50:
                logger.warning(f"Training with very limited data ({len(X)} samples). Model may not perform well.")
                
            # Track class balance for potential adjustment
            class_balance = np.mean(y)
            logger.info(f"Class balance: {class_balance:.2f} (positive class proportion)")
            
            # Train test split for validation
            train_size = int(len(X) * 0.8)
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
            
            # Scale features
            try:
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_val_scaled = self.scaler.transform(X_val)
            except Exception as e:
                logger.error(f"Error scaling features: {str(e)}")
                logger.warning("Using unscaled features due to scaling error")
                X_train_scaled = X_train
                X_val_scaled = X_val
            
            # Adjust model weights based on volatility regime
            if hasattr(self, 'high_volatility_present') and self.high_volatility_present:
                logger.info("Adjusting model weights for high volatility regime")
                
                # In high volatility regimes, we might want to give more weight to models 
                # that are more stable and less prone to overfitting
                original_weights = self.model.weights.copy()
                
                # Adjust ensemble weights for high volatility
                if 'gradient_boosting' in self.model.weights:
                    self.model.weights['gradient_boosting'] *= 1.2  # GBM often handles noise well
                    
                if 'random_forest' in self.model.weights:
                    self.model.weights['random_forest'] *= 1.1  # RF is stable with noise
                
                if 'neural_network' in self.model.weights:
                    self.model.weights['neural_network'] *= 0.8  # NN can be more sensitive to noise
                    
                # Increase threshold for higher confidence requirements in volatile markets
                original_threshold = self.model.threshold
                if self.model.threshold < 0.6:
                    self.model.threshold = min(0.6, self.model.threshold + 0.1)
                    logger.info(f"Adjusted decision threshold from {original_threshold} to {self.model.threshold} for high volatility")
                
            # Fit the ensemble model
            validation_split = self.ensemble_params.get('validation_split', 0.2)
            self.model.fit(X_train_scaled, y_train, validation_split=validation_split)
            
            # Calculate and log validation metrics
            try:
                val_metrics = self.model.score(X_val_scaled, y_val)
                logger.info(f"Validation metrics: accuracy={val_metrics.get('accuracy', 'N/A'):.4f}, "
                           f"f1={val_metrics.get('f1', 'N/A'):.4f}")
                
                # Store validation metrics for future reference
                self.validation_metrics = val_metrics
                
                # Check against 70% win rate target
                win_rate = val_metrics.get('accuracy')
                if win_rate is not None:
                    if win_rate >= 0.7:
                        logger.info(f"Model achieved win rate of {win_rate:.2%}, meeting 70% target")
                        self.target_achieved = True
                    else:
                        logger.warning(f"Model win rate of {win_rate:.2%} does not meet 70% target")
                        self.target_achieved = False
            except Exception as e:
                logger.error(f"Error calculating validation metrics: {str(e)}")
            
            # Extract feature importance from models that provide it
            try:
                for name, model in self.model.fitted_models.items():
                    if name == 'random_forest' and hasattr(model, 'feature_importances_'):
                        self.feature_importance['random_forest'] = dict(zip(self.feature_names, model.feature_importances_))
                    elif name == 'gradient_boosting' and hasattr(model, 'feature_importances_'):
                        self.feature_importance['gradient_boosting'] = dict(zip(self.feature_names, model.feature_importances_))
                    elif 'quantum' in name and hasattr(model, 'encoder') and hasattr(model.encoder, 'analyze_feature_importance'):
                        self.feature_importance[name] = model.encoder.analyze_feature_importance()
                
                # Log top features
                if 'random_forest' in self.feature_importance:
                    sorted_features = sorted(self.feature_importance['random_forest'].items(), key=lambda x: x[1], reverse=True)
                    top_features = sorted_features[:5]
                    logger.info(f"Top features by importance: {top_features}")
            except Exception as e:
                logger.error(f"Error extracting feature importance: {str(e)}")
            
            return self
            
        except Exception as e:
            logger.critical(f"Critical error during model fitting: {str(e)}")
            raise RuntimeError(f"Failed to fit hybrid model: {str(e)}")
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Make predictions with the hybrid ML model with enhanced volatility handling
        
        Args:
            data: DataFrame with market data
            
        Returns:
            Dictionary with predictions, confidence, and volatility assessment
        """
        try:
            # Initialize volatility information
            current_volatility = None
            volatility_regime = "unknown"
            volatility_warning = False
            
            # Engineer features with additional volatility analysis
            df = self._engineer_features(data)
            
            # Detect current market volatility regime if available
            if 'annualized_volatility' in df.columns:
                current_volatility = df['annualized_volatility'].mean()
                
                # Determine volatility regime
                if current_volatility < 0.15:
                    volatility_regime = "low"
                elif current_volatility < 0.25:
                    volatility_regime = "normal"
                elif current_volatility < 0.40:
                    volatility_regime = "high"
                    volatility_warning = True
                else:
                    volatility_regime = "extreme"
                    volatility_warning = True
                
                logger.info(f"Current market volatility: {current_volatility:.2%} ({volatility_regime} regime)")
                
                # Apply circuit breaker for extreme volatility (known limitation)
                if volatility_regime == "extreme" and not self.ensemble_params.get('bypass_circuit_breaker', False):
                    logger.warning(f"CIRCUIT BREAKER: Extreme volatility detected ({current_volatility:.2%}). "
                                  f"Model known to perform poorly above 40% annualized volatility.")
                    
                    return {
                        'circuit_breaker_triggered': True,
                        'reason': f"Extreme volatility detected ({current_volatility:.2%})",
                        'predictions': [],
                        'volatility_assessment': {
                            'current_volatility': float(current_volatility),
                            'regime': volatility_regime,
                            'warning': True,
                            'recommendation': "Suspend trading until volatility returns to normal levels"
                        }
                    }
            
            # Extract features
            try:
                X = df[self.feature_names].values
            except KeyError as e:
                missing_features = [f for f in self.feature_names if f not in df.columns]
                logger.error(f"Missing features in prediction data: {missing_features}")
                
                # Use only available features
                available_features = [f for f in self.feature_names if f in df.columns]
                if not available_features:
                    raise ValueError(f"No usable features available: {str(e)}")
                    
                logger.warning(f"Proceeding with limited feature set: {len(available_features)} features")
                X = df[available_features].values
                
                # Feature mismatch warning
                logger.warning("Feature mismatch between training and prediction data. Results may be unreliable.")
            
            # Scale features
            try:
                X_scaled = self.scaler.transform(X)
            except Exception as e:
                logger.error(f"Error scaling features for prediction: {str(e)}")
                logger.warning("Using unscaled features due to scaling error")
                X_scaled = X
            
            # Make predictions
            try:
                y_pred = self.model.predict(X_scaled)
                probas = self.model.predict_proba(X_scaled)
            except Exception as e:
                logger.error(f"Error making predictions: {str(e)}")
                raise RuntimeError(f"Prediction failed: {str(e)}")
            
            # Calculate confidence (probability of the predicted class)
            confidence = np.max(probas, axis=1)
            
            # Adjust confidence threshold based on volatility if circuit breaker not triggered
            confidence_threshold = self.ensemble_params.get('confidence_threshold', 0.55)
            original_threshold = confidence_threshold
            
            if volatility_regime == "high":
                # Increase threshold for high volatility environments 
                confidence_threshold = max(confidence_threshold, 0.65)
                logger.info(f"Adjusted confidence threshold to {confidence_threshold} for high volatility")
                
            # Flag low confidence predictions
            low_confidence_mask = confidence < confidence_threshold
            if np.any(low_confidence_mask):
                logger.warning(f"{np.sum(low_confidence_mask)} out of {len(confidence)} predictions have "
                              f"confidence below threshold ({confidence_threshold})")
            
            # Create a more detailed output
            predictions = []
            for i in range(len(y_pred)):
                pred_direction = "UP" if y_pred[i] == 1 else "DOWN"
                conf = confidence[i]
                up_probability = probas[i, 1]
                down_probability = probas[i, 0]
                
                # Add confidence assessment
                confidence_level = "high" if conf >= 0.75 else "medium" if conf >= 0.6 else "low"
                below_threshold = conf < confidence_threshold
                
                predictions.append({
                    'direction': pred_direction,
                    'confidence': float(conf),
                    'confidence_level': confidence_level,
                    'below_threshold': bool(below_threshold),
                    'probability_up': float(up_probability),
                    'probability_down': float(down_probability)
                })
            
            # Generate result with enhanced market condition information
            result = {
                'predictions': predictions,
                'raw_predictions': y_pred.tolist(),
                'probabilities': probas.tolist(),
                'prediction_horizon': self.prediction_horizon,
                'confidence_threshold': confidence_threshold
            }
            
            # Add volatility assessment if available
            if current_volatility is not None:
                result['volatility_assessment'] = {
                    'current_volatility': float(current_volatility),
                    'regime': volatility_regime,
                    'warning': volatility_warning
                }
                
                # Add specific recommendations for high/extreme volatility
                if volatility_warning:
                    result['volatility_assessment']['recommendation'] = (
                        "Consider increased caution and position sizing adjustments due to elevated volatility"
                    )
                    
                    # Flag bear market if detected
                    if 'bear_market' in df.columns and df['bear_market'].mean() > 0.5:
                        result['volatility_assessment']['bear_market_warning'] = True
                        result['volatility_assessment']['recommendation'] += "; Possible bear market detected"
            
            return result
            
        except Exception as e:
            logger.critical(f"Critical error during prediction: {str(e)}")
            # Return error information rather than crashing
            return {
                'error': True,
                'error_message': str(e),
                'predictions': [],
                'recommendation': "Model encountered an error during prediction. Data may be incompatible with model."
            }
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Backtest the hybrid ML model on historical data
        
        Args:
            data: DataFrame with market data
            initial_capital: Initial capital for the backtest
            
        Returns:
            Dictionary with backtest results
        """
        # Prepare data
        X, y = self._prepare_data(data)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        y_pred = self.model.predict(X_scaled)
        probas = self.model.predict_proba(X_scaled)
        
        # Create a copy of the data for backtesting
        backtest_df = data.copy()
        
        # Shift predictions to align with the future periods they're predicting
        backtest_df = backtest_df.iloc[:(len(y_pred))]
        backtest_df['prediction'] = y_pred
        backtest_df['confidence'] = np.max(probas, axis=1)
        
        # Calculate future returns
        backtest_df['future_return'] = backtest_df['close'].pct_change(self.prediction_horizon).shift(-self.prediction_horizon)
        
        # Calculate cumulative performance
        backtest_df['position'] = backtest_df['prediction']
        backtest_df['strategy_return'] = backtest_df['position'] * backtest_df['future_return']
        
        # Drop NaN values
        backtest_df = backtest_df.dropna()
        
        # Calculate cumulative returns
        backtest_df['cumulative_market_return'] = (1 + backtest_df['future_return']).cumprod() - 1
        backtest_df['cumulative_strategy_return'] = (1 + backtest_df['strategy_return']).cumprod() - 1
        
        # Calculate portfolio values
        backtest_df['market_value'] = initial_capital * (1 + backtest_df['cumulative_market_return'])
        backtest_df['strategy_value'] = initial_capital * (1 + backtest_df['cumulative_strategy_return'])
        
        # Calculate various metrics
        total_trades = backtest_df['position'].diff().abs().sum()
        winning_trades = backtest_df[backtest_df['strategy_return'] > 0].shape[0]
        losing_trades = backtest_df[backtest_df['strategy_return'] < 0].shape[0]
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate annualized metrics
        days = (backtest_df.index[-1] - backtest_df.index[0]).days
        years = days / 365.25
        
        strategy_final_return = backtest_df['cumulative_strategy_return'].iloc[-1]
        market_final_return = backtest_df['cumulative_market_return'].iloc[-1]
        
        annualized_strategy_return = (1 + strategy_final_return) ** (1 / years) - 1
        annualized_market_return = (1 + market_final_return) ** (1 / years) - 1
        
        # Calculate volatility and Sharpe ratio
        daily_strategy_returns = backtest_df['strategy_return']
        strategy_volatility = daily_strategy_returns.std() * np.sqrt(252)
        sharpe_ratio = (annualized_strategy_return - 0.02) / strategy_volatility if strategy_volatility > 0 else 0
        
        # Calculate drawdowns
        backtest_df['strategy_peak'] = backtest_df['strategy_value'].cummax()
        backtest_df['drawdown'] = (backtest_df['strategy_value'] - backtest_df['strategy_peak']) / backtest_df['strategy_peak']
        max_drawdown = backtest_df['drawdown'].min()
        
        # Calculate metrics by confidence level
        confidence_metrics = {}
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            high_conf_trades = backtest_df[backtest_df['confidence'] >= threshold]
            if len(high_conf_trades) > 0:
                high_conf_win_rate = high_conf_trades[high_conf_trades['strategy_return'] > 0].shape[0] / len(high_conf_trades)
                high_conf_avg_return = high_conf_trades['strategy_return'].mean()
                confidence_metrics[str(threshold)] = {
                    'count': len(high_conf_trades),
                    'win_rate': high_conf_win_rate,
                    'avg_return': high_conf_avg_return
                }
        
        results = {
            'final_portfolio_value': float(backtest_df['strategy_value'].iloc[-1]),
            'total_return': float(strategy_final_return),
            'annualized_return': float(annualized_strategy_return),
            'market_return': float(market_final_return),
            'market_annualized_return': float(annualized_market_return),
            'total_trades': int(total_trades),
            'winning_trades': int(winning_trades),
            'losing_trades': int(losing_trades),
            'win_rate': float(win_rate),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'volatility': float(strategy_volatility),
            'confidence_metrics': confidence_metrics
        }
        
        # Check if win rate meets our target
        if win_rate >= 0.7:
            results['win_rate_target_achieved'] = True
            logger.info(f"Win rate target of 70% achieved: {win_rate:.2%}")
        else:
            results['win_rate_target_achieved'] = False
            logger.warning(f"Win rate target of 70% not achieved: {win_rate:.2%}")
        
        return results
    
    def save(self, filepath: str):
        """
        Save the hybrid ML model to disk
        
        Args:
            filepath: Path to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save components
        model_data = {
            'lookback_periods': self.lookback_periods,
            'prediction_horizon': self.prediction_horizon,
            'feature_engineering_params': self.feature_engineering_params,
            'ensemble_params': self.ensemble_params,
            'feature_importance': self.feature_importance,
            'feature_names': self.feature_names,
            'scaler': self.scaler
        }
        
        joblib.dump(model_data, filepath)
        
        # Save ensemble model separately
        ensemble_path = os.path.join(os.path.dirname(filepath), "ensemble_model.pkl")
        self.model.save(ensemble_path)
        
        logger.info(f"Hybrid ML model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'HybridMachineLearningModel':
        """
        Load a hybrid ML model from disk
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded hybrid ML model
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        # Load model data
        model_data = joblib.load(filepath)
        
        # Create new instance
        model = cls(
            lookback_periods=model_data['lookback_periods'],
            prediction_horizon=model_data['prediction_horizon'],
            feature_engineering_params=model_data['feature_engineering_params'],
            ensemble_params=model_data['ensemble_params']
        )
        
        # Load components
        model.feature_importance = model_data['feature_importance']
        model.feature_names = model_data['feature_names']
        model.scaler = model_data['scaler']
        
        # Load ensemble model
        ensemble_path = os.path.join(os.path.dirname(filepath), "ensemble_model.pkl")
        model.model = EnsembleVotingClassifier.load(ensemble_path)
        
        return model