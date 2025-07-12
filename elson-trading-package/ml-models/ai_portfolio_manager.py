"""
AI Portfolio Manager Service
Implements advanced portfolio management features using machine learning and optimization algorithms
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from redis import Redis
from scipy import optimize
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import record_metric
from app.db.database import get_redis
from app.models.portfolio import Portfolio, Position
from app.models.trade import OrderType, Trade, TradeStatus
from app.models.user import User, UserRole
from app.services.advisor import AdvisorService, Recommendation
from app.services.market_data import MarketDataService
from app.services.market_data_processor import MarketDataProcessor
from app.services.neural_network import NeuralNetworkService

# Setup logger
logger = logging.getLogger(__name__)


class PortfolioOptimizationResult:
    """
    Result of a portfolio optimization operation
    """

    def __init__(
        self,
        target_allocation: Dict[str, float],
        expected_return: float,
        expected_risk: float,
        sharpe_ratio: float,
        optimization_method: str,
        confidence_score: float,
        rebalance_trades: Optional[List[Trade]] = None,
    ):
        self.target_allocation = target_allocation
        self.expected_return = expected_return
        self.expected_risk = expected_risk
        self.sharpe_ratio = sharpe_ratio
        self.optimization_method = optimization_method
        self.confidence_score = confidence_score
        self.rebalance_trades = rebalance_trades or []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "target_allocation": self.target_allocation,
            "expected_return": self.expected_return,
            "expected_risk": self.expected_risk,
            "sharpe_ratio": self.sharpe_ratio,
            "optimization_method": self.optimization_method,
            "confidence_score": self.confidence_score,
            "trade_count": len(self.rebalance_trades),
            "created_at": self.created_at.isoformat(),
        }


class MarketTimingSignal:
    """
    Market timing signal used for determining optimal trade execution windows
    """

    def __init__(
        self,
        symbol: str,
        signal_type: str,  # "buy", "sell", or "hold"
        strength: float,  # 0.0 to 1.0
        time_window: str,  # "immediate", "today", "this_week"
        prediction_horizon: int,  # in days
        confidence: float,
        signals: Dict[str, float],  # Individual signal components
        market_conditions: Dict[str, Any],
    ):
        self.symbol = symbol
        self.signal_type = signal_type
        self.strength = strength
        self.time_window = time_window
        self.prediction_horizon = prediction_horizon
        self.confidence = confidence
        self.signals = signals
        self.market_conditions = market_conditions
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "strength": self.strength,
            "time_window": self.time_window,
            "prediction_horizon": self.prediction_horizon,
            "confidence": self.confidence,
            "signals": self.signals,
            "market_conditions": self.market_conditions,
            "created_at": self.created_at.isoformat(),
        }


class AIPortfolioManager(AdvisorService):
    """
    Enhanced AI-driven portfolio management service
    Extends the base AdvisorService with advanced features:
    - AI-optimized portfolio allocation
    - Smart trade timing based on market conditions
    - Automated rebalancing with ML-driven allocation
    """

    # Cache keys for optimization results
    CACHE_KEY_PREFIX = "ai_portfolio_manager:"
    OPTIMIZATION_CACHE_TTL = 3600  # 1 hour

    def __init__(
        self,
        db: Session,
        market_data_service: Optional[MarketDataService] = None,
        neural_network_service: Optional[NeuralNetworkService] = None,
        redis_client: Optional[Redis] = None,
    ):
        super().__init__(db, market_data_service)
        self.neural_network = neural_network_service
        self.market_processor = MarketDataProcessor()
        self.redis = redis_client

        # Set default risk-free rate (used in optimization)
        self.risk_free_rate = settings.RISK_FREE_RATE

    def optimize_portfolio(
        self,
        user_id: int,
        method: str = "efficient_frontier",
        risk_tolerance: float = 0.5,
        lookback_days: int = 365,
        min_allocation: float = 0.05,
        max_allocation: float = 0.3,
    ) -> Optional[PortfolioOptimizationResult]:
        """
        Optimize a portfolio using modern portfolio theory or ML-based approaches

        Args:
            user_id: The user's ID
            method: Optimization method ("efficient_frontier", "black_litterman", "risk_parity")
            risk_tolerance: User's risk tolerance (0.0 to 1.0)
            lookback_days: Days of historical data to use
            min_allocation: Minimum allocation per asset
            max_allocation: Maximum allocation per asset

        Returns:
            PortfolioOptimizationResult with the optimized allocation
        """
        # Start timing for metrics
        start_time = datetime.utcnow()

        # Try to get cached optimization results first
        cache_key = (
            f"{self.CACHE_KEY_PREFIX}optimize:{user_id}:{method}:{risk_tolerance}"
        )
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Using cached optimization result for user {user_id}")
            record_metric(
                "ai_portfolio_optimization",
                (datetime.utcnow() - start_time).total_seconds(),
                {"method": method, "source": "cache"},
            )
            return cached_result

        # Get user and portfolio
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        )
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return None

        # Get current positions
        positions = (
            self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        )
        symbols = [p.symbol for p in positions]

        # Add benchmark symbols and common ETFs for diversification
        additional_symbols = [
            "SPY",
            "QQQ",
            "VTI",
            "AGG",
            "BND",
            "VEA",
            "VWO",
            "VXUS",
            "GLD",
            "VNQ",
        ]
        for symbol in additional_symbols:
            if symbol not in symbols:
                symbols.append(symbol)

        # Get historical price data
        if not self.market_data:
            logger.error("Market data service not available")
            return None

        # Get historical data for all symbols
        historical_data = self._get_historical_data(symbols, lookback_days)
        if not historical_data or len(historical_data) < 30:  # Need sufficient data
            logger.error(
                f"Insufficient historical data for optimization: {len(historical_data)} days"
            )
            return None

        # Calculate returns
        returns = self._calculate_returns(historical_data)

        # Perform optimization based on method
        try:
            if method == "efficient_frontier":
                result = self._optimize_efficient_frontier(
                    returns, risk_tolerance, min_allocation, max_allocation, symbols
                )
            elif method == "black_litterman":
                result = self._optimize_black_litterman(
                    returns,
                    risk_tolerance,
                    min_allocation,
                    max_allocation,
                    symbols,
                    portfolio,
                )
            elif method == "risk_parity":
                result = self._optimize_risk_parity(
                    returns, min_allocation, max_allocation, symbols
                )
            else:
                logger.error(f"Unknown optimization method: {method}")
                return None
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            return None

        # Calculate expected metrics for the optimized portfolio
        (
            expected_return,
            expected_risk,
            sharpe_ratio,
        ) = self._calculate_portfolio_metrics(result, returns)

        # Calculate trades needed for rebalancing
        rebalance_trades = self._calculate_rebalance_trades(
            user_id, portfolio.id, positions, result
        )

        # Create result object
        optimization_result = PortfolioOptimizationResult(
            target_allocation=result,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe_ratio,
            optimization_method=method,
            confidence_score=0.8,  # Placeholder - could be calculated based on data quality
            rebalance_trades=rebalance_trades,
        )

        # Cache the result
        self._cache_result(cache_key, optimization_result)

        # Record metrics
        record_metric(
            "ai_portfolio_optimization",
            (datetime.utcnow() - start_time).total_seconds(),
            {"method": method, "source": "calculated"},
        )

        return optimization_result

    def get_market_timing_signal(
        self, user_id: int, symbol: str, prediction_horizon: int = 7  # days
    ) -> Optional[MarketTimingSignal]:
        """
        Get a market timing signal for a specific symbol

        Args:
            user_id: The user's ID
            symbol: The symbol to analyze
            prediction_horizon: Days to look ahead for prediction

        Returns:
            MarketTimingSignal with the recommended timing
        """
        # Start timing for metrics
        start_time = datetime.utcnow()

        try:
            # Check if neural network service is available
            if not self.neural_network:
                logger.error("Neural network service not available")
                return None

            # Get market data
            if not self.market_data:
                logger.error("Market data service not available")
                return None

            # Get historical data
            historical_data = self._get_historical_data(
                [symbol], 120
            )  # 120 days of data
            if not historical_data or len(historical_data) < 60:  # Need sufficient data
                logger.error(
                    f"Insufficient historical data for timing signal: {len(historical_data)} days"
                )
                return None

            # Process market data to extract features
            features = self.market_processor.extract_features(historical_data, symbol)

            # Get neural network prediction
            prediction = self.neural_network.predict(
                symbol, features, prediction_horizon
            )
            if not prediction:
                logger.error(f"Failed to get prediction for {symbol}")
                return None

            # Get market regime and conditions
            market_regime = self.market_processor.detect_market_regime(
                historical_data, symbol
            )
            market_volatility = self.market_processor.calculate_volatility(
                historical_data, symbol, 30
            )
            market_momentum = self.market_processor.calculate_momentum(
                historical_data, symbol, 14
            )

            # Calculate technical signals
            rsi = self.market_processor.calculate_rsi(historical_data, symbol, 14)
            macd = self.market_processor.calculate_macd(historical_data, symbol)
            bollinger = self.market_processor.calculate_bollinger_bands(
                historical_data, symbol
            )

            # Combine signals for overall recommendation
            signal_strength = 0.0
            signal_type = "hold"

            # RSI signal
            rsi_signal = 0.0
            if rsi < 30:
                rsi_signal = (30 - rsi) / 30  # Buy signal (0.0 to 1.0)
            elif rsi > 70:
                rsi_signal = -1 * (rsi - 70) / 30  # Sell signal (-1.0 to 0.0)

            # MACD signal
            macd_signal = macd["signal"] if macd else 0.0

            # Bollinger signal
            bollinger_signal = 0.0
            if (
                bollinger
                and "lower" in bollinger
                and "upper" in bollinger
                and "price" in bollinger
            ):
                if bollinger["price"] < bollinger["lower"]:
                    bollinger_signal = 0.7  # Strong buy signal
                elif bollinger["price"] > bollinger["upper"]:
                    bollinger_signal = -0.7  # Strong sell signal

            # Prediction signal from neural network
            nn_signal = prediction["direction"] * prediction["confidence"]

            # Regime-based adjustment
            regime_factor = 1.0
            if market_regime == "bear":
                regime_factor = 0.7  # Reduce signal strength in bear markets
            elif market_regime == "choppy":
                regime_factor = 0.5  # Further reduce in choppy markets

            # Combine all signals with weights
            combined_signal = (
                (0.25 * rsi_signal)
                + (0.20 * macd_signal)
                + (0.15 * bollinger_signal)
                + (0.40 * nn_signal)
            ) * regime_factor

            signal_strength = abs(combined_signal)
            signal_type = (
                "buy"
                if combined_signal > 0.1
                else "sell"
                if combined_signal < -0.1
                else "hold"
            )

            # Determine time window based on signal strength
            time_window = "this_week"
            if signal_strength > 0.7:
                time_window = "immediate"
            elif signal_strength > 0.4:
                time_window = "today"

            # Calculate confidence score
            confidence = min(0.5 + signal_strength * 0.5, 0.95)  # Scale to 0.5-0.95

            # Create result
            signal = MarketTimingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=signal_strength,
                time_window=time_window,
                prediction_horizon=prediction_horizon,
                confidence=confidence,
                signals={
                    "rsi": float(rsi) if rsi is not None else None,
                    "macd": float(macd_signal) if macd_signal is not None else None,
                    "bollinger": float(bollinger_signal)
                    if bollinger_signal is not None
                    else None,
                    "nn_prediction": float(nn_signal)
                    if nn_signal is not None
                    else None,
                },
                market_conditions={
                    "regime": market_regime,
                    "volatility": float(market_volatility)
                    if market_volatility is not None
                    else None,
                    "momentum": float(market_momentum)
                    if market_momentum is not None
                    else None,
                },
            )

            # Record metrics
            record_metric(
                "market_timing_signal",
                (datetime.utcnow() - start_time).total_seconds(),
                {"symbol": symbol},
            )

            return signal

        except Exception as e:
            logger.error(f"Failed to get market timing signal: {str(e)}")
            return None

    def rebalance_portfolio_ai(
        self,
        user_id: int,
        optimization_method: str = "efficient_frontier",
        risk_tolerance: float = 0.5,
        consider_timing: bool = True,
        max_trades: int = 20,
        min_trade_impact: float = 0.02,  # 2% minimum impact to make a trade
    ) -> Tuple[List[Trade], Optional[PortfolioOptimizationResult]]:
        """
        Rebalance a portfolio using AI optimization and smart timing

        Args:
            user_id: The user's ID
            optimization_method: Method to use for optimization
            risk_tolerance: User's risk tolerance (0.0 to 1.0)
            consider_timing: Whether to consider market timing signals
            max_trades: Maximum number of trades to generate
            min_trade_impact: Minimum portfolio impact to generate a trade

        Returns:
            Tuple of (trades, optimization_result)
        """
        # Start timing for metrics
        start_time = datetime.utcnow()

        # Get user and portfolio
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return [], None

        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        )
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return [], None

        # Check if rebalancing is needed (don't rebalance too frequently)
        if (
            portfolio.last_rebalanced_at
            and (datetime.utcnow() - portfolio.last_rebalanced_at).days < 7
        ):
            logger.info(f"Portfolio {portfolio.id} was recently rebalanced, skipping")
            return [], None

        # Run portfolio optimization
        optimization_result = self.optimize_portfolio(
            user_id, method=optimization_method, risk_tolerance=risk_tolerance
        )

        if not optimization_result:
            logger.error(f"Failed to optimize portfolio for user {user_id}")
            return [], None

        # Get positions
        positions = (
            self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        )

        # Calculate trades based on optimization result
        trades = []
        if optimization_result.rebalance_trades:
            trades = optimization_result.rebalance_trades

        # If timing is considered, prioritize trades based on timing signals
        if consider_timing and trades:
            prioritized_trades = []

            for trade in trades:
                # Get timing signal for this symbol
                timing_signal = self.get_market_timing_signal(user_id, trade.symbol)

                # Skip trades with opposing signals
                if timing_signal:
                    # Strong opposing signal - skip the trade
                    if (
                        trade.trade_type == "buy"
                        and timing_signal.signal_type == "sell"
                        and timing_signal.strength > 0.7
                    ):
                        continue
                    elif (
                        trade.trade_type == "sell"
                        and timing_signal.signal_type == "buy"
                        and timing_signal.strength > 0.7
                    ):
                        continue

                    # Adjust quantity based on signal alignment
                    signal_alignment = 1.0
                    if timing_signal.signal_type == trade.trade_type:
                        # Aligned signals - boost the trade quantity
                        signal_alignment = 1.0 + (timing_signal.strength * 0.3)
                    elif timing_signal.signal_type == "hold":
                        # Neutral signal - slight reduction
                        signal_alignment = 0.9
                    else:
                        # Opposing but not strong enough to skip - reduce quantity
                        signal_alignment = 0.7 - (timing_signal.strength * 0.2)

                    # Adjust quantity
                    trade.quantity *= signal_alignment
                    trade.total_amount = trade.quantity * trade.price

                # Add trade to prioritized list if it meets minimum impact
                trade_impact = (
                    trade.total_amount / portfolio.total_value
                    if portfolio.total_value > 0
                    else 0
                )
                if trade_impact >= min_trade_impact:
                    prioritized_trades.append(trade)

            # Sort trades by alignment with timing signals and impact
            prioritized_trades.sort(key=lambda t: t.total_amount, reverse=True)

            # Limit to max_trades
            trades = prioritized_trades[:max_trades]

        # Mark trades as system-generated
        for trade in trades:
            trade.requested_by_user_id = None  # System-generated

            # Set status based on user role
            if user.role == UserRole.MINOR:
                trade.status = TradeStatus.PENDING_APPROVAL
            else:
                trade.status = TradeStatus.PENDING

            # Add timing field for execution planning
            trade.metadata = json.dumps(
                {
                    "ai_generated": True,
                    "optimization_method": optimization_method,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            )

        # Save pending trades to database
        for trade in trades:
            self.db.add(trade)

        # Update portfolio last rebalanced timestamp
        portfolio.last_rebalanced_at = datetime.utcnow()
        self.db.commit()

        # Record metrics
        record_metric(
            "portfolio_rebalance_ai",
            (datetime.utcnow() - start_time).total_seconds(),
            {"trade_count": len(trades), "method": optimization_method},
        )

        return trades, optimization_result

    def schedule_recurring_optimization(
        self,
        user_id: int,
        schedule: str = "weekly",
        optimization_method: str = "efficient_frontier",
        auto_execute: bool = False,
    ) -> bool:
        """
        Schedule recurring portfolio optimization

        Args:
            user_id: The user's ID
            schedule: Frequency ("daily", "weekly", "monthly")
            optimization_method: Method to use for optimization
            auto_execute: Whether to automatically execute trades

        Returns:
            Success flag
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return False

        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        )
        if not portfolio:
            logger.error(f"Portfolio not found for user: {user_id}")
            return False

        # Update portfolio settings
        if not portfolio.metadata:
            portfolio.metadata = "{}"

        metadata = json.loads(portfolio.metadata)
        metadata["ai_optimization"] = {
            "enabled": True,
            "schedule": schedule,
            "method": optimization_method,
            "auto_execute": auto_execute,
            "updated_at": datetime.utcnow().isoformat(),
        }

        portfolio.metadata = json.dumps(metadata)
        self.db.commit()

        logger.info(f"Scheduled recurring optimization for portfolio {portfolio.id}")
        return True

    def _get_historical_data(
        self, symbols: List[str], days: int = 365
    ) -> Dict[str, List[Dict]]:
        """Get historical price data for the given symbols"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return self.market_data.get_historical_data(symbols, start_date)
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            return {}

    def _calculate_returns(
        self, historical_data: Dict[str, List[Dict]]
    ) -> pd.DataFrame:
        """Calculate daily returns from historical data"""
        # Create a DataFrame to store price data
        prices = {}

        # Extract closing prices for each symbol
        for symbol, data in historical_data.items():
            prices[symbol] = [day["close"] for day in data]

        # Convert to DataFrame
        price_df = pd.DataFrame(prices)

        # Calculate daily returns
        returns = price_df.pct_change().dropna()

        return returns

    def _optimize_efficient_frontier(
        self,
        returns: pd.DataFrame,
        risk_tolerance: float,
        min_allocation: float,
        max_allocation: float,
        symbols: List[str],
    ) -> Dict[str, float]:
        """Optimize portfolio using efficient frontier approach"""
        # Calculate mean returns and covariance matrix
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Number of assets
        num_assets = len(returns.columns)

        # Function to calculate negative Sharpe ratio (we want to minimize this)
        def negative_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
            portfolio_return = np.sum(mean_returns * weights) * 252  # Annualized
            portfolio_std_dev = np.sqrt(
                np.dot(weights.T, np.dot(cov_matrix, weights))
            ) * np.sqrt(252)
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std_dev
            return -sharpe_ratio

        # Function to calculate portfolio variance (for risk aversion)
        def portfolio_variance(weights, mean_returns, cov_matrix):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(
                252
            )

        # Function to calculate portfolio return
        def portfolio_return(weights, mean_returns):
            return np.sum(mean_returns * weights) * 252  # Annualized

        # Function to minimize based on risk tolerance
        def objective_function(
            weights, mean_returns, cov_matrix, risk_tolerance, risk_free_rate
        ):
            port_return = portfolio_return(weights, mean_returns)
            port_variance = portfolio_variance(weights, mean_returns, cov_matrix)

            # Risk-adjusted return (higher risk_tolerance = more return-focused)
            risk_adjusted_return = (1 - risk_tolerance) * (
                -port_variance
            ) + risk_tolerance * port_return

            return -risk_adjusted_return  # Negative because we're minimizing

        # Constraints and bounds
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}  # Weights sum to 1
        bounds = tuple((min_allocation, max_allocation) for _ in range(num_assets))

        # Initial guess - equal weighting
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        # Optimize
        result = optimize.minimize(
            objective_function,
            initial_weights,
            args=(mean_returns, cov_matrix, risk_tolerance, self.risk_free_rate),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        # Create allocation dictionary with symbol keys
        allocation = {}
        for i, symbol in enumerate(returns.columns):
            # Round to 4 decimal places and ensure it's positive
            weight = max(0, round(result["x"][i], 4))
            if weight >= min_allocation:
                allocation[symbol] = weight

        # Normalize to ensure weights sum to 1.0
        total_weight = sum(allocation.values())
        if total_weight > 0:
            allocation = {s: w / total_weight for s, w in allocation.items()}

        return allocation

    def _optimize_black_litterman(
        self,
        returns: pd.DataFrame,
        risk_tolerance: float,
        min_allocation: float,
        max_allocation: float,
        symbols: List[str],
        portfolio: Portfolio,
    ) -> Dict[str, float]:
        """
        Optimize portfolio using Black-Litterman model
        This is a simplified implementation focusing on incorporating custom views
        """
        # For Black-Litterman, we first need market capitalization weights
        # For simplicity, using equal weights or current portfolio weights
        market_caps = {}

        # Get positions for current weights
        positions = (
            self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        )
        current_positions = {p.symbol: p for p in positions}

        # Calculate market weights (using equal weight if not in portfolio)
        total_value = (
            sum(p.quantity * p.current_price for p in positions) if positions else 0
        )

        for symbol in symbols:
            if symbol in current_positions and total_value > 0:
                position = current_positions[symbol]
                market_caps[symbol] = (
                    position.quantity * position.current_price
                ) / total_value
            else:
                market_caps[symbol] = 1.0 / len(symbols)  # Equal weight

        # Normalize market weights
        total_weight = sum(market_caps.values())
        market_weights = {s: w / total_weight for s, w in market_caps.items()}

        # Calculate mean returns and covariance matrix
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Get market equilibrium returns (based on market weights)
        market_weights_array = np.array(
            [market_weights.get(s, 0) for s in returns.columns]
        )
        risk_aversion = 2.5  # Risk aversion coefficient
        equilibrium_returns = risk_aversion * np.dot(cov_matrix, market_weights_array)

        # Define views - here we could incorporate ML predictions or other views
        views = {}
        confidence = {}

        # Attempt to get predictions for each symbol
        if self.neural_network:
            for symbol in symbols:
                # Get ML prediction for each symbol
                try:
                    historical_data = self._get_historical_data([symbol], 120)
                    if historical_data and len(historical_data) > 60:
                        features = self.market_processor.extract_features(
                            historical_data, symbol
                        )
                        prediction = self.neural_network.predict(
                            symbol, features, 30
                        )  # 30-day prediction

                        if prediction and "expected_return" in prediction:
                            views[symbol] = prediction["expected_return"]
                            confidence[symbol] = prediction["confidence"]
                except Exception as e:
                    logger.error(f"Failed to get prediction for {symbol}: {str(e)}")

        # Create Black-Litterman model components
        # Pick matrix - identifies which assets each view is applied to
        P = np.zeros((len(views), len(returns.columns)))
        Q = np.zeros(len(views))
        omega = np.zeros((len(views), len(views)))

        # Fill pick matrix, views vector, and confidence matrix
        for i, (symbol, view) in enumerate(views.items()):
            symbol_idx = list(returns.columns).index(symbol)
            P[i, symbol_idx] = 1.0
            Q[i] = view
            # Set uncertainty based on confidence
            uncertainty = (
                1.0 - confidence.get(symbol, 0.5)
            ) * 0.2  # Scale to reasonable value
            omega[i, i] = uncertainty

        # Tau - scalar controlling weight of market equilibrium vs. views
        tau = 0.05

        # Calculate Black-Litterman expected returns
        if len(views) > 0:
            # Convert to numpy arrays for calculation
            equilibrium_returns_array = np.array(equilibrium_returns)
            cov_matrix_array = np.array(cov_matrix)

            # Black-Litterman formula
            # Invert the matrices
            try:
                omega_inv = np.linalg.inv(omega)
                temp = np.dot(np.dot(P, tau * cov_matrix_array), P.T)
                temp_inv = np.linalg.inv(temp + omega)

                # Calculate expected returns
                middle = np.dot(np.dot(tau * cov_matrix_array, P.T), temp_inv)
                er_bl = equilibrium_returns_array + np.dot(
                    middle, (Q - np.dot(P, equilibrium_returns_array))
                )

                # Set the Black-Litterman expected returns
                bl_returns = pd.Series(er_bl, index=returns.columns)
            except np.linalg.LinAlgError as e:
                logger.error(f"Matrix inversion error in Black-Litterman: {str(e)}")
                # Fallback to equilibrium returns if calculation fails
                bl_returns = pd.Series(equilibrium_returns, index=returns.columns)
        else:
            # If no views, just use equilibrium returns
            bl_returns = pd.Series(equilibrium_returns, index=returns.columns)

        # Now optimize using the Black-Litterman expected returns
        num_assets = len(returns.columns)

        # Objective function based on risk tolerance
        def objective_function(weights, expected_returns, cov_matrix, risk_tolerance):
            port_return = np.sum(expected_returns * weights) * 252  # Annualized
            port_variance = np.sqrt(
                np.dot(weights.T, np.dot(cov_matrix, weights))
            ) * np.sqrt(252)

            # Risk-adjusted return
            risk_adjusted_return = (1 - risk_tolerance) * (
                -port_variance
            ) + risk_tolerance * port_return

            return -risk_adjusted_return  # Negative because we're minimizing

        # Constraints and bounds
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}  # Weights sum to 1
        bounds = tuple((min_allocation, max_allocation) for _ in range(num_assets))

        # Initial guess - current market weights
        initial_weights = np.array(
            [market_weights.get(s, 1.0 / num_assets) for s in returns.columns]
        )

        # Optimize
        result = optimize.minimize(
            objective_function,
            initial_weights,
            args=(bl_returns, cov_matrix, risk_tolerance),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        # Create allocation dictionary with symbol keys
        allocation = {}
        for i, symbol in enumerate(returns.columns):
            # Round to 4 decimal places and ensure it's positive
            weight = max(0, round(result["x"][i], 4))
            if weight >= min_allocation:
                allocation[symbol] = weight

        # Normalize to ensure weights sum to 1.0
        total_weight = sum(allocation.values())
        if total_weight > 0:
            allocation = {s: w / total_weight for s, w in allocation.items()}

        return allocation

    def _optimize_risk_parity(
        self,
        returns: pd.DataFrame,
        min_allocation: float,
        max_allocation: float,
        symbols: List[str],
    ) -> Dict[str, float]:
        """
        Optimize portfolio using Risk Parity approach
        Risk Parity allocates such that each asset contributes equally to the portfolio risk
        """
        # Calculate covariance matrix
        cov_matrix = returns.cov()

        # Number of assets
        num_assets = len(returns.columns)

        # Calculate asset volatilities (standard deviations)
        volatilities = np.sqrt(np.diag(cov_matrix))

        # Risk parity objective function
        def risk_parity_objective(weights, cov_matrix):
            # Calculate portfolio risk contribution for each asset
            portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            risk_contribution = weights * (np.dot(cov_matrix, weights)) / portfolio_risk

            # Calculate risk contribution difference
            target_risk_contribution = portfolio_risk / num_assets
            risk_difference = risk_contribution - target_risk_contribution

            # Return sum of squared differences (to minimize)
            return np.sum(np.square(risk_difference))

        # Constraints and bounds
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}  # Weights sum to 1
        bounds = tuple((min_allocation, max_allocation) for _ in range(num_assets))

        # Initial guess - inverse volatility weighting
        initial_weights = 1 / volatilities
        initial_weights = initial_weights / np.sum(initial_weights)

        # Optimize
        result = optimize.minimize(
            risk_parity_objective,
            initial_weights,
            args=(cov_matrix),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        # Create allocation dictionary with symbol keys
        allocation = {}
        for i, symbol in enumerate(returns.columns):
            # Round to 4 decimal places and ensure it's positive
            weight = max(0, round(result["x"][i], 4))
            if weight >= min_allocation:
                allocation[symbol] = weight

        # Normalize to ensure weights sum to 1.0
        total_weight = sum(allocation.values())
        if total_weight > 0:
            allocation = {s: w / total_weight for s, w in allocation.items()}

        return allocation

    def _calculate_portfolio_metrics(
        self, allocation: Dict[str, float], returns: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """Calculate expected return, risk, and Sharpe ratio for a portfolio allocation"""
        weights_array = np.zeros(len(returns.columns))

        # Map allocation weights to array positions
        for i, symbol in enumerate(returns.columns):
            weights_array[i] = allocation.get(symbol, 0.0)

        # Normalize weights to sum to 1.0
        weights_array = (
            weights_array / np.sum(weights_array)
            if np.sum(weights_array) > 0
            else weights_array
        )

        # Calculate mean returns
        mean_returns = returns.mean()

        # Calculate expected return (annualized)
        expected_return = np.sum(mean_returns * weights_array) * 252

        # Calculate covariance matrix
        cov_matrix = returns.cov()

        # Calculate expected risk (annualized)
        expected_risk = np.sqrt(
            np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        ) * np.sqrt(252)

        # Calculate Sharpe ratio
        sharpe_ratio = (
            (expected_return - self.risk_free_rate) / expected_risk
            if expected_risk > 0
            else 0
        )

        return float(expected_return), float(expected_risk), float(sharpe_ratio)

    def _calculate_rebalance_trades(
        self,
        user_id: int,
        portfolio_id: int,
        positions: List[Position],
        target_allocation: Dict[str, float],
    ) -> List[Trade]:
        """Calculate trades needed to rebalance to target allocation"""
        trades = []

        # Get current portfolio value
        current_positions = {p.symbol: p for p in positions}
        total_value = (
            sum(p.quantity * p.current_price for p in positions) if positions else 0
        )
        current_cash = positions[0].portfolio.cash_balance if positions else 0

        # Include cash in total portfolio value
        total_portfolio_value = total_value + current_cash

        # Calculate target value for each asset
        target_values = {
            symbol: total_portfolio_value * weight
            for symbol, weight in target_allocation.items()
        }

        # Calculate trades for existing positions
        for symbol, position in current_positions.items():
            current_value = position.quantity * position.current_price
            target_value = target_values.get(symbol, 0.0)

            # Calculate difference
            value_diff = target_value - current_value

            # Skip small changes
            if abs(value_diff) < (total_portfolio_value * 0.005):  # 0.5% threshold
                continue

            # Calculate quantity based on current price
            current_price = position.current_price
            if current_price <= 0:
                continue  # Skip if price is invalid

            quantity = abs(value_diff / current_price)

            # Create trade
            if quantity >= 0.01:  # Minimum quantity threshold
                trade = Trade(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    price=current_price,
                    trade_type="buy" if value_diff > 0 else "sell",
                    order_type=OrderType.MARKET,
                    status=TradeStatus.PENDING,
                    total_amount=quantity * current_price,
                )
                trades.append(trade)

        # Calculate trades for new positions (not currently held)
        for symbol, target_value in target_values.items():
            if symbol in current_positions:
                continue  # Already handled

            # Skip small allocations
            if target_value < (total_portfolio_value * 0.01):  # 1% threshold
                continue

            # Get current price from market data
            current_price = self._get_current_price(symbol)
            if not current_price or current_price <= 0:
                continue  # Skip if price is invalid

            quantity = target_value / current_price

            # Create trade for new position
            if quantity >= 0.01:  # Minimum quantity threshold
                trade = Trade(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    price=current_price,
                    trade_type="buy",
                    order_type=OrderType.MARKET,
                    status=TradeStatus.PENDING,
                    total_amount=quantity * current_price,
                )
                trades.append(trade)

        return trades

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if self.market_data:
                quote = self.market_data.get_quote(symbol)
                if quote and "price" in quote:
                    return quote["price"]
            return 100.0  # Fallback price for testing
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {str(e)}")
            return None

    def _get_cached_result(self, key: str) -> Optional[PortfolioOptimizationResult]:
        """Get cached optimization result"""
        if not self.redis:
            return None

        try:
            # Try to get from cache
            cached_data = self.redis.get(key)
            if cached_data:
                # Deserialize from JSON
                return eval(cached_data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")

        return None

    def _cache_result(self, key: str, result: PortfolioOptimizationResult) -> bool:
        """Cache optimization result"""
        if not self.redis:
            return False

        try:
            # Serialize to JSON-compatible string representation
            # Note: This is a simplified approach; in production you'd use proper serialization
            self.redis.setex(key, self.OPTIMIZATION_CACHE_TTL, str(result))
            return True
        except Exception as e:
            logger.error(f"Error writing to cache: {str(e)}")
            return False
