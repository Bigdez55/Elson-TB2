"""
Ichimoku Cloud (Ichimoku Kinko Hyo) Trading Strategy

Complete implementation of the Japanese Ichimoku system with:
- Tenkan-sen / Kijun-sen crossovers
- Kumo (Cloud) breakouts
- Chikou Span confirmation
- Multiple signal types
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
    name="ichimoku_cloud",
    category=StrategyCategory.TECHNICAL,
    description="Ichimoku Kinko Hyo (One Glance Equilibrium Chart) trading strategy",
    default_parameters={
        "tenkan_period": 9,
        "kijun_period": 26,
        "senkou_b_period": 52,
        "displacement": 26,
        "signal_mode": "tk_cross",  # tk_cross, kumo_breakout, combined
        "min_confidence": 0.5,
        "max_position_pct": 0.05,
    },
    required_data=["close", "high", "low"],
    timeframes=["4h", "1d", "1w"],
    risk_level="medium",
)
class IchimokuCloudStrategy(TradingStrategy):
    """
    Ichimoku Cloud Trading Strategy

    Components:
    - Tenkan-sen (Conversion Line): 9-period midpoint
    - Kijun-sen (Base Line): 26-period midpoint
    - Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, displaced 26 periods
    - Senkou Span B (Leading Span B): 52-period midpoint, displaced 26 periods
    - Chikou Span (Lagging Span): Close price, displaced 26 periods back

    Signal Types:
    1. TK Cross: Tenkan crosses Kijun
    2. Kumo Breakout: Price breaks through cloud
    3. Chikou Confirmation: Lagging span vs price
    4. Cloud Twist: Senkou A crosses Senkou B
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26,
        signal_mode: str = "combined",
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Ichimoku Cloud Strategy",
            description="Ichimoku Kinko Hyo trading system",
            parameters={
                "tenkan_period": tenkan_period,
                "kijun_period": kijun_period,
                "senkou_b_period": senkou_b_period,
                "displacement": displacement,
                "signal_mode": signal_mode,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "min_confidence": kwargs.get("min_confidence", 0.5),
            },
        )
        self.market_data_service = market_data_service
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement
        self.signal_mode = signal_mode

        # State tracking
        self.cloud_color = None  # "bullish" or "bearish"
        self.price_vs_cloud = None  # "above", "below", "inside"

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on Ichimoku analysis"""
        try:
            df = await self._get_historical_data()

            if df is None or len(df) < self.senkou_b_period + self.displacement + 10:
                return self._create_hold_signal(
                    market_data.get("price", 0.0), "Insufficient historical data"
                )

            # Calculate all Ichimoku components
            df = self._calculate_ichimoku(df)

            # Generate signal based on mode
            if self.signal_mode == "tk_cross":
                signal = self._tk_cross_signal(df)
            elif self.signal_mode == "kumo_breakout":
                signal = self._kumo_breakout_signal(df)
            else:  # combined
                signal = self._combined_signal(df)

            self.last_signal_time = datetime.utcnow()
            return signal

        except Exception as e:
            logger.error(f"Error generating Ichimoku signal: {str(e)}")
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
            start_date = end_date - timedelta(days=200)

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

    def _calculate_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all Ichimoku components"""
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")

        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        df["tenkan_sen"] = (
            df["high"].rolling(window=self.tenkan_period).max()
            + df["low"].rolling(window=self.tenkan_period).min()
        ) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        df["kijun_sen"] = (
            df["high"].rolling(window=self.kijun_period).max()
            + df["low"].rolling(window=self.kijun_period).min()
        ) / 2

        # Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, displaced forward
        df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(
            self.displacement
        )

        # Senkou Span B (Leading Span B): 52-period midpoint, displaced forward
        df["senkou_span_b"] = (
            (
                df["high"].rolling(window=self.senkou_b_period).max()
                + df["low"].rolling(window=self.senkou_b_period).min()
            )
            / 2
        ).shift(self.displacement)

        # Chikou Span (Lagging Span): Close displaced backward
        df["chikou_span"] = df["close"].shift(-self.displacement)

        # Calculate cloud boundaries (current, not displaced)
        df["cloud_top"] = df[["senkou_span_a", "senkou_span_b"]].max(axis=1)
        df["cloud_bottom"] = df[["senkou_span_a", "senkou_span_b"]].min(axis=1)

        # Cloud color/direction
        df["cloud_bullish"] = df["senkou_span_a"] > df["senkou_span_b"]

        return df

    def _tk_cross_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate Tenkan-sen / Kijun-sen crossover signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        tenkan = float(last_row["tenkan_sen"])
        kijun = float(last_row["kijun_sen"])
        prev_tenkan = float(prev_row["tenkan_sen"])
        prev_kijun = float(prev_row["kijun_sen"])
        cloud_top = float(last_row["cloud_top"])
        cloud_bottom = float(last_row["cloud_bottom"])

        action = "hold"
        confidence = 0.0
        reasons = []

        # TK Cross signals
        bullish_cross = prev_tenkan <= prev_kijun and tenkan > kijun
        bearish_cross = prev_tenkan >= prev_kijun and tenkan < kijun

        if bullish_cross:
            action = "buy"
            confidence = 0.6
            reasons.append("Tenkan crossed above Kijun (bullish)")

            # Stronger if above cloud
            if current_price > cloud_top:
                confidence = min(confidence + 0.2, 1.0)
                reasons.append("Price above cloud")
            # Weaker if below cloud
            elif current_price < cloud_bottom:
                confidence *= 0.7
                reasons.append("Warning: Price below cloud")

        elif bearish_cross:
            action = "sell"
            confidence = 0.6
            reasons.append("Tenkan crossed below Kijun (bearish)")

            # Stronger if below cloud
            if current_price < cloud_bottom:
                confidence = min(confidence + 0.2, 1.0)
                reasons.append("Price below cloud")
            # Weaker if above cloud
            elif current_price > cloud_top:
                confidence *= 0.7
                reasons.append("Warning: Price above cloud")

        return self._create_signal(
            action,
            confidence,
            current_price,
            reasons,
            tenkan,
            kijun,
            cloud_top,
            cloud_bottom,
            last_row,
        )

    def _kumo_breakout_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate Kumo (Cloud) breakout signals"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        prev_price = float(prev_row["close"])
        cloud_top = float(last_row["cloud_top"])
        cloud_bottom = float(last_row["cloud_bottom"])
        prev_cloud_top = float(prev_row["cloud_top"])
        prev_cloud_bottom = float(prev_row["cloud_bottom"])
        tenkan = float(last_row["tenkan_sen"])
        kijun = float(last_row["kijun_sen"])

        action = "hold"
        confidence = 0.0
        reasons = []

        # Kumo breakout signals
        breakout_up = prev_price <= prev_cloud_top and current_price > cloud_top
        breakout_down = prev_price >= prev_cloud_bottom and current_price < cloud_bottom

        if breakout_up:
            action = "buy"
            confidence = 0.7
            reasons.append("Price broke above Kumo (cloud)")

            # Cloud thickness confirmation
            cloud_thickness = cloud_top - cloud_bottom
            if cloud_thickness > current_price * 0.02:  # Thick cloud
                confidence = min(confidence + 0.15, 1.0)
                reasons.append("Strong breakout through thick cloud")

        elif breakout_down:
            action = "sell"
            confidence = 0.7
            reasons.append("Price broke below Kumo (cloud)")

            cloud_thickness = cloud_top - cloud_bottom
            if cloud_thickness > current_price * 0.02:
                confidence = min(confidence + 0.15, 1.0)
                reasons.append("Strong breakout through thick cloud")

        # Track price vs cloud position
        if current_price > cloud_top:
            self.price_vs_cloud = "above"
        elif current_price < cloud_bottom:
            self.price_vs_cloud = "below"
        else:
            self.price_vs_cloud = "inside"

        return self._create_signal(
            action,
            confidence,
            current_price,
            reasons,
            tenkan,
            kijun,
            cloud_top,
            cloud_bottom,
            last_row,
        )

    def _combined_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate combined signal using multiple Ichimoku components"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        current_price = float(last_row["close"])
        tenkan = float(last_row["tenkan_sen"])
        kijun = float(last_row["kijun_sen"])
        prev_tenkan = float(prev_row["tenkan_sen"])
        prev_kijun = float(prev_row["kijun_sen"])
        cloud_top = float(last_row["cloud_top"])
        cloud_bottom = float(last_row["cloud_bottom"])
        senkou_a = float(last_row["senkou_span_a"])
        senkou_b = float(last_row["senkou_span_b"])
        cloud_bullish = bool(last_row["cloud_bullish"])

        # Score-based system
        bullish_score = 0
        bearish_score = 0
        reasons = []

        # 1. Price vs Cloud (strongest signal)
        if current_price > cloud_top:
            bullish_score += 2
            reasons.append("Price above cloud")
        elif current_price < cloud_bottom:
            bearish_score += 2
            reasons.append("Price below cloud")

        # 2. TK relationship
        if tenkan > kijun:
            bullish_score += 1
            reasons.append("Tenkan above Kijun")
        elif tenkan < kijun:
            bearish_score += 1
            reasons.append("Tenkan below Kijun")

        # 3. TK Cross (recent)
        if prev_tenkan <= prev_kijun and tenkan > kijun:
            bullish_score += 2
            reasons.append("Bullish TK cross")
        elif prev_tenkan >= prev_kijun and tenkan < kijun:
            bearish_score += 2
            reasons.append("Bearish TK cross")

        # 4. Cloud color (future trend)
        if cloud_bullish:
            bullish_score += 1
            reasons.append("Cloud is bullish")
        else:
            bearish_score += 1
            reasons.append("Cloud is bearish")

        # 5. Price vs Kijun
        if current_price > kijun:
            bullish_score += 1
        else:
            bearish_score += 1

        # Determine action
        action = "hold"
        confidence = 0.0
        total_score = bullish_score + bearish_score

        if bullish_score >= 4 and bullish_score > bearish_score + 1:
            action = "buy"
            confidence = min(0.5 + (bullish_score / total_score) * 0.4, 0.95)
        elif bearish_score >= 4 and bearish_score > bullish_score + 1:
            action = "sell"
            confidence = min(0.5 + (bearish_score / total_score) * 0.4, 0.95)

        self.cloud_color = "bullish" if cloud_bullish else "bearish"

        return self._create_signal(
            action,
            confidence,
            current_price,
            reasons,
            tenkan,
            kijun,
            cloud_top,
            cloud_bottom,
            last_row,
        )

    def _create_signal(
        self,
        action: str,
        confidence: float,
        price: float,
        reasons: list,
        tenkan: float,
        kijun: float,
        cloud_top: float,
        cloud_bottom: float,
        last_row: pd.Series,
    ) -> Dict[str, Any]:
        """Create signal dictionary"""
        signal = {
            "action": action,
            "confidence": confidence,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "; ".join(reasons) if reasons else "No clear signal",
            "indicators": {
                "tenkan_sen": tenkan,
                "kijun_sen": kijun,
                "senkou_span_a": float(last_row.get("senkou_span_a", 0)),
                "senkou_span_b": float(last_row.get("senkou_span_b", 0)),
                "cloud_top": cloud_top,
                "cloud_bottom": cloud_bottom,
                "cloud_color": self.cloud_color,
                "price_vs_cloud": self.price_vs_cloud,
            },
        }

        if action in ["buy", "sell"]:
            signal.update(
                self._calculate_stop_take_profit(
                    price, action, kijun, cloud_top, cloud_bottom
                )
            )

        return signal

    def _calculate_stop_take_profit(
        self,
        price: float,
        action: str,
        kijun: float,
        cloud_top: float,
        cloud_bottom: float,
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit using Ichimoku levels"""
        if action == "buy":
            # Stop below Kijun or cloud bottom
            stop = min(kijun * 0.99, cloud_bottom * 0.99)
            # Target based on risk/reward
            risk = price - stop
            profit = price + (risk * 2)  # 2:1 R/R
            return {"stop_loss": stop, "take_profit": profit}
        else:
            # Stop above Kijun or cloud top
            stop = max(kijun * 1.01, cloud_top * 1.01)
            risk = stop - price
            profit = price - (risk * 2)
            return {"stop_loss": stop, "take_profit": profit}

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
