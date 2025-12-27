"""
Advanced Trading Service

This service integrates the sophisticated trading engine components
including AI/ML models, risk management, and quantum-inspired algorithms.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.ml_models.quantum_models.quantum_classifier import QuantumInspiredClassifier
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.services.market_data import MarketDataService
from trading_engine.engine.circuit_breaker import get_circuit_breaker
from trading_engine.engine.risk_config import RiskProfile, get_risk_config
from trading_engine.engine.trade_executor import TradeExecutor
from trading_engine.strategies import (
    StrategyRegistry,
    StrategyCategory,
    TradingStrategy,
    # Technical Analysis
    RSIStrategy,
    BollingerBandsStrategy,
    MACDStrategy,
    IchimokuCloudStrategy,
    ADXTrendStrategy,
    StochasticStrategy,
    CandlestickPatternStrategy,
    # Breakout
    SupportResistanceBreakout,
    OpeningRangeBreakout,
    DonchianBreakout,
    # Mean Reversion
    StatisticalMeanReversion,
    RSIMeanReversion,
    # Momentum
    MomentumFactorStrategy,
    TrendFollowingStrategy,
    # Arbitrage
    PairsTradingStrategy,
    # Grid/DCA
    GridTradingStrategy,
    DCAStrategy,
    # Execution
    VWAPExecutionStrategy,
    TWAPExecutionStrategy,
    IcebergExecutionStrategy,
)
from trading_engine.strategies.moving_average import MovingAverageStrategy

logger = logging.getLogger(__name__)

# Strategy configuration mapping
STRATEGY_CONFIGS = {
    "moving_average": {
        "class": MovingAverageStrategy,
        "params": {"short_window": 20, "long_window": 50},
    },
    "rsi": {
        "class": RSIStrategy,
        "params": {"rsi_period": 14, "overbought": 70, "oversold": 30},
    },
    "bollinger_bands": {
        "class": BollingerBandsStrategy,
        "params": {"period": 20, "num_std": 2.0, "mode": "combined"},
    },
    "macd": {
        "class": MACDStrategy,
        "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
    },
    "ichimoku": {
        "class": IchimokuCloudStrategy,
        "params": {"tenkan_period": 9, "kijun_period": 26, "mode": "combined"},
    },
    "adx_trend": {
        "class": ADXTrendStrategy,
        "params": {"adx_period": 14, "adx_threshold": 25.0},
    },
    "stochastic": {
        "class": StochasticStrategy,
        "params": {"k_period": 14, "d_period": 3},
    },
    "candlestick": {
        "class": CandlestickPatternStrategy,
        "params": {"require_confirmation": True},
    },
    "support_resistance": {
        "class": SupportResistanceBreakout,
        "params": {"lookback": 20, "confirmation_bars": 2},
    },
    "opening_range": {
        "class": OpeningRangeBreakout,
        "params": {"opening_range_minutes": 30},
    },
    "donchian": {
        "class": DonchianBreakout,
        "params": {"entry_period": 20, "exit_period": 10},
    },
    "mean_reversion": {
        "class": StatisticalMeanReversion,
        "params": {"lookback_period": 20, "z_score_entry": 2.0},
    },
    "rsi_reversion": {
        "class": RSIMeanReversion,
        "params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
    },
    "momentum": {
        "class": MomentumFactorStrategy,
        "params": {"momentum_period": 12, "ma_period": 50},
    },
    "trend_following": {
        "class": TrendFollowingStrategy,
        "params": {"fast_ma": 20, "slow_ma": 50, "trend_ma": 200},
    },
    "pairs_trading": {
        "class": PairsTradingStrategy,
        "params": {"lookback_period": 60, "z_score_entry": 2.0},
    },
    "grid_trading": {
        "class": GridTradingStrategy,
        "params": {"num_grids": 10, "auto_range": True},
    },
    "dca": {
        "class": DCAStrategy,
        "params": {"investment_amount": 100.0, "frequency_hours": 24},
    },
}


class AdvancedTradingService:
    """
    Advanced trading service that combines multiple strategies,
    AI/ML models, and sophisticated risk management.
    """

    def __init__(
        self,
        db: Session,
        market_data_service: MarketDataService,
        risk_profile: RiskProfile = RiskProfile.MODERATE,
    ):
        """
        Initialize the advanced trading service

        Args:
            db: Database session
            market_data_service: Market data service
            risk_profile: Risk profile to use
        """
        self.db = db
        self.market_data_service = market_data_service
        self.risk_profile = risk_profile

        # Initialize risk management
        self.risk_config = get_risk_config(risk_profile)
        self.circuit_breaker = get_circuit_breaker()

        # Initialize strategies
        self.strategies = {}
        self.ai_models = {}

        # Performance tracking
        self.performance_metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "total_return": 0.0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
        }

        logger.info(
            f"Initialized AdvancedTradingService with risk profile: {risk_profile.value}"
        )

    async def initialize_strategies(
        self,
        symbols: List[str],
        strategy_types: Optional[List[str]] = None
    ) -> None:
        """
        Initialize trading strategies for given symbols

        Args:
            symbols: List of symbols to create strategies for
            strategy_types: List of strategy types to use (default: ["moving_average"])
        """
        try:
            if strategy_types is None:
                strategy_types = ["moving_average"]

            for symbol in symbols:
                symbol_strategies = []

                for strategy_type in strategy_types:
                    strategy = self._create_strategy(symbol, strategy_type)
                    if strategy:
                        symbol_strategies.append({
                            "type": strategy_type,
                            "strategy": strategy,
                            "executor": TradeExecutor(
                                market_data_service=self.market_data_service,
                                strategy=strategy
                            ),
                        })
                        logger.info(f"Initialized {strategy_type} strategy for {symbol}")

                if symbol_strategies:
                    self.strategies[symbol] = symbol_strategies

            logger.info(
                f"Initialized {sum(len(s) for s in self.strategies.values())} "
                f"strategies for {len(symbols)} symbols"
            )

        except Exception as e:
            logger.error(f"Error initializing strategies: {str(e)}")
            raise

    def _create_strategy(
        self,
        symbol: str,
        strategy_type: str,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Optional[TradingStrategy]:
        """
        Create a strategy instance by type

        Args:
            symbol: Trading symbol
            strategy_type: Type of strategy to create
            custom_params: Custom parameters to override defaults

        Returns:
            Strategy instance or None
        """
        if strategy_type not in STRATEGY_CONFIGS:
            logger.warning(f"Unknown strategy type: {strategy_type}")
            return None

        config = STRATEGY_CONFIGS[strategy_type]
        strategy_class = config["class"]
        params = {**config["params"]}

        if custom_params:
            params.update(custom_params)

        try:
            return strategy_class(
                symbol=symbol,
                market_data_service=self.market_data_service,
                **params
            )
        except Exception as e:
            logger.error(f"Error creating {strategy_type} strategy: {str(e)}")
            return None

    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available strategy types and their configurations

        Returns:
            Dictionary of strategy types and their default parameters
        """
        return {
            name: {
                "description": config["class"].__doc__.split("\n")[0] if config["class"].__doc__ else name,
                "default_params": config["params"],
            }
            for name, config in STRATEGY_CONFIGS.items()
        }

    async def add_strategy_to_symbol(
        self,
        symbol: str,
        strategy_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new strategy to an existing symbol

        Args:
            symbol: Trading symbol
            strategy_type: Type of strategy to add
            params: Strategy parameters

        Returns:
            True if successful
        """
        try:
            strategy = self._create_strategy(symbol, strategy_type, params)
            if not strategy:
                return False

            if symbol not in self.strategies:
                self.strategies[symbol] = []

            self.strategies[symbol].append({
                "type": strategy_type,
                "strategy": strategy,
                "executor": TradeExecutor(
                    market_data_service=self.market_data_service,
                    strategy=strategy
                ),
            })

            logger.info(f"Added {strategy_type} strategy to {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error adding strategy: {str(e)}")
            return False

    async def remove_strategy_from_symbol(
        self,
        symbol: str,
        strategy_type: str
    ) -> bool:
        """
        Remove a strategy from a symbol

        Args:
            symbol: Trading symbol
            strategy_type: Type of strategy to remove

        Returns:
            True if successful
        """
        try:
            if symbol not in self.strategies:
                return False

            self.strategies[symbol] = [
                s for s in self.strategies[symbol]
                if s["type"] != strategy_type
            ]

            logger.info(f"Removed {strategy_type} strategy from {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error removing strategy: {str(e)}")
            return False

    async def initialize_ai_models(self, symbols: List[str]) -> None:
        """
        Initialize AI/ML models for prediction

        Args:
            symbols: List of symbols to create models for
        """
        try:
            for symbol in symbols:
                # Create quantum-inspired classifier
                quantum_model = QuantumInspiredClassifier(
                    n_features=10, n_qubits=4, learning_rate=0.01, max_iterations=100
                )

                self.ai_models[symbol] = {
                    "quantum_classifier": quantum_model,
                    "is_trained": False,
                    "last_prediction": None,
                    "prediction_confidence": 0.0,
                }

                logger.info(f"Initialized AI models for {symbol}")

            # Train models if we have historical data
            await self._train_ai_models()

        except Exception as e:
            logger.error(f"Error initializing AI models: {str(e)}")
            raise

    async def _train_ai_models(self) -> None:
        """Train AI models using historical data"""
        try:
            for symbol, models in self.ai_models.items():
                logger.info(f"Training AI models for {symbol}...")

                # Get historical data for training
                historical_data = await self._get_training_data(symbol)

                if historical_data is not None and len(historical_data) > 50:
                    # Prepare features and labels
                    X, y = self._prepare_training_data(historical_data)

                    if len(X) > 20:  # Minimum data requirement
                        # Train quantum classifier
                        quantum_model = models["quantum_classifier"]
                        quantum_model.fit(X, y)
                        models["is_trained"] = True

                        training_summary = quantum_model.get_training_summary()
                        logger.info(
                            f"Trained quantum model for {symbol}: {training_summary}"
                        )
                    else:
                        logger.warning(f"Insufficient data for training {symbol} model")
                else:
                    logger.warning(
                        f"No historical data available for training {symbol}"
                    )

        except Exception as e:
            logger.error(f"Error training AI models: {str(e)}")

    async def _get_training_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical data for model training"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)  # 1 year of data

            data = await self.market_data_service.get_historical_data(
                symbol, start_date.isoformat(), end_date.isoformat()
            )

            if data:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = data

                # Ensure we have required columns
                if "close" in df.columns and "volume" in df.columns:
                    return df

            return None

        except Exception as e:
            logger.error(f"Error getting training data for {symbol}: {str(e)}")
            return None

    def _prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """Prepare features and labels for ML training"""
        try:
            # Calculate technical indicators as features
            df["price_change"] = df["close"].pct_change()
            df["volume_change"] = df["volume"].pct_change()
            df["sma_5"] = df["close"].rolling(window=5).mean()
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["rsi"] = self._calculate_rsi(df["close"], window=14)
            df["bb_upper"], df["bb_lower"] = self._calculate_bollinger_bands(
                df["close"]
            )
            df["macd"] = self._calculate_macd(df["close"])

            # Create features
            feature_columns = [
                "price_change",
                "volume_change",
                "sma_5",
                "sma_20",
                "rsi",
                "bb_upper",
                "bb_lower",
                "macd",
            ]

            # Add relative position features
            df["price_vs_sma5"] = df["close"] / df["sma_5"] - 1
            df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1
            feature_columns.extend(["price_vs_sma5", "price_vs_sma20"])

            # Create labels (1 if price goes up next day, 0 otherwise)
            df["future_return"] = df["close"].shift(-1) / df["close"] - 1
            df["label"] = (df["future_return"] > 0).astype(int)

            # Remove rows with NaN values
            df = df.dropna()

            if len(df) == 0:
                return np.array([]), np.array([])

            X = df[feature_columns].values
            y = df["label"].values

            return X, y

        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return np.array([]), np.array([])

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_bollinger_bands(
        self, prices: pd.Series, window: int = 20, num_std: float = 2
    ):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, lower_band

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26
    ) -> pd.Series:
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        return exp1 - exp2

    async def generate_trading_signals(
        self,
        portfolio: Portfolio,
        combine_signals: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals for all active strategies

        Args:
            portfolio: Portfolio to trade
            combine_signals: Whether to combine signals from multiple strategies

        Returns:
            List of trading signals
        """
        signals = []

        try:
            # Check circuit breakers first
            trading_allowed, breaker_status = self.circuit_breaker.check()
            if not trading_allowed:
                logger.warning(
                    f"Trading halted due to circuit breaker: {breaker_status}"
                )
                return signals

            for symbol, strategy_list in self.strategies.items():
                try:
                    # Get current market data
                    market_data = await self.market_data_service.get_quote(symbol)

                    if not market_data:
                        logger.warning(f"No market data available for {symbol}")
                        continue

                    symbol_signals = []

                    # Generate signals from all strategies for this symbol
                    for strategy_data in strategy_list:
                        strategy = strategy_data["strategy"]
                        strategy_type = strategy_data["type"]

                        try:
                            signal = await strategy.generate_signal(market_data)

                            if signal and signal["action"] != "hold":
                                signal["strategy_type"] = strategy_type
                                symbol_signals.append(signal)

                        except Exception as e:
                            logger.error(
                                f"Error generating {strategy_type} signal for {symbol}: {str(e)}"
                            )
                            continue

                    if not symbol_signals:
                        continue

                    # Combine or process individual signals
                    if combine_signals and len(symbol_signals) > 1:
                        combined_signal = self._combine_signals(symbol_signals)
                        if combined_signal:
                            # Enhance with AI prediction
                            ai_prediction = await self._get_ai_prediction(
                                symbol, market_data
                            )
                            if ai_prediction:
                                combined_signal["ai_confidence"] = ai_prediction["confidence"]
                                combined_signal["ai_prediction"] = ai_prediction["prediction"]
                                combined_signal["combined_confidence"] = (
                                    combined_signal["confidence"] + ai_prediction["confidence"]
                                ) / 2

                            signals.append({
                                "symbol": symbol,
                                "signal": combined_signal,
                                "strategy_name": "combined",
                                "contributing_strategies": [
                                    s["strategy_type"] for s in symbol_signals
                                ],
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                    else:
                        # Add individual signals
                        for signal in symbol_signals:
                            strategy_type = signal.pop("strategy_type", "unknown")

                            # Enhance with AI prediction
                            ai_prediction = await self._get_ai_prediction(
                                symbol, market_data
                            )
                            if ai_prediction:
                                signal["ai_confidence"] = ai_prediction["confidence"]
                                signal["ai_prediction"] = ai_prediction["prediction"]
                                signal["combined_confidence"] = (
                                    signal["confidence"] + ai_prediction["confidence"]
                                ) / 2

                            signals.append({
                                "symbol": symbol,
                                "signal": signal,
                                "strategy_name": strategy_type,
                                "timestamp": datetime.utcnow().isoformat(),
                            })

                except Exception as e:
                    logger.error(f"Error generating signals for {symbol}: {str(e)}")
                    continue

            logger.info(f"Generated {len(signals)} trading signals")
            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return signals

    def _combine_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Combine multiple strategy signals into a consensus signal

        Args:
            signals: List of signals from different strategies

        Returns:
            Combined signal or None if no consensus
        """
        if not signals:
            return None

        # Count votes for each action
        action_votes = {"buy": 0, "sell": 0, "hold": 0}
        total_confidence = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        for signal in signals:
            action = signal.get("action", "hold")
            confidence = signal.get("confidence", 0.5)

            action_votes[action] += 1
            total_confidence[action] += confidence

        # Determine winning action
        if action_votes["buy"] > action_votes["sell"]:
            winning_action = "buy"
        elif action_votes["sell"] > action_votes["buy"]:
            winning_action = "sell"
        else:
            # Tie - use confidence to decide
            if total_confidence["buy"] > total_confidence["sell"]:
                winning_action = "buy"
            elif total_confidence["sell"] > total_confidence["buy"]:
                winning_action = "sell"
            else:
                winning_action = "hold"

        if winning_action == "hold":
            return None

        # Calculate combined confidence
        agreement_ratio = action_votes[winning_action] / len(signals)
        avg_confidence = (
            total_confidence[winning_action] / action_votes[winning_action]
            if action_votes[winning_action] > 0 else 0
        )
        combined_confidence = agreement_ratio * avg_confidence

        # Get average stop loss and take profit from signals
        stop_losses = [s.get("stop_loss") for s in signals if s.get("stop_loss")]
        take_profits = [s.get("take_profit") for s in signals if s.get("take_profit")]

        combined_signal = {
            "action": winning_action,
            "confidence": combined_confidence,
            "agreement_ratio": agreement_ratio,
            "num_strategies": len(signals),
            "votes": action_votes,
            "price": signals[0].get("price", 0),
            "reason": f"Consensus from {len(signals)} strategies ({action_votes[winning_action]} agree)",
        }

        if stop_losses:
            combined_signal["stop_loss"] = np.mean(stop_losses)
        if take_profits:
            combined_signal["take_profit"] = np.mean(take_profits)

        return combined_signal

    async def _get_ai_prediction(
        self, symbol: str, market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get AI model prediction for a symbol"""
        try:
            if symbol not in self.ai_models:
                return None

            model_data = self.ai_models[symbol]
            if not model_data["is_trained"]:
                return None

            # Prepare current features
            current_features = await self._prepare_current_features(symbol, market_data)
            if current_features is None:
                return None

            # Make prediction
            quantum_model = model_data["quantum_classifier"]
            prediction_proba = quantum_model.predict_proba(
                current_features.reshape(1, -1)
            )

            prediction = prediction_proba[0][1]  # Probability of positive movement
            confidence = max(prediction, 1 - prediction)  # Distance from 0.5

            model_data["last_prediction"] = prediction
            model_data["prediction_confidence"] = confidence

            return {
                "prediction": prediction,
                "confidence": confidence,
                "model_type": "quantum_classifier",
            }

        except Exception as e:
            logger.error(f"Error getting AI prediction for {symbol}: {str(e)}")
            return None

    async def _prepare_current_features(
        self, symbol: str, market_data: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """Prepare current market features for AI prediction"""
        try:
            # Get recent historical data for feature calculation
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            historical_data = await self.market_data_service.get_historical_data(
                symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not historical_data:
                return None

            if isinstance(historical_data, list):
                df = pd.DataFrame(historical_data)
            else:
                df = historical_data

            # Add current data point
            current_row = {
                "close": market_data["price"],
                "volume": market_data.get("volume", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }

            df = pd.concat([df, pd.DataFrame([current_row])], ignore_index=True)

            # Calculate features (same as training)
            X, _ = self._prepare_training_data(df)

            if len(X) > 0:
                return X[-1]  # Return the last (current) feature vector

            return None

        except Exception as e:
            logger.error(f"Error preparing current features for {symbol}: {str(e)}")
            return None

    async def execute_trades(
        self, signals: List[Dict[str, Any]], portfolio: Portfolio
    ) -> List[Trade]:
        """
        Execute trades based on signals

        Args:
            signals: List of trading signals
            portfolio: Portfolio to execute trades for

        Returns:
            List of executed trades
        """
        executed_trades = []

        try:
            for signal_data in signals:
                try:
                    symbol = signal_data["symbol"]
                    signal = signal_data["signal"]

                    if symbol not in self.strategies:
                        logger.warning(f"No strategy found for {symbol}")
                        continue

                    # Get trade executor
                    executor = self.strategies[symbol]["executor"]

                    # Execute the trade
                    trade = await executor.execute_strategy_signal(signal, portfolio)

                    if trade:
                        executed_trades.append(trade)
                        logger.info(
                            f"Executed trade for {symbol}: {trade.side.value} {trade.quantity} shares"
                        )

                        # Update performance metrics
                        self.performance_metrics["total_trades"] += 1

                except Exception as e:
                    logger.error(f"Error executing trade for signal: {str(e)}")
                    continue

            logger.info(f"Executed {len(executed_trades)} trades")
            return executed_trades

        except Exception as e:
            logger.error(f"Error executing trades: {str(e)}")
            return executed_trades

    async def monitor_positions(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Monitor existing positions and risk metrics

        Args:
            portfolio: Portfolio to monitor

        Returns:
            Position monitoring summary
        """
        try:
            monitoring_summary = {
                "total_positions": 0,
                "total_value": 0.0,
                "unrealized_pnl": 0.0,
                "risk_metrics": {},
                "alerts": [],
            }

            # Check portfolio risk limits
            daily_drawdown = portfolio.get_daily_drawdown()
            if daily_drawdown:
                max_daily_drawdown = self.risk_config.get_param(
                    "drawdown_limits.max_daily_drawdown"
                )
                if daily_drawdown > max_daily_drawdown:
                    monitoring_summary["alerts"].append(
                        {
                            "type": "risk_limit_breach",
                            "message": f"Daily drawdown {daily_drawdown:.2%} exceeds limit {max_daily_drawdown:.2%}",
                            "severity": "high",
                        }
                    )

            # Check trade frequency
            daily_trades = portfolio.get_daily_trade_count()
            max_daily_trades = self.risk_config.get_param(
                "trade_limitations.max_trades_per_day"
            )
            if daily_trades >= max_daily_trades:
                monitoring_summary["alerts"].append(
                    {
                        "type": "trade_frequency_limit",
                        "message": f"Daily trade count {daily_trades} at limit {max_daily_trades}",
                        "severity": "medium",
                    }
                )

            monitoring_summary["risk_metrics"] = {
                "daily_drawdown": daily_drawdown,
                "daily_trades": daily_trades,
                "portfolio_value": float(portfolio.total_value),
                "risk_profile": self.risk_profile.value,
            }

            return monitoring_summary

        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            return {"error": str(e)}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        return {
            "performance_metrics": self.performance_metrics,
            "active_strategies": len(self.strategies),
            "trained_ai_models": sum(
                1 for models in self.ai_models.values() if models["is_trained"]
            ),
            "risk_profile": self.risk_profile.value,
            "circuit_breaker_status": self.circuit_breaker.get_status(),
        }

    async def update_risk_profile(self, new_profile: RiskProfile) -> bool:
        """
        Update the risk profile

        Args:
            new_profile: New risk profile to use

        Returns:
            True if successful
        """
        try:
            self.risk_profile = new_profile
            self.risk_config.update_profile(new_profile)

            logger.info(f"Updated risk profile to {new_profile.value}")
            return True

        except Exception as e:
            logger.error(f"Error updating risk profile: {str(e)}")
            return False
