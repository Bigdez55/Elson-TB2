"""
VWAP (Volume Weighted Average Price) Execution Strategy

Executes orders by matching the volume profile throughout the trading day
to achieve execution price close to VWAP.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="vwap_execution",
    category=StrategyCategory.EXECUTION,
    description="Volume Weighted Average Price execution algorithm",
    default_parameters={
        "total_quantity": 1000,
        "execution_window_minutes": 240,  # 4 hours
        "num_slices": 20,
        "participation_rate": 0.10,  # Max 10% of volume
        "urgency": "normal",  # low, normal, high
        "use_historical_profile": True,
        "price_limit": None,
        "allow_crossing": True,
        "min_slice_size": 10,
        "max_slice_deviation": 0.2,  # Allow 20% deviation from target
    },
    required_data=["close", "volume"],
    timeframes=["1m", "5m"],
    risk_level="low",
)
class VWAPExecutionStrategy(TradingStrategy):
    """
    VWAP Execution Strategy

    Executes large orders by distributing them according to historical
    volume patterns to minimize market impact.

    Features:
    - Historical volume profile matching
    - Participation rate limiting
    - Dynamic slice sizing
    - Price limit support
    - Urgency adjustment
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        total_quantity: float = 1000,
        execution_window_minutes: int = 240,
        num_slices: int = 20,
        participation_rate: float = 0.10,
        urgency: str = "normal",
        use_historical_profile: bool = True,
        price_limit: Optional[float] = None,
        allow_crossing: bool = True,
        side: str = "buy",  # buy or sell
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="VWAP Execution",
            description="Volume weighted execution algorithm",
            parameters={
                "total_quantity": total_quantity,
                "execution_window_minutes": execution_window_minutes,
                "num_slices": num_slices,
                "participation_rate": participation_rate,
                "urgency": urgency,
                "use_historical_profile": use_historical_profile,
                "price_limit": price_limit,
                "allow_crossing": allow_crossing,
                "side": side,
                "min_slice_size": kwargs.get("min_slice_size", 10),
                "max_slice_deviation": kwargs.get("max_slice_deviation", 0.2),
            },
        )
        self.market_data_service = market_data_service
        self.total_quantity = total_quantity
        self.execution_window_minutes = execution_window_minutes
        self.num_slices = num_slices
        self.participation_rate = participation_rate
        self.urgency = urgency
        self.use_historical_profile = use_historical_profile
        self.price_limit = price_limit
        self.allow_crossing = allow_crossing
        self.side = side
        self.min_slice_size = kwargs.get("min_slice_size", 10)
        self.max_slice_deviation = kwargs.get("max_slice_deviation", 0.2)

        # Execution state
        self.start_time: Optional[datetime] = None
        self.executed_quantity: float = 0.0
        self.executed_value: float = 0.0
        self.slice_schedule: List[Dict[str, Any]] = []
        self.current_slice_index: int = 0
        self.volume_profile: List[float] = []
        self.execution_complete: bool = False

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution signal based on VWAP schedule"""
        try:
            current_price = market_data.get("price", 0.0)
            current_volume = market_data.get("volume", 0.0)
            current_time = datetime.utcnow()

            if current_price <= 0:
                return self._create_hold_signal(0.0, "Invalid price")

            # Initialize execution if not started
            if self.start_time is None:
                await self._initialize_execution(current_time, market_data)

            # Check if execution is complete
            if self.execution_complete:
                return self._create_completion_signal(current_price)

            # Check price limit
            if not self._check_price_limit(current_price):
                return self._create_hold_signal(
                    current_price,
                    f"Price {current_price:.2f} beyond limit {self.price_limit:.2f}",
                )

            # Determine current slice
            signal = self._generate_execution_signal(
                current_price, current_volume, current_time
            )

            self.last_signal_time = current_time
            return signal

        except Exception as e:
            logger.error(f"Error in VWAP execution: {str(e)}")
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

    async def _initialize_execution(
        self, current_time: datetime, market_data: Dict[str, Any]
    ) -> None:
        """Initialize execution schedule"""
        self.start_time = current_time
        self.executed_quantity = 0.0
        self.executed_value = 0.0
        self.execution_complete = False

        # Get historical volume profile if available
        if self.use_historical_profile:
            self.volume_profile = await self._get_volume_profile()

        if not self.volume_profile:
            # Use uniform distribution
            self.volume_profile = [1.0 / self.num_slices] * self.num_slices

        # Normalize profile
        total = sum(self.volume_profile)
        self.volume_profile = [v / total for v in self.volume_profile]

        # Create slice schedule
        self._create_slice_schedule(current_time)

        logger.info(
            f"VWAP execution initialized: {self.total_quantity} shares, "
            f"{self.num_slices} slices over {self.execution_window_minutes} minutes"
        )

    async def _get_volume_profile(self) -> List[float]:
        """Get historical intraday volume profile"""
        try:
            if self.market_data_service is None:
                return []

            # Get historical intraday data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=20)

            historical = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat(), interval="5m"
            )

            if not historical:
                return []

            # Aggregate volume by time of day
            volume_by_slot = {}
            for bar in historical:
                timestamp = bar.get("timestamp")
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

                # Create time slot (e.g., every 5 minutes)
                slot = timestamp.hour * 60 + (timestamp.minute // 5) * 5
                volume = bar.get("volume", 0)

                if slot not in volume_by_slot:
                    volume_by_slot[slot] = []
                volume_by_slot[slot].append(volume)

            # Average volume per slot
            profile = []
            slots = sorted(volume_by_slot.keys())

            # Map to our slice count
            slice_duration = self.execution_window_minutes / self.num_slices

            for i in range(self.num_slices):
                slice_start = i * slice_duration
                slice_end = (i + 1) * slice_duration

                total_vol = 0
                for slot, volumes in volume_by_slot.items():
                    if slice_start <= slot < slice_end:
                        total_vol += np.mean(volumes)

                profile.append(max(total_vol, 0.001))

            return profile

        except Exception as e:
            logger.warning(f"Could not get volume profile: {str(e)}")
            return []

    def _create_slice_schedule(self, start_time: datetime) -> None:
        """Create execution schedule based on volume profile"""
        slice_duration = timedelta(
            minutes=self.execution_window_minutes / self.num_slices
        )
        remaining_quantity = self.total_quantity

        self.slice_schedule = []

        for i in range(self.num_slices):
            slice_quantity = self.total_quantity * self.volume_profile[i]

            # Apply urgency adjustment
            if self.urgency == "high":
                # Front-load execution
                weight = 1.5 - (i / self.num_slices)
            elif self.urgency == "low":
                # Back-load execution
                weight = 0.5 + (i / self.num_slices)
            else:
                weight = 1.0

            adjusted_quantity = slice_quantity * weight

            # Ensure minimum slice size
            adjusted_quantity = max(adjusted_quantity, self.min_slice_size)

            self.slice_schedule.append(
                {
                    "index": i,
                    "start_time": start_time + (i * slice_duration),
                    "end_time": start_time + ((i + 1) * slice_duration),
                    "target_quantity": adjusted_quantity,
                    "executed_quantity": 0.0,
                    "status": "pending",
                }
            )

        # Normalize to total quantity
        total_scheduled = sum(s["target_quantity"] for s in self.slice_schedule)
        if total_scheduled > 0:
            for s in self.slice_schedule:
                s["target_quantity"] *= self.total_quantity / total_scheduled

    def _check_price_limit(self, current_price: float) -> bool:
        """Check if current price is within limit"""
        if self.price_limit is None:
            return True

        if self.side == "buy":
            return current_price <= self.price_limit
        else:
            return current_price >= self.price_limit

    def _generate_execution_signal(
        self, current_price: float, current_volume: float, current_time: datetime
    ) -> Dict[str, Any]:
        """Generate execution signal for current time"""
        # Find current slice
        current_slice = None
        for slice_info in self.slice_schedule:
            if slice_info["start_time"] <= current_time < slice_info["end_time"]:
                current_slice = slice_info
                break

        if current_slice is None:
            # Check if we're past execution window
            if current_time >= self.slice_schedule[-1]["end_time"]:
                self.execution_complete = True
                return self._create_completion_signal(current_price)
            return self._create_hold_signal(
                current_price, "Waiting for execution window"
            )

        # Calculate remaining for this slice
        remaining_slice = (
            current_slice["target_quantity"] - current_slice["executed_quantity"]
        )
        remaining_total = self.total_quantity - self.executed_quantity

        if remaining_total <= 0:
            self.execution_complete = True
            return self._create_completion_signal(current_price)

        # Determine order size based on participation rate
        participation_limit = current_volume * self.participation_rate
        order_size = min(remaining_slice, participation_limit, remaining_total)

        # Apply minimum size
        if order_size < self.min_slice_size and remaining_total >= self.min_slice_size:
            order_size = min(self.min_slice_size, remaining_total)

        if order_size <= 0:
            return self._create_hold_signal(current_price, "Waiting for volume")

        # Calculate execution metrics
        time_elapsed = (current_time - self.start_time).total_seconds() / 60
        time_progress = time_elapsed / self.execution_window_minutes
        quantity_progress = (
            self.executed_quantity / self.total_quantity
            if self.total_quantity > 0
            else 0
        )

        # Determine if we're ahead or behind schedule
        schedule_status = "on_track"
        if quantity_progress > time_progress + 0.1:
            schedule_status = "ahead"
        elif quantity_progress < time_progress - 0.1:
            schedule_status = "behind"
            # Increase urgency if behind
            order_size *= 1.2

        # Calculate current VWAP
        current_vwap = (
            self.executed_value / self.executed_quantity
            if self.executed_quantity > 0
            else current_price
        )

        # Determine action
        action = self.side  # "buy" or "sell"
        confidence = 0.8

        # Adjust confidence based on price vs VWAP
        price_vs_vwap = (
            (current_price - current_vwap) / current_vwap if current_vwap > 0 else 0
        )

        if self.side == "buy":
            if price_vs_vwap < -0.001:  # Price below VWAP - good for buying
                confidence = min(0.95, confidence + 0.1)
            elif price_vs_vwap > 0.002:  # Price above VWAP - less aggressive
                confidence = max(0.5, confidence - 0.1)
        else:
            if price_vs_vwap > 0.001:  # Price above VWAP - good for selling
                confidence = min(0.95, confidence + 0.1)
            elif price_vs_vwap < -0.002:  # Price below VWAP - less aggressive
                confidence = max(0.5, confidence - 0.1)

        reasons = [
            f"VWAP slice {current_slice['index'] + 1}/{self.num_slices}",
            f"Progress: {quantity_progress:.1%} of quantity, {time_progress:.1%} of time",
            f"Schedule: {schedule_status}",
        ]

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": current_time.isoformat(),
            "reason": "; ".join(reasons),
            "order_quantity": order_size,
            "indicators": {
                "current_vwap": current_vwap,
                "target_vwap": current_price,  # Market VWAP would go here
                "executed_quantity": self.executed_quantity,
                "remaining_quantity": remaining_total,
                "total_quantity": self.total_quantity,
                "execution_progress": quantity_progress,
                "time_progress": time_progress,
                "schedule_status": schedule_status,
                "current_slice": current_slice["index"],
                "slice_target": current_slice["target_quantity"],
                "slice_executed": current_slice["executed_quantity"],
                "participation_rate": self.participation_rate,
            },
        }

        return signal

    def record_execution(
        self, quantity: float, price: float, slice_index: Optional[int] = None
    ) -> None:
        """Record completed execution"""
        self.executed_quantity += quantity
        self.executed_value += quantity * price

        # Update slice if specified
        if slice_index is not None and 0 <= slice_index < len(self.slice_schedule):
            self.slice_schedule[slice_index]["executed_quantity"] += quantity

        logger.info(
            f"VWAP execution recorded: {quantity} @ {price:.2f}, "
            f"Total: {self.executed_quantity}/{self.total_quantity}"
        )

        if self.executed_quantity >= self.total_quantity:
            self.execution_complete = True

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution performance summary"""
        avg_price = (
            self.executed_value / self.executed_quantity
            if self.executed_quantity > 0
            else 0
        )

        return {
            "symbol": self.symbol,
            "side": self.side,
            "total_quantity": self.total_quantity,
            "executed_quantity": self.executed_quantity,
            "remaining_quantity": self.total_quantity - self.executed_quantity,
            "executed_value": self.executed_value,
            "average_price": avg_price,
            "execution_complete": self.execution_complete,
            "slices_completed": sum(
                1
                for s in self.slice_schedule
                if s["executed_quantity"] >= s["target_quantity"] * 0.95
            ),
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
            "reason": "VWAP execution complete",
            "indicators": {
                "execution_complete": True,
                "executed_quantity": summary["executed_quantity"],
                "average_price": summary["average_price"],
                "total_value": summary["executed_value"],
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
