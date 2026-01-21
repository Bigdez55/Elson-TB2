"""
Elson Financial AI - Trading Prompt Templates

Structured prompts for autonomous trading decisions.
Designed to elicit chain-of-thought reasoning from the merged model.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MarketContext:
    """Market context data for prompt building."""

    symbol: str
    current_price: float
    price_change_pct: float
    volume: int
    avg_volume: int
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    beta: Optional[float] = None


@dataclass
class TechnicalIndicators:
    """Technical indicators for prompt building."""

    rsi: float
    macd: float
    macd_signal: float
    sma_20: float
    sma_50: float
    sma_200: float
    bollinger_upper: float
    bollinger_lower: float
    atr: float
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None


@dataclass
class SentimentData:
    """Sentiment data for prompt building."""

    news_sentiment: float  # -1 to 1
    social_sentiment: float  # -1 to 1
    analyst_rating: str  # Strong Buy, Buy, Hold, Sell, Strong Sell
    recent_headlines: List[str]


@dataclass
class MLPrediction:
    """ML model prediction for prompt building."""

    predicted_direction: str  # UP, DOWN, SIDEWAYS
    confidence: float  # 0-1
    predicted_price: Optional[float] = None
    model_name: str = "hybrid_ml"


class TradingPromptBuilder:
    """
    Builds structured prompts for Elson Financial AI trading decisions.

    The prompts are designed to:
    1. Provide all relevant market context
    2. Include technical and sentiment signals
    3. Reference ML model predictions
    4. Request structured output with confidence levels
    """

    SYSTEM_PROMPT = """You are Elson-Finance-Trading, a proprietary AI model created by
Elson Wealth for autonomous trading decisions. You analyze market data, sentiment,
and technical indicators to generate high-confidence trading signals.

Your analysis must include:
1. MARKET CONTEXT: Current conditions and trend assessment
2. TECHNICAL ANALYSIS: Key indicator interpretations
3. SENTIMENT ANALYSIS: News and social sentiment impact
4. ML MODEL AGREEMENT: Correlation with ML predictions
5. RISK ASSESSMENT: Key risks and mitigation
6. RECOMMENDATION: Clear action with confidence percentage

Output format for recommendations:
- ACTION: BUY | SELL | HOLD
- CONFIDENCE: 0-100%
- ENTRY_PRICE: Suggested entry (if applicable)
- STOP_LOSS: Risk management level
- TAKE_PROFIT: Target exit level
- POSITION_SIZE: Percentage of portfolio (1-10%)
- TIME_HORIZON: Day trade | Swing (2-10 days) | Position (weeks-months)

Always explain your reasoning before providing the recommendation."""

    @classmethod
    def build_trading_analysis_prompt(
        cls,
        market: MarketContext,
        technicals: TechnicalIndicators,
        sentiment: SentimentData,
        ml_prediction: MLPrediction,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a comprehensive trading analysis prompt.

        Args:
            market: Current market context
            technicals: Technical indicators
            sentiment: Sentiment analysis data
            ml_prediction: ML model prediction
            portfolio_context: Optional portfolio state

        Returns:
            Formatted prompt string
        """
        prompt = f"""## TRADING ANALYSIS REQUEST: {market.symbol}

### MARKET DATA
- Symbol: {market.symbol}
- Current Price: ${market.current_price:.2f}
- Price Change: {market.price_change_pct:+.2f}%
- Volume: {market.volume:,} (Avg: {market.avg_volume:,})
- Volume Ratio: {market.volume / market.avg_volume:.2f}x
{f'- Market Cap: ${market.market_cap:,.0f}' if market.market_cap else ''}
{f'- Sector: {market.sector}' if market.sector else ''}
{f'- Beta: {market.beta:.2f}' if market.beta else ''}

### TECHNICAL INDICATORS
- RSI (14): {technicals.rsi:.1f} {'(Oversold)' if technicals.rsi < 30 else '(Overbought)' if technicals.rsi > 70 else '(Neutral)'}
- MACD: {technicals.macd:.4f} | Signal: {technicals.macd_signal:.4f} | {'Bullish' if technicals.macd > technicals.macd_signal else 'Bearish'}
- SMA 20/50/200: ${technicals.sma_20:.2f} / ${technicals.sma_50:.2f} / ${technicals.sma_200:.2f}
- Price vs SMAs: {'Above all' if market.current_price > technicals.sma_200 else 'Below 200 SMA'}
- Bollinger Bands: ${technicals.bollinger_lower:.2f} - ${technicals.bollinger_upper:.2f}
- ATR: ${technicals.atr:.2f} ({technicals.atr/market.current_price*100:.1f}% volatility)
{f'- Support: ${technicals.support_level:.2f}' if technicals.support_level else ''}
{f'- Resistance: ${technicals.resistance_level:.2f}' if technicals.resistance_level else ''}

### SENTIMENT ANALYSIS
- News Sentiment: {cls._sentiment_label(sentiment.news_sentiment)} ({sentiment.news_sentiment:+.2f})
- Social Sentiment: {cls._sentiment_label(sentiment.social_sentiment)} ({sentiment.social_sentiment:+.2f})
- Analyst Rating: {sentiment.analyst_rating}
- Recent Headlines:
{chr(10).join(f'  - {h}' for h in sentiment.recent_headlines[:5])}

### ML MODEL PREDICTION
- Model: {ml_prediction.model_name}
- Predicted Direction: {ml_prediction.predicted_direction}
- Model Confidence: {ml_prediction.confidence*100:.1f}%
{f'- Predicted Price: ${ml_prediction.predicted_price:.2f}' if ml_prediction.predicted_price else ''}

"""
        if portfolio_context:
            prompt += f"""### PORTFOLIO CONTEXT
- Current Position: {portfolio_context.get('current_position', 'None')}
- Portfolio Value: ${portfolio_context.get('portfolio_value', 0):,.2f}
- Available Cash: ${portfolio_context.get('available_cash', 0):,.2f}
- Risk Tolerance: {portfolio_context.get('risk_tolerance', 'Moderate')}
- Max Position Size: {portfolio_context.get('max_position_pct', 10)}%
"""

        prompt += """
### ANALYSIS REQUEST
Based on the above data, provide a comprehensive trading analysis and recommendation.
Consider the alignment between technical signals, sentiment, and ML predictions.
Assess risk/reward and provide specific entry/exit levels if recommending a trade.

Provide your analysis and recommendation:"""

        return prompt

    @classmethod
    def build_quick_signal_prompt(
        cls,
        symbol: str,
        price: float,
        rsi: float,
        macd_bullish: bool,
        sentiment_score: float,
        ml_direction: str,
        ml_confidence: float,
    ) -> str:
        """
        Build a quick signal prompt for fast decisions.

        Args:
            symbol: Stock symbol
            price: Current price
            rsi: RSI value
            macd_bullish: Whether MACD is bullish
            sentiment_score: Aggregate sentiment (-1 to 1)
            ml_direction: ML prediction direction
            ml_confidence: ML confidence (0-1)

        Returns:
            Concise prompt for quick analysis
        """
        return f"""## QUICK SIGNAL: {symbol}

Price: ${price:.2f} | RSI: {rsi:.0f} | MACD: {'Bullish' if macd_bullish else 'Bearish'}
Sentiment: {cls._sentiment_label(sentiment_score)} | ML: {ml_direction} ({ml_confidence*100:.0f}%)

Provide a brief trading signal:
- ACTION: BUY | SELL | HOLD
- CONFIDENCE: 0-100%
- STOP_LOSS_PCT: Percentage below entry for stop
- REASONING: One sentence explanation"""

    @classmethod
    def build_risk_assessment_prompt(
        cls,
        symbol: str,
        position_size: float,
        entry_price: float,
        current_price: float,
        portfolio_value: float,
        existing_positions: List[Dict[str, Any]],
    ) -> str:
        """
        Build a risk assessment prompt for position sizing.

        Args:
            symbol: Stock symbol
            position_size: Proposed position size in dollars
            entry_price: Proposed entry price
            current_price: Current market price
            portfolio_value: Total portfolio value
            existing_positions: List of existing positions

        Returns:
            Prompt for risk assessment
        """
        position_pct = (position_size / portfolio_value) * 100

        positions_str = "\n".join(
            [
                f"  - {p['symbol']}: ${p['value']:,.2f} ({p['weight']*100:.1f}%)"
                for p in existing_positions[:10]
            ]
        )

        return f"""## RISK ASSESSMENT: {symbol} Position

### PROPOSED TRADE
- Symbol: {symbol}
- Position Size: ${position_size:,.2f} ({position_pct:.1f}% of portfolio)
- Entry Price: ${entry_price:.2f}
- Current Price: ${current_price:.2f}
- Slippage Risk: {abs(current_price - entry_price) / entry_price * 100:.2f}%

### PORTFOLIO STATE
- Total Value: ${portfolio_value:,.2f}
- Existing Positions:
{positions_str}

### ASSESSMENT REQUEST
Evaluate this position from a risk management perspective:
1. Is the position size appropriate given portfolio value?
2. Does this create concentration risk?
3. What correlations exist with current holdings?
4. Recommended adjustments to position size?
5. Suggested stop-loss level based on risk tolerance?

Provide your risk assessment:"""

    @staticmethod
    def _sentiment_label(score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.3:
            return "Bullish"
        elif score > 0.1:
            return "Slightly Bullish"
        elif score < -0.3:
            return "Bearish"
        elif score < -0.1:
            return "Slightly Bearish"
        return "Neutral"

    @classmethod
    def parse_recommendation(cls, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured recommendation.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed recommendation dictionary
        """
        import re

        result = {
            "action": "HOLD",
            "confidence": 0.5,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "position_size_pct": 5,
            "time_horizon": "swing",
            "reasoning": response_text,
        }

        # Extract action
        action_match = re.search(r"ACTION[:\s]*(BUY|SELL|HOLD)", response_text, re.I)
        if action_match:
            result["action"] = action_match.group(1).upper()

        # Extract confidence
        conf_match = re.search(
            r"CONFIDENCE[:\s]*(\d+(?:\.\d+)?)\s*%?", response_text, re.I
        )
        if conf_match:
            result["confidence"] = float(conf_match.group(1)) / 100

        # Extract prices
        entry_match = re.search(
            r"ENTRY[_\s]*PRICE[:\s]*\$?(\d+(?:\.\d+)?)", response_text, re.I
        )
        if entry_match:
            result["entry_price"] = float(entry_match.group(1))

        stop_match = re.search(
            r"STOP[_\s]*LOSS[:\s]*\$?(\d+(?:\.\d+)?)", response_text, re.I
        )
        if stop_match:
            result["stop_loss"] = float(stop_match.group(1))

        tp_match = re.search(
            r"TAKE[_\s]*PROFIT[:\s]*\$?(\d+(?:\.\d+)?)", response_text, re.I
        )
        if tp_match:
            result["take_profit"] = float(tp_match.group(1))

        # Extract position size
        size_match = re.search(
            r"POSITION[_\s]*SIZE[:\s]*(\d+(?:\.\d+)?)\s*%?", response_text, re.I
        )
        if size_match:
            result["position_size_pct"] = float(size_match.group(1))

        # Extract time horizon
        if "day trade" in response_text.lower():
            result["time_horizon"] = "day"
        elif (
            "position" in response_text.lower() or "long term" in response_text.lower()
        ):
            result["time_horizon"] = "position"
        else:
            result["time_horizon"] = "swing"

        return result
