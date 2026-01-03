"""
Bollinger Bands Trading Strategy

Implements multiple Bollinger Bands strategies:
- Mean reversion (bounce from bands)
- Squeeze breakout (volatility expansion)
- %B indicator trading
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="bollinger_bands",
    category=StrategyCategory.TECHNICAL,
    description="Bollinger Bands strategy with squeeze detection and mean reversion",
    default_parameters={
        "period": 20,
        "std_dev": 2.0,
        "squeeze_threshold": 0.06,
        "mode": "mean_reversion",  # mean_reversion, breakout, or combined
        "use_rsi_filter": True,
        "rsi_period": 14,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close", "high", "low", "volume"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class BollingerBandsStrategy(TradingStrategy):
    """
    Bollinger Bands Trading Strategy

    Modes:
    - mean_reversion: Buy at lower band, sell at upper band
    - breakout: Trade in direction of band breakout
    - combined: Use squeeze for breakout, bands for mean reversion

    Features:
    - Bollinger Band Width (BBW) for squeeze detection
    - %B indicator for relative position
    - RSI filter for confirmation
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        period: int = 20,
        std_dev: float = 2.0,
        squeeze_threshold: float = 0.06,
        mode: str = "mean_reversion",
        use_rsi_filter: bool = True,
        rsi_period: int = 14,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Bollinger Bands Strategy",
            description=f"Bollinger Bands {mode} strategy",
            parameters={
                "period": period,
                "std_dev": std_dev,
                "squeeze_threshold": squeeze_threshold,
                "mode": mode,
                "use_rsi_filter": use_rsi_filter,
                "rsi_period": rsi_period,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.period = period
        self.std_dev = std_dev
        self.squeeze_threshold = squeeze_threshold
        self.mode = mode
        self.use_rsi_filter = use_rsi_filter
        self.rsi_period = rsi_period

        # State tracking
        self.last_bandwidth = None
        self.in_squeeze = False

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on Bollinger Bands"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.period + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            # Calculate Bollinger Bands
            df = self._calculate_bollinger_bands(df)

            # Calculate RSI if using filter
            if self.use_rsi_filter:
                df = self._calculate_rsi(df)

            # Generate trading decision based on mode
            if self.mode == "mean_reversion":
                signal = self._mean_reversion_signal(df)
            elif self.mode == "breakout":
                signal = self._breakout_signal(df)
            else:  # combined
                signal = self._combined_signal(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating Bollinger Bands signal: {str(e)}")
            return self._create_hold_signal(
                market_data.get("price", 0.0),
                f"Error: {str(e)}"
            )

    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters"""
        try:
            for key, value in new_parameters.items():
                if key in self.parameters:
                    self.parameters[key] = value
                    if hasattr(self, key):
                        setattr(self, key, value)
            logger.info(f"Updated Bollinger Bands parameters: {new_parameters}")
            return True
        except Exception as e:
            logger.error(f"Error updating parameters: {str(e)}")
            return False

    async def _get_historical_data(self) -> Optional[pd.DataFrame]:
        """Get historical market data"""
        try:
            if self.market_data_service is None:
                return None

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=100)

            data = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not data:
                return None

            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = data

            df.columns = df.columns.str.lower()
            df = df.sort_values("timestamp" if "timestamp" in df.columns else df.index)
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands and related indicators"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Calculate SMA (middle band)
        df["bb_middle"] = df["close"].rolling(window=self.period).mean()

        # Calculate standard deviation
        df["bb_std"] = df["close"].rolling(window=self.period).std()

        # Calculate upper and lower bands
        df["bb_upper"] = df["bb_middle"] + (df["bb_std"] * self.std_dev)
        df["bb_lower"] = df["bb_middle"] - (df["bb_std"] * self.std_dev)

        # Calculate %B (relative position within bands)
        df["percent_b"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        # Calculate Bollinger Band Width (BBW)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

        # Calculate bandwidth percentile (for squeeze detection)
        df["bbw_percentile"] = df["bb_width"].rolling(window=100).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )

        return df

    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI for confirmation"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        return df

    def _mean_reversion_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate mean reversion signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        percent_b = float(last_row["percent_b"])
        bb_width = float(last_row["bb_width"])
        bb_upper = float(last_row["bb_upper"])
        bb_lower = float(last_row["bb_lower"])
        bb_middle = float(last_row["bb_middle"])

        action = "hold"
        confidence = 0.0
        reasons = []

        # Buy signal: price near or below lower band
        if percent_b < 0:  # Below lower band
            action = "buy"
            confidence = 0.8
            reasons.append(f"Price below lower band (%B: {percent_b:.2f})")
        elif percent_b < 0.2:  # Near lower band
            action = "buy"
            confidence = 0.6
            reasons.append(f"Price near lower band (%B: {percent_b:.2f})")

        # Sell signal: price near or above upper band
        elif percent_b > 1:  # Above upper band
            action = "sell"
            confidence = 0.8
            reasons.append(f"Price above upper band (%B: {percent_b:.2f})")
        elif percent_b > 0.8:  # Near upper band
            action = "sell"
            confidence = 0.6
            reasons.append(f"Price near upper band (%B: {percent_b:.2f})")

        # RSI confirmation
        if self.use_rsi_filter and "rsi" in last_row:
            rsi = float(last_row["rsi"])
            if action == "buy" and rsi < 30:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append(f"RSI confirms oversold ({rsi:.1f})")
            elif action == "sell" and rsi > 70:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append(f"RSI confirms overbought ({rsi:.1f})")
            elif action == "buy" and rsi > 70:
                confidence *= 0.5  # Reduce confidence if RSI disagrees
                reasons.append(f"RSI divergence warning ({rsi:.1f})")
            elif action == "sell" and rsi < 30:
                confidence *= 0.5
                reasons.append(f"RSI divergence warning ({rsi:.1f})")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No signal",
            "indicators": {
                "percent_b": percent_b,
                "bb_width": bb_width,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
                "bb_middle": bb_middle,
                "rsi": float(last_row.get("rsi", 50)),
            },
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(
                current_price, action, bb_middle, bb_upper, bb_lower
            ))

        return signal

    def _breakout_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate breakout signals (from squeeze)"""
        last_row = df.iloc[-1]
        prev_rows = df.iloc[-5:-1]  # Look at last 4 bars

        current_price = float(last_row["close"])
        bb_width = float(last_row["bb_width"])
        percent_b = float(last_row["percent_b"])
        bb_upper = float(last_row["bb_upper"])
        bb_lower = float(last_row["bb_lower"])
        bb_middle = float(last_row["bb_middle"])

        # Check for squeeze (low bandwidth)
        was_in_squeeze = prev_rows["bb_width"].mean() < self.squeeze_threshold
        expanding = bb_width > prev_rows["bb_width"].mean()

        self.in_squeeze = bb_width < self.squeeze_threshold
        self.last_bandwidth = bb_width

        action = "hold"
        confidence = 0.0
        reasons = []

        if was_in_squeeze and expanding:
            # Squeeze is releasing - trade the breakout direction
            if percent_b > 0.8:  # Breaking upward
                action = "buy"
                confidence = 0.7
                reasons.append("Squeeze breakout - upward")
            elif percent_b < 0.2:  # Breaking downward
                action = "sell"
                confidence = 0.7
                reasons.append("Squeeze breakout - downward")

        # Volume confirmation
        if "volume" in last_row and "volume" in prev_rows.columns:
            vol_ratio = float(last_row["volume"]) / prev_rows["volume"].mean()
            if vol_ratio > 1.5 and action != "hold":
                confidence = min(confidence + 0.15, 1.0)
                reasons.append(f"Volume confirms breakout ({vol_ratio:.1f}x)")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No breakout signal",
            "indicators": {
                "percent_b": percent_b,
                "bb_width": bb_width,
                "in_squeeze": self.in_squeeze,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
            },
        }

        if action in ["buy", "sell"]:
            # For breakouts, use wider stops
            signal.update(self._calculate_breakout_stops(
                current_price, action, bb_width
            ))

        return signal

    def _combined_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Combine mean reversion and breakout strategies"""
        last_row = df.iloc[-1]
        bb_width = float(last_row["bb_width"])

        # Use breakout strategy if in squeeze
        if bb_width < self.squeeze_threshold:
            return self._breakout_signal(df)
        else:
            return self._mean_reversion_signal(df)

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        middle: float,
        upper: float,
        lower: float,
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit for mean reversion"""
        if action == "buy":
            return {
                "stop_loss": lower * 0.99,  # Just below lower band
                "take_profit": middle,  # Target middle band
            }
        else:  # sell
            return {
                "stop_loss": upper * 1.01,  # Just above upper band
                "take_profit": middle,  # Target middle band
            }

    def _calculate_breakout_stops(
        self,
        price: float,
        action: str,
        bb_width: float,
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit for breakouts"""
        # Use BB width as a volatility measure
        stop_distance = price * bb_width * 0.5
        profit_distance = price * bb_width * 1.5  # 3:1 reward/risk

        if action == "buy":
            return {
                "stop_loss": price - stop_distance,
                "take_profit": price + profit_distance,
            }
        else:  # sell
            return {
                "stop_loss": price + stop_distance,
                "take_profit": price - profit_distance,
            }

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create a hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {},
        }
