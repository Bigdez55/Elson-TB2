"""
Donchian Channel Breakout Strategy (Turtle Trading)

Implementation of the famous Turtle Trading system using
Donchian Channels with ATR-based position sizing.
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
    name="donchian_breakout",
    category=StrategyCategory.BREAKOUT,
    description="Donchian Channel breakout (Turtle Trading style)",
    default_parameters={
        "entry_period": 20,  # System 1: 20-day breakout
        "exit_period": 10,  # Exit on 10-day low/high
        "atr_period": 20,
        "risk_per_trade": 0.02,  # 2% risk per trade
        "use_system_2": False,  # 55-day breakout
        "system_2_entry": 55,
        "system_2_exit": 20,
        "pyramiding_enabled": True,
        "max_units": 4,
        "pyramid_threshold": 0.5,  # Add every 0.5 ATR
        "min_confidence": 0.5,
        "max_position_pct": 0.10,  # Higher for trend following
    },
    required_data=["high", "low", "close"],
    timeframes=["1d"],
    risk_level="high",
)
class DonchianBreakout(TradingStrategy):
    """
    Donchian Channel / Turtle Trading Strategy

    Classic trend-following system:
    - Entry: Break of 20-day high/low
    - Exit: Break of 10-day low/high
    - Position sizing: Based on ATR (N)
    - Pyramiding: Add positions every 0.5N

    Two systems:
    - System 1: 20-day entry, 10-day exit (skip if last signal profitable)
    - System 2: 55-day entry, 20-day exit (take all signals)
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 20,
        risk_per_trade: float = 0.02,
        use_system_2: bool = False,
        system_2_entry: int = 55,
        system_2_exit: int = 20,
        pyramiding_enabled: bool = True,
        max_units: int = 4,
        pyramid_threshold: float = 0.5,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Donchian Breakout (Turtle)",
            description="Turtle Trading with Donchian Channels",
            parameters={
                "entry_period": entry_period,
                "exit_period": exit_period,
                "atr_period": atr_period,
                "risk_per_trade": risk_per_trade,
                "use_system_2": use_system_2,
                "system_2_entry": system_2_entry,
                "system_2_exit": system_2_exit,
                "pyramiding_enabled": pyramiding_enabled,
                "max_units": max_units,
                "pyramid_threshold": pyramid_threshold,
                "max_position_pct": kwargs.get("max_position_pct", 0.10),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.risk_per_trade = risk_per_trade
        self.use_system_2 = use_system_2
        self.system_2_entry = system_2_entry
        self.system_2_exit = system_2_exit
        self.pyramiding_enabled = pyramiding_enabled
        self.max_units = max_units
        self.pyramid_threshold = pyramid_threshold

        # State tracking
        self.current_units = 0
        self.last_entry_price = None
        self.last_signal_profitable = None
        self.position_direction = None  # "long" or "short"
        self.n_value = None  # ATR (N)

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on Donchian breakout"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < max(self.entry_period, self.system_2_entry) + 5:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Calculate Donchian Channels and ATR
            df = self._calculate_indicators(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in Donchian strategy: {str(e)}")
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
            start_date = end_date - timedelta(days=150)

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

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian Channels and ATR"""
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        # Donchian Channels - System 1
        df["dc_upper"] = df["high"].rolling(window=self.entry_period).max()
        df["dc_lower"] = df["low"].rolling(window=self.entry_period).min()
        df["dc_middle"] = (df["dc_upper"] + df["dc_lower"]) / 2

        # Exit channels
        df["exit_upper"] = df["high"].rolling(window=self.exit_period).max()
        df["exit_lower"] = df["low"].rolling(window=self.exit_period).min()

        # System 2 channels (if enabled)
        if self.use_system_2:
            df["dc_upper_s2"] = df["high"].rolling(window=self.system_2_entry).max()
            df["dc_lower_s2"] = df["low"].rolling(window=self.system_2_entry).min()
            df["exit_upper_s2"] = df["high"].rolling(window=self.system_2_exit).max()
            df["exit_lower_s2"] = df["low"].rolling(window=self.system_2_exit).min()

        # ATR (N value)
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift(1))
        df["tr3"] = abs(df["low"] - df["close"].shift(1))
        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
        df["atr"] = df["tr"].rolling(window=self.atr_period).mean()

        return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on Donchian breakout"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        current_high = float(last_row["high"])
        current_low = float(last_row["low"])
        dc_upper = float(prev_row["dc_upper"])  # Use previous day's channel
        dc_lower = float(prev_row["dc_lower"])
        exit_upper = float(prev_row["exit_upper"])
        exit_lower = float(prev_row["exit_lower"])
        atr = float(last_row["atr"])

        self.n_value = atr

        action = "hold"
        confidence = 0.0
        reasons = []

        # Check for exit signals first (if in position)
        if self.position_direction == "long":
            if current_low < exit_lower:
                action = "sell"
                confidence = 0.9
                reasons.append(f"Exit long: price below {self.exit_period}-day low")
                self._reset_position()

        elif self.position_direction == "short":
            if current_high > exit_upper:
                action = "buy"
                confidence = 0.9
                reasons.append(f"Exit short: price above {self.exit_period}-day high")
                self._reset_position()

        # Check for entry signals (if not in position or pyramiding)
        if action == "hold":
            # System 1: Skip if last signal was profitable
            skip_system_1 = (
                self.last_signal_profitable is True and not self.use_system_2
            )

            # Long entry: break above upper channel
            if current_high > dc_upper and not skip_system_1:
                if self.position_direction is None:
                    action = "buy"
                    confidence = 0.7
                    reasons.append(f"Breakout above {self.entry_period}-day high")
                    self.position_direction = "long"
                    self.current_units = 1
                    self.last_entry_price = current_price

                elif self.position_direction == "long" and self.pyramiding_enabled:
                    # Check for pyramid add
                    if self._should_pyramid(current_price, "long"):
                        action = "buy"
                        confidence = 0.6
                        reasons.append(f"Pyramid add (unit {self.current_units + 1})")
                        self.current_units += 1
                        self.last_entry_price = current_price

            # Short entry: break below lower channel
            elif current_low < dc_lower and not skip_system_1:
                if self.position_direction is None:
                    action = "sell"
                    confidence = 0.7
                    reasons.append(f"Breakdown below {self.entry_period}-day low")
                    self.position_direction = "short"
                    self.current_units = 1
                    self.last_entry_price = current_price

                elif self.position_direction == "short" and self.pyramiding_enabled:
                    if self._should_pyramid(current_price, "short"):
                        action = "sell"
                        confidence = 0.6
                        reasons.append(f"Pyramid add (unit {self.current_units + 1})")
                        self.current_units += 1
                        self.last_entry_price = current_price

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No signal",
            "indicators": {
                "dc_upper": dc_upper,
                "dc_lower": dc_lower,
                "dc_middle": float(prev_row["dc_middle"]),
                "exit_upper": exit_upper,
                "exit_lower": exit_lower,
                "atr": atr,
                "position_direction": self.position_direction,
                "current_units": self.current_units,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(
                    current_price, action, atr, exit_lower, exit_upper
                )
            )

        return signal

    def _should_pyramid(self, current_price: float, direction: str) -> bool:
        """Check if we should add a pyramid position"""
        if self.current_units >= self.max_units:
            return False

        if self.last_entry_price is None or self.n_value is None:
            return False

        # Add every 0.5N move in our favor
        threshold = self.n_value * self.pyramid_threshold

        if direction == "long":
            return current_price > self.last_entry_price + threshold
        else:  # short
            return current_price < self.last_entry_price - threshold

    def _reset_position(self) -> None:
        """Reset position tracking"""
        self.position_direction = None
        self.current_units = 0
        self.last_entry_price = None

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        atr: float,
        exit_lower: float,
        exit_upper: float,
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit (Turtle style: 2N stop)"""
        stop_distance = atr * 2  # 2N stop loss

        if action == "buy":
            # Use exit channel or 2N, whichever is closer
            atr_stop = price - stop_distance
            stop_loss = max(atr_stop, exit_lower * 0.99)
            # Trend following: let profits run, no fixed target
            take_profit = price + (stop_distance * 3)  # 3:1 minimum R/R
        else:
            atr_stop = price + stop_distance
            stop_loss = min(atr_stop, exit_upper * 1.01)
            take_profit = price - (stop_distance * 3)

        return {"stop_loss": stop_loss, "take_profit": take_profit}

    async def calculate_position_size(
        self,
        portfolio_value: float,
        current_price: float,
        confidence: float,
        volatility: Optional[float] = None,
    ) -> float:
        """
        Calculate position size using Turtle's N-based method.

        Unit = (Portfolio * Risk%) / (N * Dollar per Point)
        """
        if self.n_value is None or self.n_value == 0:
            return await super().calculate_position_size(
                portfolio_value, current_price, confidence, volatility
            )

        # Risk amount per trade
        risk_amount = portfolio_value * self.risk_per_trade

        # Dollar volatility (1N move)
        dollar_volatility = self.n_value

        # Position size = risk amount / (2N stop loss)
        stop_distance = self.n_value * 2
        position_value = risk_amount / (stop_distance / current_price)

        # Convert to shares
        position_size = position_value / current_price

        # Cap at max position percentage
        max_position = portfolio_value * self.parameters.get("max_position_pct", 0.10)
        max_shares = max_position / current_price

        return min(position_size, max_shares)

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {
                "position_direction": self.position_direction,
                "current_units": self.current_units,
            },
        }
