"""
Quantum Model Backtesting Framework.
Provides specialized backtesting tools for quantum machine learning models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
import joblib
import json

# Local imports
from ..ai_model_engine.quantum_models import QuantumKernelClassifier, QuantumVariationalClassifier, quantum_range_prediction
from ...services.market_data import MarketDataService

logger = logging.getLogger(__name__)

class QuantumModelBacktester:
    """
    Specialized backtesting framework for quantum models in trading applications.
    Supports time-series cross-validation, walk-forward testing, and benchmark comparisons.
    """
    
    def __init__(
        self,
        market_data_service: MarketDataService = None,
        results_dir: str = "backtest_results",
        benchmark_models: Dict[str, Any] = None
    ):
        """
        Initialize the quantum model backtester
        
        Args:
            market_data_service: Service for fetching market data
            results_dir: Directory to store backtest results
            benchmark_models: Dictionary of classical models to benchmark against
        """
        self.market_data_service = market_data_service
        self.results_dir = results_dir
        self.benchmark_models = benchmark_models or {}
        
        # Create results directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        
        # Store backtest results
        self.results = {}
    
    async def prepare_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        feature_columns: List[str],
        target_column: str,
        target_shift: int = 5,
        split_ratio: float = 0.8,
        include_technical_indicators: bool = True
    ) -> Dict[str, Union[pd.DataFrame, np.ndarray]]:
        """
        Prepare data for backtesting
        
        Args:
            symbol: Trading symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            feature_columns: List of columns to use as features
            target_column: Column to use as target (typically 'Close')
            target_shift: Number of periods to shift target for prediction
            split_ratio: Train/test split ratio
            include_technical_indicators: Whether to add technical indicators as features
            
        Returns:
            Dictionary containing prepared datasets
        """
        if self.market_data_service is None:
            raise ValueError("Market data service not provided")
        
        # Fetch historical data
        data = await self.market_data_service.get_historical_data(
            symbol, start_date, end_date
        )
        
        if data.empty:
            raise ValueError(f"No data available for {symbol} in the specified date range")
        
        # Add technical indicators if requested
        if include_technical_indicators:
            data = self._add_technical_indicators(data)
        
        # Create target variable (future price direction)
        data['future_return'] = data[target_column].pct_change(target_shift).shift(-target_shift)
        data['target'] = (data['future_return'] > 0).astype(int)
        
        # Drop rows with NaN values
        data = data.dropna()
        
        # Select features and target
        X = data[feature_columns].values
        y = data['target'].values
        
        # Split data into train and test sets (respecting time order)
        train_size = int(len(data) * split_ratio)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Store time indices for analysis
        train_dates = data.index[:train_size]
        test_dates = data.index[train_size:]
        
        return {
            'data': data,
            'X_train': X_train,
            'y_train': y_train,
            'X_test': X_test,
            'y_test': y_test,
            'train_dates': train_dates,
            'test_dates': test_dates,
            'feature_columns': feature_columns
        }
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataset
        
        Args:
            data: Price data with OHLCV columns
            
        Returns:
            DataFrame with added technical indicators
        """
        df = data.copy()
        
        # Moving averages
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_30'] = df['Close'].rolling(window=30).mean()
        df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        
        # Volatility
        df['ATR'] = self._calculate_atr(df)
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # Momentum indicators
        df['RSI'] = self._calculate_rsi(df, window=14)
        
        # Price relative to moving averages
        df['Price_to_SMA10'] = df['Close'] / df['SMA_10']
        df['Price_to_SMA30'] = df['Close'] / df['SMA_30']
        
        return df
    
    def _calculate_rsi(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(window=window).mean()
    
    def perform_time_series_cv(
        self,
        model_constructor: Callable,
        X: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5,
        **model_params
    ) -> Dict[str, Any]:
        """
        Perform time-series cross-validation
        
        Args:
            model_constructor: Function that returns a new model instance
            X: Feature data
            y: Target data
            n_splits: Number of splits for time-series CV
            **model_params: Parameters to pass to the model constructor
            
        Returns:
            Dictionary of cross-validation results
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        cv_scores = []
        
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]
            
            # Create and train model
            model = model_constructor(**model_params)
            model.fit(X_train, y_train)
            
            # Evaluate model
            predictions = model.predict(X_test)
            score = accuracy_score(y_test, predictions)
            cv_scores.append(score)
        
        return {
            'cv_scores': cv_scores,
            'mean_cv_score': np.mean(cv_scores),
            'std_cv_score': np.std(cv_scores)
        }
    
    def perform_walk_forward_validation(
        self,
        model_constructor: Callable,
        X: np.ndarray,
        y: np.ndarray,
        dates: pd.DatetimeIndex,
        initial_train_size: float = 0.5,
        retrain_interval: int = 30,
        **model_params
    ) -> Dict[str, Any]:
        """
        Perform walk-forward validation with periodic model retraining
        
        Args:
            model_constructor: Function that returns a new model instance
            X: Feature data
            y: Target data
            dates: Corresponding dates for the data points
            initial_train_size: Initial training set size as a fraction of total data
            retrain_interval: Number of steps between model retraining
            **model_params: Parameters to pass to the model constructor
            
        Returns:
            Dictionary with walk-forward validation results
        """
        n_samples = len(X)
        initial_train_samples = int(n_samples * initial_train_size)
        
        all_predictions = []
        all_actual = []
        training_dates = []
        
        current_model = None
        last_train_idx = 0
        
        for i in range(initial_train_samples, n_samples):
            # Check if we need to retrain the model
            if current_model is None or (i - last_train_idx) >= retrain_interval:
                # Use all data up to current point for training
                X_train, y_train = X[:i], y[:i]
                current_model = model_constructor(**model_params)
                current_model.fit(X_train, y_train)
                
                last_train_idx = i
                training_dates.append(dates[i])
            
            # Make prediction for current point
            X_current = X[i].reshape(1, -1)
            prediction = current_model.predict(X_current)[0]
            
            all_predictions.append(prediction)
            all_actual.append(y[i])
        
        # Calculate performance metrics
        all_predictions = np.array(all_predictions)
        all_actual = np.array(all_actual)
        
        metrics = {
            'accuracy': accuracy_score(all_actual, all_predictions),
            'precision': precision_score(all_actual, all_predictions, zero_division=0),
            'recall': recall_score(all_actual, all_predictions, zero_division=0),
            'f1': f1_score(all_actual, all_predictions, zero_division=0),
            'training_dates': training_dates,
            'predictions': all_predictions,
            'actual': all_actual,
            'prediction_dates': dates[initial_train_samples:n_samples]
        }
        
        return metrics
    
    def compare_with_benchmarks(
        self,
        quantum_model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        benchmark_models: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare quantum model performance with classical benchmarks
        
        Args:
            quantum_model: Quantum model to evaluate
            X_train: Training features
            y_train: Training targets
            X_test: Test features
            y_test: Test targets
            benchmark_models: Dictionary of benchmark models
            
        Returns:
            Dictionary of performance metrics for each model
        """
        models_to_compare = {
            'quantum': quantum_model
        }
        
        # Add benchmark models if provided
        if benchmark_models:
            models_to_compare.update(benchmark_models)
        elif self.benchmark_models:
            models_to_compare.update(self.benchmark_models)
        
        results = {}
        
        for name, model in models_to_compare.items():
            # Skip quantum model if it's already trained
            if name != 'quantum' or not hasattr(quantum_model, 'model') or quantum_model.model is None:
                model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'f1': f1_score(y_test, y_pred, zero_division=0)
            }
            
            results[name] = metrics
        
        return results
    
    def test_prediction_impact(
        self,
        predictions: np.ndarray,
        actual_returns: np.ndarray,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Test the financial impact of predictions
        
        Args:
            predictions: Model predictions (0 or 1)
            actual_returns: Actual price returns
            initial_capital: Initial capital for backtesting
            
        Returns:
            Dictionary of performance metrics
        """
        if len(predictions) != len(actual_returns):
            raise ValueError("Predictions and returns arrays must have the same length")
        
        capital = initial_capital
        portfolio_values = [capital]
        position = 0
        positions = [position]
        
        for i in range(len(predictions)):
            # Update portfolio value based on position
            capital *= (1 + position * actual_returns[i])
            
            # Update position based on prediction (1 = long, 0 = cash)
            position = 1 if predictions[i] == 1 else 0
            
            portfolio_values.append(capital)
            positions.append(position)
        
        # Calculate returns and metrics
        portfolio_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # Buy and hold strategy
        buy_hold_values = [initial_capital]
        for ret in actual_returns:
            buy_hold_values.append(buy_hold_values[-1] * (1 + ret))
        
        # Market investment only on positive days (perfect foresight)
        perfect_values = [initial_capital]
        for ret in actual_returns:
            perfect_values.append(perfect_values[-1] * (1 + max(0, ret)))
        
        # Results
        sharpe_ratio = np.mean(portfolio_returns) / np.std(portfolio_returns) * np.sqrt(252) if np.std(portfolio_returns) > 0 else 0
        
        return {
            'final_capital': portfolio_values[-1],
            'total_return': (portfolio_values[-1] / initial_capital) - 1,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'portfolio_values': portfolio_values,
            'positions': positions,
            'buy_hold_values': buy_hold_values,
            'perfect_values': perfect_values,
            'win_rate': np.mean((np.array(positions[:-1]) > 0) & (actual_returns > 0))
        }
    
    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """Calculate maximum drawdown from a list of values"""
        cumulative_max = np.maximum.accumulate(values)
        drawdowns = (cumulative_max - values) / cumulative_max
        return np.max(drawdowns)
    
    def plot_results(
        self,
        portfolio_values: List[float],
        buy_hold_values: List[float],
        perfect_values: List[float],
        dates: pd.DatetimeIndex,
        positions: List[int],
        title: str
    ) -> plt.Figure:
        """
        Plot backtest results
        
        Args:
            portfolio_values: Portfolio values over time
            buy_hold_values: Buy and hold strategy values
            perfect_values: Perfect foresight strategy values
            dates: Dates corresponding to values
            positions: Position sizes over time
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        # Create figure and axes
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[3, 1], sharex=True, gridspec_kw={'hspace': 0.02})
        
        # Plot portfolio values
        ax1.plot(dates, portfolio_values[1:], label='Model Strategy', linewidth=2)
        ax1.plot(dates, buy_hold_values[1:], label='Buy & Hold', linewidth=1.5, alpha=0.7)
        ax1.plot(dates, perfect_values[1:], label='Perfect Foresight', linewidth=1, linestyle='--', alpha=0.5)
        
        ax1.set_title(title)
        ax1.set_ylabel('Portfolio Value')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot positions
        ax2.fill_between(dates, positions[1:], 0, step='post', alpha=0.7, label='Position')
        ax2.set_ylabel('Position')
        ax2.set_ylim([-0.1, 1.1])
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('Date')
        
        fig.tight_layout()
        return fig
    
    def save_results(self, results: Dict[str, Any], symbol: str, model_name: str) -> str:
        """
        Save backtest results to disk
        
        Args:
            results: Dictionary of backtest results
            symbol: Trading symbol
            model_name: Name of the model used
            
        Returns:
            Path to the saved results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{model_name}_{timestamp}"
        
        # Prepare results for saving
        save_data = {k: v for k, v in results.items() if not isinstance(v, (plt.Figure, np.ndarray, pd.DatetimeIndex))}
        
        # Convert numpy arrays to lists for JSON serialization
        for key, value in save_data.items():
            if isinstance(value, np.ndarray):
                save_data[key] = value.tolist()
        
        # Save JSON results
        results_path = os.path.join(self.results_dir, f"{filename}.json")
        with open(results_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        # Save figures if present
        if 'figure' in results:
            fig_path = os.path.join(self.results_dir, f"{filename}.png")
            results['figure'].savefig(fig_path, dpi=300, bbox_inches='tight')
        
        logger.info(f"Saved backtest results to {results_path}")
        return results_path
    
    async def run_full_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        model_constructor: Callable,
        feature_columns: List[str],
        target_column: str = 'Close',
        model_params: Dict[str, Any] = None,
        use_walk_forward: bool = True,
        initial_train_size: float = 0.5,
        retrain_interval: int = 30,
        classical_benchmarks: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run a complete backtest for a quantum model
        
        Args:
            symbol: Trading symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            model_constructor: Function that returns a new model instance
            feature_columns: Features to use for the model
            target_column: Target column (typically 'Close')
            model_params: Parameters for the model
            use_walk_forward: Whether to use walk-forward validation
            initial_train_size: Initial training set size as fraction
            retrain_interval: Steps between model retraining
            classical_benchmarks: Dictionary of classical models to compare with
            
        Returns:
            Dictionary of comprehensive backtest results
        """
        # Prepare data
        data_dict = await self.prepare_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            feature_columns=feature_columns,
            target_column=target_column
        )
        
        # Create model
        model_params = model_params or {}
        model = model_constructor(**model_params)
        
        # Run time-series cross-validation
        cv_results = self.perform_time_series_cv(
            model_constructor=model_constructor,
            X=data_dict['X_train'],
            y=data_dict['y_train'],
            **model_params
        )
        
        # Fit model on training data
        model.fit(data_dict['X_train'], data_dict['y_train'])
        
        # Simple train/test evaluation
        y_pred_train = model.predict(data_dict['X_train'])
        y_pred_test = model.predict(data_dict['X_test'])
        
        train_metrics = {
            'accuracy': accuracy_score(data_dict['y_train'], y_pred_train),
            'precision': precision_score(data_dict['y_train'], y_pred_train, zero_division=0),
            'recall': recall_score(data_dict['y_train'], y_pred_train, zero_division=0),
            'f1': f1_score(data_dict['y_train'], y_pred_train, zero_division=0)
        }
        
        test_metrics = {
            'accuracy': accuracy_score(data_dict['y_test'], y_pred_test),
            'precision': precision_score(data_dict['y_test'], y_pred_test, zero_division=0),
            'recall': recall_score(data_dict['y_test'], y_pred_test, zero_division=0),
            'f1': f1_score(data_dict['y_test'], y_pred_test, zero_division=0)
        }
        
        # Walk-forward validation if requested
        walk_forward_results = None
        if use_walk_forward:
            walk_forward_results = self.perform_walk_forward_validation(
                model_constructor=model_constructor,
                X=np.concatenate([data_dict['X_train'], data_dict['X_test']]),
                y=np.concatenate([data_dict['y_train'], data_dict['y_test']]),
                dates=data_dict['data'].index,
                initial_train_size=initial_train_size,
                retrain_interval=retrain_interval,
                **model_params
            )
        
        # Compare with classical benchmarks
        benchmark_results = self.compare_with_benchmarks(
            quantum_model=model,
            X_train=data_dict['X_train'],
            y_train=data_dict['y_train'],
            X_test=data_dict['X_test'],
            y_test=data_dict['y_test'],
            benchmark_models=classical_benchmarks
        )
        
        # Calculate financial impact
        # Get future returns for test set
        test_returns = data_dict['data']['future_return'].iloc[-len(data_dict['y_test']):].values
        
        financial_impact = self.test_prediction_impact(
            predictions=y_pred_test,
            actual_returns=test_returns
        )
        
        # Create visualization
        fig = self.plot_results(
            portfolio_values=financial_impact['portfolio_values'],
            buy_hold_values=financial_impact['buy_hold_values'],
            perfect_values=financial_impact['perfect_values'],
            dates=data_dict['test_dates'],
            positions=financial_impact['positions'],
            title=f"Quantum Model Backtest: {symbol}"
        )
        
        # Compile and save results
        results = {
            'symbol': symbol,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'model_params': model_params,
            'time_series_cv': cv_results,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'walk_forward_results': walk_forward_results,
            'benchmark_comparison': benchmark_results,
            'financial_impact': financial_impact,
            'feature_columns': feature_columns,
            'figure': fig
        }
        
        # Save results
        model_name = model.__class__.__name__
        self.save_results(results, symbol, model_name)
        
        return results