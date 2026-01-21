"""
Feature Engineering module for the trading engine.
Implements technical indicators and other feature transformations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Feature engineering for market data"""

    def __init__(self):
        self.name = "feature_engineering"

    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate all technical indicators and features for a DataFrame

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with additional technical indicator columns
        """
        df = data.copy()

        # Ensure we have the required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col.lower() in df.columns for col in required_cols):
            raise ValueError(f"Data must contain columns: {required_cols}")

        # Make sure column names are lowercase
        df.columns = [col.lower() for col in df.columns]

        # Calculate technical indicators
        df = self.add_moving_averages(df)
        df = self.add_bollinger_bands(df)
        df = self.add_rsi(df)
        df = self.add_macd(df)
        df = self.add_stochastic_oscillator(df)
        df = self.add_atr(df)
        df = self.add_obv(df)
        df = self.add_momentum_indicators(df)
        df = self.add_volatility_indicators(df)

        # Add price patterns
        df = self.add_candlestick_patterns(df)

        # Add price returns
        df = self.add_returns(df)

        # Drop NaN values that may have been introduced
        df = df.dropna()

        return df

    def add_moving_averages(
        self, df: pd.DataFrame, windows: List[int] = [5, 10, 20, 50, 200]
    ) -> pd.DataFrame:
        """Add simple and exponential moving averages"""
        for window in windows:
            # Simple Moving Average (SMA)
            df[f"sma_{window}"] = df["close"].rolling(window=window).mean()

            # Exponential Moving Average (EMA)
            df[f"ema_{window}"] = df["close"].ewm(span=window, adjust=False).mean()

            # Moving Average Relative Strength
            df[f"ma_strength_{window}"] = df["close"] / df[f"sma_{window}"] - 1

        return df

    def add_bollinger_bands(
        self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0
    ) -> pd.DataFrame:
        """Add Bollinger Bands"""
        # Simple Moving Average
        df["bb_middle"] = df["close"].rolling(window=window).mean()

        # Standard deviation of price
        df["bb_std"] = df["close"].rolling(window=window).std()

        # Upper and Lower Bollinger Bands
        df["bb_upper"] = df["bb_middle"] + (df["bb_std"] * num_std)
        df["bb_lower"] = df["bb_middle"] - (df["bb_std"] * num_std)

        # Bollinger Band Width
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

        # Bollinger Band Percentage (where price is within the bands)
        df["bb_pct"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        return df

    def add_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index"""
        delta = df["close"].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Add RSI-based features
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)
        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)

        return df

    def add_macd(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """Add Moving Average Convergence Divergence (MACD)"""
        # Calculate EMAs
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        # Calculate MACD line
        df["macd"] = ema_fast - ema_slow

        # Calculate signal line
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()

        # Calculate MACD histogram
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # Add MACD cross signals
        df["macd_cross_up"] = (
            (df["macd"] > df["macd_signal"])
            & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
        ).astype(int)

        df["macd_cross_down"] = (
            (df["macd"] < df["macd_signal"])
            & (df["macd"].shift(1) >= df["macd_signal"].shift(1))
        ).astype(int)

        return df

    def add_stochastic_oscillator(
        self, df: pd.DataFrame, k_window: int = 14, d_window: int = 3
    ) -> pd.DataFrame:
        """Add Stochastic Oscillator"""
        # Calculate %K
        low_min = df["low"].rolling(window=k_window).min()
        high_max = df["high"].rolling(window=k_window).max()

        df["stoch_k"] = 100 * ((df["close"] - low_min) / (high_max - low_min))

        # Calculate %D (3-day SMA of %K)
        df["stoch_d"] = df["stoch_k"].rolling(window=d_window).mean()

        # Add Stochastic crosses
        df["stoch_cross_up"] = (
            (df["stoch_k"] > df["stoch_d"])
            & (df["stoch_k"].shift(1) <= df["stoch_d"].shift(1))
        ).astype(int)

        df["stoch_cross_down"] = (
            (df["stoch_k"] < df["stoch_d"])
            & (df["stoch_k"].shift(1) >= df["stoch_d"].shift(1))
        ).astype(int)

        # Add overbought/oversold indicators
        df["stoch_overbought"] = (df["stoch_k"] > 80).astype(int)
        df["stoch_oversold"] = (df["stoch_k"] < 20).astype(int)

        return df

    def add_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Add Average True Range (ATR)"""
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        # True range is the maximum of the three price ranges
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        # Average True Range
        df["atr"] = true_range.rolling(window=window).mean()

        # Normalized ATR (ATR as percentage of price)
        df["atr_pct"] = df["atr"] / df["close"] * 100

        return df

    def add_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add On-Balance Volume (OBV)"""
        # Calculate daily price change
        price_change = df["close"].diff()

        # Create a list to store OBV values
        obv = [0]

        # Calculate OBV
        for i in range(1, len(df)):
            if price_change.iloc[i] > 0:
                obv.append(obv[-1] + df["volume"].iloc[i])
            elif price_change.iloc[i] < 0:
                obv.append(obv[-1] - df["volume"].iloc[i])
            else:
                obv.append(obv[-1])

        # Add OBV to dataframe
        df["obv"] = obv

        # Add OBV momentum (rate of change)
        df["obv_momentum"] = df["obv"].pct_change(periods=5) * 100

        return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        # Price Rate of Change (ROC)
        df["price_roc_5"] = df["close"].pct_change(periods=5) * 100
        df["price_roc_10"] = df["close"].pct_change(periods=10) * 100
        df["price_roc_20"] = df["close"].pct_change(periods=20) * 100

        # Money Flow Index (MFI)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]

        # Positive and negative money flow
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)

        # Money Flow Ratio
        pos_sum = positive_flow.rolling(window=14).sum()
        neg_sum = negative_flow.rolling(window=14).sum()

        money_ratio = pos_sum / neg_sum

        # Money Flow Index (similar to RSI)
        df["mfi"] = 100 - (100 / (1 + money_ratio))

        return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        # Historical Volatility (close-to-close)
        df["returns"] = df["close"].pct_change()
        df["volatility_10"] = df["returns"].rolling(window=10).std() * np.sqrt(252)
        df["volatility_20"] = df["returns"].rolling(window=20).std() * np.sqrt(252)

        # Garman-Klass volatility estimator (uses OHLC prices)
        log_hl = (df["high"] / df["low"]).apply(np.log)
        log_co = (df["close"] / df["open"]).apply(np.log)

        gk_vol = 0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2
        df["gk_volatility"] = np.sqrt(gk_vol.rolling(window=10).mean() * 252)

        return df

    def add_candlestick_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add common candlestick pattern indicators"""
        # Doji (open and close are very close)
        df["doji"] = (
            np.abs(df["close"] - df["open"]) <= 0.1 * (df["high"] - df["low"])
        ).astype(int)

        # Hammer (small body at the top, long lower wick)
        body_size = np.abs(df["close"] - df["open"])
        lower_wick = np.minimum(df["open"], df["close"]) - df["low"]
        upper_wick = df["high"] - np.maximum(df["open"], df["close"])

        df["hammer"] = (
            (body_size <= 0.3 * (df["high"] - df["low"]))
            & (lower_wick >= 2 * body_size)
            & (upper_wick <= 0.2 * body_size)
        ).astype(int)

        # Shooting Star (small body at the bottom, long upper wick)
        df["shooting_star"] = (
            (body_size <= 0.3 * (df["high"] - df["low"]))
            & (upper_wick >= 2 * body_size)
            & (lower_wick <= 0.2 * body_size)
        ).astype(int)

        # Engulfing patterns
        bullish_engulfing = (
            (df["close"].shift(1) < df["open"].shift(1))
            & (df["close"] > df["open"])
            & (df["close"] > df["open"].shift(1))
            & (df["open"] < df["close"].shift(1))
        )

        bearish_engulfing = (
            (df["close"].shift(1) > df["open"].shift(1))
            & (df["close"] < df["open"])
            & (df["close"] < df["open"].shift(1))
            & (df["open"] > df["close"].shift(1))
        )

        df["bullish_engulfing"] = bullish_engulfing.astype(int)
        df["bearish_engulfing"] = bearish_engulfing.astype(int)

        return df

    def add_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add future price returns for training models"""
        # Short-term returns
        df["ret_1d"] = df["close"].pct_change(periods=1).shift(-1)
        df["ret_3d"] = df["close"].pct_change(periods=3).shift(-3)
        df["ret_5d"] = df["close"].pct_change(periods=5).shift(-5)

        # Medium-term returns
        df["ret_10d"] = df["close"].pct_change(periods=10).shift(-10)
        df["ret_20d"] = df["close"].pct_change(periods=20).shift(-20)

        # Long-term returns
        df["ret_60d"] = df["close"].pct_change(periods=60).shift(-60)

        # Binary direction (up/down)
        df["direction_1d"] = (df["ret_1d"] > 0).astype(int)
        df["direction_5d"] = (df["ret_5d"] > 0).astype(int)
        df["direction_20d"] = (df["ret_20d"] > 0).astype(int)

        return df


class SentimentFeatures:
    """Generate sentiment features from news and social media data"""

    def __init__(self):
        self.name = "sentiment_features"

    def generate_features(self, news_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate sentiment features from news data

        Args:
            news_df: DataFrame with news articles

        Returns:
            DataFrame with sentiment features aggregated by date
        """
        # This function would typically use NLP models to analyze sentiment
        # For now, we'll simulate sentiment scores
        if news_df.empty:
            return pd.DataFrame()

        # Make sure we have required columns
        if "title" not in news_df.columns or "publishedAt" not in news_df.columns:
            raise ValueError("News data must contain 'title' and 'publishedAt' columns")

        # Create a copy of the DataFrame
        df = news_df.copy()

        # Simulate sentiment scores
        df["sentiment_score"] = np.random.normal(0, 1, len(df))

        # Normalize scores to [-1, 1] range
        max_score = max(
            abs(df["sentiment_score"].max()), abs(df["sentiment_score"].min())
        )
        df["sentiment_score"] = df["sentiment_score"] / max_score

        # Add sentiment categories
        df["sentiment"] = pd.cut(
            df["sentiment_score"],
            bins=[-1, -0.3, 0.3, 1],
            labels=["negative", "neutral", "positive"],
        )

        # Aggregate by date
        df["date"] = df["publishedAt"].dt.date

        agg_df = df.groupby("date").agg(
            {
                "sentiment_score": ["mean", "std", "count"],
                "sentiment": lambda x: x.value_counts().to_dict(),
            }
        )

        # Flatten the column hierarchy
        agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]

        # Extract sentiment counts
        agg_df["positive_count"] = agg_df["sentiment_<lambda>"].apply(
            lambda x: x.get("positive", 0) if isinstance(x, dict) else 0
        )
        agg_df["neutral_count"] = agg_df["sentiment_<lambda>"].apply(
            lambda x: x.get("neutral", 0) if isinstance(x, dict) else 0
        )
        agg_df["negative_count"] = agg_df["sentiment_<lambda>"].apply(
            lambda x: x.get("negative", 0) if isinstance(x, dict) else 0
        )

        # Calculate sentiment ratio
        agg_df["positive_ratio"] = (
            agg_df["positive_count"] / agg_df["sentiment_score_count"]
        )
        agg_df["negative_ratio"] = (
            agg_df["negative_count"] / agg_df["sentiment_score_count"]
        )

        # Calculate bullish/bearish score
        agg_df["bull_bear_score"] = agg_df["positive_ratio"] - agg_df["negative_ratio"]

        # Drop the dictionary column
        agg_df = agg_df.drop(columns=["sentiment_<lambda>"])

        # Reset index to get date as a column
        agg_df = agg_df.reset_index()
        agg_df["date"] = pd.to_datetime(agg_df["date"])

        return agg_df


class DataCombiner:
    """Combine market data with other data sources"""

    def __init__(self):
        self.name = "data_combiner"

    def combine_market_and_sentiment(
        self, market_data: pd.DataFrame, sentiment_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Combine market data with sentiment data

        Args:
            market_data: DataFrame with market data
            sentiment_data: DataFrame with sentiment features

        Returns:
            Combined DataFrame
        """
        if sentiment_data.empty:
            return market_data

        # Make sure we have a date column in market data
        if market_data.index.name != "date" and "date" not in market_data.columns:
            market_data = market_data.reset_index()
            if "date" not in market_data.columns and "Date" in market_data.columns:
                market_data = market_data.rename(columns={"Date": "date"})

        # Ensure date columns are datetime
        if "date" in market_data.columns:
            market_data["date"] = pd.to_datetime(market_data["date"])

        # Merge the data
        combined_df = pd.merge(market_data, sentiment_data, on="date", how="left")

        # Fill missing sentiment values
        numeric_cols = sentiment_data.select_dtypes(include=[np.number]).columns
        combined_df[numeric_cols] = combined_df[numeric_cols].fillna(0)

        return combined_df

    def combine_market_and_economic(
        self, market_data: pd.DataFrame, economic_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Combine market data with economic indicators

        Args:
            market_data: DataFrame with market data
            economic_data: Dictionary of DataFrames with economic indicators

        Returns:
            Combined DataFrame
        """
        if not economic_data:
            return market_data

        # Make sure we have a date column in market data
        if market_data.index.name != "date" and "date" not in market_data.columns:
            market_data = market_data.reset_index()
            if "date" not in market_data.columns and "Date" in market_data.columns:
                market_data = market_data.rename(columns={"Date": "date"})

        # Ensure date columns are datetime
        if "date" in market_data.columns:
            market_data["date"] = pd.to_datetime(market_data["date"])

        combined_df = market_data.copy()

        # Add each economic indicator
        for indicator, data in economic_data.items():
            # Reset index if needed
            if data.index.name == "date":
                data = data.reset_index()

            # Rename the value column to the indicator name
            if "value" in data.columns:
                data = data.rename(columns={"value": indicator})

            # Merge with market data
            combined_df = pd.merge(
                combined_df, data[["date", indicator]], on="date", how="left"
            )

            # Forward fill missing values (economic data is often reported less frequently)
            combined_df[indicator] = combined_df[indicator].fillna(method="ffill")

        return combined_df


# Helper function to prepare data for ML models
def prepare_ml_features(
    data: pd.DataFrame,
    feature_cols: List[str] = None,
    target_col: str = "ret_1d",
    split_ratio: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare features and target for ML models

    Args:
        data: DataFrame with features and target
        feature_cols: List of feature column names (default: use all numeric columns except targets)
        target_col: Target column name
        split_ratio: Train/test split ratio

    Returns:
        X_train, X_test, y_train, y_test
    """
    # Drop rows with NaN values
    data = data.dropna()

    # If feature_cols not provided, use all numeric columns except targets
    if not feature_cols:
        # Exclude target columns and date-related columns
        exclude_patterns = ["ret_", "direction_", "date", "index"]
        feature_cols = [
            col
            for col in data.select_dtypes(include=[np.number]).columns
            if not any(pattern in col for pattern in exclude_patterns)
        ]

    # Extract features and target
    X = data[feature_cols].values
    y = data[target_col].values

    # Calculate split index
    split_idx = int(len(data) * split_ratio)

    # Split data
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    return X_train, X_test, y_train, y_test
