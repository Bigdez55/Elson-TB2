"""
Base Advisor Service
Provides base functionality for financial advisory services
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Types of recommendations"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REDUCE = "reduce"
    INCREASE = "increase"


class RiskLevel(str, Enum):
    """Risk levels for recommendations"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Recommendation(BaseModel):
    """
    Recommendation model for investment advice
    """

    symbol: str
    recommendation_type: RecommendationType
    confidence: float  # 0.0 to 1.0
    risk_level: RiskLevel
    target_allocation: Optional[float] = None
    reasoning: str
    expected_return: Optional[float] = None
    expected_risk: Optional[float] = None
    time_horizon: Optional[str] = None  # "short", "medium", "long"
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class AdvisorService(ABC):
    """
    Abstract base class for advisor services
    """

    def __init__(self, db: Session, name: str):
        self.db = db
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def generate_recommendation(self, user_id: int, symbol: str, context: Dict[str, Any]) -> Recommendation:
        """
        Generate a recommendation for a specific symbol

        Args:
            user_id: User ID
            symbol: Stock symbol
            context: Additional context for recommendation

        Returns:
            Recommendation object
        """
        pass

    @abstractmethod
    async def generate_portfolio_recommendations(
        self, user_id: int, portfolio_symbols: List[str], context: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate recommendations for an entire portfolio

        Args:
            user_id: User ID
            portfolio_symbols: List of symbols in portfolio
            context: Additional context for recommendations

        Returns:
            List of Recommendation objects
        """
        pass

    async def get_recommendation_history(
        self, user_id: int, symbol: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recommendation history for a user

        Args:
            user_id: User ID
            symbol: Optional symbol filter
            limit: Maximum number of recommendations to return

        Returns:
            List of historical recommendations
        """
        # This would typically query a database table
        # For now, return empty list as placeholder
        return []

    def _calculate_confidence_score(self, signals: Dict[str, float], weights: Dict[str, float]) -> float:
        """
        Calculate confidence score based on weighted signals

        Args:
            signals: Dictionary of signal names and values
            weights: Dictionary of signal names and weights

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not signals or not weights:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for signal_name, signal_value in signals.items():
            if signal_name in weights:
                weight = weights[signal_name]
                weighted_sum += abs(signal_value) * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return min(weighted_sum / total_weight, 1.0)

    def _determine_risk_level(self, volatility: float, market_conditions: Dict[str, Any]) -> RiskLevel:
        """
        Determine risk level based on volatility and market conditions

        Args:
            volatility: Asset volatility
            market_conditions: Current market conditions

        Returns:
            RiskLevel enum value
        """
        # Simple risk level determination
        if volatility > 0.4:
            return RiskLevel.VERY_HIGH
        elif volatility > 0.25:
            return RiskLevel.HIGH
        elif volatility > 0.15:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


class BasicAdvisorService(AdvisorService):
    """
    Basic implementation of advisor service for AI Portfolio Manager
    """

    def __init__(self, db: Session):
        super().__init__(db, "BasicAdvisor")

    async def generate_recommendation(self, user_id: int, symbol: str, context: Dict[str, Any]) -> Recommendation:
        """
        Generate a basic recommendation for a symbol
        """
        try:
            # Get relevant data from context
            # Note: current_price extracted for future use in price-based recommendations
            _current_price = context.get("current_price", 0.0)  # noqa: F841
            volatility = context.get("volatility", 0.2)
            market_trend = context.get("market_trend", 0.0)
            technical_signals = context.get("technical_signals", {})

            # Simple recommendation logic
            recommendation_type = RecommendationType.HOLD
            confidence = 0.5
            reasoning = "Default hold recommendation"

            # Analyze signals
            if technical_signals:
                bullish_signals = sum(1 for v in technical_signals.values() if v > 0)
                bearish_signals = sum(1 for v in technical_signals.values() if v < 0)
                total_signals = len(technical_signals)

                if total_signals > 0:
                    bullish_ratio = bullish_signals / total_signals

                    if bullish_ratio > 0.7:
                        recommendation_type = RecommendationType.BUY
                        confidence = bullish_ratio
                        reasoning = f"Strong bullish signals ({bullish_signals}/{total_signals})"
                    elif bullish_ratio < 0.3:
                        recommendation_type = RecommendationType.SELL
                        confidence = 1 - bullish_ratio
                        reasoning = f"Strong bearish signals ({bearish_signals}/{total_signals})"
                    else:
                        reasoning = f"Mixed signals ({bullish_signals} bullish, {bearish_signals} bearish)"

            # Adjust based on market trend
            if market_trend > 0.1 and recommendation_type == RecommendationType.HOLD:
                recommendation_type = RecommendationType.BUY
                confidence = min(confidence + 0.1, 1.0)
                reasoning += " with positive market trend"
            elif market_trend < -0.1 and recommendation_type == RecommendationType.HOLD:
                recommendation_type = RecommendationType.SELL
                confidence = min(confidence + 0.1, 1.0)
                reasoning += " with negative market trend"

            # Determine risk level
            risk_level = self._determine_risk_level(volatility, context)

            return Recommendation(
                symbol=symbol,
                recommendation_type=recommendation_type,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=reasoning,
                expected_return=market_trend * 12 if market_trend > 0 else None,  # Annualized
                expected_risk=volatility,
                time_horizon="medium",
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"Error generating recommendation for {symbol}: {str(e)}")
            return Recommendation(
                symbol=symbol,
                recommendation_type=RecommendationType.HOLD,
                confidence=0.0,
                risk_level=RiskLevel.MEDIUM,
                reasoning=f"Error in analysis: {str(e)}",
                created_at=datetime.utcnow(),
            )

    async def generate_portfolio_recommendations(
        self, user_id: int, portfolio_symbols: List[str], context: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate recommendations for all symbols in portfolio
        """
        recommendations = []

        for symbol in portfolio_symbols:
            # Create symbol-specific context
            symbol_context = context.copy()
            symbol_context.update(context.get(symbol, {}))

            recommendation = await self.generate_recommendation(user_id, symbol, symbol_context)
            recommendations.append(recommendation)

        return recommendations


class QuantitativeAdvisorService(AdvisorService):
    """
    Quantitative advisor service using advanced analytics
    """

    def __init__(self, db: Session):
        super().__init__(db, "QuantitativeAdvisor")

    async def generate_recommendation(self, user_id: int, symbol: str, context: Dict[str, Any]) -> Recommendation:
        """
        Generate quantitative-based recommendation
        """
        try:
            # Get quantitative metrics from context
            sharpe_ratio = context.get("sharpe_ratio", 0.0)
            sortino_ratio = context.get("sortino_ratio", 0.0)
            max_drawdown = context.get("max_drawdown", 0.0)
            beta = context.get("beta", 1.0)
            alpha = context.get("alpha", 0.0)

            # Calculate score based on quantitative metrics
            score = 0.0
            score += min(sharpe_ratio / 2.0, 1.0) * 0.3  # Sharpe ratio weight
            score += min(sortino_ratio / 2.0, 1.0) * 0.2  # Sortino ratio weight
            score += max(1 + max_drawdown, 0.0) * 0.2  # Max drawdown (negative impact)
            score += (alpha > 0) * 0.2  # Alpha positive weight
            score += (beta < 1.5) * 0.1  # Beta not too high weight

            # Determine recommendation based on score
            if score > 0.7:
                recommendation_type = RecommendationType.BUY
                confidence = score
                reasoning = f"Strong quantitative metrics (score: {score:.2f})"
            elif score < 0.3:
                recommendation_type = RecommendationType.SELL
                confidence = 1 - score
                reasoning = f"Weak quantitative metrics (score: {score:.2f})"
            else:
                recommendation_type = RecommendationType.HOLD
                confidence = 0.5
                reasoning = f"Neutral quantitative metrics (score: {score:.2f})"

            volatility = context.get("volatility", 0.2)
            risk_level = self._determine_risk_level(volatility, context)

            return Recommendation(
                symbol=symbol,
                recommendation_type=recommendation_type,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=reasoning,
                expected_return=alpha,
                expected_risk=volatility,
                time_horizon="long",
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"Error in quantitative analysis for {symbol}: {str(e)}")
            return Recommendation(
                symbol=symbol,
                recommendation_type=RecommendationType.HOLD,
                confidence=0.0,
                risk_level=RiskLevel.MEDIUM,
                reasoning=f"Error in quantitative analysis: {str(e)}",
                created_at=datetime.utcnow(),
            )
