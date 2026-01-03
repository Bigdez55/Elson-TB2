"""
Stochastic Oscillator Trading Strategy

Implements Stochastic %K/%D trading with overbought/oversold levels
and multiple signal types.
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
    name="stochastic",
    category=StrategyCategory.TECHNICAL,
    description="Stochastic oscillator strategy with %K/%D crossovers",
    default_parameters={
        "k_period": 14,
        "d_period": 3,
        "smooth_k": 3,
        "overbought": 80,
        "oversold": 20,
        "use_slow_stochastic": True,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close", "high", "low"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class StochasticStrategy(TradingStrategy):
    """
    Stochastic Oscillator Strategy

    Signals:
    - %K crosses above %D in oversold zone: Buy
    - %K crosses below %D in overbought zone: Sell
    - Divergence detection for stronger signals
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
        overbought: int = 80,
        oversold: int = 20,
        use_slow_stochastic: bool = True,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Stochastic Strategy",
            description="Stochastic oscillator with %K/%D crossovers",
            parameters={
                "k_period": k_period,
                "d_period": d_period,
                "smooth_k": smooth_k,
                "overbought": overbought,
                "oversold": oversold,
                "use_slow_stochastic": use_slow_stochastic,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.k_period = k_period
        self.d_period = d_period
        self.smooth_k = smooth_k
        self.overbought = overbought
        self.oversold = oversold
        self.use_slow_stochastic = use_slow_stochastic

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on Stochastic analysis"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.k_period + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    "Insufficient historical data"
                )

            df = self._calculate_stochastic(df)
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating Stochastic signal: {str(e)}")
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

    def _calculate_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic %K and %D"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")

        # Calculate highest high and lowest low
        df["highest_high"] = df["high"].rolling(window=self.k_period).max()
        df["lowest_low"] = df["low"].rolling(window=self.k_period).min()

        # Fast %K
        df["fast_k"] = 100 * (df["close"] - df["lowest_low"]) / (
            df["highest_high"] - df["lowest_low"]
        )

        if self.use_slow_stochastic:
            # Slow Stochastic: %K is smoothed
            df["stoch_k"] = df["fast_k"].rolling(window=self.smooth_k).mean()
        else:
            df["stoch_k"] = df["fast_k"]

        # %D is SMA of %K
        df["stoch_d"] = df["stoch_k"].rolling(window=self.d_period).mean()

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on Stochastic"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        stoch_k = float(last_row["stoch_k"])
        stoch_d = float(last_row["stoch_d"])
        prev_k = float(prev_row["stoch_k"])
        prev_d = float(prev_row["stoch_d"])

        action = "hold"
        confidence = 0.0
        reasons = []

        # Bullish crossover in oversold zone
        if prev_k <= prev_d and stoch_k > stoch_d:
            if stoch_k < self.oversold or stoch_d < self.oversold:
                action = "buy"
                confidence = 0.75
                reasons.append(f"Bullish crossover in oversold zone (%K: {stoch_k:.1f})")
            else:
                action = "buy"
                confidence = 0.55
                reasons.append(f"Bullish crossover (%K: {stoch_k:.1f})")

        # Bearish crossover in overbought zone
        elif prev_k >= prev_d and stoch_k < stoch_d:
            if stoch_k > self.overbought or stoch_d > self.overbought:
                action = "sell"
                confidence = 0.75
                reasons.append(f"Bearish crossover in overbought zone (%K: {stoch_k:.1f})")
            else:
                action = "sell"
                confidence = 0.55
                reasons.append(f"Bearish crossover (%K: {stoch_k:.1f})")

        # Extreme levels without crossover
        elif stoch_k < 10:
            action = "buy"
            confidence = 0.6
            reasons.append(f"Extreme oversold (%K: {stoch_k:.1f})")
        elif stoch_k > 90:
            action = "sell"
            confidence = 0.6
            reasons.append(f"Extreme overbought (%K: {stoch_k:.1f})")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear signal",
            "indicators": {
                "stoch_k": stoch_k,
                "stoch_d": stoch_d,
                "overbought": stoch_k > self.overbought,
                "oversold": stoch_k < self.oversold,
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
        """Calculate stop loss and take profit"""
        stop_pct = 0.02
        profit_pct = 0.04

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
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {},
        }
