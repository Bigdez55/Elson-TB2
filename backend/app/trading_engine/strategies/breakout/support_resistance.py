"""
Support/Resistance Breakout Strategy

Identifies key support and resistance levels and trades breakouts
with volume confirmation and retest entries.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="support_resistance_breakout",
    category=StrategyCategory.BREAKOUT,
    description="Support/Resistance breakout with volume confirmation",
    default_parameters={
        "lookback_period": 20,
        "level_tolerance": 0.002,  # 0.2% tolerance for level clustering
        "volume_confirmation": 1.5,  # Volume must be 1.5x average
        "breakout_threshold": 0.005,  # 0.5% beyond level
        "retest_enabled": True,
        "min_touches": 2,  # Minimum touches to confirm level
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["open", "high", "low", "close", "volume"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class SupportResistanceBreakout(TradingStrategy):
    """
    Support/Resistance Breakout Strategy

    Features:
    - Automatic S/R level identification using swing highs/lows
    - Level clustering for stronger zones
    - Volume confirmation for breakouts
    - Optional retest entry strategy
    - False breakout filtering
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        lookback_period: int = 20,
        level_tolerance: float = 0.002,
        volume_confirmation: float = 1.5,
        breakout_threshold: float = 0.005,
        retest_enabled: bool = True,
        min_touches: int = 2,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Support/Resistance Breakout",
            description="Breakout trading at key S/R levels",
            parameters={
                "lookback_period": lookback_period,
                "level_tolerance": level_tolerance,
                "volume_confirmation": volume_confirmation,
                "breakout_threshold": breakout_threshold,
                "retest_enabled": retest_enabled,
                "min_touches": min_touches,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.lookback_period = lookback_period
        self.level_tolerance = level_tolerance
        self.volume_confirmation = volume_confirmation
        self.breakout_threshold = breakout_threshold
        self.retest_enabled = retest_enabled
        self.min_touches = min_touches

        # State
        self.support_levels: List[float] = []
        self.resistance_levels: List[float] = []
        self.recent_breakout = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on S/R breakout"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.lookback_period * 2:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Identify S/R levels
            self._identify_levels(df)

            # Calculate volume metrics
            df = self._calculate_volume_metrics(df)

            # Check for breakout
            signal = self._check_breakout(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in S/R breakout strategy: {str(e)}")
            return self._create_hold_signal(
                market_data.get("price", 0.0), f"Error: {str(e)}"
            )

    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters"""
        try:
            for key, value in new_parameters.items():
                if key in self.parameters:
                    self.parameters[key] = value
                    if hasattr(self, key):
                        setattr(self, key, value)
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
            start_date = end_date - timedelta(days=90)

            data = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not data:
                return None

            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data]) if isinstance(data, dict) else data

            df.columns = df.columns.str.lower()
            df = df.sort_values("timestamp" if "timestamp" in df.columns else df.index)
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None

    def _identify_levels(self, df: pd.DataFrame) -> None:
        """Identify support and resistance levels"""
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Find swing highs and lows
        swing_highs = []
        swing_lows = []

        for i in range(2, len(df) - 2):
            # Swing high: higher than 2 bars on each side
            if (
                df.iloc[i]["high"] > df.iloc[i - 1]["high"]
                and df.iloc[i]["high"] > df.iloc[i - 2]["high"]
                and df.iloc[i]["high"] > df.iloc[i + 1]["high"]
                and df.iloc[i]["high"] > df.iloc[i + 2]["high"]
            ):
                swing_highs.append(float(df.iloc[i]["high"]))

            # Swing low: lower than 2 bars on each side
            if (
                df.iloc[i]["low"] < df.iloc[i - 1]["low"]
                and df.iloc[i]["low"] < df.iloc[i - 2]["low"]
                and df.iloc[i]["low"] < df.iloc[i + 1]["low"]
                and df.iloc[i]["low"] < df.iloc[i + 2]["low"]
            ):
                swing_lows.append(float(df.iloc[i]["low"]))

        # Cluster nearby levels
        self.resistance_levels = self._cluster_levels(swing_highs)
        self.support_levels = self._cluster_levels(swing_lows)

    def _cluster_levels(self, levels: List[float]) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []

        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            # Check if level is within tolerance of cluster average
            cluster_avg = np.mean(current_cluster)
            if abs(level - cluster_avg) / cluster_avg < self.level_tolerance:
                current_cluster.append(level)
            else:
                # Save cluster if it has enough touches
                if len(current_cluster) >= self.min_touches:
                    clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        # Don't forget last cluster
        if len(current_cluster) >= self.min_touches:
            clustered.append(np.mean(current_cluster))

        return clustered

    def _calculate_volume_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-related metrics"""
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["volume_ma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma"]
        return df

    def _check_breakout(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for breakout signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        current_high = float(last_row["high"])
        current_low = float(last_row["low"])
        prev_close = float(prev_row["close"])
        volume_ratio = float(last_row.get("volume_ratio", 1.0))

        action = "hold"
        confidence = 0.0
        reasons = []

        # Check resistance breakout
        for resistance in self.resistance_levels:
            # Price broke above resistance
            if prev_close < resistance and current_high > resistance * (
                1 + self.breakout_threshold
            ):
                action = "buy"
                confidence = 0.6
                reasons.append(f"Broke resistance at {resistance:.2f}")

                # Volume confirmation
                if volume_ratio > self.volume_confirmation:
                    confidence = min(confidence + 0.2, 1.0)
                    reasons.append(f"Volume confirms ({volume_ratio:.1f}x avg)")
                else:
                    confidence *= 0.8
                    reasons.append("Warning: Low volume breakout")

                # Check if it's a retest after initial breakout
                if self.retest_enabled:
                    # Look for recent breakout followed by pullback
                    recent_data = df.tail(10)
                    if self._is_retest_entry(recent_data, resistance, "resistance"):
                        confidence = min(confidence + 0.15, 1.0)
                        reasons.append("Retest entry confirmed")

                break

        # Check support breakout (breakdown)
        if action == "hold":
            for support in self.support_levels:
                if prev_close > support and current_low < support * (
                    1 - self.breakout_threshold
                ):
                    action = "sell"
                    confidence = 0.6
                    reasons.append(f"Broke support at {support:.2f}")

                    if volume_ratio > self.volume_confirmation:
                        confidence = min(confidence + 0.2, 1.0)
                        reasons.append(f"Volume confirms ({volume_ratio:.1f}x avg)")
                    else:
                        confidence *= 0.8
                        reasons.append("Warning: Low volume breakdown")

                    if self.retest_enabled:
                        recent_data = df.tail(10)
                        if self._is_retest_entry(recent_data, support, "support"):
                            confidence = min(confidence + 0.15, 1.0)
                            reasons.append("Retest entry confirmed")

                    break

        # Find nearest levels for stop calculation
        nearest_support = max(
            [s for s in self.support_levels if s < current_price],
            default=current_price * 0.95,
        )
        nearest_resistance = min(
            [r for r in self.resistance_levels if r > current_price],
            default=current_price * 1.05,
        )

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No breakout detected",
            "indicators": {
                "support_levels": (
                    self.support_levels[-3:] if self.support_levels else []
                ),
                "resistance_levels": (
                    self.resistance_levels[-3:] if self.resistance_levels else []
                ),
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "volume_ratio": volume_ratio,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(
                    current_price, action, nearest_support, nearest_resistance
                )
            )

        return signal

    def _is_retest_entry(
        self, data: pd.DataFrame, level: float, level_type: str
    ) -> bool:
        """Check if current price action represents a retest entry"""
        if len(data) < 5:
            return False

        closes = data["close"].values

        if level_type == "resistance":
            # First broke above, then pulled back to level, now bouncing
            broke_above = any(closes[:-3] > level)
            pulled_back = any(abs(closes[-3:] - level) / level < 0.01)
            bouncing = closes[-1] > closes[-2]
            return broke_above and pulled_back and bouncing
        else:  # support
            broke_below = any(closes[:-3] < level)
            pulled_back = any(abs(closes[-3:] - level) / level < 0.01)
            bouncing = closes[-1] < closes[-2]
            return broke_below and pulled_back and bouncing

    def _calculate_stop_take_profit(
        self, price: float, action: str, support: float, resistance: float
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit using S/R levels"""
        if action == "buy":
            stop_loss = support * 0.99  # Just below support
            # Target next resistance or 2:1 R/R
            risk = price - stop_loss
            take_profit = max(resistance, price + risk * 2)
        else:
            stop_loss = resistance * 1.01  # Just above resistance
            risk = stop_loss - price
            take_profit = min(support, price - risk * 2)

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
