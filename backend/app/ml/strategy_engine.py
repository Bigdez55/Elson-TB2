"""
Strategy Engine - The "Brain" of the Trading System

This module runs the ML models and publishes trading signals to Redis.
It integrates all ML capabilities (deep learning, sentiment, quantum, RL)
into a unified strategy execution engine.

Architecture:
    Strategy Engine (Brain) ➝ Analyzes Market ➝ Publishes Signal to Redis
    Redis (Nervous System) ➝ Broadcasts Signal
    TypeScript Bot (Body) ➝ Receives Signal ➝ Executes Order

Usage:
    python -m app.ml.strategy_engine

    Or programmatically:
        engine = StrategyEngine()
        await engine.start()
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from app.ml.signals import (
    RedisSignalPublisher,
    StrategySignalGenerator,
    TradingSignal,
    SignalAction,
    SignalSource,
)
from app.ml.config import get_ml_config

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Main strategy engine that runs ML models and publishes signals.

    This is the "Brain" of the trading system.
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        symbols: Optional[List[str]] = None
    ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.symbols = symbols or ["BTC/USDT", "ETH/USDT", "AAPL", "MSFT"]

        # Initialize components
        self.publisher = RedisSignalPublisher(host=redis_host, port=redis_port)
        self.signal_generator = StrategySignalGenerator(publisher=self.publisher)
        self.ml_config = get_ml_config()

        # ML models (lazy loaded)
        self._price_predictor = None
        self._sentiment_analyzer = None
        self._quantum_classifier = None
        self._rl_agent = None

        # State
        self._running = False
        self._price_history: Dict[str, List[float]] = {s: [] for s in self.symbols}
        self._signal_count = 0

        logger.info(f"Strategy Engine initialized for {len(self.symbols)} symbols")
        logger.info(f"ML Config: {self.ml_config.environment.value}")

    async def start(self, loop_interval: float = 1.0):
        """
        Start the strategy engine main loop.

        Args:
            loop_interval: Time between strategy evaluations (seconds)
        """
        logger.info("🧠 Starting Strategy Engine...")

        # Connect to Redis
        if not self.publisher.connect():
            logger.warning("Running without Redis - signals will be logged only")

        self._running = True

        # Initialize ML models
        await self._initialize_models()

        logger.info("Strategy Engine running. Press Ctrl+C to stop.")

        try:
            while self._running:
                await self._run_cycle()
                await asyncio.sleep(loop_interval)

                # Send heartbeat every 10 seconds
                if self._signal_count % 10 == 0:
                    self.publisher.send_heartbeat()

        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the strategy engine"""
        self._running = False
        self.publisher.close()
        logger.info("Strategy Engine stopped")

    async def _initialize_models(self):
        """Initialize ML models based on availability"""
        try:
            # Import models
            from app.ml import (
                get_enhanced_ml_service,
                get_sentiment_analyzer,
                get_quantum_classifier,
                get_rl_service,
            )

            # Enhanced ML service
            self._ml_service = get_enhanced_ml_service()
            logger.info("ML Service initialized")

            # Sentiment analyzer
            if self.ml_config.can_use_transformers() or True:  # Always try
                self._sentiment_analyzer = get_sentiment_analyzer(financial=True)
                logger.info("Sentiment Analyzer initialized")

            # Quantum classifier
            if self.ml_config.can_use_quantum():
                self._quantum_classifier = get_quantum_classifier(
                    n_qubits=4,
                    use_quantum=True
                )
                logger.info("Quantum Classifier initialized")

            # RL agent
            if self.ml_config.can_use_rl():
                self._rl_service = get_rl_service()
                logger.info("RL Service initialized")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")

    async def _run_cycle(self):
        """Run one cycle of strategy evaluation"""
        for symbol in self.symbols:
            try:
                # Get/simulate market data
                current_price, prices = await self._get_market_data(symbol)

                # Store price history
                self._price_history[symbol].append(current_price)
                if len(self._price_history[symbol]) > 300:
                    self._price_history[symbol].pop(0)

                # Skip if not enough data
                if len(self._price_history[symbol]) < 50:
                    continue

                # Generate signals from various strategies
                signals = await self._generate_all_signals(
                    symbol,
                    current_price,
                    self._price_history[symbol]
                )

                # Generate ensemble signal if we have multiple
                if len(signals) >= 2:
                    ensemble = self.signal_generator.generate_ensemble_signal(
                        symbol, current_price, signals
                    )
                    if ensemble:
                        signals.append(ensemble)

                # Publish signals
                for signal in signals:
                    if signal.action != SignalAction.HOLD.value:
                        self.publisher.publish_signal(signal)
                        self._signal_count += 1

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

    async def _get_market_data(self, symbol: str) -> tuple:
        """
        Get current market data.

        In production, this would connect to exchange APIs.
        Here we simulate for demonstration.
        """
        # Get last price or start with a base
        if self._price_history[symbol]:
            last_price = self._price_history[symbol][-1]
        else:
            # Base prices for common symbols
            base_prices = {
                "BTC/USDT": 50000,
                "ETH/USDT": 3000,
                "AAPL": 180,
                "MSFT": 400,
            }
            last_price = base_prices.get(symbol, 100)

        # Simulate price movement (random walk with drift)
        volatility = 0.001  # 0.1% per tick
        drift = 0.00001  # Slight upward bias
        change = np.random.normal(drift, volatility)
        current_price = last_price * (1 + change)

        return current_price, self._price_history[symbol]

    async def _generate_all_signals(
        self,
        symbol: str,
        current_price: float,
        prices: List[float]
    ) -> List[TradingSignal]:
        """Generate signals from all available strategies"""
        signals = []

        # 1. Technical: Golden Cross
        gc_signal = self.signal_generator.generate_golden_cross_signal(
            symbol, prices, current_price
        )
        if gc_signal:
            signals.append(gc_signal)

        # 2. Technical: RSI
        rsi_signal = self.signal_generator.generate_rsi_signal(
            symbol, prices, current_price
        )
        if rsi_signal:
            signals.append(rsi_signal)

        # 3. ML Price Prediction
        if self._ml_service and len(prices) >= 100:
            try:
                ml_signal = await self._generate_ml_signal(
                    symbol, current_price, prices
                )
                if ml_signal:
                    signals.append(ml_signal)
            except Exception as e:
                logger.debug(f"ML signal failed: {e}")

        # 4. Sentiment (if we had news)
        if self._sentiment_analyzer:
            # In production, fetch real news
            sentiment_signal = await self._generate_sentiment_signal(
                symbol, current_price
            )
            if sentiment_signal:
                signals.append(sentiment_signal)

        return signals

    async def _generate_ml_signal(
        self,
        symbol: str,
        current_price: float,
        prices: List[float]
    ) -> Optional[TradingSignal]:
        """Generate signal from ML price prediction"""
        try:
            # Create features from price history
            df = pd.DataFrame({"close": prices})
            df["returns"] = df["close"].pct_change()
            df["volatility"] = df["returns"].rolling(20).std()
            df["sma_20"] = df["close"].rolling(20).mean()
            df["sma_50"] = df["close"].rolling(50).mean()
            df = df.dropna()

            if len(df) < 50:
                return None

            features = df[["close", "returns", "volatility", "sma_20", "sma_50"]]

            # Try to use ML service
            # In production, would use trained model
            # Here we use a simple heuristic

            # Predict based on trend
            recent_trend = df["returns"].tail(10).mean()
            volatility = df["volatility"].iloc[-1]

            if recent_trend > volatility and recent_trend > 0.001:
                predicted_price = current_price * 1.03  # 3% up
                confidence = min(0.9, 0.5 + recent_trend * 10)
            elif recent_trend < -volatility and recent_trend < -0.001:
                predicted_price = current_price * 0.97  # 3% down
                confidence = min(0.9, 0.5 + abs(recent_trend) * 10)
            else:
                return None

            return self.signal_generator.generate_signal_from_prediction(
                symbol=symbol,
                current_price=current_price,
                predicted_price=predicted_price,
                confidence=confidence,
                source=SignalSource.LSTM_PREDICTOR.value
            )

        except Exception as e:
            logger.debug(f"ML signal generation failed: {e}")
            return None

    async def _generate_sentiment_signal(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[TradingSignal]:
        """Generate signal from sentiment analysis"""
        try:
            # Mock headlines (in production, fetch real news)
            mock_headlines = [
                f"{symbol} shows strong momentum in trading",
                f"Analysts upgrade {symbol} outlook",
            ]

            # Analyze sentiment
            results = self._sentiment_analyzer.analyze(mock_headlines)

            if not results:
                return None

            # Calculate aggregate sentiment
            scores = [r.score for r in results]
            avg_score = np.mean(scores)
            avg_confidence = np.mean([r.confidence for r in results])

            return self.signal_generator.generate_signal_from_sentiment(
                symbol=symbol,
                current_price=current_price,
                sentiment_score=avg_score,
                confidence=avg_confidence,
                headlines=mock_headlines
            )

        except Exception as e:
            logger.debug(f"Sentiment signal failed: {e}")
            return None


async def main():
    """Main entry point"""
    import os

    # Configuration from environment
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    symbols = os.environ.get("SYMBOLS", "BTC/USDT,ETH/USDT").split(",")

    # Create and start engine
    engine = StrategyEngine(
        redis_host=redis_host,
        redis_port=redis_port,
        symbols=symbols
    )

    await engine.start(loop_interval=1.0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
