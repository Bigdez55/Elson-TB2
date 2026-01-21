"""
Statistical Mean Reversion Strategy

Uses Z-score analysis and statistical deviation from mean
to identify reversion opportunities.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="statistical_mean_reversion",
    category=StrategyCategory.MEAN_REVERSION,
    description="Statistical mean reversion using Z-score analysis",
    default_parameters={
        "lookback_period": 20,
        "z_score_entry": 2.0,
        "z_score_exit": 0.5,
        "z_score_extreme": 3.0,
        "use_bollinger": True,
        "bollinger_std": 2.0,
        "half_life_check": True,
        "min_half_life": 5,
        "max_half_life": 50,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class StatisticalMeanReversion(TradingStrategy):
    """
    Statistical Mean Reversion Strategy

    Uses Z-score to identify when price has deviated significantly
    from its mean, betting on reversion to the mean.

    Features:
    - Z-score based entry/exit
    - Half-life estimation for mean reversion speed
    - Bollinger Band integration
    - Extreme level detection
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        lookback_period: int = 20,
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        z_score_extreme: float = 3.0,
        use_bollinger: bool = True,
        bollinger_std: float = 2.0,
        half_life_check: bool = True,
        min_half_life: int = 5,
        max_half_life: int = 50,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Statistical Mean Reversion",
            description="Z-score based mean reversion",
            parameters={
                "lookback_period": lookback_period,
                "z_score_entry": z_score_entry,
                "z_score_exit": z_score_exit,
                "z_score_extreme": z_score_extreme,
                "use_bollinger": use_bollinger,
                "bollinger_std": bollinger_std,
                "half_life_check": half_life_check,
                "min_half_life": min_half_life,
                "max_half_life": max_half_life,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.lookback_period = lookback_period
        self.z_score_entry = z_score_entry
        self.z_score_exit = z_score_exit
        self.z_score_extreme = z_score_extreme
        self.use_bollinger = use_bollinger
        self.bollinger_std = bollinger_std
        self.half_life_check = half_life_check
        self.min_half_life = min_half_life
        self.max_half_life = max_half_life

        # State
        self.current_z_score = None
        self.estimated_half_life = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on mean reversion"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.lookback_period * 2:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Calculate Z-score and related metrics
            df = self._calculate_statistics(df)

            # Check half-life if enabled
            if self.half_life_check:
                half_life = self._estimate_half_life(df)
                self.estimated_half_life = half_life

                if half_life < self.min_half_life or half_life > self.max_half_life:
                    return self._create_hold_signal(
                        float(df.iloc[-1]["close"]),
                        f"Half-life ({half_life:.1f}) outside acceptable range",
                    )

            # Generate trading decision
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in mean reversion strategy: {str(e)}")
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

    def _calculate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate statistical measures"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Rolling mean and standard deviation
        df["mean"] = df["close"].rolling(window=self.lookback_period).mean()
        df["std"] = df["close"].rolling(window=self.lookback_period).std()

        # Z-score
        df["z_score"] = (df["close"] - df["mean"]) / df["std"]

        # Bollinger Bands if enabled
        if self.use_bollinger:
            df["bb_upper"] = df["mean"] + (df["std"] * self.bollinger_std)
            df["bb_lower"] = df["mean"] - (df["std"] * self.bollinger_std)
            df["percent_b"] = (df["close"] - df["bb_lower"]) / (
                df["bb_upper"] - df["bb_lower"]
            )

        # Price distance from mean
        df["distance_pct"] = (df["close"] - df["mean"]) / df["mean"]

        return df

    def _estimate_half_life(self, df: pd.DataFrame) -> float:
        """
        Estimate the half-life of mean reversion using OLS regression.

        Half-life = -log(2) / log(1 + beta)
        where beta is the regression coefficient of price changes on lagged prices.
        """
        try:
            prices = df["close"].dropna().values
            if len(prices) < 20:
                return self.max_half_life + 1

            # Calculate spread from mean
            spread = prices - np.mean(prices)

            # Lag the spread
            spread_lag = np.roll(spread, 1)[1:]
            spread_diff = np.diff(spread)

            # OLS regression
            beta = np.cov(spread_diff, spread_lag)[0, 1] / np.var(spread_lag)

            if beta >= 0:
                return self.max_half_life + 1  # Not mean reverting

            half_life = -np.log(2) / beta

            return max(0, half_life)

        except Exception as e:
            logger.error(f"Error estimating half-life: {str(e)}")
            return self.max_half_life + 1

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on Z-score"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        z_score = float(last_row["z_score"])
        prev_z_score = float(prev_row["z_score"])
        mean = float(last_row["mean"])
        std = float(last_row["std"])

        self.current_z_score = z_score

        action = "hold"
        confidence = 0.0
        reasons = []

        # Extreme oversold - strong buy
        if z_score < -self.z_score_extreme:
            action = "buy"
            confidence = 0.85
            reasons.append(f"Extreme oversold (Z: {z_score:.2f})")

        # Oversold - buy
        elif z_score < -self.z_score_entry:
            action = "buy"
            confidence = 0.65
            reasons.append(f"Oversold (Z: {z_score:.2f})")

            # Momentum confirmation
            if z_score > prev_z_score:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("Z-score rising")

        # Extreme overbought - strong sell
        elif z_score > self.z_score_extreme:
            action = "sell"
            confidence = 0.85
            reasons.append(f"Extreme overbought (Z: {z_score:.2f})")

        # Overbought - sell
        elif z_score > self.z_score_entry:
            action = "sell"
            confidence = 0.65
            reasons.append(f"Overbought (Z: {z_score:.2f})")

            if z_score < prev_z_score:
                confidence = min(confidence + 0.1, 1.0)
                reasons.append("Z-score falling")

        # Exit signals (reversion to mean)
        elif (
            abs(z_score) < self.z_score_exit and abs(prev_z_score) >= self.z_score_exit
        ):
            # Close existing positions (signal depends on position)
            if prev_z_score < -self.z_score_exit:
                reasons.append("Mean reversion target reached (was long)")
            elif prev_z_score > self.z_score_exit:
                reasons.append("Mean reversion target reached (was short)")

        # Add half-life confidence
        if self.estimated_half_life:
            if self.min_half_life <= self.estimated_half_life <= self.max_half_life:
                confidence = (
                    min(confidence + 0.1, 1.0) if confidence > 0 else confidence
                )
                reasons.append(f"Good half-life: {self.estimated_half_life:.1f} days")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No signal",
            "indicators": {
                "z_score": z_score,
                "mean": mean,
                "std": std,
                "distance_pct": float(last_row.get("distance_pct", 0)),
                "half_life": self.estimated_half_life,
                "percent_b": (
                    float(last_row.get("percent_b", 0.5))
                    if self.use_bollinger
                    else None
                ),
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(current_price, action, mean, std)
            )

        return signal

    def _calculate_stop_take_profit(
        self, price: float, action: str, mean: float, std: float
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit based on mean/std"""
        if action == "buy":
            # Stop at extreme Z-score (price continues falling)
            stop_loss = mean - (std * (self.z_score_extreme + 0.5))
            # Target: mean (Z=0)
            take_profit = mean
        else:
            stop_loss = mean + (std * (self.z_score_extreme + 0.5))
            take_profit = mean

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
                "z_score": self.current_z_score,
                "half_life": self.estimated_half_life,
            },
        }
