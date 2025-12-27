"""
Trading Signal Publisher Module

Implements the "Brain" side of the Brain & Body architecture.
Publishes trading signals to Redis for consumption by the TypeScript execution bot.

Architecture:
    Python Engine (Brain) ➝ Analyzes Market ➝ Publishes Signal to Redis
    Redis (Nervous System) ➝ Stores/Broadcasts Signal
    TypeScript Bot (Body) ➝ Receives Signal ➝ Executes Order on Exchange
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# Redis availability
REDIS_AVAILABLE = False
try:
    import redis
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
    logger.info("Redis client available")
except ImportError:
    logger.warning("Redis not available - signals will be logged only")


class SignalAction(Enum):
    """Trading signal actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"


class SignalSource(Enum):
    """Source of the trading signal"""
    LSTM_PREDICTOR = "lstm_predictor"
    CNN_PREDICTOR = "cnn_predictor"
    TRANSFORMER = "transformer"
    SENTIMENT = "sentiment"
    QUANTUM = "quantum"
    RL_AGENT = "rl_agent"
    TECHNICAL = "technical"
    ENSEMBLE = "ensemble"
    GOLDEN_CROSS = "golden_cross"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"


@dataclass
class TradingSignal:
    """
    Trading signal data structure.

    This is the payload that flows from Python (Brain) to TypeScript (Body).
    """
    # Core signal data
    symbol: str
    action: str  # BUY, SELL, HOLD, CLOSE
    price: float
    timestamp: float

    # Signal metadata
    strategy: str
    source: str  # Which model generated this
    confidence: float  # 0.0 to 1.0

    # Optional fields
    quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # Risk management
    risk_score: Optional[float] = None  # 0.0 to 1.0
    position_size_pct: Optional[float] = None  # % of portfolio

    # Additional context
    indicators: Optional[Dict[str, float]] = None
    reasoning: Optional[str] = None

    # Signal ID for tracking
    signal_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingSignal":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class RedisSignalPublisher:
    """
    Publishes trading signals to Redis pub/sub channels.

    This is the "nervous system" connection from the Python Brain.
    """

    # Redis channels
    CHANNEL_SIGNALS = "trade_signals"
    CHANNEL_ALERTS = "trade_alerts"
    CHANNEL_HEARTBEAT = "engine_heartbeat"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        self._sync_client: Optional[redis.Redis] = None
        self._async_client: Optional[aioredis.Redis] = None
        self._connected = False

        # Signal history for deduplication
        self._recent_signals: List[str] = []
        self._max_history = 100

    def connect(self) -> bool:
        """Establish synchronous connection to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available")
            return False

        try:
            self._sync_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            self._sync_client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def connect_async(self) -> bool:
        """Establish async connection to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available")
            return False

        try:
            self._async_client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            await self._async_client.ping()
            self._connected = True
            logger.info(f"Async connected to Redis at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to async connect to Redis: {e}")
            self._connected = False
            return False

    def publish_signal(self, signal: TradingSignal) -> bool:
        """
        Publish a trading signal to Redis (synchronous).

        Args:
            signal: The trading signal to publish

        Returns:
            True if published successfully
        """
        if not self._connected or self._sync_client is None:
            if not self.connect():
                logger.warning(f"Signal not published (no Redis): {signal.to_dict()}")
                return False

        try:
            # Generate signal ID if not present
            if not signal.signal_id:
                signal.signal_id = f"{signal.symbol}_{signal.action}_{int(signal.timestamp * 1000)}"

            # Check for duplicate
            if signal.signal_id in self._recent_signals:
                logger.debug(f"Duplicate signal skipped: {signal.signal_id}")
                return False

            # Publish to channel
            payload = signal.to_json()
            subscribers = self._sync_client.publish(self.CHANNEL_SIGNALS, payload)

            # Store in recent history
            self._recent_signals.append(signal.signal_id)
            if len(self._recent_signals) > self._max_history:
                self._recent_signals.pop(0)

            # Also store in a list for persistence
            self._sync_client.lpush("signal_history", payload)
            self._sync_client.ltrim("signal_history", 0, 999)  # Keep last 1000

            logger.info(f"📡 Signal published to {subscribers} subscriber(s): {signal.action} {signal.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish signal: {e}")
            return False

    async def publish_signal_async(self, signal: TradingSignal) -> bool:
        """
        Publish a trading signal to Redis (async).

        Args:
            signal: The trading signal to publish

        Returns:
            True if published successfully
        """
        if not self._connected or self._async_client is None:
            if not await self.connect_async():
                logger.warning(f"Signal not published (no Redis): {signal.to_dict()}")
                return False

        try:
            if not signal.signal_id:
                signal.signal_id = f"{signal.symbol}_{signal.action}_{int(signal.timestamp * 1000)}"

            if signal.signal_id in self._recent_signals:
                return False

            payload = signal.to_json()
            subscribers = await self._async_client.publish(self.CHANNEL_SIGNALS, payload)

            self._recent_signals.append(signal.signal_id)
            if len(self._recent_signals) > self._max_history:
                self._recent_signals.pop(0)

            await self._async_client.lpush("signal_history", payload)
            await self._async_client.ltrim("signal_history", 0, 999)

            logger.info(f"📡 Signal published to {subscribers} subscriber(s): {signal.action} {signal.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish signal: {e}")
            return False

    def publish_alert(self, alert_type: str, message: str, data: Optional[Dict] = None) -> bool:
        """Publish an alert (not a trading signal)"""
        if not self._connected or self._sync_client is None:
            return False

        try:
            payload = json.dumps({
                "type": alert_type,
                "message": message,
                "data": data or {},
                "timestamp": time.time()
            })
            self._sync_client.publish(self.CHANNEL_ALERTS, payload)
            return True
        except Exception as e:
            logger.error(f"Failed to publish alert: {e}")
            return False

    def send_heartbeat(self) -> bool:
        """Send heartbeat to indicate engine is alive"""
        if not self._connected or self._sync_client is None:
            return False

        try:
            payload = json.dumps({
                "status": "alive",
                "timestamp": time.time(),
                "engine": "python_ml"
            })
            self._sync_client.publish(self.CHANNEL_HEARTBEAT, payload)
            self._sync_client.set("engine_last_heartbeat", payload)
            return True
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    def get_recent_signals(self, count: int = 10) -> List[Dict]:
        """Get recent signals from history"""
        if not self._connected or self._sync_client is None:
            return []

        try:
            signals = self._sync_client.lrange("signal_history", 0, count - 1)
            return [json.loads(s) for s in signals]
        except Exception as e:
            logger.error(f"Failed to get recent signals: {e}")
            return []

    def close(self):
        """Close Redis connections"""
        if self._sync_client:
            self._sync_client.close()
        self._connected = False


class StrategySignalGenerator:
    """
    Generates trading signals from various strategies and ML models.

    Integrates with the ML module to generate signals from:
    - LSTM/CNN price predictions
    - Sentiment analysis
    - Quantum classifiers
    - RL agents
    - Technical indicators
    """

    def __init__(self, publisher: Optional[RedisSignalPublisher] = None):
        self.publisher = publisher or RedisSignalPublisher()

        # Import ML components
        try:
            from app.ml import get_ml_config, get_sentiment_analyzer
            self.ml_config = get_ml_config()
            self._sentiment_analyzer = None
        except ImportError:
            self.ml_config = None
            self._sentiment_analyzer = None

    def generate_signal_from_prediction(
        self,
        symbol: str,
        current_price: float,
        predicted_price: float,
        confidence: float,
        source: str = "ml_predictor"
    ) -> Optional[TradingSignal]:
        """
        Generate a signal from a price prediction.

        Args:
            symbol: Trading symbol
            current_price: Current market price
            predicted_price: Predicted price
            confidence: Model confidence (0-1)
            source: Source model name

        Returns:
            TradingSignal if action warranted, None otherwise
        """
        # Calculate expected change
        change_pct = (predicted_price - current_price) / current_price

        # Thresholds for action
        BUY_THRESHOLD = 0.02  # 2% expected gain
        SELL_THRESHOLD = -0.02  # 2% expected loss
        MIN_CONFIDENCE = 0.6

        if confidence < MIN_CONFIDENCE:
            return None

        if change_pct >= BUY_THRESHOLD:
            action = SignalAction.BUY.value
            # Set targets based on prediction
            stop_loss = current_price * 0.98  # 2% stop
            take_profit = predicted_price
        elif change_pct <= SELL_THRESHOLD:
            action = SignalAction.SELL.value
            stop_loss = current_price * 1.02
            take_profit = predicted_price
        else:
            return None  # No clear signal

        signal = TradingSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            timestamp=time.time(),
            strategy="ML_Price_Prediction",
            source=source,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit,
            indicators={
                "predicted_price": predicted_price,
                "expected_change_pct": change_pct
            },
            reasoning=f"Expected {change_pct*100:.2f}% move with {confidence*100:.1f}% confidence"
        )

        return signal

    def generate_signal_from_sentiment(
        self,
        symbol: str,
        current_price: float,
        sentiment_score: float,
        confidence: float,
        headlines: Optional[List[str]] = None
    ) -> Optional[TradingSignal]:
        """
        Generate a signal from sentiment analysis.

        Args:
            symbol: Trading symbol
            current_price: Current market price
            sentiment_score: Sentiment score (-1 to 1)
            confidence: Analysis confidence
            headlines: Source headlines
        """
        # Sentiment thresholds
        BULLISH_THRESHOLD = 0.5
        BEARISH_THRESHOLD = -0.5
        MIN_CONFIDENCE = 0.7

        if confidence < MIN_CONFIDENCE:
            return None

        if sentiment_score >= BULLISH_THRESHOLD:
            action = SignalAction.BUY.value
        elif sentiment_score <= BEARISH_THRESHOLD:
            action = SignalAction.SELL.value
        else:
            return None

        signal = TradingSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            timestamp=time.time(),
            strategy="Sentiment_Analysis",
            source=SignalSource.SENTIMENT.value,
            confidence=confidence,
            indicators={
                "sentiment_score": sentiment_score,
                "headline_count": len(headlines) if headlines else 0
            },
            reasoning=f"Sentiment score: {sentiment_score:.2f}"
        )

        return signal

    def generate_golden_cross_signal(
        self,
        symbol: str,
        prices: List[float],
        current_price: float
    ) -> Optional[TradingSignal]:
        """
        Generate signal from Golden Cross (SMA 50/200 crossover).

        Args:
            symbol: Trading symbol
            prices: Historical close prices (need 200+)
            current_price: Current price
        """
        if len(prices) < 201:
            return None

        prices_arr = np.array(prices)

        # Calculate SMAs
        sma_50 = np.mean(prices_arr[-50:])
        sma_200 = np.mean(prices_arr[-200:])
        prev_sma_50 = np.mean(prices_arr[-51:-1])
        prev_sma_200 = np.mean(prices_arr[-201:-1])

        action = None

        # Golden Cross (bullish)
        if prev_sma_50 <= prev_sma_200 and sma_50 > sma_200:
            action = SignalAction.BUY.value
        # Death Cross (bearish)
        elif prev_sma_50 >= prev_sma_200 and sma_50 < sma_200:
            action = SignalAction.SELL.value

        if action is None:
            return None

        signal = TradingSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            timestamp=time.time(),
            strategy="Golden_Cross",
            source=SignalSource.GOLDEN_CROSS.value,
            confidence=0.75,  # Technical signals have moderate confidence
            indicators={
                "sma_50": sma_50,
                "sma_200": sma_200
            },
            reasoning="Golden Cross" if action == "BUY" else "Death Cross"
        )

        return signal

    def generate_rsi_signal(
        self,
        symbol: str,
        prices: List[float],
        current_price: float,
        period: int = 14
    ) -> Optional[TradingSignal]:
        """
        Generate signal from RSI indicator.
        """
        if len(prices) < period + 1:
            return None

        # Calculate RSI
        prices_arr = np.array(prices)
        deltas = np.diff(prices_arr)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        action = None

        if rsi < 30:  # Oversold
            action = SignalAction.BUY.value
        elif rsi > 70:  # Overbought
            action = SignalAction.SELL.value

        if action is None:
            return None

        # Confidence based on how extreme the RSI is
        confidence = min(abs(rsi - 50) / 50, 1.0)

        signal = TradingSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            timestamp=time.time(),
            strategy="RSI_Reversal",
            source=SignalSource.RSI.value,
            confidence=confidence,
            indicators={"rsi": rsi},
            reasoning=f"RSI: {rsi:.1f} ({'Oversold' if rsi < 30 else 'Overbought'})"
        )

        return signal

    def generate_ensemble_signal(
        self,
        symbol: str,
        current_price: float,
        signals: List[TradingSignal]
    ) -> Optional[TradingSignal]:
        """
        Generate a consensus signal from multiple signals.

        Args:
            symbol: Trading symbol
            current_price: Current price
            signals: List of signals from different strategies
        """
        if not signals:
            return None

        # Count votes
        buy_votes = 0
        sell_votes = 0
        total_confidence = 0

        for sig in signals:
            weight = sig.confidence
            if sig.action == SignalAction.BUY.value:
                buy_votes += weight
            elif sig.action == SignalAction.SELL.value:
                sell_votes += weight
            total_confidence += sig.confidence

        avg_confidence = total_confidence / len(signals)

        # Determine consensus
        if buy_votes > sell_votes and buy_votes > 0.5:
            action = SignalAction.BUY.value
            consensus_strength = buy_votes / (buy_votes + sell_votes)
        elif sell_votes > buy_votes and sell_votes > 0.5:
            action = SignalAction.SELL.value
            consensus_strength = sell_votes / (buy_votes + sell_votes)
        else:
            return None  # No consensus

        signal = TradingSignal(
            symbol=symbol,
            action=action,
            price=current_price,
            timestamp=time.time(),
            strategy="Ensemble_Consensus",
            source=SignalSource.ENSEMBLE.value,
            confidence=consensus_strength * avg_confidence,
            indicators={
                "buy_votes": buy_votes,
                "sell_votes": sell_votes,
                "signal_count": len(signals)
            },
            reasoning=f"Consensus from {len(signals)} signals"
        )

        return signal


# Convenience functions
def get_signal_publisher(
    host: str = "localhost",
    port: int = 6379
) -> RedisSignalPublisher:
    """Get a signal publisher instance"""
    return RedisSignalPublisher(host=host, port=port)


def get_signal_generator(
    publisher: Optional[RedisSignalPublisher] = None
) -> StrategySignalGenerator:
    """Get a signal generator instance"""
    return StrategySignalGenerator(publisher=publisher)
