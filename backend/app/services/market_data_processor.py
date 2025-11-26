"""
Market Data Processor Service
Handles processing and analysis of market data for AI/ML models
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class MarketDataProcessor:
    """
    Advanced market data processing for AI/ML applications
    """

    def __init__(self, db: Session, market_data_service: MarketDataService):
        self.db = db
        self.market_data_service = market_data_service

    async def get_processed_historical_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        features: Optional[List[str]] = None,
        normalize: bool = True,
    ) -> pd.DataFrame:
        """
        Get processed historical data with technical indicators and features

        Args:
            symbols: List of stock symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            features: List of features to include (default: all)
            normalize: Whether to normalize the data

        Returns:
            DataFrame with processed market data
        """
        try:
            # Get raw historical data
            all_data = []
            for symbol in symbols:
                data = await self.market_data_service.get_historical_data(symbol, start_date, end_date)
                if data:
                    df = pd.DataFrame(data)
                    df["symbol"] = symbol
                    all_data.append(df)

            if not all_data:
                logger.warning(f"No historical data found for symbols: {symbols}")
                return pd.DataFrame()

            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
            combined_df = combined_df.sort_values(["symbol", "timestamp"])

            # Calculate technical indicators
            processed_df = self._calculate_technical_indicators(combined_df)

            # Add features if specified
            if features:
                available_features = processed_df.columns.tolist()
                selected_features = ["symbol", "timestamp"] + [f for f in features if f in available_features]
                processed_df = processed_df[selected_features]

            # Normalize if requested
            if normalize:
                processed_df = self._normalize_data(processed_df)

            return processed_df

        except Exception as e:
            logger.error(f"Error processing historical data: {str(e)}")
            return pd.DataFrame()

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the dataset"""
        result_dfs = []

        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol].copy()
            symbol_df = symbol_df.sort_values("timestamp")

            # Price-based indicators
            symbol_df["sma_20"] = symbol_df["close"].rolling(window=20).mean()
            symbol_df["sma_50"] = symbol_df["close"].rolling(window=50).mean()
            symbol_df["ema_12"] = symbol_df["close"].ewm(span=12).mean()
            symbol_df["ema_26"] = symbol_df["close"].ewm(span=26).mean()

            # MACD
            symbol_df["macd"] = symbol_df["ema_12"] - symbol_df["ema_26"]
            symbol_df["macd_signal"] = symbol_df["macd"].ewm(span=9).mean()
            symbol_df["macd_histogram"] = symbol_df["macd"] - symbol_df["macd_signal"]

            # RSI
            symbol_df["rsi"] = self._calculate_rsi(symbol_df["close"])

            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            symbol_df["bb_middle"] = symbol_df["close"].rolling(window=bb_period).mean()
            bb_std_dev = symbol_df["close"].rolling(window=bb_period).std()
            symbol_df["bb_upper"] = symbol_df["bb_middle"] + (bb_std_dev * bb_std)
            symbol_df["bb_lower"] = symbol_df["bb_middle"] - (bb_std_dev * bb_std)
            symbol_df["bb_width"] = symbol_df["bb_upper"] - symbol_df["bb_lower"]
            symbol_df["bb_position"] = (symbol_df["close"] - symbol_df["bb_lower"]) / symbol_df["bb_width"]

            # Volume indicators
            symbol_df["volume_sma"] = symbol_df["volume"].rolling(window=20).mean()
            symbol_df["volume_ratio"] = symbol_df["volume"] / symbol_df["volume_sma"]

            # Price change indicators
            symbol_df["price_change"] = symbol_df["close"].pct_change()
            symbol_df["price_change_5d"] = symbol_df["close"].pct_change(periods=5)
            symbol_df["price_volatility"] = symbol_df["price_change"].rolling(window=20).std()

            # Support and resistance levels
            symbol_df["high_20d"] = symbol_df["high"].rolling(window=20).max()
            symbol_df["low_20d"] = symbol_df["low"].rolling(window=20).min()

            result_dfs.append(symbol_df)

        return pd.concat(result_dfs, ignore_index=True)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical columns"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        exclude_columns = ["symbol", "timestamp"]

        for col in numeric_columns:
            if col not in exclude_columns:
                # Use min-max normalization
                col_min = df[col].min()
                col_max = df[col].max()
                if col_max != col_min:
                    df[col] = (df[col] - col_min) / (col_max - col_min)

        return df

    async def calculate_correlation_matrix(self, symbols: List[str], lookback_days: int = 252) -> pd.DataFrame:
        """
        Calculate correlation matrix for a list of symbols

        Args:
            symbols: List of stock symbols
            lookback_days: Number of days to look back for correlation calculation

        Returns:
            Correlation matrix as DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        # Get price data for all symbols
        price_data = {}
        for symbol in symbols:
            data = await self.market_data_service.get_historical_data(symbol, start_date, end_date)
            if data:
                df = pd.DataFrame(data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp")["close"]
                price_data[symbol] = df

        if not price_data:
            return pd.DataFrame()

        # Create price DataFrame
        price_df = pd.DataFrame(price_data)

        # Calculate returns
        returns_df = price_df.pct_change().dropna()

        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()

        return correlation_matrix

    async def calculate_volatility_metrics(self, symbol: str, lookback_days: int = 30) -> Dict[str, float]:
        """
        Calculate various volatility metrics for a symbol

        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back

        Returns:
            Dictionary with volatility metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        data = await self.market_data_service.get_historical_data(symbol, start_date, end_date)

        if not data:
            return {}

        df = pd.DataFrame(data)
        df["returns"] = df["close"].pct_change()

        # Calculate various volatility measures
        daily_vol = df["returns"].std()
        annualized_vol = daily_vol * np.sqrt(252)

        # Calculate high-low volatility
        df["hl_vol"] = np.log(df["high"] / df["low"])
        hl_volatility = df["hl_vol"].mean() * np.sqrt(252)

        # Calculate maximum drawdown
        df["cumulative"] = (1 + df["returns"]).cumprod()
        df["rolling_max"] = df["cumulative"].expanding().max()
        df["drawdown"] = df["cumulative"] / df["rolling_max"] - 1
        max_drawdown = df["drawdown"].min()

        return {
            "daily_volatility": daily_vol,
            "annualized_volatility": annualized_vol,
            "high_low_volatility": hl_volatility,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": df["returns"].mean() / daily_vol if daily_vol > 0 else 0,
        }

    async def detect_market_regime(self, symbols: List[str], lookback_days: int = 60) -> Dict[str, Any]:
        """
        Detect current market regime based on multiple indicators

        Args:
            symbols: List of market symbols to analyze
            lookback_days: Number of days to analyze

        Returns:
            Dictionary with market regime information
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        regime_scores = []

        for symbol in symbols:
            data = await self.market_data_service.get_historical_data(symbol, start_date, end_date)

            if not data:
                continue

            df = pd.DataFrame(data)
            df["returns"] = df["close"].pct_change()

            # Calculate regime indicators
            volatility = df["returns"].std()
            trend = df["close"].iloc[-1] / df["close"].iloc[0] - 1

            # Volatility regime (high volatility = stress)
            vol_percentile = df["returns"].rolling(20).std().rank(pct=True).iloc[-1]

            regime_scores.append(
                {"symbol": symbol, "volatility_percentile": vol_percentile, "trend": trend, "volatility": volatility}
            )

        if not regime_scores:
            return {"regime": "unknown", "confidence": 0.0}

        # Aggregate scores
        avg_vol_percentile = np.mean([s["volatility_percentile"] for s in regime_scores])
        avg_trend = np.mean([s["trend"] for s in regime_scores])

        # Determine regime
        if avg_vol_percentile > 0.8:
            regime = "high_volatility"
        elif avg_vol_percentile < 0.2 and avg_trend > 0.02:
            regime = "bull_market"
        elif avg_vol_percentile < 0.2 and avg_trend < -0.02:
            regime = "bear_market"
        else:
            regime = "normal"

        confidence = min(abs(avg_vol_percentile - 0.5) * 2, 1.0)

        return {
            "regime": regime,
            "confidence": confidence,
            "volatility_percentile": avg_vol_percentile,
            "trend": avg_trend,
            "details": regime_scores,
        }
