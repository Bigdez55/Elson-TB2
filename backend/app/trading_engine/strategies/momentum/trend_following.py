"""
Trend Following Strategy

Classic trend following using multiple moving averages,
ADX for trend strength, and ATR for position sizing.
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
    name="trend_following",
    category=StrategyCategory.MOMENTUM,
    description="Classic trend following with multiple timeframe analysis",
    default_parameters={
        "fast_ma": 20,
        "medium_ma": 50,
        "slow_ma": 200,
        "adx_period": 14,
        "adx_threshold": 25,
        "atr_period": 14,
        "use_supertrend": True,
        "supertrend_multiplier": 3.0,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["high", "low", "close"],
    timeframes=["4h", "1d"],
    risk_level="medium",
)
class TrendFollowingStrategy(TradingStrategy):
    """
    Trend Following Strategy

    Uses multiple moving averages and ADX to identify
    and follow strong trends.

    Features:
    - Triple MA system (fast/medium/slow)
    - ADX trend strength filter
    - Supertrend for entries/exits
    - ATR-based stops
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        fast_ma: int = 20,
        medium_ma: int = 50,
        slow_ma: int = 200,
        adx_period: int = 14,
        adx_threshold: int = 25,
        atr_period: int = 14,
        use_supertrend: bool = True,
        supertrend_multiplier: float = 3.0,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Trend Following",
            description="Multi-MA trend following with ADX",
            parameters={
                "fast_ma": fast_ma,
                "medium_ma": medium_ma,
                "slow_ma": slow_ma,
                "adx_period": adx_period,
                "adx_threshold": adx_threshold,
                "atr_period": atr_period,
                "use_supertrend": use_supertrend,
                "supertrend_multiplier": supertrend_multiplier,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.fast_ma = fast_ma
        self.medium_ma = medium_ma
        self.slow_ma = slow_ma
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.atr_period = atr_period
        self.use_supertrend = use_supertrend
        self.supertrend_multiplier = supertrend_multiplier

        # State
        self.current_trend = None
        self.trend_strength = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.slow_ma + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient data"
                )

            df = self._calculate_indicators(df)
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in trend following: {str(e)}")
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
        except Exception:
            return False

    async def _get_historical_data(self) -> Optional[pd.DataFrame]:
        """Get historical data"""
        try:
            if self.market_data_service is None:
                return None

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=300)

            data = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not data:
                return None

            df = pd.DataFrame(data) if isinstance(data, list) else data
            df.columns = df.columns.str.lower()
            df = df.sort_values("timestamp" if "timestamp" in df.columns else df.index)
            return df.reset_index(drop=True)

        except Exception:
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend indicators"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")

        # Moving averages
        df["ma_fast"] = df["close"].rolling(window=self.fast_ma).mean()
        df["ma_medium"] = df["close"].rolling(window=self.medium_ma).mean()
        df["ma_slow"] = df["close"].rolling(window=self.slow_ma).mean()

        # ADX
        df = self._calculate_adx(df)

        # ATR
        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1))
            )
        )
        df["atr"] = df["tr"].rolling(window=self.atr_period).mean()

        # Supertrend
        if self.use_supertrend:
            df = self._calculate_supertrend(df)

        # MA alignment
        df["ma_bullish"] = (
            (df["ma_fast"] > df["ma_medium"]) &
            (df["ma_medium"] > df["ma_slow"])
        )
        df["ma_bearish"] = (
            (df["ma_fast"] < df["ma_medium"]) &
            (df["ma_medium"] < df["ma_slow"])
        )

        return df

    def _calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX indicator"""
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift(1))
        df["tr3"] = abs(df["low"] - df["close"].shift(1))
        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

        df["dm_plus"] = np.where(
            (df["high"] - df["high"].shift(1)) > (df["low"].shift(1) - df["low"]),
            np.maximum(df["high"] - df["high"].shift(1), 0), 0
        )
        df["dm_minus"] = np.where(
            (df["low"].shift(1) - df["low"]) > (df["high"] - df["high"].shift(1)),
            np.maximum(df["low"].shift(1) - df["low"], 0), 0
        )

        df["atr_adx"] = df["tr"].rolling(window=self.adx_period).mean()
        df["dm_plus_smooth"] = df["dm_plus"].rolling(window=self.adx_period).mean()
        df["dm_minus_smooth"] = df["dm_minus"].rolling(window=self.adx_period).mean()

        df["di_plus"] = 100 * df["dm_plus_smooth"] / df["atr_adx"]
        df["di_minus"] = 100 * df["dm_minus_smooth"] / df["atr_adx"]

        df["dx"] = 100 * abs(df["di_plus"] - df["di_minus"]) / (df["di_plus"] + df["di_minus"])
        df["adx"] = df["dx"].rolling(window=self.adx_period).mean()

        return df

    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        hl2 = (df["high"] + df["low"]) / 2
        atr = df["atr"]

        upper_band = hl2 + (self.supertrend_multiplier * atr)
        lower_band = hl2 - (self.supertrend_multiplier * atr)

        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        for i in range(1, len(df)):
            if df["close"].iloc[i] > upper_band.iloc[i-1]:
                direction.iloc[i] = 1
            elif df["close"].iloc[i] < lower_band.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]

            if direction.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        df["supertrend"] = supertrend
        df["supertrend_direction"] = direction

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        adx = float(last_row.get("adx", 0))
        di_plus = float(last_row.get("di_plus", 0))
        di_minus = float(last_row.get("di_minus", 0))
        ma_bullish = bool(last_row.get("ma_bullish", False))
        ma_bearish = bool(last_row.get("ma_bearish", False))
        atr = float(last_row.get("atr", 0))

        self.trend_strength = "strong" if adx > 40 else ("moderate" if adx > 25 else "weak")

        action = "hold"
        confidence = 0.0
        reasons = []

        # Only trade when trend is present
        if adx < self.adx_threshold:
            return {
                "action": "hold",
                "confidence": 0.0,
                "price": current_price,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": f"No trend (ADX: {adx:.1f})",
                "indicators": self._get_indicators(last_row),
            }

        # Bullish trend
        if ma_bullish and di_plus > di_minus:
            action = "buy"
            confidence = 0.6
            reasons.append("MAs aligned bullish")
            reasons.append(f"+DI > -DI ({di_plus:.1f} > {di_minus:.1f})")

            if adx > 40:
                confidence = min(confidence + 0.2, 1.0)
                reasons.append(f"Strong trend (ADX: {adx:.1f})")

            # Supertrend confirmation
            if self.use_supertrend:
                st_dir = last_row.get("supertrend_direction", 0)
                if st_dir == 1:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Supertrend bullish")
                elif st_dir == -1:
                    confidence *= 0.7
                    reasons.append("Supertrend disagrees")

            self.current_trend = "bullish"

        # Bearish trend
        elif ma_bearish and di_minus > di_plus:
            action = "sell"
            confidence = 0.6
            reasons.append("MAs aligned bearish")
            reasons.append(f"-DI > +DI ({di_minus:.1f} > {di_plus:.1f})")

            if adx > 40:
                confidence = min(confidence + 0.2, 1.0)
                reasons.append(f"Strong trend (ADX: {adx:.1f})")

            if self.use_supertrend:
                st_dir = last_row.get("supertrend_direction", 0)
                if st_dir == -1:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Supertrend bearish")
                elif st_dir == 1:
                    confidence *= 0.7
                    reasons.append("Supertrend disagrees")

            self.current_trend = "bearish"

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear trend",
            "indicators": self._get_indicators(last_row),
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(current_price, action, atr))

        return signal

    def _get_indicators(self, row: pd.Series) -> Dict[str, Any]:
        """Get indicator values"""
        return {
            "ma_fast": float(row.get("ma_fast", 0)),
            "ma_medium": float(row.get("ma_medium", 0)),
            "ma_slow": float(row.get("ma_slow", 0)),
            "adx": float(row.get("adx", 0)),
            "di_plus": float(row.get("di_plus", 0)),
            "di_minus": float(row.get("di_minus", 0)),
            "atr": float(row.get("atr", 0)),
            "supertrend": float(row.get("supertrend", 0)) if pd.notna(row.get("supertrend")) else None,
            "supertrend_direction": int(row.get("supertrend_direction", 0)) if pd.notna(row.get("supertrend_direction")) else None,
            "trend_strength": self.trend_strength,
            "current_trend": self.current_trend,
        }

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        atr: float
    ) -> Dict[str, float]:
        """Calculate stops using ATR"""
        atr_multiplier = 2.5

        if action == "buy":
            stop_loss = price - (atr * atr_multiplier)
            take_profit = price + (atr * atr_multiplier * 3)  # 3:1 R/R
        else:
            stop_loss = price + (atr * atr_multiplier)
            take_profit = price - (atr * atr_multiplier * 3)

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
