"""
Data Handler for Backtesting

Manages historical data loading, preprocessing, and iteration for backtests.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Bar:
    """Represents a single price bar (OHLCV)"""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol,
        }


class DataHandler:
    """
    Handles historical data for backtesting.

    Supports multiple data sources and formats, with built-in
    validation and preprocessing.
    """

    def __init__(self):
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_index: int = 0
        self.symbols: List[str] = []
        self._preprocessed: bool = False

    def load_dataframe(
        self,
        symbol: str,
        df: pd.DataFrame,
        date_column: str = "timestamp",
    ) -> None:
        """
        Load data from a pandas DataFrame.

        Args:
            symbol: Symbol identifier
            df: DataFrame with OHLCV data
            date_column: Name of date column
        """
        df = df.copy()

        # Standardize column names
        df.columns = df.columns.str.lower()

        # Ensure we have required columns
        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Handle date column
        if date_column in df.columns:
            df["timestamp"] = pd.to_datetime(df[date_column])
        elif "timestamp" not in df.columns:
            df["timestamp"] = df.index

        df["symbol"] = symbol
        df = df.sort_values("timestamp").reset_index(drop=True)

        self.data[symbol] = df
        if symbol not in self.symbols:
            self.symbols.append(symbol)

        logger.info(f"Loaded {len(df)} bars for {symbol}")

    def load_dict(
        self,
        symbol: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """
        Load data from a list of dictionaries.

        Args:
            symbol: Symbol identifier
            data: List of OHLCV dictionaries
        """
        df = pd.DataFrame(data)
        self.load_dataframe(symbol, df)

    def load_csv(
        self,
        symbol: str,
        filepath: str,
        date_column: str = "timestamp",
        date_format: Optional[str] = None,
    ) -> None:
        """
        Load data from a CSV file.

        Args:
            symbol: Symbol identifier
            filepath: Path to CSV file
            date_column: Name of date column
            date_format: Date format string
        """
        parse_dates = [date_column] if date_format is None else False
        df = pd.read_csv(filepath, parse_dates=parse_dates)

        if date_format:
            df[date_column] = pd.to_datetime(df[date_column], format=date_format)

        self.load_dataframe(symbol, df, date_column)

    def preprocess(
        self,
        fill_missing: bool = True,
        remove_outliers: bool = False,
        outlier_std: float = 5.0,
    ) -> None:
        """
        Preprocess loaded data.

        Args:
            fill_missing: Forward-fill missing values
            remove_outliers: Remove extreme outliers
            outlier_std: Standard deviations for outlier detection
        """
        for symbol in self.symbols:
            df = self.data[symbol]

            # Fill missing values
            if fill_missing:
                df = df.fillna(method="ffill").fillna(method="bfill")

            # Remove outliers
            if remove_outliers:
                returns = df["close"].pct_change()
                mean_ret = returns.mean()
                std_ret = returns.std()
                mask = abs(returns - mean_ret) <= outlier_std * std_ret
                mask = mask | mask.isna()  # Keep first row
                df = df[mask]

            # Ensure data types
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            self.data[symbol] = df.reset_index(drop=True)

        self._preprocessed = True
        logger.info(f"Preprocessed data for {len(self.symbols)} symbols")

    def get_date_range(self) -> tuple:
        """Get the common date range across all symbols"""
        if not self.data:
            return None, None

        start_dates = []
        end_dates = []

        for df in self.data.values():
            start_dates.append(df["timestamp"].min())
            end_dates.append(df["timestamp"].max())

        return max(start_dates), min(end_dates)

    def align_data(self) -> None:
        """Align all data to common timestamps"""
        if len(self.symbols) <= 1:
            return

        # Get common timestamps
        common_timestamps = None
        for symbol in self.symbols:
            timestamps = set(self.data[symbol]["timestamp"])
            if common_timestamps is None:
                common_timestamps = timestamps
            else:
                common_timestamps = common_timestamps.intersection(timestamps)

        # Filter to common timestamps
        for symbol in self.symbols:
            df = self.data[symbol]
            df = df[df["timestamp"].isin(common_timestamps)]
            self.data[symbol] = df.reset_index(drop=True)

        logger.info(f"Aligned data to {len(common_timestamps)} common timestamps")

    def get_bar(self, symbol: str, index: int) -> Optional[Bar]:
        """Get a specific bar by index"""
        if symbol not in self.data:
            return None

        df = self.data[symbol]
        if index < 0 or index >= len(df):
            return None

        row = df.iloc[index]
        return Bar(
            timestamp=row["timestamp"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            symbol=symbol,
        )

    def get_bars(self, symbol: str, start_index: int, count: int) -> List[Bar]:
        """Get multiple bars"""
        bars = []
        for i in range(start_index, min(start_index + count, len(self.data[symbol]))):
            bar = self.get_bar(symbol, i)
            if bar:
                bars.append(bar)
        return bars

    def get_lookback(
        self, symbol: str, current_index: int, lookback: int
    ) -> pd.DataFrame:
        """
        Get lookback window of data.

        Args:
            symbol: Symbol to get data for
            current_index: Current bar index
            lookback: Number of bars to look back

        Returns:
            DataFrame with lookback data
        """
        if symbol not in self.data:
            return pd.DataFrame()

        start = max(0, current_index - lookback + 1)
        end = current_index + 1

        return self.data[symbol].iloc[start:end].copy()

    def iterate_bars(self, warmup: int = 0) -> Generator[Dict[str, Bar], None, None]:
        """
        Iterate through bars for all symbols.

        Args:
            warmup: Number of initial bars to skip (for indicator warmup)

        Yields:
            Dictionary of symbol -> Bar for each timestamp
        """
        if not self.data:
            return

        # Get minimum length
        min_length = min(len(df) for df in self.data.values())

        for i in range(warmup, min_length):
            self.current_index = i
            bars = {}

            for symbol in self.symbols:
                bar = self.get_bar(symbol, i)
                if bar:
                    bars[symbol] = bar

            if bars:
                yield bars

    def get_market_data(self, symbol: str, index: int) -> Dict[str, Any]:
        """
        Get market data dictionary for strategy consumption.

        Args:
            symbol: Symbol to get data for
            index: Bar index

        Returns:
            Market data dictionary
        """
        bar = self.get_bar(symbol, index)
        if not bar:
            return {}

        return {
            "symbol": symbol,
            "price": bar.close,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "timestamp": bar.timestamp.isoformat(),
        }

    def add_indicator(
        self, symbol: str, name: str, values: Union[List[float], np.ndarray, pd.Series]
    ) -> None:
        """
        Add a calculated indicator to the data.

        Args:
            symbol: Symbol to add indicator to
            name: Indicator name
            values: Indicator values
        """
        if symbol not in self.data:
            return

        if len(values) != len(self.data[symbol]):
            raise ValueError(
                f"Indicator length {len(values)} doesn't match "
                f"data length {len(self.data[symbol])}"
            )

        self.data[symbol][name] = values

    def calculate_returns(self, symbol: str) -> pd.Series:
        """Calculate daily returns for a symbol"""
        if symbol not in self.data:
            return pd.Series()
        return self.data[symbol]["close"].pct_change()

    def get_statistics(self, symbol: str) -> Dict[str, float]:
        """Get basic statistics for a symbol"""
        if symbol not in self.data:
            return {}

        df = self.data[symbol]
        returns = self.calculate_returns(symbol)

        return {
            "count": len(df),
            "start_date": str(df["timestamp"].min()),
            "end_date": str(df["timestamp"].max()),
            "min_price": df["close"].min(),
            "max_price": df["close"].max(),
            "avg_price": df["close"].mean(),
            "avg_volume": df["volume"].mean(),
            "volatility": returns.std() * np.sqrt(252),  # Annualized
            "total_return": (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100,
        }

    def __len__(self) -> int:
        """Get minimum data length"""
        if not self.data:
            return 0
        return min(len(df) for df in self.data.values())
