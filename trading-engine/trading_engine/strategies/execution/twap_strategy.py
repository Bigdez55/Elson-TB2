"""
TWAP (Time Weighted Average Price) Execution Strategy

Executes orders by distributing them evenly across time intervals
to minimize timing risk and achieve execution close to TWAP.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="twap_execution",
    category=StrategyCategory.EXECUTION,
    description="Time Weighted Average Price execution algorithm",
    default_parameters={
        "total_quantity": 1000,
        "execution_window_minutes": 60,
        "num_slices": 12,
        "randomize_timing": True,
        "randomize_size": True,
        "size_variance": 0.2,  # +/- 20% size variation
        "timing_variance": 0.3,  # +/- 30% timing variation
        "price_limit": None,
        "min_slice_size": 10,
        "catch_up_enabled": True,
    },
    required_data=["close"],
    timeframes=["1m", "5m"],
    risk_level="low",
)
class TWAPExecutionStrategy(TradingStrategy):
    """
    TWAP Execution Strategy

    Executes large orders by distributing them evenly across time
    with optional randomization to avoid detection.

    Features:
    - Equal time-based distribution
    - Random timing variation
    - Random size variation
    - Catch-up mechanism for missed slices
    - Price limit support
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        total_quantity: float = 1000,
        execution_window_minutes: int = 60,
        num_slices: int = 12,
        randomize_timing: bool = True,
        randomize_size: bool = True,
        size_variance: float = 0.2,
        timing_variance: float = 0.3,
        price_limit: Optional[float] = None,
        side: str = "buy",
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="TWAP Execution",
            description="Time weighted execution algorithm",
            parameters={
                "total_quantity": total_quantity,
                "execution_window_minutes": execution_window_minutes,
                "num_slices": num_slices,
                "randomize_timing": randomize_timing,
                "randomize_size": randomize_size,
                "size_variance": size_variance,
                "timing_variance": timing_variance,
                "price_limit": price_limit,
                "side": side,
                "min_slice_size": kwargs.get("min_slice_size", 10),
                "catch_up_enabled": kwargs.get("catch_up_enabled", True),
            },
        )
        self.market_data_service = market_data_service
        self.total_quantity = total_quantity
        self.execution_window_minutes = execution_window_minutes
        self.num_slices = num_slices
        self.randomize_timing = randomize_timing
        self.randomize_size = randomize_size
        self.size_variance = size_variance
        self.timing_variance = timing_variance
        self.price_limit = price_limit
        self.side = side
        self.min_slice_size = kwargs.get("min_slice_size", 10)
        self.catch_up_enabled = kwargs.get("catch_up_enabled", True)

        # Execution state
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.executed_quantity: float = 0.0
        self.executed_value: float = 0.0
        self.slice_schedule: List[Dict[str, Any]] = []
        self.execution_complete: bool = False
        self.prices: List[float] = []

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution signal based on TWAP schedule"""
        try:
            current_price = market_data.get("price", 0.0)
            current_time = datetime.utcnow()

            if current_price <= 0:
                return self._create_hold_signal(0.0, "Invalid price")

            # Track prices for TWAP calculation
            self.prices.append(current_price)

            # Initialize execution if not started
            if self.start_time is None:
                self._initialize_execution(current_time)

            # Check if execution is complete
            if self.execution_complete:
                return self._create_completion_signal(current_price)

            # Check if past execution window
            if current_time >= self.end_time:
                self.execution_complete = True
                return self._create_completion_signal(current_price)

            # Check price limit
            if not self._check_price_limit(current_price):
                return self._create_hold_signal(
                    current_price,
                    f"Price {current_price:.2f} beyond limit {self.price_limit:.2f}"
                )

            # Generate execution signal
            signal = self._generate_execution_signal(current_price, current_time)

            self.last_signal_time = current_time
            return signal

        except Exception as e:
            logger.error(f"Error in TWAP execution: {str(e)}")
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
        except Exception:
            return False

    def _initialize_execution(self, current_time: datetime) -> None:
        """Initialize execution schedule"""
        self.start_time = current_time
        self.end_time = current_time + timedelta(minutes=self.execution_window_minutes)
        self.executed_quantity = 0.0
        self.executed_value = 0.0
        self.execution_complete = False
        self.prices = []

        # Create equal-sized slices
        base_slice_size = self.total_quantity / self.num_slices
        slice_duration = timedelta(minutes=self.execution_window_minutes / self.num_slices)

        self.slice_schedule = []

        for i in range(self.num_slices):
            # Base timing
            base_start = current_time + (i * slice_duration)
            base_end = current_time + ((i + 1) * slice_duration)

            # Apply timing randomization
            if self.randomize_timing and i > 0:  # Don't randomize first slice
                max_offset = slice_duration * self.timing_variance
                offset_seconds = random.uniform(
                    -max_offset.total_seconds(),
                    max_offset.total_seconds()
                )
                actual_time = base_start + timedelta(seconds=offset_seconds)
                # Ensure we don't go before previous slice
                actual_time = max(actual_time, base_start)
            else:
                actual_time = base_start

            # Apply size randomization
            if self.randomize_size:
                size_multiplier = 1 + random.uniform(-self.size_variance, self.size_variance)
                target_quantity = base_slice_size * size_multiplier
            else:
                target_quantity = base_slice_size

            target_quantity = max(target_quantity, self.min_slice_size)

            self.slice_schedule.append({
                "index": i,
                "target_time": actual_time,
                "window_start": base_start,
                "window_end": base_end,
                "target_quantity": target_quantity,
                "executed_quantity": 0.0,
                "executed": False,
            })

        # Normalize quantities to total
        total_scheduled = sum(s["target_quantity"] for s in self.slice_schedule)
        if total_scheduled > 0:
            for s in self.slice_schedule:
                s["target_quantity"] *= self.total_quantity / total_scheduled

        logger.info(
            f"TWAP execution initialized: {self.total_quantity} shares, "
            f"{self.num_slices} slices over {self.execution_window_minutes} minutes"
        )

    def _check_price_limit(self, current_price: float) -> bool:
        """Check if current price is within limit"""
        if self.price_limit is None:
            return True

        if self.side == "buy":
            return current_price <= self.price_limit
        else:
            return current_price >= self.price_limit

    def _generate_execution_signal(
        self,
        current_price: float,
        current_time: datetime
    ) -> Dict[str, Any]:
        """Generate execution signal for current time"""
        remaining_total = self.total_quantity - self.executed_quantity

        if remaining_total <= 0:
            self.execution_complete = True
            return self._create_completion_signal(current_price)

        # Find slices that should be executed
        slices_to_execute = []
        for slice_info in self.slice_schedule:
            if slice_info["executed"]:
                continue

            # Check if it's time for this slice
            if current_time >= slice_info["target_time"]:
                slices_to_execute.append(slice_info)
            # Also check if we're in the slice window and past target
            elif (
                slice_info["window_start"] <= current_time < slice_info["window_end"]
                and current_time >= slice_info["target_time"]
            ):
                slices_to_execute.append(slice_info)

        if not slices_to_execute:
            # Find next scheduled slice
            next_slice = None
            for s in self.slice_schedule:
                if not s["executed"] and s["target_time"] > current_time:
                    next_slice = s
                    break

            if next_slice:
                time_until = (next_slice["target_time"] - current_time).total_seconds()
                return self._create_hold_signal(
                    current_price,
                    f"Next slice in {time_until:.0f}s"
                )
            else:
                return self._create_hold_signal(current_price, "No pending slices")

        # Calculate order size (combine multiple pending slices if behind)
        order_size = 0.0
        slices_being_executed = []

        for slice_info in slices_to_execute:
            remaining_slice = slice_info["target_quantity"] - slice_info["executed_quantity"]
            if remaining_slice > 0:
                order_size += remaining_slice
                slices_being_executed.append(slice_info["index"])

        # Apply catch-up if behind schedule
        if self.catch_up_enabled:
            time_progress = (
                (current_time - self.start_time).total_seconds() /
                (self.end_time - self.start_time).total_seconds()
            )
            expected_executed = self.total_quantity * time_progress
            shortfall = expected_executed - self.executed_quantity

            if shortfall > 0:
                # Add catch-up quantity
                catch_up = min(shortfall * 0.5, remaining_total - order_size)
                if catch_up > 0:
                    order_size += catch_up

        # Cap at remaining
        order_size = min(order_size, remaining_total)

        if order_size < self.min_slice_size and remaining_total >= self.min_slice_size:
            order_size = self.min_slice_size

        if order_size <= 0:
            return self._create_hold_signal(current_price, "Waiting")

        # Calculate metrics
        time_elapsed = (current_time - self.start_time).total_seconds() / 60
        time_progress = time_elapsed / self.execution_window_minutes
        quantity_progress = self.executed_quantity / self.total_quantity if self.total_quantity > 0 else 0

        # Calculate actual TWAP
        actual_twap = sum(self.prices) / len(self.prices) if self.prices else current_price

        # Average execution price
        avg_exec_price = (
            self.executed_value / self.executed_quantity
            if self.executed_quantity > 0 else 0
        )

        # Schedule status
        schedule_status = "on_track"
        if quantity_progress > time_progress + 0.15:
            schedule_status = "ahead"
        elif quantity_progress < time_progress - 0.15:
            schedule_status = "behind"

        # Confidence based on price vs TWAP
        confidence = 0.8
        price_vs_twap = (current_price - actual_twap) / actual_twap if actual_twap > 0 else 0

        if self.side == "buy":
            if price_vs_twap < -0.002:
                confidence = min(0.95, confidence + 0.1)
            elif price_vs_twap > 0.003:
                confidence = max(0.6, confidence - 0.15)
        else:
            if price_vs_twap > 0.002:
                confidence = min(0.95, confidence + 0.1)
            elif price_vs_twap < -0.003:
                confidence = max(0.6, confidence - 0.15)

        reasons = [
            f"TWAP slice(s) {slices_being_executed}",
            f"Progress: {quantity_progress:.1%} qty, {time_progress:.1%} time",
            f"Schedule: {schedule_status}",
        ]

        signal = {
            "action": self.side,
            "confidence": confidence,
            "price": current_price,
            "timestamp": current_time.isoformat(),
            "reason": "; ".join(reasons),
            "order_quantity": order_size,
            "indicators": {
                "market_twap": actual_twap,
                "execution_avg_price": avg_exec_price,
                "executed_quantity": self.executed_quantity,
                "remaining_quantity": remaining_total,
                "total_quantity": self.total_quantity,
                "execution_progress": quantity_progress,
                "time_progress": time_progress,
                "schedule_status": schedule_status,
                "slices_executed": sum(1 for s in self.slice_schedule if s["executed"]),
                "total_slices": self.num_slices,
                "slices_pending": slices_being_executed,
            },
        }

        return signal

    def record_execution(
        self,
        quantity: float,
        price: float,
        slice_indices: Optional[List[int]] = None
    ) -> None:
        """Record completed execution"""
        self.executed_quantity += quantity
        self.executed_value += quantity * price

        # Mark slices as executed
        if slice_indices:
            for idx in slice_indices:
                if 0 <= idx < len(self.slice_schedule):
                    self.slice_schedule[idx]["executed"] = True
                    self.slice_schedule[idx]["executed_quantity"] = (
                        self.slice_schedule[idx]["target_quantity"]
                    )

        logger.info(
            f"TWAP execution recorded: {quantity} @ {price:.2f}, "
            f"Total: {self.executed_quantity}/{self.total_quantity}"
        )

        if self.executed_quantity >= self.total_quantity:
            self.execution_complete = True

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution performance summary"""
        avg_exec_price = (
            self.executed_value / self.executed_quantity
            if self.executed_quantity > 0 else 0
        )
        market_twap = sum(self.prices) / len(self.prices) if self.prices else 0

        # Calculate slippage vs TWAP
        if market_twap > 0 and avg_exec_price > 0:
            if self.side == "buy":
                slippage_bps = (avg_exec_price - market_twap) / market_twap * 10000
            else:
                slippage_bps = (market_twap - avg_exec_price) / market_twap * 10000
        else:
            slippage_bps = 0

        return {
            "symbol": self.symbol,
            "side": self.side,
            "total_quantity": self.total_quantity,
            "executed_quantity": self.executed_quantity,
            "remaining_quantity": self.total_quantity - self.executed_quantity,
            "executed_value": self.executed_value,
            "average_execution_price": avg_exec_price,
            "market_twap": market_twap,
            "slippage_bps": slippage_bps,
            "execution_complete": self.execution_complete,
            "slices_completed": sum(1 for s in self.slice_schedule if s["executed"]),
            "total_slices": len(self.slice_schedule),
        }

    def _create_completion_signal(self, price: float) -> Dict[str, Any]:
        """Create signal for completed execution"""
        summary = self.get_execution_summary()

        return {
            "action": "hold",
            "confidence": 1.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": f"TWAP execution complete. Slippage: {summary['slippage_bps']:.1f} bps",
            "indicators": {
                "execution_complete": True,
                "executed_quantity": summary["executed_quantity"],
                "average_price": summary["average_execution_price"],
                "market_twap": summary["market_twap"],
                "slippage_bps": summary["slippage_bps"],
            },
        }

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {
                "executed_quantity": self.executed_quantity,
                "remaining_quantity": self.total_quantity - self.executed_quantity,
                "execution_complete": self.execution_complete,
            },
        }
