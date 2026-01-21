"""
Momentum Factor Strategy

Implements factor-based momentum investing using multiple
momentum indicators and relative strength.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="momentum_factor",
    category=StrategyCategory.MOMENTUM,
    description="Multi-factor momentum strategy with relative strength",
    default_parameters={
        "momentum_period": 12,  # 12-month momentum (for daily = ~252 days)
        "skip_period": 1,  # Skip most recent month (21 days)
        "roc_periods": [21, 63, 126, 252],  # Multiple ROC periods
        "relative_strength_period": 63,
        "moving_average_filter": True,
        "ma_period": 200,
        "volume_confirm": True,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close", "volume"],
    timeframes=["1d", "1w"],
    risk_level="medium",
)
class MomentumFactorStrategy(TradingStrategy):
    """
    Momentum Factor Strategy

    Based on academic research showing that stocks with high
    past returns tend to continue outperforming.

    Components:
    - Price Rate of Change (ROC) at multiple timeframes
    - Relative strength vs benchmark
    - Moving average filter
    - Volume confirmation
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        momentum_period: int = 252,
        skip_period: int = 21,
        roc_periods: List[int] = None,
        relative_strength_period: int = 63,
        moving_average_filter: bool = True,
        ma_period: int = 200,
        volume_confirm: bool = True,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Momentum Factor",
            description="Multi-factor momentum with relative strength",
            parameters={
                "momentum_period": momentum_period,
                "skip_period": skip_period,
                "roc_periods": roc_periods or [21, 63, 126, 252],
                "relative_strength_period": relative_strength_period,
                "moving_average_filter": moving_average_filter,
                "ma_period": ma_period,
                "volume_confirm": volume_confirm,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.momentum_period = momentum_period
        self.skip_period = skip_period
        self.roc_periods = roc_periods or [21, 63, 126, 252]
        self.relative_strength_period = relative_strength_period
        self.moving_average_filter = moving_average_filter
        self.ma_period = ma_period
        self.volume_confirm = volume_confirm

        # State
        self.momentum_score = None
        self.momentum_rank = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on momentum factors"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.momentum_period + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Calculate momentum indicators
            df = self._calculate_momentum_indicators(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in momentum factor strategy: {str(e)}")
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
            return False

    async def _get_historical_data(self) -> Optional[pd.DataFrame]:
        """Get historical market data"""
        try:
            if self.market_data_service is None:
                return None

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(
                days=400
            )  # Need enough for 252-day momentum

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

    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate multiple momentum indicators"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        # Rate of Change at multiple periods
        for period in self.roc_periods:
            if len(df) > period:
                df[f"roc_{period}"] = (
                    (df["close"] - df["close"].shift(period))
                    / df["close"].shift(period)
                ) * 100

        # Classic momentum (skip most recent period to avoid reversal)
        if len(df) > self.momentum_period:
            df["momentum_classic"] = (
                (
                    df["close"].shift(self.skip_period)
                    - df["close"].shift(self.momentum_period)
                )
                / df["close"].shift(self.momentum_period)
            ) * 100

        # Moving averages
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["sma_200"] = df["close"].rolling(window=self.ma_period).mean()

        # Price vs moving average
        df["above_ma"] = df["close"] > df["sma_200"]

        # Volume trend
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        df["volume_trend"] = df["volume"] > df["volume_sma"]

        # Composite momentum score (weighted average of ROCs)
        weights = {21: 0.1, 63: 0.2, 126: 0.3, 252: 0.4}
        df["momentum_score"] = 0
        for period in self.roc_periods:
            if f"roc_{period}" in df.columns:
                weight = weights.get(period, 0.25)
                df["momentum_score"] += df[f"roc_{period}"].fillna(0) * weight

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on momentum"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        momentum_score = float(last_row.get("momentum_score", 0))
        roc_21 = float(last_row.get("roc_21", 0))
        roc_63 = float(last_row.get("roc_63", 0))
        above_ma = bool(last_row.get("above_ma", False))
        volume_trend = bool(last_row.get("volume_trend", False))

        self.momentum_score = momentum_score

        action = "hold"
        confidence = 0.0
        reasons = []

        # Strong positive momentum
        if momentum_score > 20:  # 20% composite return
            action = "buy"
            confidence = 0.7
            reasons.append(f"Strong momentum score: {momentum_score:.1f}%")

            # Trend confirmation
            if self.moving_average_filter and above_ma:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append("Price above 200 MA")
            elif self.moving_average_filter and not above_ma:
                confidence *= 0.7
                reasons.append("Warning: Below 200 MA")

            # Volume confirmation
            if self.volume_confirm and volume_trend:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("Volume confirms")

            # Short-term momentum alignment
            if roc_21 > 0 and roc_63 > 0:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("All timeframes aligned bullish")

        # Moderate positive momentum
        elif momentum_score > 10:
            if above_ma:
                action = "buy"
                confidence = 0.55
                reasons.append(f"Moderate momentum: {momentum_score:.1f}%")
                reasons.append("Above 200 MA support")

        # Strong negative momentum
        elif momentum_score < -20:
            action = "sell"
            confidence = 0.7
            reasons.append(f"Strong negative momentum: {momentum_score:.1f}%")

            if self.moving_average_filter and not above_ma:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append("Price below 200 MA")

            if roc_21 < 0 and roc_63 < 0:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("All timeframes aligned bearish")

        # Moderate negative momentum
        elif momentum_score < -10:
            if not above_ma:
                action = "sell"
                confidence = 0.55
                reasons.append(f"Moderate negative momentum: {momentum_score:.1f}%")
                reasons.append("Below 200 MA resistance")

        # Momentum reversal signals
        prev_momentum = float(prev_row.get("momentum_score", 0))
        if momentum_score > 0 > prev_momentum:
            confidence = min(confidence + 0.1, 1.0) if action == "buy" else confidence
            reasons.append("Momentum turned positive")
        elif momentum_score < 0 < prev_momentum:
            confidence = min(confidence + 0.1, 1.0) if action == "sell" else confidence
            reasons.append("Momentum turned negative")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear momentum signal",
            "indicators": {
                "momentum_score": momentum_score,
                "roc_21": roc_21,
                "roc_63": roc_63,
                "roc_126": float(last_row.get("roc_126", 0)),
                "roc_252": float(last_row.get("roc_252", 0)),
                "above_200ma": above_ma,
                "volume_trend": volume_trend,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(current_price, action))

        return signal

    def _calculate_stop_take_profit(
        self, price: float, action: str
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit"""
        # Momentum strategies use wider stops
        stop_pct = 0.08  # 8% stop
        profit_pct = 0.20  # 20% target (momentum can run)

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
            "indicators": {"momentum_score": self.momentum_score},
        }
