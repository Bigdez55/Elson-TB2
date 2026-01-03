"""
RSI (Relative Strength Index) Trading Strategy

Generates buy/sell signals based on RSI overbought/oversold levels
with divergence detection and multi-timeframe confirmation.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="rsi_strategy",
    category=StrategyCategory.TECHNICAL,
    description="RSI-based trading strategy with overbought/oversold levels and divergence detection",
    default_parameters={
        "rsi_period": 14,
        "overbought": 70,
        "oversold": 30,
        "extreme_overbought": 80,
        "extreme_oversold": 20,
        "divergence_lookback": 14,
        "use_divergence": True,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
        "base_position_pct": 0.02,
    },
    required_data=["close", "high", "low"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class RSIStrategy(TradingStrategy):
    """
    RSI Trading Strategy

    Generates signals based on:
    - RSI overbought (>70) and oversold (<30) levels
    - RSI divergence detection (bullish/bearish)
    - Extreme levels for stronger signals
    - Optional multi-timeframe confirmation
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        rsi_period: int = 14,
        overbought: int = 70,
        oversold: int = 30,
        extreme_overbought: int = 80,
        extreme_oversold: int = 20,
        divergence_lookback: int = 14,
        use_divergence: bool = True,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="RSI Strategy",
            description="RSI-based trading with divergence detection",
            parameters={
                "rsi_period": rsi_period,
                "overbought": overbought,
                "oversold": oversold,
                "extreme_overbought": extreme_overbought,
                "extreme_oversold": extreme_oversold,
                "divergence_lookback": divergence_lookback,
                "use_divergence": use_divergence,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.extreme_overbought = extreme_overbought
        self.extreme_oversold = extreme_oversold
        self.divergence_lookback = divergence_lookback
        self.use_divergence = use_divergence

        # State tracking
        self.last_rsi = None
        self.last_divergence = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on RSI analysis"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.rsi_period + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            # Calculate RSI
            df = self._calculate_rsi(df)

            # Detect divergence if enabled
            divergence = None
            if self.use_divergence:
                divergence = self._detect_divergence(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df, divergence)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating RSI signal for {self.symbol}: {str(e)}")
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
            logger.info(f"Updated RSI strategy parameters: {new_parameters}")
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

            # Normalize column names
            df.columns = df.columns.str.lower()

            required_columns = ["close", "high", "low"]
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Missing column: {col}")
                    return None

            df = df.sort_values("timestamp" if "timestamp" in df.columns else df.index)
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None

    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()

        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        # Calculate RSI slope for momentum
        df["rsi_slope"] = df["rsi"].diff(3)

        return df

    def _detect_divergence(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect bullish or bearish divergence

        Bullish divergence: Price makes lower low, RSI makes higher low
        Bearish divergence: Price makes higher high, RSI makes lower high
        """
        try:
            lookback = self.divergence_lookback
            if len(df) < lookback * 2:
                return None

            recent = df.tail(lookback)
            prev = df.iloc[-lookback*2:-lookback]

            # Get price and RSI highs/lows
            recent_price_high = recent["high"].max()
            recent_price_low = recent["low"].min()
            recent_rsi_high = recent["rsi"].max()
            recent_rsi_low = recent["rsi"].min()

            prev_price_high = prev["high"].max()
            prev_price_low = prev["low"].min()
            prev_rsi_high = prev["rsi"].max()
            prev_rsi_low = prev["rsi"].min()

            # Bullish divergence
            if recent_price_low < prev_price_low and recent_rsi_low > prev_rsi_low:
                return "bullish_divergence"

            # Bearish divergence
            if recent_price_high > prev_price_high and recent_rsi_high < prev_rsi_high:
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
        """Generate trading decision based on RSI and divergence"""
        last_row = df.iloc[-1]
        current_rsi = float(last_row["rsi"])
        current_price = float(last_row["close"])
        rsi_slope = float(last_row.get("rsi_slope", 0))

        self.last_rsi = current_rsi
        self.last_divergence = divergence

        action = "hold"
        confidence = 0.0
        reasons = []

        # Oversold signals (buy)
        if current_rsi < self.extreme_oversold:
            action = "buy"
            confidence = 0.8
            reasons.append(f"Extreme oversold (RSI: {current_rsi:.1f})")
        elif current_rsi < self.oversold:
            action = "buy"
            confidence = 0.6
            reasons.append(f"Oversold (RSI: {current_rsi:.1f})")

        # Overbought signals (sell)
        elif current_rsi > self.extreme_overbought:
            action = "sell"
            confidence = 0.8
            reasons.append(f"Extreme overbought (RSI: {current_rsi:.1f})")
        elif current_rsi > self.overbought:
            action = "sell"
            confidence = 0.6
            reasons.append(f"Overbought (RSI: {current_rsi:.1f})")

        # Divergence signals
        if divergence == "bullish_divergence":
            if action == "buy":
                confidence = min(confidence + 0.2, 1.0)
            elif action == "hold":
                action = "buy"
                confidence = 0.65
            reasons.append("Bullish divergence detected")
        elif divergence == "bearish_divergence":
            if action == "sell":
                confidence = min(confidence + 0.2, 1.0)
            elif action == "hold":
                action = "sell"
                confidence = 0.65
            reasons.append("Bearish divergence detected")

        # RSI slope confirmation
        if action == "buy" and rsi_slope > 0:
            confidence = min(confidence + 0.1, 1.0)
            reasons.append("RSI momentum positive")
        elif action == "sell" and rsi_slope < 0:
            confidence = min(confidence + 0.1, 1.0)
            reasons.append("RSI momentum negative")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear signal",
            "indicators": {
                "rsi": current_rsi,
                "rsi_slope": rsi_slope,
                "divergence": divergence,
            },
        }

        # Add stop loss and take profit for actionable signals
        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(current_price, action))

        return signal

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        # Use ATR-based stops if available, otherwise use percentage
        stop_pct = 0.02  # 2% stop loss
        profit_pct = 0.04  # 4% take profit (2:1 reward/risk)

        if action == "buy":
            return {
                "stop_loss": price * (1 - stop_pct),
                "take_profit": price * (1 + profit_pct),
            }
        else:  # sell
            return {
                "stop_loss": price * (1 + stop_pct),
                "take_profit": price * (1 - profit_pct),
            }

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create a hold signal with given reason"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {},
        }

    async def _custom_validation(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> bool:
        """Custom validation for RSI signals"""
        # Check RSI is in valid range
        indicators = signal.get("indicators", {})
        rsi = indicators.get("rsi")

        if rsi is not None and not (0 <= rsi <= 100):
            logger.warning(f"Invalid RSI value: {rsi}")
            return False

        return True
