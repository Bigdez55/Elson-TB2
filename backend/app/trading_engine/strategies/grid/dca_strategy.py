"""
Dollar Cost Averaging (DCA) Strategy

Systematic investment strategy that buys fixed amounts at regular
intervals regardless of price.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..base import TradingStrategy
from ..registry import StrategyRegistry, StrategyCategory

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="dca_strategy",
    category=StrategyCategory.GRID,
    description="Dollar Cost Averaging systematic investment",
    default_parameters={
        "investment_amount": 100.0,  # Fixed amount per period
        "frequency_hours": 24,  # Daily by default
        "use_value_averaging": False,  # VA variant
        "target_growth_rate": 0.01,  # 1% target growth for VA
        "dip_buying_enabled": True,
        "dip_threshold": 0.05,  # 5% drop triggers extra buy
        "dip_multiplier": 2.0,  # Buy 2x on dips
        "max_single_buy_pct": 0.05,
        "min_confidence": 0.5,
        "max_position_pct": 0.50,  # DCA can accumulate large positions
    },
    required_data=["close"],
    timeframes=["1h", "4h", "1d"],
    risk_level="low",
)
class DCAStrategy(TradingStrategy):
    """
    Dollar Cost Averaging Strategy

    Systematically invests fixed amounts at regular intervals,
    with optional enhancements:

    Features:
    - Fixed interval buying
    - Value Averaging variant
    - Dip buying (extra buys on drops)
    - Configurable frequency
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        investment_amount: float = 100.0,
        frequency_hours: int = 24,
        use_value_averaging: bool = False,
        target_growth_rate: float = 0.01,
        dip_buying_enabled: bool = True,
        dip_threshold: float = 0.05,
        dip_multiplier: float = 2.0,
        max_single_buy_pct: float = 0.05,
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="DCA Strategy",
            description="Dollar Cost Averaging investment",
            parameters={
                "investment_amount": investment_amount,
                "frequency_hours": frequency_hours,
                "use_value_averaging": use_value_averaging,
                "target_growth_rate": target_growth_rate,
                "dip_buying_enabled": dip_buying_enabled,
                "dip_threshold": dip_threshold,
                "dip_multiplier": dip_multiplier,
                "max_single_buy_pct": max_single_buy_pct,
                "max_position_pct": kwargs.get("max_position_pct", 0.50),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.investment_amount = investment_amount
        self.frequency_hours = frequency_hours
        self.use_value_averaging = use_value_averaging
        self.target_growth_rate = target_growth_rate
        self.dip_buying_enabled = dip_buying_enabled
        self.dip_threshold = dip_threshold
        self.dip_multiplier = dip_multiplier
        self.max_single_buy_pct = max_single_buy_pct

        # State tracking
        self.last_buy_time: Optional[datetime] = None
        self.total_invested: float = 0.0
        self.total_shares: float = 0.0
        self.average_cost: float = 0.0
        self.period_count: int = 0
        self.recent_high: Optional[float] = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate DCA buy signal"""
        try:
            current_price = market_data.get("price", 0.0)
            current_time = datetime.utcnow()

            if current_price <= 0:
                return self._create_hold_signal(0.0, "Invalid price")

            # Update recent high for dip detection
            if self.recent_high is None or current_price > self.recent_high:
                self.recent_high = current_price

            # Check if it's time for regular DCA buy
            time_for_dca = self._is_time_for_dca(current_time)

            # Check for dip buying opportunity
            dip_opportunity = self._check_dip_opportunity(current_price)

            # Generate signal
            signal = self._generate_dca_signal(
                current_price, current_time, time_for_dca, dip_opportunity
            )

            self.last_signal_time = current_time
            return signal

        except Exception as e:
            logger.error(f"Error in DCA strategy: {str(e)}")
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

    def _is_time_for_dca(self, current_time: datetime) -> bool:
        """Check if it's time for the next DCA purchase"""
        if self.last_buy_time is None:
            return True

        time_since_last = current_time - self.last_buy_time
        return time_since_last >= timedelta(hours=self.frequency_hours)

    def _check_dip_opportunity(self, current_price: float) -> Dict[str, Any]:
        """Check if current price represents a dip buying opportunity"""
        if not self.dip_buying_enabled or self.recent_high is None:
            return {"is_dip": False, "drop_pct": 0.0}

        drop_pct = (self.recent_high - current_price) / self.recent_high

        return {
            "is_dip": drop_pct >= self.dip_threshold,
            "drop_pct": drop_pct,
            "recent_high": self.recent_high,
        }

    def _calculate_value_averaging_amount(
        self,
        current_price: float
    ) -> float:
        """Calculate investment amount for Value Averaging"""
        # Target value after this period
        target_value = self.investment_amount * (self.period_count + 1) * (
            1 + self.target_growth_rate
        ) ** (self.period_count + 1)

        # Current value
        current_value = self.total_shares * current_price

        # Amount needed to reach target
        amount_needed = target_value - current_value

        # Cap at reasonable maximum
        max_amount = self.investment_amount * 3

        return max(0, min(amount_needed, max_amount))

    def _generate_dca_signal(
        self,
        current_price: float,
        current_time: datetime,
        time_for_dca: bool,
        dip_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the DCA trading signal"""
        action = "hold"
        confidence = 0.0
        reasons = []
        buy_amount = 0.0

        # Regular DCA time
        if time_for_dca:
            action = "buy"

            if self.use_value_averaging:
                buy_amount = self._calculate_value_averaging_amount(current_price)
                reasons.append(f"Value Averaging: ${buy_amount:.2f}")
            else:
                buy_amount = self.investment_amount
                reasons.append(f"Regular DCA: ${buy_amount:.2f}")

            confidence = 0.7
            reasons.append(f"Period {self.period_count + 1}")

        # Dip buying (can trigger even if not regular DCA time)
        if dip_info["is_dip"]:
            drop_pct = dip_info["drop_pct"]

            if action == "buy":
                # Enhance existing buy
                buy_amount *= self.dip_multiplier
                confidence = min(confidence + 0.15, 0.95)
                reasons.append(f"Dip detected ({drop_pct:.1%} from high)")
            else:
                # New dip buy
                action = "buy"
                buy_amount = self.investment_amount * self.dip_multiplier
                confidence = 0.75
                reasons.append(f"Dip buying ({drop_pct:.1%} from high)")

        # Calculate shares to buy
        shares_to_buy = buy_amount / current_price if buy_amount > 0 and current_price > 0 else 0

        # Update tracking if we're buying
        if action == "buy" and buy_amount > 0:
            # These will be confirmed after actual execution
            projected_total_invested = self.total_invested + buy_amount
            projected_total_shares = self.total_shares + shares_to_buy
            projected_avg_cost = (
                projected_total_invested / projected_total_shares
                if projected_total_shares > 0 else current_price
            )
        else:
            projected_avg_cost = self.average_cost

        # Provide context on performance
        if self.average_cost > 0 and self.total_shares > 0:
            current_value = self.total_shares * current_price
            unrealized_pnl = current_value - self.total_invested
            unrealized_pnl_pct = unrealized_pnl / self.total_invested if self.total_invested > 0 else 0
            reasons.append(f"Current P/L: {unrealized_pnl_pct:.1%}")

        signal = {
            "action": action,
            "confidence": confidence,
            "price": current_price,
            "timestamp": current_time.isoformat(),
            "reason": "; ".join(reasons) if reasons else "Waiting for next DCA period",
            "indicators": {
                "investment_amount": buy_amount,
                "shares_to_buy": shares_to_buy,
                "total_invested": self.total_invested,
                "total_shares": self.total_shares,
                "average_cost": self.average_cost,
                "period_count": self.period_count,
                "is_dip": dip_info["is_dip"],
                "drop_from_high": dip_info["drop_pct"],
                "recent_high": self.recent_high,
                "time_for_dca": time_for_dca,
                "hours_until_next": self._hours_until_next_dca(current_time),
            },
        }

        # DCA doesn't use traditional stop/take profit
        # but we can provide target prices
        if action == "buy":
            signal["suggested_investment"] = buy_amount

        return signal

    def _hours_until_next_dca(self, current_time: datetime) -> float:
        """Calculate hours until next scheduled DCA"""
        if self.last_buy_time is None:
            return 0.0

        next_dca_time = self.last_buy_time + timedelta(hours=self.frequency_hours)
        time_until = next_dca_time - current_time

        return max(0, time_until.total_seconds() / 3600)

    def record_buy(
        self,
        shares: float,
        price: float,
        amount: float
    ) -> None:
        """Record a completed buy (call after order fills)"""
        self.total_shares += shares
        self.total_invested += amount
        self.average_cost = self.total_invested / self.total_shares if self.total_shares > 0 else price
        self.period_count += 1
        self.last_buy_time = datetime.utcnow()

        logger.info(
            f"DCA buy recorded: {shares:.6f} shares at ${price:.2f}, "
            f"total invested: ${self.total_invested:.2f}"
        )

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of DCA portfolio"""
        return {
            "symbol": self.symbol,
            "total_invested": self.total_invested,
            "total_shares": self.total_shares,
            "average_cost": self.average_cost,
            "period_count": self.period_count,
            "last_buy_time": self.last_buy_time.isoformat() if self.last_buy_time else None,
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
                "total_invested": self.total_invested,
                "total_shares": self.total_shares,
                "average_cost": self.average_cost,
            },
        }
