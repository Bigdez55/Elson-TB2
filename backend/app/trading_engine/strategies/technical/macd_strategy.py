"""
MACD (Moving Average Convergence Divergence) Trading Strategy

Enhanced MACD strategy with:
- Signal line crossovers
- Zero line crossovers
- Histogram divergence
- Multi-timeframe confirmation
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
    name="macd_strategy",
    category=StrategyCategory.TECHNICAL,
    description="Enhanced MACD strategy with divergence detection and histogram analysis",
    default_parameters={
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "use_histogram_divergence": True,
        "use_zero_line": True,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class MACDStrategy(TradingStrategy):
    """
    Enhanced MACD Trading Strategy

    Signal types:
    1. Signal Line Crossover: MACD crosses above/below signal line
    2. Zero Line Crossover: MACD crosses above/below zero
    3. Histogram Divergence: Price/MACD histogram divergence
    4. Histogram Reversal: Histogram changes direction
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        use_histogram_divergence: bool = True,
        use_zero_line: bool = True,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="MACD Strategy",
            description="Enhanced MACD with divergence detection",
            parameters={
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
                "use_histogram_divergence": use_histogram_divergence,
                "use_zero_line": use_zero_line,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.use_histogram_divergence = use_histogram_divergence
        self.use_zero_line = use_zero_line

        # State tracking
        self.last_macd = None
        self.last_signal = None
        self.last_histogram = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on MACD analysis"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.slow_period + self.signal_period + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            # Calculate MACD
            df = self._calculate_macd(df)

            # Detect divergence if enabled
            divergence = None
            if self.use_histogram_divergence:
                divergence = self._detect_divergence(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df, divergence)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating MACD signal for {self.symbol}: {str(e)}")
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
            logger.info(f"Updated MACD parameters: {new_parameters}")
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
            start_date = end_date - timedelta(days=120)

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

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD, Signal line, and Histogram"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Calculate EMAs
        df["ema_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()

        # MACD Line
        df["macd"] = df["ema_fast"] - df["ema_slow"]

        # Signal Line
        df["macd_signal"] = df["macd"].ewm(span=self.signal_period, adjust=False).mean()

        # Histogram
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        # Histogram slope (for momentum)
        df["histogram_slope"] = df["macd_histogram"].diff()

        # MACD slope
        df["macd_slope"] = df["macd"].diff()

        return df

    def _detect_divergence(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect bullish or bearish divergence using histogram

        Bullish: Price lower low, histogram higher low
        Bearish: Price higher high, histogram lower high
        """
        try:
            lookback = 14
            if len(df) < lookback * 2:
                return None

            recent = df.tail(lookback)
            prev = df.iloc[-lookback*2:-lookback]

            # Get highs and lows
            recent_price_high = recent["close"].max()
            recent_price_low = recent["close"].min()
            recent_hist_high = recent["macd_histogram"].max()
            recent_hist_low = recent["macd_histogram"].min()

            prev_price_high = prev["close"].max()
            prev_price_low = prev["close"].min()
            prev_hist_high = prev["macd_histogram"].max()
            prev_hist_low = prev["macd_histogram"].min()

            # Bullish divergence
            if recent_price_low < prev_price_low and recent_hist_low > prev_hist_low:
                return "bullish_divergence"

            # Bearish divergence
            if recent_price_high > prev_price_high and recent_hist_high < prev_hist_high:
                return "bearish_divergence"

            return None

        except Exception as e:
            logger.error(f"Error detecting divergence: {str(e)}")
            return None

    def _generate_trading_decision(
        self,
        df: pd.DataFrame,
        divergence: Optional[str]
    ) -> Dict[str, Any]:
        """Generate trading decision based on MACD signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        macd = float(last_row["macd"])
        macd_signal = float(last_row["macd_signal"])
        histogram = float(last_row["macd_histogram"])
        prev_macd = float(prev_row["macd"])
        prev_signal = float(prev_row["macd_signal"])
        prev_histogram = float(prev_row["macd_histogram"])
        histogram_slope = float(last_row.get("histogram_slope", 0))

        # Store state
        self.last_macd = macd
        self.last_signal = macd_signal
        self.last_histogram = histogram

        action = "hold"
        confidence = 0.0
        reasons = []

        # Signal Line Crossover (primary signal)
        signal_crossover_up = prev_macd < prev_signal and macd > macd_signal
        signal_crossover_down = prev_macd > prev_signal and macd < macd_signal

        if signal_crossover_up:
            action = "buy"
            confidence = 0.65
            reasons.append("MACD crossed above signal line")
        elif signal_crossover_down:
            action = "sell"
            confidence = 0.65
            reasons.append("MACD crossed below signal line")

        # Zero Line Crossover (trend confirmation)
        if self.use_zero_line:
            zero_cross_up = prev_macd < 0 and macd > 0
            zero_cross_down = prev_macd > 0 and macd < 0

            if zero_cross_up:
                if action == "buy":
                    confidence = min(confidence + 0.2, 1.0)
                elif action == "hold":
                    action = "buy"
                    confidence = 0.55
                reasons.append("MACD crossed above zero")
            elif zero_cross_down:
                if action == "sell":
                    confidence = min(confidence + 0.2, 1.0)
                elif action == "hold":
                    action = "sell"
                    confidence = 0.55
                reasons.append("MACD crossed below zero")

        # Histogram momentum
        hist_increasing = histogram > prev_histogram and histogram_slope > 0
        hist_decreasing = histogram < prev_histogram and histogram_slope < 0

        if action == "buy" and hist_increasing:
            confidence = min(confidence + 0.1, 1.0)
            reasons.append("Histogram momentum positive")
        elif action == "sell" and hist_decreasing:
            confidence = min(confidence + 0.1, 1.0)
            reasons.append("Histogram momentum negative")

        # Histogram reversal (early signal)
        if action == "hold":
            if prev_histogram < 0 and histogram > prev_histogram and histogram_slope > 0:
                action = "buy"
                confidence = 0.5
                reasons.append("Histogram reversal - bullish")
            elif prev_histogram > 0 and histogram < prev_histogram and histogram_slope < 0:
                action = "sell"
                confidence = 0.5
                reasons.append("Histogram reversal - bearish")

        # Divergence signals
        if divergence == "bullish_divergence":
            if action == "buy":
                confidence = min(confidence + 0.15, 1.0)
            elif action == "hold":
                action = "buy"
                confidence = 0.6
            reasons.append("Bullish divergence detected")
        elif divergence == "bearish_divergence":
            if action == "sell":
                confidence = min(confidence + 0.15, 1.0)
            elif action == "hold":
                action = "sell"
                confidence = 0.6
            reasons.append("Bearish divergence detected")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear signal",
            "indicators": {
                "macd": macd,
                "macd_signal": macd_signal,
                "histogram": histogram,
                "histogram_slope": histogram_slope,
                "divergence": divergence,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(current_price, action))

        return signal

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        stop_pct = 0.025  # 2.5% stop loss
        profit_pct = 0.05  # 5% take profit (2:1 reward/risk)

        if action == "buy":
            return {
                "stop_loss": price * (1 - stop_pct),
                "take_profit": price * (1 + profit_pct),
            }
        else:
            return {
                "stop_loss": price * (1 + stop_pct),
                "take_profit": price * (1 - profit_pct),
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
