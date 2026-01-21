"""
Elson Financial AI - Ensemble Model

Combines the proprietary Elson-Finance LLM with existing ML models
for comprehensive trading decisions.

Weights:
- Elson-Finance LLM: 40% (reasoning, context understanding)
- Hybrid ML Models: 35% (pattern recognition, predictions)
- Sentiment Analysis: 25% (market mood)

Copyright (c) 2024 Elson Wealth. All rights reserved.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

from .inference.base_client import BaseInferenceClient, GenerationConfig
from .prompts.trading_prompts import (
    MarketContext,
    MLPrediction,
    SentimentData,
    TechnicalIndicators,
    TradingPromptBuilder,
)

logger = logging.getLogger(__name__)


class TradingAction(Enum):
    """Trading action types."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class TradingDecision:
    """
    Structured trading decision from ElsonFinanceEnsemble.

    Attributes:
        symbol: Stock symbol
        action: Trading action (BUY, SELL, HOLD)
        confidence: Combined confidence score (0-1)
        entry_price: Suggested entry price
        stop_loss: Stop-loss price
        take_profit: Take-profit price
        position_size_pct: Suggested position size (% of portfolio)
        time_horizon: Expected holding period
        reasoning: LLM reasoning explanation
        llm_confidence: LLM-specific confidence
        ml_confidence: ML model confidence
        sentiment_score: Aggregate sentiment score
    """

    symbol: str
    action: TradingAction
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size_pct: float = 5.0
    time_horizon: str = "swing"
    reasoning: str = ""
    llm_confidence: float = 0.5
    ml_confidence: float = 0.5
    sentiment_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "action": self.action.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_pct": self.position_size_pct,
            "time_horizon": self.time_horizon,
            "reasoning": self.reasoning,
            "component_scores": {
                "llm": self.llm_confidence,
                "ml": self.ml_confidence,
                "sentiment": self.sentiment_score,
            },
        }

    @property
    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk/reward ratio if levels are set."""
        if self.entry_price and self.stop_loss and self.take_profit:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.take_profit - self.entry_price)
            if risk > 0:
                return reward / risk
        return None


class ElsonFinanceEnsemble:
    """
    Ensemble combining Elson Financial AI LLM with existing ML models.

    This is the primary interface for generating trading decisions
    using the proprietary Elson-Finance-Trading model.

    Architecture:
        1. Gather market data, technicals, and sentiment
        2. Get ML model prediction (fast)
        3. Query Elson-Finance LLM for reasoning (slower, more nuanced)
        4. Combine signals with weighted voting
        5. Return structured TradingDecision

    Usage:
        ensemble = ElsonFinanceEnsemble(llm_client=client)
        decision = await ensemble.generate_trading_decision(
            symbol="AAPL",
            market_data=df,
            news=headlines
        )
    """

    # Default ensemble weights
    DEFAULT_WEIGHTS = {
        "llm": 0.40,  # Elson-Finance LLM
        "ml": 0.35,  # Hybrid ML models
        "sentiment": 0.25,  # Sentiment analysis
    }

    def __init__(
        self,
        llm_client: BaseInferenceClient,
        hybrid_model: Optional[Any] = None,
        sentiment_analyzer: Optional[Any] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize ElsonFinanceEnsemble.

        Args:
            llm_client: Inference client for Elson-Finance LLM
            hybrid_model: Optional existing hybrid ML model
            sentiment_analyzer: Optional sentiment analysis model
            weights: Optional custom weights for ensemble
        """
        self.llm_client = llm_client
        self.hybrid_model = hybrid_model
        self.sentiment_analyzer = sentiment_analyzer
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

        logger.info(f"ElsonFinanceEnsemble initialized with weights: {self.weights}")

    async def generate_trading_decision(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        news: List[str],
        portfolio_context: Optional[Dict[str, Any]] = None,
        config: Optional[GenerationConfig] = None,
    ) -> TradingDecision:
        """
        Generate a comprehensive trading decision.

        Args:
            symbol: Stock symbol
            market_data: DataFrame with OHLCV and indicator data
            news: Recent news headlines
            portfolio_context: Optional portfolio state
            config: Optional LLM generation config

        Returns:
            TradingDecision with action, confidence, and levels
        """
        # Step 1: Extract market context
        market = self._extract_market_context(symbol, market_data)

        # Step 2: Extract technical indicators
        technicals = self._extract_technicals(market_data)

        # Step 3: Get ML prediction (if model available)
        ml_prediction = await self._get_ml_prediction(symbol, market_data)

        # Step 4: Get sentiment score
        sentiment = await self._get_sentiment(symbol, news)

        # Step 5: Query LLM for reasoning
        llm_response = await self._query_llm(
            market, technicals, sentiment, ml_prediction, portfolio_context, config
        )

        # Step 6: Combine signals
        decision = self._combine_signals(
            symbol, market, llm_response, ml_prediction, sentiment
        )

        logger.info(
            f"Trading decision for {symbol}: {decision.action.value} "
            f"(confidence: {decision.confidence:.2%})"
        )

        return decision

    async def generate_quick_signal(
        self,
        symbol: str,
        price: float,
        rsi: float,
        macd_bullish: bool,
        sentiment_score: float = 0.0,
    ) -> TradingDecision:
        """
        Generate a quick trading signal with minimal data.

        Args:
            symbol: Stock symbol
            price: Current price
            rsi: RSI value
            macd_bullish: Whether MACD is bullish
            sentiment_score: Aggregate sentiment (-1 to 1)

        Returns:
            TradingDecision with action and confidence
        """
        # Build quick prompt
        prompt = TradingPromptBuilder.build_quick_signal_prompt(
            symbol=symbol,
            price=price,
            rsi=rsi,
            macd_bullish=macd_bullish,
            sentiment_score=sentiment_score,
            ml_direction="UP" if macd_bullish else "DOWN",
            ml_confidence=0.6,
        )

        # Query LLM
        response = await self.llm_client.generate(prompt)

        # Parse response
        parsed = TradingPromptBuilder.parse_recommendation(response.text)

        return TradingDecision(
            symbol=symbol,
            action=TradingAction[parsed["action"]],
            confidence=parsed["confidence"],
            entry_price=price,
            stop_loss=price * (1 - parsed.get("stop_loss_pct", 5) / 100),
            reasoning=parsed.get("reasoning", response.text),
            llm_confidence=response.confidence or parsed["confidence"],
        )

    def _extract_market_context(self, symbol: str, df: pd.DataFrame) -> MarketContext:
        """Extract market context from DataFrame."""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        return MarketContext(
            symbol=symbol,
            current_price=float(latest.get("close", latest.get("Close", 0))),
            price_change_pct=(
                float(
                    (latest.get("close", 0) - prev.get("close", 0))
                    / prev.get("close", 1)
                    * 100
                )
                if prev.get("close", 0) > 0
                else 0
            ),
            volume=int(latest.get("volume", latest.get("Volume", 0))),
            avg_volume=int(
                df["volume"].mean()
                if "volume" in df
                else df.get("Volume", pd.Series([0])).mean()
            ),
            sector=latest.get("sector"),
            beta=latest.get("beta"),
        )

    def _extract_technicals(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Extract technical indicators from DataFrame."""
        latest = df.iloc[-1]

        return TechnicalIndicators(
            rsi=float(latest.get("rsi", latest.get("RSI", 50))),
            macd=float(latest.get("macd", latest.get("MACD", 0))),
            macd_signal=float(latest.get("macd_signal", latest.get("MACD_Signal", 0))),
            sma_20=float(
                latest.get("sma_20", latest.get("SMA_20", latest.get("close", 0)))
            ),
            sma_50=float(
                latest.get("sma_50", latest.get("SMA_50", latest.get("close", 0)))
            ),
            sma_200=float(
                latest.get("sma_200", latest.get("SMA_200", latest.get("close", 0)))
            ),
            bollinger_upper=float(
                latest.get("bb_upper", latest.get("close", 0) * 1.02)
            ),
            bollinger_lower=float(
                latest.get("bb_lower", latest.get("close", 0) * 0.98)
            ),
            atr=float(latest.get("atr", latest.get("ATR", 1))),
            support_level=latest.get("support"),
            resistance_level=latest.get("resistance"),
        )

    async def _get_ml_prediction(self, symbol: str, df: pd.DataFrame) -> MLPrediction:
        """Get prediction from existing ML model."""
        if self.hybrid_model is None:
            # Default prediction if no ML model
            return MLPrediction(
                predicted_direction="SIDEWAYS", confidence=0.5, model_name="none"
            )

        try:
            # Call existing hybrid model
            prediction = self.hybrid_model.predict(df)
            return MLPrediction(
                predicted_direction=prediction.get("direction", "SIDEWAYS"),
                confidence=prediction.get("confidence", 0.5),
                predicted_price=prediction.get("price"),
                model_name="hybrid_ml",
            )
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            return MLPrediction(
                predicted_direction="SIDEWAYS", confidence=0.5, model_name="none"
            )

    async def _get_sentiment(self, symbol: str, news: List[str]) -> SentimentData:
        """Get sentiment from news and social data."""
        if self.sentiment_analyzer is None or not news:
            # Default sentiment if no analyzer
            return SentimentData(
                news_sentiment=0.0,
                social_sentiment=0.0,
                analyst_rating="Hold",
                recent_headlines=news[:5] if news else [],
            )

        try:
            # Call existing sentiment analyzer
            result = self.sentiment_analyzer.analyze(news)
            return SentimentData(
                news_sentiment=result.get("news", 0.0),
                social_sentiment=result.get("social", 0.0),
                analyst_rating=result.get("analyst", "Hold"),
                recent_headlines=news[:5],
            )
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return SentimentData(
                news_sentiment=0.0,
                social_sentiment=0.0,
                analyst_rating="Hold",
                recent_headlines=news[:5] if news else [],
            )

    async def _query_llm(
        self,
        market: MarketContext,
        technicals: TechnicalIndicators,
        sentiment: SentimentData,
        ml_prediction: MLPrediction,
        portfolio_context: Optional[Dict[str, Any]],
        config: Optional[GenerationConfig],
    ) -> Dict[str, Any]:
        """Query Elson-Finance LLM for trading analysis."""
        # Build comprehensive prompt
        prompt = TradingPromptBuilder.build_trading_analysis_prompt(
            market=market,
            technicals=technicals,
            sentiment=sentiment,
            ml_prediction=ml_prediction,
            portfolio_context=portfolio_context,
        )

        # Query LLM
        response = await self.llm_client.generate(
            prompt=prompt,
            config=config,
            system_prompt=TradingPromptBuilder.SYSTEM_PROMPT,
        )

        # Parse response
        parsed = TradingPromptBuilder.parse_recommendation(response.text)
        parsed["raw_response"] = response.text
        parsed["llm_confidence"] = response.confidence or parsed["confidence"]
        parsed["latency_ms"] = response.latency_ms

        return parsed

    def _combine_signals(
        self,
        symbol: str,
        market: MarketContext,
        llm_response: Dict[str, Any],
        ml_prediction: MLPrediction,
        sentiment: SentimentData,
    ) -> TradingDecision:
        """Combine signals from all sources using weighted voting."""
        # Convert signals to numeric scores (-1 to 1)
        llm_score = self._action_to_score(llm_response["action"])
        ml_score = self._direction_to_score(ml_prediction.predicted_direction)
        sentiment_score = (sentiment.news_sentiment + sentiment.social_sentiment) / 2

        # Weighted combination
        combined_score = (
            self.weights["llm"] * llm_score
            + self.weights["ml"] * ml_score
            + self.weights["sentiment"] * sentiment_score
        )

        # Convert back to action
        action = self._score_to_action(combined_score)

        # Calculate combined confidence
        combined_confidence = (
            self.weights["llm"] * llm_response["confidence"]
            + self.weights["ml"] * ml_prediction.confidence
            + self.weights["sentiment"] * abs(sentiment_score)
        )

        return TradingDecision(
            symbol=symbol,
            action=action,
            confidence=min(combined_confidence, 1.0),
            entry_price=llm_response.get("entry_price") or market.current_price,
            stop_loss=llm_response.get("stop_loss"),
            take_profit=llm_response.get("take_profit"),
            position_size_pct=llm_response.get("position_size_pct", 5),
            time_horizon=llm_response.get("time_horizon", "swing"),
            reasoning=llm_response.get("raw_response", ""),
            llm_confidence=llm_response["confidence"],
            ml_confidence=ml_prediction.confidence,
            sentiment_score=sentiment_score,
        )

    @staticmethod
    def _action_to_score(action: str) -> float:
        """Convert action to numeric score."""
        scores = {
            "STRONG_BUY": 1.0,
            "BUY": 0.5,
            "HOLD": 0.0,
            "SELL": -0.5,
            "STRONG_SELL": -1.0,
        }
        return scores.get(action.upper(), 0.0)

    @staticmethod
    def _direction_to_score(direction: str) -> float:
        """Convert direction to numeric score."""
        scores = {"UP": 0.5, "SIDEWAYS": 0.0, "DOWN": -0.5}
        return scores.get(direction.upper(), 0.0)

    @staticmethod
    def _score_to_action(score: float) -> TradingAction:
        """Convert numeric score to action."""
        if score > 0.6:
            return TradingAction.STRONG_BUY
        elif score > 0.2:
            return TradingAction.BUY
        elif score > -0.2:
            return TradingAction.HOLD
        elif score > -0.6:
            return TradingAction.SELL
        else:
            return TradingAction.STRONG_SELL
