"""
Deep Learning models for the trading engine.
Implementations of LSTM, CNN and transformer models for price prediction.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.regularizers import l1_l2
from tensorflow.keras.metrics import RootMeanSquaredError
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Tuple, Union, Optional, Any
import logging
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class TimeSeriesGenerator:
    """
    Generate time series data for training and testing deep learning models.
    """
    
    def __init__(self, seq_length: int = 30, normalization: bool = True):
        """
        Initialize the time series generator
        
        Args:
            seq_length: Length of the sequence for input
            normalization: Whether to normalize the data
        """
        self.seq_length = seq_length
        self.normalization = normalization
        self.feature_scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'TimeSeriesGenerator':
        """
        Fit the scalers for normalization
        
        Args:
            X: Input features (samples, features)
            y: Target values (if None, only X will be normalized)
            
        Returns:
            Self
        """
        if self.normalization:
            self.feature_scaler.fit(X)
            if y is not None:
                # Reshape to 2D if needed
                if len(y.shape) == 1:
                    y = y.reshape(-1, 1)
                self.target_scaler.fit(y)
        
        return self
    
    def transform(
        self, 
        X: np.ndarray, 
        y: np.ndarray = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Transform data for normalization
        
        Args:
            X: Input features
            y: Target values (if None, only X will be transformed)
            
        Returns:
            Tuple of transformed X and y (y is None if input y was None)
        """
        X_transformed = X.copy()
        y_transformed = None
        
        if self.normalization:
            X_transformed = self.feature_scaler.transform(X_transformed)
            if y is not None:
                # Reshape to 2D if needed
                if len(y.shape) == 1:
                    y = y.reshape(-1, 1)
                y_transformed = self.target_scaler.transform(y)
                
                # Return to original shape if needed
                if len(y.shape) == 1:
                    y_transformed = y_transformed.flatten()
        else:
            y_transformed = y
        
        return X_transformed, y_transformed
    
    def inverse_transform_y(self, y: np.ndarray) -> np.ndarray:
        """
        Inverse transform target values
        
        Args:
            y: Normalized target values
            
        Returns:
            Original scale target values
        """
        if not self.normalization:
            return y
        
        # Reshape to 2D if needed
        original_shape = y.shape
        if len(y.shape) == 1:
            y = y.reshape(-1, 1)
            
        y_original = self.target_scaler.inverse_transform(y)
        
        # Return to original shape if needed
        if len(original_shape) == 1:
            y_original = y_original.flatten()
            
        return y_original
    
    def create_sequences(
        self, 
        X: np.ndarray, 
        y: np.ndarray = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Create sequences for time series prediction
        
        Args:
            X: Input features (samples, features)
            y: Target values (samples,) or (samples, n_targets)
            
        Returns:
            Tuple of (X_seq, y_seq) where:
                X_seq is (samples, seq_length, features)
                y_seq is either None or has the shape of original y
        """
        n_samples = X.shape[0]
        n_features = X.shape[1]
        
        # We can only create sequences up to (n_samples - seq_length)
        n_sequences = n_samples - self.seq_length
        
        if n_sequences <= 0:
            raise ValueError(f"Not enough samples ({n_samples}) for given sequence length ({self.seq_length})")
        
        # Initialize output arrays
        X_seq = np.zeros((n_sequences, self.seq_length, n_features))
        
        # Create sequences
        for i in range(n_sequences):
            X_seq[i] = X[i:i+self.seq_length]
        
        # Handle target values if provided
        y_seq = None
        if y is not None:
            # If y is 1D, we need to handle it differently
            if len(y.shape) == 1:
                y_seq = y[self.seq_length:]
            else:
                y_seq = y[self.seq_length:]
        
        return X_seq, y_seq
    
    def prepare_data(
        self, 
        X: np.ndarray, 
        y: np.ndarray = None, 
        train_ratio: float = 0.8
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data for training and testing
        
        Args:
            X: Input features (samples, features)
            y: Target values (samples,) or (samples, n_targets)
            train_ratio: Ratio of data to use for training
            
        Returns:
            Dictionary with keys:
                X_train, X_test: Sequences for training and testing
                y_train, y_test: Target values for training and testing
        """
        # Normalize the data
        X_norm, y_norm = self.transform(X, y)
        
        # Create sequences
        X_seq, y_seq = self.create_sequences(X_norm, y_norm)
        
        # Split into train and test sets
        train_size = int(len(X_seq) * train_ratio)
        
        X_train, X_test = X_seq[:train_size], X_seq[train_size:]
        
        result = {
            'X_train': X_train,
            'X_test': X_test
        }
        
        if y is not None:
            y_train, y_test = y_seq[:train_size], y_seq[train_size:]
            result['y_train'] = y_train
            result['y_test'] = y_test
        
        return result


class LSTMPricePredictor:
    """
    LSTM model for time series prediction of stock prices.
    """
    
    def __init__(
        self,
        seq_length: int = 30,
        lstm_units: List[int] = [64, 64],
        dense_units: List[int] = [32],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        loss: str = 'mean_squared_error',
        metrics: List[str] = ['mae'],
        multi_step: bool = False,
        forecast_horizon: int = 1
    ):
        """
        Initialize the LSTM Price Predictor
        
        Args:
            seq_length: Length of the input sequence
            lstm_units: List of units for LSTM layers
            dense_units: List of units for Dense layers
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
            loss: Loss function
            metrics: Evaluation metrics
            multi_step: Whether to predict multiple steps ahead
            forecast_horizon: Number of steps to forecast (used if multi_step=True)
        """
        self.seq_length = seq_length
        self.lstm_units = lstm_units
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.loss = loss
        self.metrics = metrics
        self.multi_step = multi_step
        self.forecast_horizon = forecast_horizon
        
        self.model = None
        self.generator = TimeSeriesGenerator(seq_length=seq_length)
        self.history = None
    
    def build_model(self, input_shape: Tuple[int, int]) -> tf.keras.Model:
        """
        Build the LSTM model
        
        Args:
            input_shape: Shape of the input data (seq_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        model = models.Sequential()
        
        # Add LSTM layers
        for i, units in enumerate(self.lstm_units):
            return_sequences = i < len(self.lstm_units) - 1  # Return sequences for all but last LSTM layer
            
            if i == 0:
                # First layer needs to specify input shape
                model.add(layers.LSTM(
                    units, 
                    return_sequences=return_sequences, 
                    input_shape=input_shape,
                    recurrent_regularizer=l1_l2(l1=0.01, l2=0.01)
                ))
            else:
                model.add(layers.LSTM(
                    units, 
                    return_sequences=return_sequences,
                    recurrent_regularizer=l1_l2(l1=0.01, l2=0.01)
                ))
            
            # Add dropout after each LSTM layer
            model.add(layers.Dropout(self.dropout_rate))
        
        # Add dense layers
        for units in self.dense_units:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(self.dropout_rate))
        
        # Output layer
        if self.multi_step:
            model.add(layers.Dense(self.forecast_horizon))
        else:
            model.add(layers.Dense(1))
        
        # Compile the model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss=self.loss,
            metrics=self.metrics
        )
        
        return model
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        callbacks: List[tf.keras.callbacks.Callback] = None,
        verbose: int = 1
    ) -> 'LSTMPricePredictor':
        """
        Fit the LSTM model
        
        Args:
            X: Input features (samples, features)
            y: Target values
            epochs: Number of epochs
            batch_size: Batch size
            validation_split: Validation split ratio
            callbacks: List of Keras callbacks
            verbose: Verbosity level
            
        Returns:
            Self
        """
        # Prepare the data
        self.generator.fit(X, y)
        data = self.generator.prepare_data(X, y, train_ratio=1 - validation_split)
        
        X_train, y_train = data['X_train'], data['y_train']
        X_val, y_val = data['X_test'], data['y_test']
        
        # Build the model
        if self.model is None:
            input_shape = (X_train.shape[1], X_train.shape[2])
            self.model = self.build_model(input_shape)
        
        # Set up callbacks
        if callbacks is None:
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001
                )
            ]
        
        # Train the model
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=verbose
        )
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with the model
        
        Args:
            X: Input features (samples, features)
            
        Returns:
            Predicted values in original scale
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        # Normalize the data
        X_norm, _ = self.generator.transform(X)
        
        # Create sequences
        X_seq, _ = self.generator.create_sequences(X_norm)
        
        # Make predictions
        y_pred_norm = self.model.predict(X_seq)
        
        # Inverse transform to get original scale
        y_pred = self.generator.inverse_transform_y(y_pred_norm)
        
        return y_pred
    
    def predict_future(
        self, 
        X: np.ndarray, 
        steps: int = 30, 
        use_monte_carlo: bool = False,
        n_simulations: int = 100,
        noise_level: float = 0.01
    ) -> Dict[str, np.ndarray]:
        """
        Predict future values beyond available data
        
        Args:
            X: Current data (at least seq_length samples)
            steps: Number of steps to predict
            use_monte_carlo: Whether to use Monte Carlo simulations
            n_simulations: Number of Monte Carlo simulations
            noise_level: Level of noise for Monte Carlo simulations
            
        Returns:
            Dictionary with future predictions and confidence intervals
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        # Ensure we have enough data for the sequence
        if len(X) < self.seq_length:
            raise ValueError(f"Input data must have at least {self.seq_length} samples")
        
        # Normalize the data
        X_norm, _ = self.generator.transform(X)
        
        # Initialize containers for predictions
        if use_monte_carlo:
            all_predictions = np.zeros((n_simulations, steps))
        
        # Make predictions
        future_preds = []
        curr_sequence = X_norm[-self.seq_length:].copy()
        
        if use_monte_carlo:
            # Monte Carlo simulations
            for sim in range(n_simulations):
                curr_sim_sequence = curr_sequence.copy()
                sim_preds = []
                
                for step in range(steps):
                    # Add noise to the sequence for this simulation
                    if noise_level > 0:
                        noisy_sequence = curr_sim_sequence + np.random.normal(0, noise_level, curr_sim_sequence.shape)
                    else:
                        noisy_sequence = curr_sim_sequence
                    
                    # Reshape for prediction
                    X_seq = noisy_sequence.reshape(1, self.seq_length, X.shape[1])
                    
                    # Predict next step
                    next_pred = self.model.predict(X_seq, verbose=0)
                    
                    # For multi-step, take the next point; otherwise use the single prediction
                    if self.multi_step and step < self.forecast_horizon:
                        y_pred = next_pred[0, step]
                    else:
                        y_pred = next_pred[0, 0]
                        
                    sim_preds.append(y_pred)
                    
                    # Update sequence for next prediction by shifting and adding the new prediction
                    new_datapoint = np.zeros((1, X.shape[1]))
                    # Typically first column would be the value we're predicting
                    new_datapoint[0, 0] = y_pred
                    curr_sim_sequence = np.vstack([curr_sim_sequence[1:], new_datapoint])
                
                all_predictions[sim, :] = np.array(sim_preds)
            
            # Calculate mean and confidence intervals
            mean_preds = np.mean(all_predictions, axis=0)
            lower_bound = np.percentile(all_predictions, 10, axis=0)  # 10th percentile
            upper_bound = np.percentile(all_predictions, 90, axis=0)  # 90th percentile
            
            # Inverse transform to get original scale
            mean_preds_original = self.generator.inverse_transform_y(mean_preds.reshape(-1, 1)).flatten()
            lower_bound_original = self.generator.inverse_transform_y(lower_bound.reshape(-1, 1)).flatten()
            upper_bound_original = self.generator.inverse_transform_y(upper_bound.reshape(-1, 1)).flatten()
            
            return {
                'mean': mean_preds_original,
                'lower': lower_bound_original,
                'upper': upper_bound_original
            }
            
        else:
            # Single prediction path
            for step in range(steps):
                # Reshape for prediction
                X_seq = curr_sequence.reshape(1, self.seq_length, X.shape[1])
                
                # Predict next step
                if self.multi_step:
                    next_pred = self.model.predict(X_seq, verbose=0)
                    # For the first prediction, we can use all forecast steps
                    if step == 0 and steps <= self.forecast_horizon:
                        future_preds = next_pred[0, :steps]
                        break
                    else:
                        # Otherwise, just take the next step
                        y_pred = next_pred[0, 0]
                else:
                    y_pred = self.model.predict(X_seq, verbose=0)[0, 0]
                
                future_preds.append(y_pred)
                
                # Update sequence for next prediction
                new_datapoint = np.zeros((1, X.shape[1]))
                new_datapoint[0, 0] = y_pred  # Typically first column is the target
                curr_sequence = np.vstack([curr_sequence[1:], new_datapoint])
            
            # Convert to array
            future_preds = np.array(future_preds)
            
            # Inverse transform to get original scale
            future_preds_original = self.generator.inverse_transform_y(future_preds.reshape(-1, 1)).flatten()
            
            return {
                'mean': future_preds_original,
                'lower': None,
                'upper': None
            }


class CNNPricePredictor:
    """
    CNN model for price pattern recognition and prediction.
    """
    
    def __init__(
        self,
        seq_length: int = 30,
        filters: List[int] = [64, 128, 256],
        kernel_sizes: List[int] = [3, 3, 3],
        pool_sizes: List[int] = [2, 2, 2],
        dense_units: List[int] = [128, 64],
        dropout_rate: float = 0.3,
        learning_rate: float = 0.001,
        loss: str = 'mean_squared_error',
        metrics: List[str] = ['mae'],
        forecast_horizon: int = 1
    ):
        """
        Initialize the CNN Price Predictor
        
        Args:
            seq_length: Length of the input sequence
            filters: List of filters for Conv1D layers
            kernel_sizes: List of kernel sizes for Conv1D layers
            pool_sizes: List of pool sizes for MaxPooling1D layers
            dense_units: List of units for Dense layers
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
            loss: Loss function
            metrics: Evaluation metrics
            forecast_horizon: Number of steps to forecast
        """
        self.seq_length = seq_length
        self.filters = filters
        self.kernel_sizes = kernel_sizes
        self.pool_sizes = pool_sizes
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.loss = loss
        self.metrics = metrics
        self.forecast_horizon = forecast_horizon
        
        self.model = None
        self.generator = TimeSeriesGenerator(seq_length=seq_length)
        self.history = None
    
    def build_model(self, input_shape: Tuple[int, int]) -> tf.keras.Model:
        """
        Build the CNN model
        
        Args:
            input_shape: Shape of the input data (seq_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        model = models.Sequential()
        
        # Add convolutional layers
        for i, (filters, kernel_size, pool_size) in enumerate(zip(self.filters, self.kernel_sizes, self.pool_sizes)):
            if i == 0:
                model.add(layers.Conv1D(
                    filters=filters,
                    kernel_size=kernel_size,
                    activation='relu',
                    input_shape=input_shape,
                    padding='same'
                ))
            else:
                model.add(layers.Conv1D(
                    filters=filters,
                    kernel_size=kernel_size,
                    activation='relu',
                    padding='same'
                ))
            
            # Add max pooling
            model.add(layers.MaxPooling1D(pool_size=pool_size))
            
            # Add dropout
            model.add(layers.Dropout(self.dropout_rate))
        
        # Flatten before dense layers
        model.add(layers.Flatten())
        
        # Add dense layers
        for units in self.dense_units:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(self.dropout_rate))
        
        # Output layer
        model.add(layers.Dense(self.forecast_horizon))
        
        # Compile the model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss=self.loss,
            metrics=self.metrics
        )
        
        return model
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        callbacks: List[tf.keras.callbacks.Callback] = None,
        verbose: int = 1
    ) -> 'CNNPricePredictor':
        """
        Fit the CNN model
        
        Args:
            X: Input features (samples, features)
            y: Target values
            epochs: Number of epochs
            batch_size: Batch size
            validation_split: Validation split ratio
            callbacks: List of Keras callbacks
            verbose: Verbosity level
            
        Returns:
            Self
        """
        # Prepare the data
        self.generator.fit(X, y)
        data = self.generator.prepare_data(X, y, train_ratio=1 - validation_split)
        
        X_train, y_train = data['X_train'], data['y_train']
        X_val, y_val = data['X_test'], data['y_test']
        
        # Build the model
        if self.model is None:
            input_shape = (X_train.shape[1], X_train.shape[2])
            self.model = self.build_model(input_shape)
        
        # Set up callbacks
        if callbacks is None:
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001
                )
            ]
        
        # Train the model
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            verbose=verbose
        )
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions with the model
        
        Args:
            X: Input features (samples, features)
            
        Returns:
            Predicted values in original scale
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        # Normalize the data
        X_norm, _ = self.generator.transform(X)
        
        # Create sequences
        X_seq, _ = self.generator.create_sequences(X_norm)
        
        # Make predictions
        y_pred_norm = self.model.predict(X_seq)
        
        # Inverse transform to get original scale
        y_pred = self.generator.inverse_transform_y(y_pred_norm)
        
        return y_pred
    
    def visualize_filters(self, layer_idx: int = 0, max_filters: int = 16) -> plt.Figure:
        """
        Visualize filters in a convolutional layer
        
        Args:
            layer_idx: Index of the Conv1D layer to visualize
            max_filters: Maximum number of filters to visualize
            
        Returns:
            Matplotlib figure
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        # Get the weights from the specified convolutional layer
        conv_layers = [layer for layer in self.model.layers if isinstance(layer, layers.Conv1D)]
        
        if layer_idx >= len(conv_layers):
            raise ValueError(f"Layer index {layer_idx} is out of range. There are {len(conv_layers)} Conv1D layers.")
        
        weights, biases = conv_layers[layer_idx].get_weights()
        
        # Get the number of filters and their size
        n_filters = weights.shape[-1]
        filter_size = weights.shape[0]
        
        # Adjust the number of filters to visualize
        n_filters = min(n_filters, max_filters)
        
        # Create a figure to show the filters
        fig, axes = plt.subplots(n_filters, 1, figsize=(10, 2 * n_filters))
        if n_filters == 1:
            axes = [axes]
        
        for i in range(n_filters):
            # Get the filter values for all input channels
            filter_vals = weights[:, :, i]
            
            # If there are multiple input channels, take the mean
            if filter_vals.shape[1] > 1:
                filter_vals = np.mean(filter_vals, axis=1)
            else:
                filter_vals = filter_vals.flatten()
            
            # Plot the filter
            axes[i].plot(filter_vals)
            axes[i].set_title(f'Filter {i+1}')
            axes[i].set_ylim(np.min(weights), np.max(weights))
        
        plt.tight_layout()
        
        return fig


def deep_learning_range_prediction(
    model: Union[LSTMPricePredictor, CNNPricePredictor],
    X: np.ndarray,
    confidence_level: float = 0.8,
    n_samples: int = 30,
    noise_level: float = 0.01
) -> Dict[str, np.ndarray]:
    """
    Generate range-based predictions with confidence intervals using deep learning models
    
    Args:
        model: Trained deep learning model
        X: Input features
        confidence_level: Confidence level for prediction intervals
        n_samples: Number of samples for Monte Carlo simulation
        noise_level: Level of noise to add for Monte Carlo simulation
        
    Returns:
        Dictionary with mean predictions and confidence intervals
    """
    # Use model's built-in predict_future method if it's an LSTM with Monte Carlo
    if isinstance(model, LSTMPricePredictor):
        return model.predict_future(
            X, 
            steps=1, 
            use_monte_carlo=True,
            n_simulations=n_samples,
            noise_level=noise_level
        )
    
    # For other models, implement Monte Carlo here
    predictions = []
    
    # Add noise to inputs and generate multiple predictions
    for _ in range(n_samples):
        # Add noise to create slightly different inputs
        X_noisy = X + np.random.normal(0, noise_level * np.std(X, axis=0), X.shape)
        
        # Make predictions
        pred = model.predict(X_noisy)
        predictions.append(pred)
    
    # Convert to array
    predictions = np.array(predictions)
    
    # Calculate mean and confidence intervals
    mean_pred = np.mean(predictions, axis=0)
    
    # Calculate lower and upper bounds
    lower_percentile = (1 - confidence_level) / 2 * 100
    upper_percentile = (1 + confidence_level) / 2 * 100
    
    lower_bound = np.percentile(predictions, lower_percentile, axis=0)
    upper_bound = np.percentile(predictions, upper_percentile, axis=0)
    
    return {
        'mean': mean_pred,
        'lower': lower_bound,
        'upper': upper_bound
    }