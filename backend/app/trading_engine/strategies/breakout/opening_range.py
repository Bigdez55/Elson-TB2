"""
Opening Range Breakout (ORB) Strategy

Trades breakouts from the opening range defined by the first
N minutes of the trading session.
"""

import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="opening_range_breakout",
    category=StrategyCategory.BREAKOUT,
    description="Opening Range Breakout strategy for intraday trading",
    default_parameters={
        "opening_minutes": 30,  # First 30 minutes
        "breakout_buffer": 0.001,  # 0.1% beyond range
        "min_range_pct": 0.005,  # Minimum 0.5% range
        "max_range_pct": 0.03,  # Maximum 3% range
        "volume_filter": 1.2,  # Volume must be 1.2x average
        "use_gap_filter": True,
        "max_gap_pct": 0.03,  # Skip if gap > 3%
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["open", "high", "low", "close", "volume", "timestamp"],
    timeframes=["1m", "5m", "15m"],
    risk_level="high",
)
class OpeningRangeBreakout(TradingStrategy):
    """
    Opening Range Breakout (ORB) Strategy

    Classic day trading strategy:
    1. Define opening range (first N minutes high/low)
    2. Buy on breakout above range high
    3. Sell on breakdown below range low
    4. Use range as stop loss reference
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        opening_minutes: int = 30,
        breakout_buffer: float = 0.001,
        min_range_pct: float = 0.005,
        max_range_pct: float = 0.03,
        volume_filter: float = 1.2,
        use_gap_filter: bool = True,
        max_gap_pct: float = 0.03,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Opening Range Breakout",
            description="ORB intraday breakout strategy",
            parameters={
                "opening_minutes": opening_minutes,
                "breakout_buffer": breakout_buffer,
                "min_range_pct": min_range_pct,
                "max_range_pct": max_range_pct,
                "volume_filter": volume_filter,
                "use_gap_filter": use_gap_filter,
                "max_gap_pct": max_gap_pct,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.opening_minutes = opening_minutes
        self.breakout_buffer = breakout_buffer
        self.min_range_pct = min_range_pct
        self.max_range_pct = max_range_pct
        self.volume_filter = volume_filter
        self.use_gap_filter = use_gap_filter
        self.max_gap_pct = max_gap_pct

        # Daily state
        self.range_high: Optional[float] = None
        self.range_low: Optional[float] = None
        self.range_defined = False
        self.breakout_triggered = False
        self.last_session_date = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on ORB"""
        try:
            df = await self._get_intraday_data()

            if df is None or len(df) < 5:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient intraday data"
                )

            # Check if new session
            self._check_new_session(df)

            # Define opening range if not set
            if not self.range_defined:
                self._define_opening_range(df)

            if not self.range_defined:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Opening range not yet defined"
                )

            # Check for breakout
            signal = self._check_breakout(df, market_data)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in ORB strategy: {str(e)}")
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

    async def _get_intraday_data(self) -> Optional[pd.DataFrame]:
        """Get intraday market data"""
        try:
            if self.market_data_service is None:
                return None

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=2)

            data = await self.market_data_service.get_historical_data(
                self.symbol,
                start_date.isoformat(),
                end_date.isoformat(),
                interval="5m",  # 5-minute bars
            )

            if not data:
                return None

            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data]) if isinstance(data, dict) else data

            df.columns = df.columns.str.lower()

            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")

            df = df.reset_index(drop=True)
            return df

        except Exception as e:
            logger.error(f"Error getting intraday data: {str(e)}")
            return None

    def _check_new_session(self, df: pd.DataFrame) -> None:
        """Check if we're in a new trading session"""
        if "timestamp" not in df.columns:
            return

        current_date = df.iloc[-1]["timestamp"].date()

        if self.last_session_date != current_date:
            # New session - reset everything
            self.range_high = None
            self.range_low = None
            self.range_defined = False
            self.breakout_triggered = False
            self.last_session_date = current_date
            logger.info(f"New session detected for {self.symbol}: {current_date}")

    def _define_opening_range(self, df: pd.DataFrame) -> None:
        """Define the opening range for the current session"""
        if "timestamp" not in df.columns:
            return

        # Get today's data
        today = df.iloc[-1]["timestamp"].date()
        today_data = df[df["timestamp"].dt.date == today]

        if len(today_data) == 0:
            return

        # Market open time (assuming 9:30 AM ET)
        market_open = datetime.combine(today, time(9, 30))
        range_end = market_open + timedelta(minutes=self.opening_minutes)

        # Filter data within opening range period
        opening_data = today_data[
            (today_data["timestamp"] >= market_open)
            & (today_data["timestamp"] <= range_end)
        ]

        if len(opening_data) < 3:  # Need at least a few bars
            return

        # Check if opening range period is complete
        last_timestamp = today_data.iloc[-1]["timestamp"]
        if last_timestamp < range_end:
            return  # Still in opening range period

        # Define range
        self.range_high = float(opening_data["high"].max())
        self.range_low = float(opening_data["low"].min())

        # Validate range
        range_pct = (self.range_high - self.range_low) / self.range_low

        if range_pct < self.min_range_pct:
            logger.info(f"Opening range too tight: {range_pct:.2%}")
            self.range_defined = False
            return

        if range_pct > self.max_range_pct:
            logger.info(f"Opening range too wide: {range_pct:.2%}")
            self.range_defined = False
            return

        self.range_defined = True
        logger.info(
            f"Opening range defined: {self.range_low:.2f} - {self.range_high:.2f}"
        )

    def _check_breakout(
        self, df: pd.DataFrame, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for opening range breakout"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        current_high = float(last_row["high"])
        current_low = float(last_row["low"])
        prev_close = float(prev_row["close"])

        # Calculate volume metrics
        volume = float(last_row.get("volume", 0))
        avg_volume = df["volume"].rolling(window=20).mean().iloc[-1]
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        action = "hold"
        confidence = 0.0
        reasons = []

        # Check for gap if enabled
        if self.use_gap_filter:
            # Get previous day close
            today = last_row["timestamp"].date() if "timestamp" in last_row else None
            if today:
                prev_day_data = df[df["timestamp"].dt.date < today]
                if len(prev_day_data) > 0:
                    prev_day_close = float(prev_day_data.iloc[-1]["close"])
                    today_open = float(
                        df[df["timestamp"].dt.date == today].iloc[0]["open"]
                    )
                    gap_pct = abs(today_open - prev_day_close) / prev_day_close

                    if gap_pct > self.max_gap_pct:
                        return self._create_hold_signal(
                            current_price,
                            f"Gap too large ({gap_pct:.1%}), skipping ORB",
                        )

        # Breakout above range high
        breakout_high = self.range_high * (1 + self.breakout_buffer)
        breakout_low = self.range_low * (1 - self.breakout_buffer)

        if current_high > breakout_high and prev_close <= self.range_high:
            action = "buy"
            confidence = 0.65
            reasons.append(f"Broke above opening range ({self.range_high:.2f})")

            # Volume confirmation
            if volume_ratio > self.volume_filter:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append(f"Volume confirms ({volume_ratio:.1f}x)")

            # First breakout of the day is stronger
            if not self.breakout_triggered:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("First breakout of session")
                self.breakout_triggered = True

        # Breakdown below range low
        elif current_low < breakout_low and prev_close >= self.range_low:
            action = "sell"
            confidence = 0.65
            reasons.append(f"Broke below opening range ({self.range_low:.2f})")

            if volume_ratio > self.volume_filter:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append(f"Volume confirms ({volume_ratio:.1f}x)")

            if not self.breakout_triggered:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("First breakout of session")
                self.breakout_triggered = True

        range_size = self.range_high - self.range_low

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No breakout",
            "indicators": {
                "range_high": self.range_high,
                "range_low": self.range_low,
                "range_size": range_size,
                "range_pct": range_size / self.range_low,
                "volume_ratio": volume_ratio,
                "breakout_triggered": self.breakout_triggered,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(current_price, action, range_size)
            )

        return signal

    def _calculate_stop_take_profit(
        self, price: float, action: str, range_size: float
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit"""
        if action == "buy":
            # Stop at opposite side of range
            stop_loss = self.range_low * 0.99
            # Target 1.5-2x the range size
            take_profit = price + (range_size * 1.5)
        else:
            stop_loss = self.range_high * 1.01
            take_profit = price - (range_size * 1.5)

        return {"stop_loss": stop_loss, "take_profit": take_profit}

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {
                "range_high": self.range_high,
                "range_low": self.range_low,
                "range_defined": self.range_defined,
            },
        }

    async def on_market_open(self) -> None:
        """Reset state on market open"""
        self.range_high = None
        self.range_low = None
        self.range_defined = False
        self.breakout_triggered = False
        logger.info(f"ORB strategy reset for {self.symbol}")

    async def on_market_close(self) -> None:
        """Log performance at market close"""
        logger.info(f"ORB session ended for {self.symbol}")
