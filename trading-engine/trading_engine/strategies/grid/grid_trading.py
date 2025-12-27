"""
Grid Trading Strategy

Automated grid trading that places buy orders at lower price levels
and sell orders at higher levels within a defined range.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="grid_trading",
    category=StrategyCategory.GRID,
    description="Automated grid trading within price range",
    default_parameters={
        "grid_type": "arithmetic",  # arithmetic or geometric
        "num_grids": 10,
        "upper_price": None,  # Set dynamically or manually
        "lower_price": None,
        "auto_range": True,
        "range_multiplier": 0.1,  # 10% above/below current price
        "order_size_pct": 0.02,  # 2% of portfolio per grid
        "take_profit_grids": 1,  # Sell after N grids up
        "trailing_enabled": False,
        "min_confidence": 0.5,
        "max_position_pct": 0.30,  # Grid can use more capital
    },
    required_data=["close", "high", "low"],
    timeframes=["1h", "4h"],
    risk_level="medium",
)
class GridTradingStrategy(TradingStrategy):
    """
    Grid Trading Strategy

    Creates a grid of buy and sell orders within a price range.
    Profits from price oscillations within the range.

    Features:
    - Arithmetic or geometric grid spacing
    - Auto-range calculation based on ATR
    - Configurable grid count
    - Position tracking at each level
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        grid_type: str = "arithmetic",
        num_grids: int = 10,
        upper_price: Optional[float] = None,
        lower_price: Optional[float] = None,
        auto_range: bool = True,
        range_multiplier: float = 0.1,
        order_size_pct: float = 0.02,
        take_profit_grids: int = 1,
        trailing_enabled: bool = False,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Grid Trading",
            description="Grid-based range trading",
            parameters={
                "grid_type": grid_type,
                "num_grids": num_grids,
                "upper_price": upper_price,
                "lower_price": lower_price,
                "auto_range": auto_range,
                "range_multiplier": range_multiplier,
                "order_size_pct": order_size_pct,
                "take_profit_grids": take_profit_grids,
                "trailing_enabled": trailing_enabled,
                "max_position_pct": kwargs.get("max_position_pct", 0.30),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.grid_type = grid_type
        self.num_grids = num_grids
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.auto_range = auto_range
        self.range_multiplier = range_multiplier
        self.order_size_pct = order_size_pct
        self.take_profit_grids = take_profit_grids
        self.trailing_enabled = trailing_enabled

        # Grid state
        self.grid_levels: List[float] = []
        self.positions_at_level: Dict[int, float] = {}  # level_index: quantity
        self.last_price_level: Optional[int] = None
        self.grid_initialized = False

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on grid levels"""
        try:
            current_price = market_data.get("price", 0.0)

            if current_price <= 0:
                return self._create_hold_signal(0.0, "Invalid price")

            # Initialize grid if needed
            if not self.grid_initialized or self.auto_range:
                await self._initialize_grid(current_price, market_data)

            if not self.grid_levels:
                return self._create_hold_signal(current_price, "Grid not initialized")

            # Find current price level
            current_level = self._find_price_level(current_price)

            # Check for grid crossings
            signal = self._check_grid_crossing(current_price, current_level)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error in grid trading: {str(e)}")
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

            # Reinitialize grid if range parameters changed
            if any(k in new_parameters for k in ["upper_price", "lower_price", "num_grids"]):
                self.grid_initialized = False

            return True
        except Exception:
            return False

    async def _initialize_grid(
        self,
        current_price: float,
        market_data: Dict[str, Any]
    ) -> None:
        """Initialize grid levels"""
        # Determine range
        if self.auto_range:
            self.upper_price = current_price * (1 + self.range_multiplier)
            self.lower_price = current_price * (1 - self.range_multiplier)
        elif self.upper_price is None or self.lower_price is None:
            self.upper_price = current_price * 1.1
            self.lower_price = current_price * 0.9

        # Calculate grid levels
        if self.grid_type == "arithmetic":
            # Equal spacing
            step = (self.upper_price - self.lower_price) / self.num_grids
            self.grid_levels = [
                self.lower_price + (i * step)
                for i in range(self.num_grids + 1)
            ]
        else:  # geometric
            # Percentage spacing
            ratio = (self.upper_price / self.lower_price) ** (1 / self.num_grids)
            self.grid_levels = [
                self.lower_price * (ratio ** i)
                for i in range(self.num_grids + 1)
            ]

        # Initialize positions at each level
        self.positions_at_level = {i: 0.0 for i in range(len(self.grid_levels))}

        # Set current level
        self.last_price_level = self._find_price_level(current_price)
        self.grid_initialized = True

        logger.info(
            f"Grid initialized: {self.lower_price:.2f} - {self.upper_price:.2f}, "
            f"{self.num_grids} levels"
        )

    def _find_price_level(self, price: float) -> int:
        """Find which grid level the price is at"""
        for i, level in enumerate(self.grid_levels):
            if price < level:
                return max(0, i - 1)
        return len(self.grid_levels) - 1

    def _check_grid_crossing(
        self,
        current_price: float,
        current_level: int
    ) -> Dict[str, Any]:
        """Check for grid level crossings and generate signals"""
        if self.last_price_level is None:
            self.last_price_level = current_level
            return self._create_hold_signal(current_price, "Initializing position")

        action = "hold"
        confidence = 0.0
        reasons = []

        # Price crossed down to a lower level - BUY
        if current_level < self.last_price_level:
            levels_crossed = self.last_price_level - current_level
            action = "buy"
            confidence = min(0.6 + (levels_crossed * 0.1), 0.9)
            reasons.append(f"Price dropped to grid level {current_level}")
            reasons.append(f"Crossed {levels_crossed} level(s) down")

            # Track position at this level
            self.positions_at_level[current_level] = (
                self.positions_at_level.get(current_level, 0) + 1
            )

        # Price crossed up to a higher level - SELL (if we have positions)
        elif current_level > self.last_price_level:
            levels_crossed = current_level - self.last_price_level

            # Check if we have positions to sell
            positions_below = sum(
                self.positions_at_level.get(i, 0)
                for i in range(current_level)
            )

            if positions_below > 0:
                action = "sell"
                confidence = min(0.6 + (levels_crossed * 0.1), 0.9)
                reasons.append(f"Price rose to grid level {current_level}")
                reasons.append(f"Crossed {levels_crossed} level(s) up")

                # Clear positions at lower levels
                for i in range(current_level):
                    if self.positions_at_level.get(i, 0) > 0:
                        self.positions_at_level[i] = max(
                            0, self.positions_at_level[i] - 1
                        )
                        break

        # Update last level
        self.last_price_level = current_level

        # Check if price is outside grid range
        if current_price > self.upper_price:
            reasons.append("Warning: Price above grid range")
            confidence *= 0.7 if action != "hold" else confidence
        elif current_price < self.lower_price:
            reasons.append("Warning: Price below grid range")
            confidence *= 0.7 if action != "hold" else confidence

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "Waiting for grid crossing",
            "indicators": {
                "current_level": current_level,
                "grid_levels": self.grid_levels,
                "upper_price": self.upper_price,
                "lower_price": self.lower_price,
                "positions_at_levels": dict(self.positions_at_level),
                "total_positions": sum(self.positions_at_level.values()),
                "grid_spacing": self.grid_levels[1] - self.grid_levels[0] if len(self.grid_levels) > 1 else 0,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(self._calculate_stop_take_profit(
                current_price, action, current_level
            ))

        return signal

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        level: int
    ) -> Dict[str, float]:
        """Calculate stop and target based on grid"""
        if action == "buy":
            # Stop at lower grid or below range
            stop_level = max(0, level - 2)
            stop_loss = self.grid_levels[stop_level] * 0.99

            # Target at higher grid
            target_level = min(len(self.grid_levels) - 1, level + self.take_profit_grids)
            take_profit = self.grid_levels[target_level]
        else:
            stop_level = min(len(self.grid_levels) - 1, level + 2)
            stop_loss = self.grid_levels[stop_level] * 1.01

            target_level = max(0, level - self.take_profit_grids)
            take_profit = self.grid_levels[target_level]

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
                "grid_levels": self.grid_levels,
                "grid_initialized": self.grid_initialized,
            },
        }
