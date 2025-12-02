"""
Market Regime Detection module.

This module provides functionality to detect different market regimes
(e.g., trending, ranging, volatile) based on market data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import kurtosis, skew
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum, auto

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Enumeration of market regime types."""
    
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    VOLATILE = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    MEAN_REVERTING = auto()
    BREAKOUT = auto()
    UNKNOWN = auto()


class MarketRegimeDetector:
    """
    Detects market regimes based on various indicators and patterns.
    """
    
    def __init__(
        self,
        window_size: int = 20,
        volatility_window: int = 10,
        num_regimes: int = 4,
        trend_threshold: float = 0.1,
        volatility_threshold: float = 0.015,
        kurtosis_threshold: float = 3.0
    ):
        """
        Initialize the market regime detector.
        
        Args:
            window_size: Window size for moving averages
            volatility_window: Window size for volatility calculation
            num_regimes: Number of regimes to cluster into
            trend_threshold: Threshold for trend detection
            volatility_threshold: Threshold for volatility categorization
            kurtosis_threshold: Threshold for kurtosis (fat tails)
        """
        self.window_size = window_size
        self.volatility_window = volatility_window
        self.num_regimes = num_regimes
        self.trend_threshold = trend_threshold
        self.volatility_threshold = volatility_threshold
        self.kurtosis_threshold = kurtosis_threshold
        self.scaler = StandardScaler()
        self.regime_model = None
        self.regime_labels = None
        
    def extract_features(self, prices: np.ndarray) -> pd.DataFrame:
        """
        Extract regime-related features from price series.
        
        Args:
            prices: Array of price data
            
        Returns:
            DataFrame of extracted features
        """
        # Convert to pandas Series for easier calculation
        price_series = pd.Series(prices)
        returns = price_series.pct_change().fillna(0)
        
        # Calculate features
        features = pd.DataFrame()
        
        # Trend features
        features['ma_short'] = price_series.rolling(self.window_size // 2).mean()
        features['ma_long'] = price_series.rolling(self.window_size).mean()
        features['ma_ratio'] = features['ma_short'] / features['ma_long']
        features['trend'] = price_series.diff(self.window_size) / price_series.shift(self.window_size)
        
        # Volatility features
        features['volatility'] = returns.rolling(self.volatility_window).std()
        features['volatility_change'] = features['volatility'].pct_change(self.volatility_window).fillna(0)
        
        # Statistical features
        rolling_returns = returns.rolling(self.window_size)
        features['return_kurtosis'] = rolling_returns.apply(lambda x: kurtosis(x))
        features['return_skew'] = rolling_returns.apply(lambda x: skew(x))
        
        # Momentum features
        features['rsi'] = self._calculate_rsi(price_series, window=14)
        
        # Mean reversion features
        features['mean_dev'] = (price_series - price_series.rolling(self.window_size).mean()) / price_series.rolling(self.window_size).std()
        
        # Fill NaN values
        features = features.fillna(0)
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate the Relative Strength Index."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # Fill NaNs with neutral value
    
    def train(self, prices: np.ndarray, plot: bool = False) -> Dict:
        """
        Train the regime detection model.
        
        Args:
            prices: Training price data
            plot: Whether to plot the clustering results
            
        Returns:
            Dictionary of training results and regime characteristics
        """
        # Extract features
        features = self.extract_features(prices)
        
        # Normalize features
        X = self.scaler.fit_transform(features)
        
        # Cluster regimes
        kmeans = KMeans(n_clusters=self.num_regimes, random_state=42)
        labels = kmeans.fit_predict(X)
        self.regime_model = kmeans
        
        # Analyze regimes
        features['regime'] = labels
        self.regime_labels = labels
        
        # Determine regime characteristics
        regime_stats = {}
        for regime in range(self.num_regimes):
            regime_data = features[features['regime'] == regime]
            
            # Get average values for this regime
            avg_trend = regime_data['trend'].mean()
            avg_volatility = regime_data['volatility'].mean()
            avg_kurtosis = regime_data['return_kurtosis'].mean()
            avg_mean_dev = regime_data['mean_dev'].mean()
            avg_rsi = regime_data['rsi'].mean()
            
            # Determine regime type
            regime_type = self._determine_regime_type(
                avg_trend, avg_volatility, avg_kurtosis, avg_mean_dev, avg_rsi
            )
            
            # Store statistics
            regime_stats[regime] = {
                'type': regime_type.name,
                'avg_trend': avg_trend,
                'avg_volatility': avg_volatility,
                'avg_kurtosis': avg_kurtosis,
                'avg_mean_dev': avg_mean_dev,
                'avg_rsi': avg_rsi
            }
        
        # Plot if requested
        if plot:
            self._plot_regimes(features, prices)
            
        return regime_stats
    
    def _determine_regime_type(
        self, 
        trend: float, 
        volatility: float, 
        kurtosis_val: float, 
        mean_dev: float, 
        rsi: float
    ) -> MarketRegime:
        """
        Determine the type of market regime based on characteristics.
        
        Args:
            trend: Average trend
            volatility: Average volatility
            kurtosis_val: Kurtosis of returns
            mean_dev: Mean deviation
            rsi: Relative Strength Index
            
        Returns:
            Market regime enum value
        """
        # First check for trending markets
        if trend > self.trend_threshold:
            if rsi > 60:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.BREAKOUT
        elif trend < -self.trend_threshold:
            if rsi < 40:
                return MarketRegime.TRENDING_DOWN
            else:
                return MarketRegime.BREAKOUT
        
        # Then check for volatility regimes
        if volatility > self.volatility_threshold * 1.5:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < self.volatility_threshold * 0.5:
            return MarketRegime.LOW_VOLATILITY
        
        # Check for mean reversion
        if abs(mean_dev) > 1.5 and ((mean_dev < 0 and rsi > 50) or (mean_dev > 0 and rsi < 50)):
            return MarketRegime.MEAN_REVERTING
        
        # Check for ranging markets
        if abs(trend) < self.trend_threshold * 0.5 and volatility < self.volatility_threshold:
            return MarketRegime.RANGING
        
        # Check for general volatility
        if kurtosis_val > self.kurtosis_threshold or volatility > self.volatility_threshold:
            return MarketRegime.VOLATILE
        
        # Default
        return MarketRegime.UNKNOWN
    
    def _plot_regimes(self, features: pd.DataFrame, prices: np.ndarray):
        """
        Plot the detected market regimes.
        
        Args:
            features: Feature DataFrame with regime labels
            prices: Price data
        """
        plt.figure(figsize=(14, 10))
        
        # Plot 1: Prices with regime backgrounds
        plt.subplot(3, 1, 1)
        plt.title('Price with Market Regimes')
        
        # Create a colormap for regimes
        colors = ['lightblue', 'lightgreen', 'lightsalmon', 'lightgray']
        
        # Plot price
        plt.plot(prices, 'k-', linewidth=1.5)
        
        # Color the background by regime
        for regime in range(self.num_regimes):
            mask = features['regime'] == regime
            plt.fill_between(
                range(len(prices)), 
                min(prices), 
                max(prices), 
                where=mask, 
                alpha=0.3, 
                color=colors[regime % len(colors)]
            )
        
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Volatility
        plt.subplot(3, 1, 2)
        plt.title('Volatility')
        plt.plot(features['volatility'], 'r-')
        plt.axhline(self.volatility_threshold, color='k', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Trend
        plt.subplot(3, 1, 3)
        plt.title('Trend')
        plt.plot(features['trend'], 'b-')
        plt.axhline(self.trend_threshold, color='g', linestyle='--', alpha=0.5)
        plt.axhline(-self.trend_threshold, color='r', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def predict(self, prices: np.ndarray) -> List[MarketRegime]:
        """
        Predict market regimes for the given price data.
        
        Args:
            prices: Price data
            
        Returns:
            List of market regime types
        """
        if self.regime_model is None:
            raise ValueError("Model has not been trained yet. Call train() first.")
        
        # Extract features
        features = self.extract_features(prices)
        
        # Normalize features
        X = self.scaler.transform(features)
        
        # Predict regimes
        regime_indices = self.regime_model.predict(X)
        
        # Map indices to named regimes
        predicted_regimes = []
        for i, regime_idx in enumerate(regime_indices):
            # Calculate characteristics for this specific data point
            trend = features['trend'].iloc[i]
            volatility = features['volatility'].iloc[i]
            kurtosis_val = features['return_kurtosis'].iloc[i]
            mean_dev = features['mean_dev'].iloc[i]
            rsi = features['rsi'].iloc[i]
            
            # Determine regime type based on characteristics
            regime_type = self._determine_regime_type(
                trend, volatility, kurtosis_val, mean_dev, rsi
            )
            
            predicted_regimes.append(regime_type)
        
        return predicted_regimes
    
    def current_regime(self, prices: np.ndarray) -> MarketRegime:
        """
        Detect the current market regime.
        
        Args:
            prices: Recent price data
            
        Returns:
            Current market regime type
        """
        regimes = self.predict(prices)
        # Return the most recent regime
        return regimes[-1] if regimes else MarketRegime.UNKNOWN
    
    def optimal_strategy(self, regime: MarketRegime) -> str:
        """
        Suggest optimal trading strategy for the given market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Suggested trading strategy
        """
        strategy_map = {
            MarketRegime.TRENDING_UP: "Trend following with trailing stops",
            MarketRegime.TRENDING_DOWN: "Short positions or reduced exposure",
            MarketRegime.RANGING: "Mean reversion strategies or range trading",
            MarketRegime.VOLATILE: "Reduced position sizes and wider stops",
            MarketRegime.HIGH_VOLATILITY: "Very small positions or stay in cash",
            MarketRegime.LOW_VOLATILITY: "Breakout strategies or increased position sizes",
            MarketRegime.MEAN_REVERTING: "Counter-trend strategies",
            MarketRegime.BREAKOUT: "Momentum strategies with tight stops",
            MarketRegime.UNKNOWN: "Balanced approach with default risk parameters"
        }
        
        return strategy_map.get(regime, "Default strategy")
    
    def regime_adjusted_parameters(self, regime: MarketRegime) -> Dict:
        """
        Get adjusted trading parameters for the given market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Dictionary of adjusted parameters for trading algorithms
        """
        # Base parameters
        base_params = {
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.04,
            "position_size_pct": 0.05,
            "trailing_stop_pct": 0.015,
            "entry_threshold": 0.5,
            "exit_threshold": 0.5
        }
        
        # Adjustments for different regimes
        adjustments = {
            MarketRegime.TRENDING_UP: {
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.06,
                "position_size_pct": 0.07,
                "trailing_stop_pct": 0.02,
                "entry_threshold": 0.4,
                "exit_threshold": 0.6
            },
            MarketRegime.TRENDING_DOWN: {
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.06,
                "position_size_pct": 0.07,
                "trailing_stop_pct": 0.02,
                "entry_threshold": 0.6,
                "exit_threshold": 0.4
            },
            MarketRegime.RANGING: {
                "stop_loss_pct": 0.015,
                "take_profit_pct": 0.03,
                "position_size_pct": 0.05,
                "trailing_stop_pct": 0.01,
                "entry_threshold": 0.7,
                "exit_threshold": 0.7
            },
            MarketRegime.VOLATILE: {
                "stop_loss_pct": 0.03,
                "take_profit_pct": 0.05,
                "position_size_pct": 0.03,
                "trailing_stop_pct": 0.025,
                "entry_threshold": 0.6,
                "exit_threshold": 0.6
            },
            MarketRegime.HIGH_VOLATILITY: {
                "stop_loss_pct": 0.04,
                "take_profit_pct": 0.07,
                "position_size_pct": 0.02,
                "trailing_stop_pct": 0.03,
                "entry_threshold": 0.7,
                "exit_threshold": 0.7
            },
            MarketRegime.LOW_VOLATILITY: {
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.025,
                "position_size_pct": 0.08,
                "trailing_stop_pct": 0.008,
                "entry_threshold": 0.4,
                "exit_threshold": 0.4
            },
            MarketRegime.MEAN_REVERTING: {
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.035,
                "position_size_pct": 0.06,
                "trailing_stop_pct": 0.015,
                "entry_threshold": 0.6,
                "exit_threshold": 0.4
            },
            MarketRegime.BREAKOUT: {
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.05,
                "position_size_pct": 0.05,
                "trailing_stop_pct": 0.02,
                "entry_threshold": 0.4,
                "exit_threshold": 0.5
            }
        }
        
        # Apply adjustments if available for the regime
        if regime in adjustments:
            params = base_params.copy()
            params.update(adjustments[regime])
            return params
        else:
            return base_params