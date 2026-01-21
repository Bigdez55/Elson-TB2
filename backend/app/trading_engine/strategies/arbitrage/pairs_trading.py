"""
Pairs Trading Strategy

Market-neutral strategy based on cointegration between two securities.
When the spread deviates from historical mean, trade the convergence.
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
    name="pairs_trading",
    category=StrategyCategory.ARBITRAGE,
    description="Cointegration-based pairs trading strategy",
    default_parameters={
        "lookback_period": 60,
        "z_score_entry": 2.0,
        "z_score_exit": 0.5,
        "z_score_stop": 3.5,
        "hedge_ratio_method": "ols",  # ols, rolling, kalman
        "rolling_window": 20,
        "min_correlation": 0.7,
        "rebalance_threshold": 0.1,
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close"],
    timeframes=["1h", "4h", "1d"],
    risk_level="medium",
)
class PairsTradingStrategy(TradingStrategy):
    """
    Pairs Trading Strategy

    A market-neutral strategy that:
    1. Identifies cointegrated pairs
    2. Calculates the hedge ratio
    3. Monitors the spread for mean reversion opportunities
    4. Goes long the underperformer, short the outperformer

    Features:
    - Multiple hedge ratio calculation methods
    - Z-score based entry/exit
    - Dynamic hedge ratio adjustment
    - Correlation monitoring
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        pair_symbol: str = None,  # The other symbol in the pair
        lookback_period: int = 60,
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        z_score_stop: float = 3.5,
        hedge_ratio_method: str = "ols",
        rolling_window: int = 20,
        min_correlation: float = 0.7,
        rebalance_threshold: float = 0.1,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Pairs Trading",
            description=f"Pairs trading {symbol} vs {pair_symbol}",
            parameters={
                "pair_symbol": pair_symbol,
                "lookback_period": lookback_period,
                "z_score_entry": z_score_entry,
                "z_score_exit": z_score_exit,
                "z_score_stop": z_score_stop,
                "hedge_ratio_method": hedge_ratio_method,
                "rolling_window": rolling_window,
                "min_correlation": min_correlation,
                "rebalance_threshold": rebalance_threshold,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.pair_symbol = pair_symbol
        self.lookback_period = lookback_period
        self.z_score_entry = z_score_entry
        self.z_score_exit = z_score_exit
        self.z_score_stop = z_score_stop
        self.hedge_ratio_method = hedge_ratio_method
        self.rolling_window = rolling_window
        self.min_correlation = min_correlation
        self.rebalance_threshold = rebalance_threshold

        # State tracking
        self.hedge_ratio: Optional[float] = None
        self.current_z_score: Optional[float] = None
        self.spread_mean: Optional[float] = None
        self.spread_std: Optional[float] = None
        self.correlation: Optional[float] = None
        self.position_side: Optional[str] = None  # "long_spread" or "short_spread"

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on pairs spread"""
        try:
            if self.pair_symbol is None:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "No pair symbol configured"
                )

            # Get data for both symbols
            df = await self._get_pair_data()

            if df is None or len(df) < self.lookback_period:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Calculate spread and statistics
            df = self._calculate_spread(df)

            # Check correlation
            self.correlation = df["symbol_1"].corr(df["symbol_2"])
            if abs(self.correlation) < self.min_correlation:
                return self._create_hold_signal(
                    market_data.get("price", 0.0),
                    f"Correlation too low ({self.correlation:.2f})",
                )

            # Generate trading decision
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in pairs trading: {str(e)}")
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
        except Exception:
            return False

    async def _get_pair_data(self) -> Optional[pd.DataFrame]:
        """Get historical data for both symbols"""
        try:
            if self.market_data_service is None:
                return None

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=150)

            # Get data for primary symbol
            data_1 = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat()
            )

            # Get data for pair symbol
            data_2 = await self.market_data_service.get_historical_data(
                self.pair_symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not data_1 or not data_2:
                return None

            # Create DataFrames
            df1 = pd.DataFrame(data_1) if isinstance(data_1, list) else data_1
            df2 = pd.DataFrame(data_2) if isinstance(data_2, list) else data_2

            df1.columns = df1.columns.str.lower()
            df2.columns = df2.columns.str.lower()

            # Merge on timestamp
            df1 = df1.rename(columns={"close": "symbol_1"})
            df2 = df2.rename(columns={"close": "symbol_2"})

            if "timestamp" in df1.columns and "timestamp" in df2.columns:
                df = pd.merge(
                    df1[["timestamp", "symbol_1"]],
                    df2[["timestamp", "symbol_2"]],
                    on="timestamp",
                    how="inner",
                )
            else:
                # Assume aligned by index
                df = pd.DataFrame(
                    {
                        "symbol_1": df1["symbol_1"].values[: min(len(df1), len(df2))],
                        "symbol_2": df2["symbol_2"].values[: min(len(df1), len(df2))],
                    }
                )

            df["symbol_1"] = pd.to_numeric(df["symbol_1"], errors="coerce")
            df["symbol_2"] = pd.to_numeric(df["symbol_2"], errors="coerce")
            df = df.dropna()

            return df

        except Exception as e:
            logger.error(f"Error getting pair data: {str(e)}")
            return None

    def _calculate_spread(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate spread between the pair"""
        # Calculate hedge ratio
        self.hedge_ratio = self._calculate_hedge_ratio(df)

        # Calculate spread: S1 - hedge_ratio * S2
        df["spread"] = df["symbol_1"] - self.hedge_ratio * df["symbol_2"]

        # Calculate spread statistics
        df["spread_mean"] = df["spread"].rolling(window=self.lookback_period).mean()
        df["spread_std"] = df["spread"].rolling(window=self.lookback_period).std()

        # Z-score of spread
        df["z_score"] = (df["spread"] - df["spread_mean"]) / df["spread_std"]

        # Store current values
        self.spread_mean = float(df["spread_mean"].iloc[-1])
        self.spread_std = float(df["spread_std"].iloc[-1])

        return df

    def _calculate_hedge_ratio(self, df: pd.DataFrame) -> float:
        """Calculate hedge ratio using specified method"""
        if self.hedge_ratio_method == "ols":
            # Simple OLS regression
            x = df["symbol_2"].values
            y = df["symbol_1"].values

            # Add constant and solve
            X = np.vstack([x, np.ones(len(x))]).T
            hedge_ratio, _ = np.linalg.lstsq(X, y, rcond=None)[0]

            return hedge_ratio

        elif self.hedge_ratio_method == "rolling":
            # Rolling hedge ratio
            recent = df.tail(self.rolling_window)
            x = recent["symbol_2"].values
            y = recent["symbol_1"].values

            cov = np.cov(x, y)[0, 1]
            var = np.var(x)

            return cov / var if var != 0 else 1.0

        else:  # Default to simple ratio
            return df["symbol_1"].iloc[-1] / df["symbol_2"].iloc[-1]

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on spread Z-score"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        z_score = float(last_row["z_score"])
        prev_z_score = float(prev_row["z_score"])
        current_spread = float(last_row["spread"])
        symbol_1_price = float(last_row["symbol_1"])
        symbol_2_price = float(last_row["symbol_2"])

        self.current_z_score = z_score

        action = "hold"
        confidence = 0.0
        reasons = []
        position_type = None

        # Stop loss check (spread diverging further)
        if self.position_side == "long_spread" and z_score < -self.z_score_stop:
            action = "sell"  # Close long spread position
            confidence = 0.9
            reasons.append(f"Stop loss triggered (Z: {z_score:.2f})")
            self.position_side = None

        elif self.position_side == "short_spread" and z_score > self.z_score_stop:
            action = "buy"  # Close short spread position
            confidence = 0.9
            reasons.append(f"Stop loss triggered (Z: {z_score:.2f})")
            self.position_side = None

        # Exit signals (spread mean reverted)
        elif self.position_side == "long_spread" and z_score > -self.z_score_exit:
            action = "sell"
            confidence = 0.8
            reasons.append(f"Mean reversion target reached (Z: {z_score:.2f})")
            self.position_side = None

        elif self.position_side == "short_spread" and z_score < self.z_score_exit:
            action = "buy"
            confidence = 0.8
            reasons.append(f"Mean reversion target reached (Z: {z_score:.2f})")
            self.position_side = None

        # Entry signals
        elif self.position_side is None:
            # Spread too low - buy spread (long S1, short S2)
            if z_score < -self.z_score_entry:
                action = "buy"
                confidence = 0.7
                reasons.append(f"Spread oversold (Z: {z_score:.2f})")
                reasons.append(f"Long {self.symbol}, Short {self.pair_symbol}")
                self.position_side = "long_spread"
                position_type = "long_spread"

                # Z-score momentum
                if z_score > prev_z_score:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Spread starting to revert")

            # Spread too high - sell spread (short S1, long S2)
            elif z_score > self.z_score_entry:
                action = "sell"
                confidence = 0.7
                reasons.append(f"Spread overbought (Z: {z_score:.2f})")
                reasons.append(f"Short {self.symbol}, Long {self.pair_symbol}")
                self.position_side = "short_spread"
                position_type = "short_spread"

                if z_score < prev_z_score:
                    confidence = min(confidence + 0.1, 1.0)
                    reasons.append("Spread starting to revert")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": symbol_1_price,  # Primary symbol price
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No signal",
            "indicators": {
                "z_score": z_score,
                "spread": current_spread,
                "spread_mean": self.spread_mean,
                "spread_std": self.spread_std,
                "hedge_ratio": self.hedge_ratio,
                "correlation": self.correlation,
                "symbol_1_price": symbol_1_price,
                "symbol_2_price": symbol_2_price,
                "pair_symbol": self.pair_symbol,
                "position_type": position_type or self.position_side,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(symbol_1_price, action, z_score)
            )

        return signal

    def _calculate_stop_take_profit(
        self, price: float, action: str, z_score: float
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit based on spread statistics"""
        # For pairs trading, stops are based on Z-score levels
        # Converting to price levels is approximate

        spread_at_stop = self.spread_mean + (
            self.z_score_stop * self.spread_std * (-1 if action == "buy" else 1)
        )
        spread_at_target = self.spread_mean  # Target is mean

        # Approximate price impact (simplified)
        current_spread = price - self.hedge_ratio * (price / (1 + self.hedge_ratio))

        if action == "buy":
            # Long spread: stop if spread goes more negative
            stop_loss = price * 0.95  # Fallback
            take_profit = price * 1.05
        else:
            stop_loss = price * 1.05
            take_profit = price * 0.95

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
                "hedge_ratio": self.hedge_ratio,
                "correlation": self.correlation,
                "pair_symbol": self.pair_symbol,
            },
        }
