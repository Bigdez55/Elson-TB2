"""
Candlestick Pattern Recognition Strategy

Detects and trades Japanese candlestick patterns including:
- Doji, Hammer, Shooting Star
- Engulfing patterns
- Morning/Evening Star
- Three White Soldiers/Black Crows
- And more...
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="candlestick_patterns",
    category=StrategyCategory.TECHNICAL,
    description="Japanese candlestick pattern recognition and trading",
    default_parameters={
        "body_threshold": 0.001,  # Minimum body size as % of price
        "doji_threshold": 0.1,    # Body/range ratio for doji
        "shadow_ratio": 2.0,      # Shadow to body ratio for hammer/star
        "engulfing_margin": 1.0,  # How much larger engulfing body should be
        "use_trend_filter": True,
        "trend_period": 20,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["open", "high", "low", "close", "volume"],
    timeframes=["4h", "1d"],
    risk_level="medium",
)
class CandlestickPatternStrategy(TradingStrategy):
    """
    Candlestick Pattern Recognition Strategy

    Detects multiple candlestick patterns and generates trading signals
    based on pattern type and trend context.
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        body_threshold: float = 0.001,
        doji_threshold: float = 0.1,
        shadow_ratio: float = 2.0,
        engulfing_margin: float = 1.0,
        use_trend_filter: bool = True,
        trend_period: int = 20,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Candlestick Patterns",
            description="Japanese candlestick pattern recognition",
            parameters={
                "body_threshold": body_threshold,
                "doji_threshold": doji_threshold,
                "shadow_ratio": shadow_ratio,
                "engulfing_margin": engulfing_margin,
                "use_trend_filter": use_trend_filter,
                "trend_period": trend_period,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.body_threshold = body_threshold
        self.doji_threshold = doji_threshold
        self.shadow_ratio = shadow_ratio
        self.engulfing_margin = engulfing_margin
        self.use_trend_filter = use_trend_filter
        self.trend_period = trend_period

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on candlestick patterns"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.trend_period + 5:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            # Calculate candle properties
            df = self._calculate_candle_properties(df)

            # Detect patterns
            patterns = self._detect_patterns(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df, patterns)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in candlestick pattern detection: {str(e)}")
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
            start_date = end_date - timedelta(days=60)

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

    def _calculate_candle_properties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate candle body, shadows, and other properties"""
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Body
        df["body"] = df["close"] - df["open"]
        df["body_abs"] = abs(df["body"])
        df["bullish"] = df["close"] > df["open"]

        # Range
        df["range"] = df["high"] - df["low"]

        # Shadows
        df["upper_shadow"] = df["high"] - df[["open", "close"]].max(axis=1)
        df["lower_shadow"] = df[["open", "close"]].min(axis=1) - df["low"]

        # Body to range ratio
        df["body_ratio"] = df["body_abs"] / df["range"].replace(0, np.nan)

        # Trend (SMA)
        df["sma"] = df["close"].rolling(window=self.trend_period).mean()
        df["trend"] = np.where(df["close"] > df["sma"], "up", "down")

        return df

    def _detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect all candlestick patterns in recent data"""
        patterns = []

        # Check last 3 candles for patterns
        if len(df) < 3:
            return patterns

        c1 = df.iloc[-1]  # Current candle
        c2 = df.iloc[-2]  # Previous candle
        c3 = df.iloc[-3]  # Two candles ago

        price = float(c1["close"])

        # Single candle patterns
        # Doji
        if self._is_doji(c1):
            patterns.append({
                "name": "doji",
                "type": "neutral",
                "strength": 0.4,
                "description": "Doji - Market indecision"
            })

        # Hammer (bullish reversal)
        if self._is_hammer(c1) and c1["trend"] == "down":
            patterns.append({
                "name": "hammer",
                "type": "bullish",
                "strength": 0.65,
                "description": "Hammer - Potential bullish reversal"
            })

        # Shooting Star (bearish reversal)
        if self._is_shooting_star(c1) and c1["trend"] == "up":
            patterns.append({
                "name": "shooting_star",
                "type": "bearish",
                "strength": 0.65,
                "description": "Shooting Star - Potential bearish reversal"
            })

        # Marubozu (strong candle)
        if self._is_marubozu(c1):
            if c1["bullish"]:
                patterns.append({
                    "name": "bullish_marubozu",
                    "type": "bullish",
                    "strength": 0.6,
                    "description": "Bullish Marubozu - Strong buying"
                })
            else:
                patterns.append({
                    "name": "bearish_marubozu",
                    "type": "bearish",
                    "strength": 0.6,
                    "description": "Bearish Marubozu - Strong selling"
                })

        # Two candle patterns
        # Bullish Engulfing
        if self._is_bullish_engulfing(c1, c2):
            patterns.append({
                "name": "bullish_engulfing",
                "type": "bullish",
                "strength": 0.75,
                "description": "Bullish Engulfing - Strong reversal signal"
            })

        # Bearish Engulfing
        if self._is_bearish_engulfing(c1, c2):
            patterns.append({
                "name": "bearish_engulfing",
                "type": "bearish",
                "strength": 0.75,
                "description": "Bearish Engulfing - Strong reversal signal"
            })

        # Piercing Line
        if self._is_piercing_line(c1, c2):
            patterns.append({
                "name": "piercing_line",
                "type": "bullish",
                "strength": 0.65,
                "description": "Piercing Line - Bullish reversal"
            })

        # Dark Cloud Cover
        if self._is_dark_cloud_cover(c1, c2):
            patterns.append({
                "name": "dark_cloud_cover",
                "type": "bearish",
                "strength": 0.65,
                "description": "Dark Cloud Cover - Bearish reversal"
            })

        # Harami patterns
        if self._is_bullish_harami(c1, c2):
            patterns.append({
                "name": "bullish_harami",
                "type": "bullish",
                "strength": 0.55,
                "description": "Bullish Harami - Potential reversal"
            })

        if self._is_bearish_harami(c1, c2):
            patterns.append({
                "name": "bearish_harami",
                "type": "bearish",
                "strength": 0.55,
                "description": "Bearish Harami - Potential reversal"
            })

        # Three candle patterns
        # Morning Star
        if self._is_morning_star(c1, c2, c3):
            patterns.append({
                "name": "morning_star",
                "type": "bullish",
                "strength": 0.8,
                "description": "Morning Star - Strong bullish reversal"
            })

        # Evening Star
        if self._is_evening_star(c1, c2, c3):
            patterns.append({
                "name": "evening_star",
                "type": "bearish",
                "strength": 0.8,
                "description": "Evening Star - Strong bearish reversal"
            })

        # Three White Soldiers
        if self._is_three_white_soldiers(c1, c2, c3):
            patterns.append({
                "name": "three_white_soldiers",
                "type": "bullish",
                "strength": 0.85,
                "description": "Three White Soldiers - Strong bullish trend"
            })

        # Three Black Crows
        if self._is_three_black_crows(c1, c2, c3):
            patterns.append({
                "name": "three_black_crows",
                "type": "bearish",
                "strength": 0.85,
                "description": "Three Black Crows - Strong bearish trend"
            })

        return patterns

    # Pattern detection methods
    def _is_doji(self, candle: pd.Series) -> bool:
        """Check if candle is a doji"""
        body_ratio = candle.get("body_ratio", 1)
        return pd.notna(body_ratio) and body_ratio < self.doji_threshold

    def _is_hammer(self, candle: pd.Series) -> bool:
        """Check if candle is a hammer"""
        if candle["range"] == 0:
            return False
        lower_shadow = candle["lower_shadow"]
        body = candle["body_abs"]
        upper_shadow = candle["upper_shadow"]

        return (
            lower_shadow > body * self.shadow_ratio and
            upper_shadow < body * 0.5 and
            body > candle["close"] * self.body_threshold
        )

    def _is_shooting_star(self, candle: pd.Series) -> bool:
        """Check if candle is a shooting star"""
        if candle["range"] == 0:
            return False
        upper_shadow = candle["upper_shadow"]
        body = candle["body_abs"]
        lower_shadow = candle["lower_shadow"]

        return (
            upper_shadow > body * self.shadow_ratio and
            lower_shadow < body * 0.5 and
            body > candle["close"] * self.body_threshold
        )

    def _is_marubozu(self, candle: pd.Series) -> bool:
        """Check if candle is a marubozu (no shadows)"""
        body = candle["body_abs"]
        range_ = candle["range"]

        if range_ == 0:
            return False

        return body / range_ > 0.9

    def _is_bullish_engulfing(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for bullish engulfing pattern"""
        return (
            not c2["bullish"] and  # Previous candle bearish
            c1["bullish"] and  # Current candle bullish
            c1["open"] < c2["close"] and  # Opens below prev close
            c1["close"] > c2["open"] and  # Closes above prev open
            c1["body_abs"] > c2["body_abs"] * self.engulfing_margin
        )

    def _is_bearish_engulfing(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for bearish engulfing pattern"""
        return (
            c2["bullish"] and  # Previous candle bullish
            not c1["bullish"] and  # Current candle bearish
            c1["open"] > c2["close"] and  # Opens above prev close
            c1["close"] < c2["open"] and  # Closes below prev open
            c1["body_abs"] > c2["body_abs"] * self.engulfing_margin
        )

    def _is_piercing_line(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for piercing line pattern"""
        return (
            not c2["bullish"] and  # Previous bearish
            c1["bullish"] and  # Current bullish
            c1["open"] < c2["low"] and  # Opens below prev low
            c1["close"] > (c2["open"] + c2["close"]) / 2  # Closes above midpoint
        )

    def _is_dark_cloud_cover(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for dark cloud cover pattern"""
        return (
            c2["bullish"] and  # Previous bullish
            not c1["bullish"] and  # Current bearish
            c1["open"] > c2["high"] and  # Opens above prev high
            c1["close"] < (c2["open"] + c2["close"]) / 2  # Closes below midpoint
        )

    def _is_bullish_harami(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for bullish harami pattern"""
        return (
            not c2["bullish"] and
            c1["bullish"] and
            c1["body_abs"] < c2["body_abs"] and
            c1["high"] < c2["open"] and
            c1["low"] > c2["close"]
        )

    def _is_bearish_harami(self, c1: pd.Series, c2: pd.Series) -> bool:
        """Check for bearish harami pattern"""
        return (
            c2["bullish"] and
            not c1["bullish"] and
            c1["body_abs"] < c2["body_abs"] and
            c1["high"] < c2["close"] and
            c1["low"] > c2["open"]
        )

    def _is_morning_star(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> bool:
        """Check for morning star pattern"""
        return (
            not c3["bullish"] and  # First candle bearish
            c2["body_abs"] < c3["body_abs"] * 0.3 and  # Middle small body
            c1["bullish"] and  # Third candle bullish
            c1["close"] > (c3["open"] + c3["close"]) / 2
        )

    def _is_evening_star(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> bool:
        """Check for evening star pattern"""
        return (
            c3["bullish"] and  # First candle bullish
            c2["body_abs"] < c3["body_abs"] * 0.3 and  # Middle small body
            not c1["bullish"] and  # Third candle bearish
            c1["close"] < (c3["open"] + c3["close"]) / 2
        )

    def _is_three_white_soldiers(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> bool:
        """Check for three white soldiers pattern"""
        return (
            c3["bullish"] and c2["bullish"] and c1["bullish"] and
            c2["open"] > c3["open"] and c2["close"] > c3["close"] and
            c1["open"] > c2["open"] and c1["close"] > c2["close"] and
            c3["body_abs"] > c3["close"] * self.body_threshold and
            c2["body_abs"] > c2["close"] * self.body_threshold and
            c1["body_abs"] > c1["close"] * self.body_threshold
        )

    def _is_three_black_crows(self, c1: pd.Series, c2: pd.Series, c3: pd.Series) -> bool:
        """Check for three black crows pattern"""
        return (
            not c3["bullish"] and not c2["bullish"] and not c1["bullish"] and
            c2["open"] < c3["open"] and c2["close"] < c3["close"] and
            c1["open"] < c2["open"] and c1["close"] < c2["close"] and
            c3["body_abs"] > c3["close"] * self.body_threshold and
            c2["body_abs"] > c2["close"] * self.body_threshold and
            c1["body_abs"] > c1["close"] * self.body_threshold
        )

    def _generate_trading_decision(
        self,
        df: pd.DataFrame,
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trading decision based on detected patterns"""
        last_row = df.iloc[-1]
        current_price = float(last_row["close"])
        current_trend = last_row["trend"]

        if not patterns:
            return self._create_hold_signal(current_price, "No patterns detected")

        # Score patterns
        bullish_score = 0.0
        bearish_score = 0.0
        pattern_names = []

        for pattern in patterns:
            pattern_names.append(pattern["name"])
            if pattern["type"] == "bullish":
                # Stronger if against current trend (reversal)
                multiplier = 1.2 if current_trend == "down" else 0.8
                bullish_score += pattern["strength"] * multiplier
            elif pattern["type"] == "bearish":
                multiplier = 1.2 if current_trend == "up" else 0.8
                bearish_score += pattern["strength"] * multiplier

        action = "hold"
        confidence = 0.0
        reasons = []

        if bullish_score > bearish_score and bullish_score >= 0.5:
            action = "buy"
            confidence = min(bullish_score, 0.95)
            reasons = [p["description"] for p in patterns if p["type"] == "bullish"]
        elif bearish_score > bullish_score and bearish_score >= 0.5:
            action = "sell"
            confidence = min(bearish_score, 0.95)
            reasons = [p["description"] for p in patterns if p["type"] == "bearish"]

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No actionable patterns",
            "indicators": {
                "patterns_detected": pattern_names,
                "bullish_score": bullish_score,
                "bearish_score": bearish_score,
                "trend": current_trend,
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
        """Calculate stop loss and take profit"""
        # Use recent high/low for stops
        recent_high = df.tail(5)["high"].max()
        recent_low = df.tail(5)["low"].min()

        if action == "buy":
            stop_loss = recent_low * 0.99
            risk = price - stop_loss
            take_profit = price + (risk * 2)
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
