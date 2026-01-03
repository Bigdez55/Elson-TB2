"""
RSI Mean Reversion Strategy

Uses RSI extremes to identify mean reversion opportunities
with multiple confirmation filters.
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
    name="rsi_mean_reversion",
    category=StrategyCategory.MEAN_REVERSION,
    description="RSI-based mean reversion with trend filter",
    default_parameters={
        "rsi_period": 14,
        "oversold_level": 30,
        "overbought_level": 70,
        "extreme_oversold": 20,
        "extreme_overbought": 80,
        "use_trend_filter": True,
        "trend_period": 50,
        "require_reversal_candle": True,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["open", "high", "low", "close"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class RSIMeanReversion(TradingStrategy):
    """
    RSI Mean Reversion Strategy

    Trades reversals when RSI reaches extreme levels,
    with optional trend filter and reversal candle confirmation.
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        rsi_period: int = 14,
        oversold_level: int = 30,
        overbought_level: int = 70,
        extreme_oversold: int = 20,
        extreme_overbought: int = 80,
        use_trend_filter: bool = True,
        trend_period: int = 50,
        require_reversal_candle: bool = True,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="RSI Mean Reversion",
            description="RSI extremes with reversal confirmation",
            parameters={
                "rsi_period": rsi_period,
                "oversold_level": oversold_level,
                "overbought_level": overbought_level,
                "extreme_oversold": extreme_oversold,
                "extreme_overbought": extreme_overbought,
                "use_trend_filter": use_trend_filter,
                "trend_period": trend_period,
                "require_reversal_candle": require_reversal_candle,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.rsi_period = rsi_period
        self.oversold_level = oversold_level
        self.overbought_level = overbought_level
        self.extreme_oversold = extreme_oversold
        self.extreme_overbought = extreme_overbought
        self.use_trend_filter = use_trend_filter
        self.trend_period = trend_period
        self.require_reversal_candle = require_reversal_candle

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < max(self.rsi_period, self.trend_period) + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient data"
                )

            df = self._calculate_indicators(df)
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in RSI mean reversion: {str(e)}")
            return self._create_hold_signal(
                market_data.get("price", 0.0),
                f"Error: {str(e)}"
            )

    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update parameters"""
        try:
            for key, value in new_parameters.items():
                if key in self.parameters:
                    self.parameters[key] = value
                    if hasattr(self, key):
                        setattr(self, key, value)
            return True
        except Exception as e:
            return False

    async def _get_historical_data(self) -> Optional[pd.DataFrame]:
        """Get historical data"""
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

            df = pd.DataFrame(data) if isinstance(data, list) else data
            df.columns = df.columns.str.lower()
            df = df.sort_values("timestamp" if "timestamp" in df.columns else df.index)
            return df.reset_index(drop=True)

        except Exception as e:
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI and trend indicators"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        # Trend filter
        if self.use_trend_filter:
            df["sma"] = df["close"].rolling(window=self.trend_period).mean()
            df["trend"] = np.where(df["close"] > df["sma"], "up", "down")

        # Reversal candle detection
        df["bullish_candle"] = df["close"] > df["open"]
        df["bearish_candle"] = df["close"] < df["open"]

        # Candle body size
        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        rsi = float(last_row["rsi"])
        prev_rsi = float(prev_row["rsi"])

        action = "hold"
        confidence = 0.0
        reasons = []

        # Trend context
        trend = last_row.get("trend", "neutral") if self.use_trend_filter else "neutral"

        # Oversold conditions - potential buy
        if rsi < self.oversold_level:
            # Check for RSI turning up
            rsi_turning_up = rsi > prev_rsi

            if rsi < self.extreme_oversold:
                action = "buy"
                confidence = 0.75
                reasons.append(f"Extreme oversold RSI: {rsi:.1f}")
            elif rsi_turning_up:
                action = "buy"
                confidence = 0.6
                reasons.append(f"RSI oversold and turning ({rsi:.1f})")

            # Reversal candle confirmation
            if self.require_reversal_candle:
                if last_row["bullish_candle"]:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Bullish reversal candle")
                else:
                    confidence *= 0.7
                    reasons.append("No reversal candle yet")

            # Trend filter
            if self.use_trend_filter and trend == "up":
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("With overall uptrend")
            elif self.use_trend_filter and trend == "down":
                confidence *= 0.8
                reasons.append("Against downtrend (caution)")

        # Overbought conditions - potential sell
        elif rsi > self.overbought_level:
            rsi_turning_down = rsi < prev_rsi

            if rsi > self.extreme_overbought:
                action = "sell"
                confidence = 0.75
                reasons.append(f"Extreme overbought RSI: {rsi:.1f}")
            elif rsi_turning_down:
                action = "sell"
                confidence = 0.6
                reasons.append(f"RSI overbought and turning ({rsi:.1f})")

            if self.require_reversal_candle:
                if last_row["bearish_candle"]:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Bearish reversal candle")
                else:
                    confidence *= 0.7
                    reasons.append("No reversal candle yet")

            if self.use_trend_filter and trend == "down":
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("With overall downtrend")
            elif self.use_trend_filter and trend == "up":
                confidence *= 0.8
                reasons.append("Against uptrend (caution)")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No signal",
            "indicators": {
                "rsi": rsi,
                "prev_rsi": prev_rsi,
                "trend": trend,
                "bullish_candle": bool(last_row.get("bullish_candle", False)),
                "bearish_candle": bool(last_row.get("bearish_candle", False)),
            },
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(current_price, action, df))

        return signal

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        df: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate stops using recent swing points"""
        recent_high = df.tail(10)["high"].max()
        recent_low = df.tail(10)["low"].min()

        if action == "buy":
            stop_loss = recent_low * 0.99
            risk = price - stop_loss
            take_profit = price + (risk * 2)  # 2:1 R/R
        else:
            stop_loss = recent_high * 1.01
            risk = stop_loss - price
            take_profit = price - (risk * 2)

        return {"stop_loss": stop_loss, "take_profit": take_profit}

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {},
        }
