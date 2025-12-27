"""
ADX (Average Directional Index) Trend Strategy

Uses ADX for trend strength measurement with +DI/-DI for direction.
Includes Parabolic SAR for trailing stops.
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
    name="adx_trend",
    category=StrategyCategory.TECHNICAL,
    description="ADX trend strength strategy with directional indicators",
    default_parameters={
        "adx_period": 14,
        "adx_threshold": 25,
        "strong_trend_threshold": 40,
        "use_parabolic_sar": True,
        "sar_acceleration": 0.02,
        "sar_maximum": 0.2,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close", "high", "low"],
    timeframes=["4h", "1d"],
    risk_level="medium",
)
class ADXTrendStrategy(TradingStrategy):
    """
    ADX Trend Strategy

    Components:
    - ADX: Measures trend strength (0-100)
    - +DI: Positive Directional Indicator (bullish pressure)
    - -DI: Negative Directional Indicator (bearish pressure)
    - Parabolic SAR: Trailing stop and reversal points

    Signals:
    - ADX > 25: Trend is present
    - +DI > -DI: Bullish trend
    - -DI > +DI: Bearish trend
    - DI crossovers: Trend change
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        adx_period: int = 14,
        adx_threshold: int = 25,
        strong_trend_threshold: int = 40,
        use_parabolic_sar: bool = True,
        sar_acceleration: float = 0.02,
        sar_maximum: float = 0.2,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="ADX Trend Strategy",
            description="Trend following using ADX and directional indicators",
            parameters={
                "adx_period": adx_period,
                "adx_threshold": adx_threshold,
                "strong_trend_threshold": strong_trend_threshold,
                "use_parabolic_sar": use_parabolic_sar,
                "sar_acceleration": sar_acceleration,
                "sar_maximum": sar_maximum,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.strong_trend_threshold = strong_trend_threshold
        self.use_parabolic_sar = use_parabolic_sar
        self.sar_acceleration = sar_acceleration
        self.sar_maximum = sar_maximum

        # State
        self.trend_direction = None
        self.trend_strength = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on ADX analysis"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.adx_period * 2:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            # Calculate ADX and DI
            df = self._calculate_adx(df)

            # Calculate Parabolic SAR if enabled
            if self.use_parabolic_sar:
                df = self._calculate_parabolic_sar(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating ADX signal: {str(e)}")
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
            start_date = end_date - timedelta(days=100)

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

    def _calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX, +DI, and -DI"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")

        # True Range
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift(1))
        df["tr3"] = abs(df["low"] - df["close"].shift(1))
        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

        # Directional Movement
        df["dm_plus"] = np.where(
            (df["high"] - df["high"].shift(1)) > (df["low"].shift(1) - df["low"]),
            np.maximum(df["high"] - df["high"].shift(1), 0),
            0
        )
        df["dm_minus"] = np.where(
            (df["low"].shift(1) - df["low"]) > (df["high"] - df["high"].shift(1)),
            np.maximum(df["low"].shift(1) - df["low"], 0),
            0
        )

        # Smoothed averages
        df["atr"] = df["tr"].rolling(window=self.adx_period).mean()
        df["dm_plus_smooth"] = df["dm_plus"].rolling(window=self.adx_period).mean()
        df["dm_minus_smooth"] = df["dm_minus"].rolling(window=self.adx_period).mean()

        # Directional Indicators
        df["di_plus"] = 100 * df["dm_plus_smooth"] / df["atr"]
        df["di_minus"] = 100 * df["dm_minus_smooth"] / df["atr"]

        # DX and ADX
        df["dx"] = 100 * abs(df["di_plus"] - df["di_minus"]) / (df["di_plus"] + df["di_minus"])
        df["adx"] = df["dx"].rolling(window=self.adx_period).mean()

        return df

    def _calculate_parabolic_sar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Parabolic SAR"""
        high = df["high"].values
        low = df["low"].values
        close = df["close"].values
        n = len(df)

        psar = np.zeros(n)
        af = self.sar_acceleration
        trend = np.zeros(n)
        ep = np.zeros(n)

        # Initialize
        psar[0] = close[0]
        trend[0] = 1  # Start with uptrend
        ep[0] = high[0]

        for i in range(1, n):
            if trend[i-1] == 1:  # Uptrend
                psar[i] = psar[i-1] + af * (ep[i-1] - psar[i-1])
                psar[i] = min(psar[i], low[i-1], low[i-2] if i > 1 else low[i-1])

                if low[i] < psar[i]:
                    trend[i] = -1
                    psar[i] = ep[i-1]
                    ep[i] = low[i]
                    af = self.sar_acceleration
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af = min(af + self.sar_acceleration, self.sar_maximum)
                    else:
                        ep[i] = ep[i-1]
            else:  # Downtrend
                psar[i] = psar[i-1] + af * (ep[i-1] - psar[i-1])
                psar[i] = max(psar[i], high[i-1], high[i-2] if i > 1 else high[i-1])

                if high[i] > psar[i]:
                    trend[i] = 1
                    psar[i] = ep[i-1]
                    ep[i] = high[i]
                    af = self.sar_acceleration
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af = min(af + self.sar_acceleration, self.sar_maximum)
                    else:
                        ep[i] = ep[i-1]

        df["psar"] = psar
        df["psar_trend"] = trend

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on ADX and DI"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        adx = float(last_row["adx"])
        di_plus = float(last_row["di_plus"])
        di_minus = float(last_row["di_minus"])
        prev_di_plus = float(prev_row["di_plus"])
        prev_di_minus = float(prev_row["di_minus"])

        # Update state
        self.trend_strength = "strong" if adx > self.strong_trend_threshold else (
            "moderate" if adx > self.adx_threshold else "weak"
        )
        self.trend_direction = "bullish" if di_plus > di_minus else "bearish"

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
                "reason": f"No trend (ADX: {adx:.1f} < {self.adx_threshold})",
                "indicators": self._get_indicators(last_row),
            }

        # DI Crossover signals
        bullish_cross = prev_di_plus <= prev_di_minus and di_plus > di_minus
        bearish_cross = prev_di_plus >= prev_di_minus and di_plus < di_minus

        if bullish_cross:
            action = "buy"
            confidence = 0.6
            reasons.append(f"+DI crossed above -DI")
        elif bearish_cross:
            action = "sell"
            confidence = 0.6
            reasons.append(f"-DI crossed above +DI")

        # Trend strength confirmation
        if adx > self.strong_trend_threshold:
            if action != "hold":
                confidence = min(confidence + 0.15, 1.0)
            reasons.append(f"Strong trend (ADX: {adx:.1f})")
        elif adx > self.adx_threshold:
            reasons.append(f"Moderate trend (ADX: {adx:.1f})")

        # Existing trend continuation
        if action == "hold":
            if di_plus > di_minus and adx > self.adx_threshold:
                # Already in uptrend
                if di_plus - di_minus > 10:  # Strong directional difference
                    action = "buy"
                    confidence = 0.5
                    reasons.append("Bullish trend continuation")
            elif di_minus > di_plus and adx > self.adx_threshold:
                if di_minus - di_plus > 10:
                    action = "sell"
                    confidence = 0.5
                    reasons.append("Bearish trend continuation")

        # Parabolic SAR confirmation
        if self.use_parabolic_sar and "psar" in last_row:
            psar = float(last_row["psar"])
            psar_trend = float(last_row["psar_trend"])

            if action == "buy" and psar_trend == 1:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("SAR confirms uptrend")
            elif action == "sell" and psar_trend == -1:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("SAR confirms downtrend")
            elif action == "buy" and psar_trend == -1:
                confidence *= 0.7
                reasons.append("Warning: SAR shows downtrend")
            elif action == "sell" and psar_trend == 1:
                confidence *= 0.7
                reasons.append("Warning: SAR shows uptrend")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear signal",
            "indicators": self._get_indicators(last_row),
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(
                current_price, action, last_row
            ))

        return signal

    def _get_indicators(self, row: pd.Series) -> Dict[str, Any]:
        """Get indicator values from row"""
        return {
            "adx": float(row.get("adx", 0)),
            "di_plus": float(row.get("di_plus", 0)),
            "di_minus": float(row.get("di_minus", 0)),
            "atr": float(row.get("atr", 0)),
            "psar": float(row.get("psar", 0)) if "psar" in row else None,
            "trend_strength": self.trend_strength,
            "trend_direction": self.trend_direction,
        }

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        row: pd.Series,
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit using ATR and SAR"""
        atr = float(row.get("atr", price * 0.02))

        # Use Parabolic SAR as stop if available
        if self.use_parabolic_sar and "psar" in row:
            psar = float(row["psar"])
            if action == "buy":
                stop_loss = psar * 0.99
            else:
                stop_loss = psar * 1.01
        else:
            # Use ATR-based stop
            if action == "buy":
                stop_loss = price - (atr * 2)
            else:
                stop_loss = price + (atr * 2)

        # Take profit at 3:1 risk/reward
        risk = abs(price - stop_loss)
        if action == "buy":
            take_profit = price + (risk * 3)
        else:
            take_profit = price - (risk * 3)

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
