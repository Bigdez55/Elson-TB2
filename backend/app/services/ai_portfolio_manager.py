from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import redis
from app.core.logging_config import (
    log_ai_operation,
    log_system_error,
)
import uuid

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.market_data import MarketDataService
from app.services.neural_network import NeuralNetworkService
from app.services.market_data_processor import MarketDataProcessor
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.trade import Trade, TradeType, OrderType, TradeStatus
from app.models.user import User

logger = logging.getLogger(__name__)

# Redis connection for caching
try:
    redis_client = (
        redis.Redis.from_url(settings.REDIS_URL)
        if hasattr(settings, "REDIS_URL")
        else None
    )
except (redis.ConnectionError, redis.TimeoutError, AttributeError):
    redis_client = None


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods available."""

    EFFICIENT_FRONTIER = "efficient_frontier"
    BLACK_LITTERMAN = "black_litterman"
    RISK_PARITY = "risk_parity"
    ML_ENHANCED = "ml_enhanced"


class MarketTimingSignal(str, Enum):
    """Market timing signals."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class PortfolioOptimizationResult:
    """Results from portfolio optimization."""

    user_id: int
    method: OptimizationMethod
    target_allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    trade_recommendations: List[Dict[str, Any]]
    confidence_score: float
    optimization_timestamp: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["optimization_timestamp"] = self.optimization_timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioOptimizationResult":
        """Create from dictionary."""
        data["optimization_timestamp"] = datetime.fromisoformat(
            data["optimization_timestamp"]
        )
        data["method"] = OptimizationMethod(data["method"])
        return cls(**data)


@dataclass
class MarketTimingResult:
    """Market timing signal result."""

    symbol: str
    signal: MarketTimingSignal
    confidence: float
    recommendation: str
    technical_indicators: Dict[str, float]
    ml_prediction: float
    optimal_time_window: Tuple[datetime, datetime]
    metadata: Dict[str, Any]


class AIPortfolioManager:
    """
    Advanced AI-driven portfolio management service.

    Provides sophisticated portfolio optimization using multiple algorithms:
    - Efficient Frontier (Modern Portfolio Theory)
    - Black-Litterman Model
    - Risk Parity
    - ML-Enhanced optimization

    Includes market timing capabilities and automated rebalancing.
    """

    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService()
        self.neural_network_service = NeuralNetworkService()
        self.market_data_processor = MarketDataProcessor()

        # Configuration
        self.risk_free_rate = getattr(settings, "RISK_FREE_RATE", 0.02)
        self.min_allocation = getattr(settings, "MIN_ALLOCATION_PCT", 0.05)
        self.max_allocation = getattr(settings, "MAX_ALLOCATION_PCT", 0.30)
        self.min_trade_impact = getattr(settings, "MIN_TRADE_IMPACT_PCT", 0.02)
        self.cache_ttl = getattr(settings, "OPTIMIZATION_CACHE_TTL", 3600)

        # Market timing configuration
        self.timing_enabled = getattr(settings, "MARKET_TIMING_ENABLED", True)
        self.lookback_days = getattr(settings, "TIMING_SIGNAL_LOOKBACK_DAYS", 120)
        self.prediction_horizon = getattr(settings, "TIMING_PREDICTION_HORIZON_DAYS", 7)

    async def optimize_portfolio(
        self,
        user_id: int,
        method: OptimizationMethod = OptimizationMethod.EFFICIENT_FRONTIER,
        risk_tolerance: float = 0.5,
        symbols: Optional[List[str]] = None,
    ) -> PortfolioOptimizationResult:
        """
        Optimize portfolio using the specified method.

        Args:
            user_id: User ID for portfolio optimization
            method: Optimization method to use
            risk_tolerance: Risk tolerance (0.0 = conservative, 1.0 = aggressive)
            symbols: Optional list of symbols to include (uses current holdings if None)

        Returns:
            PortfolioOptimizationResult with target allocation and recommendations
        """
        try:
            # Check cache first
            cache_key = (
                f"ai_portfolio_manager:optimize:{user_id}:{method}:{risk_tolerance}"
            )
            if redis_client:
                try:
                    cached_result = redis_client.get(cache_key)
                    if cached_result:
                        data = json.loads(cached_result)
                        logger.info(
                            f"Returning cached optimization result for user {user_id}"
                        )
                        return PortfolioOptimizationResult.from_dict(data)
                except Exception as e:
                    logger.warning(f"Cache retrieval error: {e}")

            # Get user portfolio and current holdings
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            if not portfolio:
                raise ValueError(f"No portfolio found for user {user_id}")

            # Get symbols to optimize
            if symbols is None:
                holdings = (
                    self.db.query(Holding)
                    .filter(Holding.portfolio_id == portfolio.id)
                    .all()
                )
                symbols = [h.symbol for h in holdings if h.quantity > 0]

            if not symbols:
                raise ValueError("No symbols available for optimization")

            # Get historical data for optimization
            historical_data = await self._get_historical_data(
                symbols, self.lookback_days
            )

            # Calculate returns matrix
            returns_df = self._calculate_returns(historical_data)

            # Choose optimization method
            if method == OptimizationMethod.EFFICIENT_FRONTIER:
                target_allocation = await self._optimize_efficient_frontier(
                    returns_df, risk_tolerance
                )
            elif method == OptimizationMethod.BLACK_LITTERMAN:
                target_allocation = await self._optimize_black_litterman(
                    returns_df, symbols
                )
            elif method == OptimizationMethod.RISK_PARITY:
                target_allocation = await self._optimize_risk_parity(returns_df)
            elif method == OptimizationMethod.ML_ENHANCED:
                target_allocation = await self._optimize_ml_enhanced(
                    returns_df, symbols, risk_tolerance
                )
            else:
                raise ValueError(f"Unknown optimization method: {method}")

            # Calculate expected metrics
            (
                expected_return,
                expected_risk,
                sharpe_ratio,
            ) = self._calculate_portfolio_metrics(target_allocation, returns_df)

            # Generate trade recommendations
            trade_recommendations = await self._generate_trade_recommendations(
                portfolio, target_allocation
            )

            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(
                target_allocation, returns_df, method
            )

            # Create result
            result = PortfolioOptimizationResult(
                user_id=user_id,
                method=method,
                target_allocation=target_allocation,
                expected_return=expected_return,
                expected_risk=expected_risk,
                sharpe_ratio=sharpe_ratio,
                trade_recommendations=trade_recommendations,
                confidence_score=confidence_score,
                optimization_timestamp=datetime.utcnow(),
                metadata={
                    "risk_tolerance": risk_tolerance,
                    "symbols_count": len(symbols),
                    "lookback_days": self.lookback_days,
                    "optimization_constraints": {
                        "min_allocation": self.min_allocation,
                        "max_allocation": self.max_allocation,
                    },
                },
            )

            # Cache the result
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key, self.cache_ttl, json.dumps(result.to_dict())
                    )
                except Exception as e:
                    logger.warning(f"Cache storage error: {e}")

            # Enhanced AI operation logging
            log_ai_operation(
                operation="portfolio_optimization",
                model_type=method.value,
                confidence=confidence_score,
                execution_time=(
                    datetime.utcnow() - result.optimization_timestamp
                ).total_seconds(),
                user_id=user_id,
                symbols_count=len(symbols),
                expected_return=expected_return,
                expected_risk=expected_risk,
                sharpe_ratio=sharpe_ratio,
            )

            logger.info(
                f"Portfolio optimization completed for user {user_id} using {method}"
            )
            return result

        except Exception as e:
            log_system_error(
                error=e,
                context="portfolio_optimization",
                user_id=user_id,
                recovery_action="optimization_failed",
            )
            logger.error(f"Portfolio optimization failed for user {user_id}: {str(e)}")
            raise

    async def _optimize_efficient_frontier(
        self, returns_df: pd.DataFrame, risk_tolerance: float
    ) -> Dict[str, float]:
        """
        Optimize portfolio using efficient frontier (Modern Portfolio Theory).

        Maximizes risk-adjusted returns (Sharpe ratio) subject to constraints.
        """
        returns = returns_df.mean() * 252  # Annualized returns
        cov_matrix = returns_df.cov() * 252  # Annualized covariance

        n_assets = len(returns)

        # Objective function: minimize negative Sharpe ratio
        def objective(weights):
            portfolio_return = np.sum(returns * weights)
            portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_risk == 0:
                return -np.inf
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
            return -sharpe_ratio  # Minimize negative Sharpe ratio

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},  # Weights sum to 1
        ]

        # Bounds for each weight
        bounds = tuple(
            (self.min_allocation, self.max_allocation) for _ in range(n_assets)
        )

        # Initial guess (equal weights)
        initial_weights = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            logger.warning(f"Efficient frontier optimization failed: {result.message}")
            # Fall back to equal weights
            weights = initial_weights
        else:
            weights = result.x

        # Adjust for risk tolerance (0.0 = conservative, 1.0 = aggressive)
        if risk_tolerance < 0.5:
            # Make more conservative by adding cash allocation
            cash_allocation = (0.5 - risk_tolerance) * 0.4  # Up to 20% cash
            weights = weights * (1 - cash_allocation)
            weights = np.append(weights, [cash_allocation])
            symbols = list(returns_df.columns) + ["CASH"]
        else:
            symbols = list(returns_df.columns)

        return dict(zip(symbols, weights))

    async def _optimize_black_litterman(
        self, returns_df: pd.DataFrame, symbols: List[str]
    ) -> Dict[str, float]:
        """
        Optimize portfolio using Black-Litterman model with ML predictions as views.
        """
        # Market equilibrium assumptions (simplified)
        returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252

        # Get ML predictions as "views" for Black-Litterman
        ml_predictions = {}
        for symbol in symbols:
            try:
                prediction = await self.neural_network_service.predict_price(
                    symbol, days_ahead=30
                )
                if prediction:
                    # Convert price prediction to return prediction
                    current_price = await self.market_data_service.get_current_price(
                        symbol
                    )
                    if current_price:
                        expected_return = (prediction - current_price) / current_price
                        ml_predictions[symbol] = expected_return
            except Exception as e:
                logger.warning(f"Failed to get ML prediction for {symbol}: {e}")

        # If we have ML predictions, use them as views
        if ml_predictions:
            # Simplified Black-Litterman: adjust expected returns based on ML views
            adjusted_returns = returns.copy()
            confidence_factor = 0.3  # How much to trust ML predictions

            for symbol, ml_return in ml_predictions.items():
                if symbol in adjusted_returns.index:
                    # Blend historical and ML-predicted returns
                    adjusted_returns[symbol] = (
                        1 - confidence_factor
                    ) * adjusted_returns[
                        symbol
                    ] + confidence_factor * ml_return * 252  # Annualize ML prediction

            # Optimize with adjusted returns
            n_assets = len(adjusted_returns)

            def objective(weights):
                portfolio_return = np.sum(adjusted_returns * weights)
                portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                if portfolio_risk == 0:
                    return -np.inf
                return -(portfolio_return - self.risk_free_rate) / portfolio_risk

            constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
            bounds = tuple(
                (self.min_allocation, self.max_allocation) for _ in range(n_assets)
            )
            initial_weights = np.array([1.0 / n_assets] * n_assets)

            result = minimize(
                objective,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if result.success:
                return dict(zip(symbols, result.x))

        # Fall back to efficient frontier if Black-Litterman fails
        logger.warning(
            "Black-Litterman optimization failed, falling back to efficient frontier"
        )
        return await self._optimize_efficient_frontier(returns_df, 0.5)

    async def _optimize_risk_parity(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        """
        Optimize portfolio using risk parity (equal risk contribution).
        """
        cov_matrix = returns_df.cov() * 252  # Annualized covariance
        n_assets = len(returns_df.columns)

        def objective(weights):
            # Calculate risk contributions
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_contribs = np.dot(cov_matrix, weights) / portfolio_vol
            contribs = weights * marginal_contribs

            # Minimize difference from equal risk contribution
            target_contrib = portfolio_vol / n_assets
            return np.sum((contribs - target_contrib) ** 2)

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
        bounds = tuple(
            (self.min_allocation, self.max_allocation) for _ in range(n_assets)
        )

        # Start with inverse volatility weights
        vols = np.sqrt(np.diag(cov_matrix))
        initial_weights = (1 / vols) / np.sum(1 / vols)

        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if result.success:
            weights = result.x
        else:
            logger.warning(
                "Risk parity optimization failed, using inverse volatility weights"
            )
            weights = initial_weights

        return dict(zip(returns_df.columns, weights))

    async def _optimize_ml_enhanced(
        self, returns_df: pd.DataFrame, symbols: List[str], risk_tolerance: float
    ) -> Dict[str, float]:
        """
        ML-enhanced optimization combining multiple approaches.
        """
        # Get multiple optimization results
        efficient_frontier = await self._optimize_efficient_frontier(
            returns_df, risk_tolerance
        )
        risk_parity = await self._optimize_risk_parity(returns_df)

        # Get ML confidence scores for each symbol
        ml_scores = {}
        for symbol in symbols:
            try:
                # Get volatility prediction as confidence indicator
                vol_prediction = await self.neural_network_service.predict_volatility(
                    symbol
                )
                if vol_prediction:
                    # Lower predicted volatility = higher confidence
                    historical_vol = returns_df[symbol].std() * np.sqrt(252)
                    if historical_vol > 0:
                        confidence = max(0.1, 1.0 - (vol_prediction / historical_vol))
                        ml_scores[symbol] = confidence
            except Exception as e:
                logger.warning(f"Failed to get ML confidence for {symbol}: {e}")

        # Blend allocations based on ML confidence and risk tolerance
        blended_allocation = {}
        for symbol in symbols:
            ef_weight = efficient_frontier.get(symbol, 0)
            rp_weight = risk_parity.get(symbol, 0)
            ml_confidence = ml_scores.get(symbol, 0.5)

            # Higher risk tolerance = more weight to efficient frontier
            # Higher ML confidence = more weight to the symbol
            blend_factor = risk_tolerance * ml_confidence

            blended_allocation[symbol] = (
                blend_factor * ef_weight + (1 - blend_factor) * rp_weight
            )

        # Normalize to sum to 1
        total_weight = sum(blended_allocation.values())
        if total_weight > 0:
            blended_allocation = {
                k: v / total_weight for k, v in blended_allocation.items()
            }

        return blended_allocation

    def _calculate_returns(
        self, historical_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Calculate returns matrix from historical price data."""
        price_data = {}

        for symbol, df in historical_data.items():
            if not df.empty and "close" in df.columns:
                price_data[symbol] = df["close"]

        if not price_data:
            raise ValueError("No valid price data available for optimization")

        # Create aligned price dataframe
        price_df = pd.DataFrame(price_data)

        # Calculate returns
        returns_df = price_df.pct_change().dropna()

        return returns_df

    def _calculate_portfolio_metrics(
        self, allocation: Dict[str, float], returns_df: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """Calculate expected return, risk, and Sharpe ratio for allocation."""
        # Filter allocation to only include symbols in returns data
        valid_allocation = {
            k: v for k, v in allocation.items() if k in returns_df.columns
        }

        if not valid_allocation:
            return 0.0, 0.0, 0.0

        # Normalize allocation
        total_weight = sum(valid_allocation.values())
        if total_weight > 0:
            weights = np.array(
                [
                    valid_allocation[col] / total_weight
                    for col in returns_df.columns
                    if col in valid_allocation
                ]
            )
            returns = (
                returns_df[
                    [col for col in returns_df.columns if col in valid_allocation]
                ].mean()
                * 252
            )
            cov_matrix = (
                returns_df[
                    [col for col in returns_df.columns if col in valid_allocation]
                ].cov()
                * 252
            )

            expected_return = np.sum(returns * weights)
            expected_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            if expected_risk > 0:
                sharpe_ratio = (expected_return - self.risk_free_rate) / expected_risk
            else:
                sharpe_ratio = 0.0

            return expected_return, expected_risk, sharpe_ratio

        return 0.0, 0.0, 0.0

    async def _generate_trade_recommendations(
        self, portfolio: Portfolio, target_allocation: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate trade recommendations to achieve target allocation."""
        recommendations = []

        # Get current holdings
        current_holdings = (
            self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        )
        current_allocation = {}
        total_value = portfolio.total_value or 0

        for holding in current_holdings:
            if total_value > 0:
                current_allocation[holding.symbol] = holding.market_value / total_value
            else:
                current_allocation[holding.symbol] = 0

        # Calculate required trades
        for symbol, target_weight in target_allocation.items():
            if symbol == "CASH":
                continue

            current_weight = current_allocation.get(symbol, 0)
            weight_diff = target_weight - current_weight

            # Only recommend trades above minimum impact threshold
            if abs(weight_diff) >= self.min_trade_impact:
                trade_value = weight_diff * total_value

                # Get current price for quantity calculation
                try:
                    current_price = await self.market_data_service.get_current_price(
                        symbol
                    )
                    if current_price and current_price > 0:
                        quantity = abs(trade_value) / current_price

                        recommendation = {
                            "symbol": symbol,
                            "action": "BUY" if weight_diff > 0 else "SELL",
                            "quantity": quantity,
                            "estimated_price": current_price,
                            "estimated_value": abs(trade_value),
                            "current_weight": current_weight,
                            "target_weight": target_weight,
                            "weight_change": weight_diff,
                            "priority": "HIGH" if abs(weight_diff) > 0.1 else "MEDIUM",
                        }

                        recommendations.append(recommendation)

                except Exception as e:
                    logger.warning(f"Failed to get price for {symbol}: {e}")

        # Sort by absolute weight change (largest first)
        recommendations.sort(key=lambda x: abs(x["weight_change"]), reverse=True)

        return recommendations

    async def _calculate_confidence_score(
        self,
        allocation: Dict[str, float],
        returns_df: pd.DataFrame,
        method: OptimizationMethod,
    ) -> float:
        """Calculate confidence score for the optimization result."""
        base_confidence = {
            OptimizationMethod.EFFICIENT_FRONTIER: 0.7,
            OptimizationMethod.BLACK_LITTERMAN: 0.8,
            OptimizationMethod.RISK_PARITY: 0.6,
            OptimizationMethod.ML_ENHANCED: 0.9,
        }.get(method, 0.5)

        # Adjust based on data quality
        data_quality_factor = min(1.0, len(returns_df) / 252)  # Prefer more data

        # Adjust based on diversification
        diversification_factor = 1.0 - max(
            0, max(allocation.values()) - 0.5
        )  # Penalize concentration

        confidence = base_confidence * data_quality_factor * diversification_factor

        return max(0.1, min(1.0, confidence))

    async def _get_historical_data(
        self, symbols: List[str], lookback_days: int
    ) -> Dict[str, pd.DataFrame]:
        """Get historical data for all symbols."""
        historical_data = {}

        for symbol in symbols:
            try:
                data = await self.market_data_service.get_historical_data(
                    symbol, timeframe="1day", limit=lookback_days
                )

                if data:
                    df = pd.DataFrame(data)
                    if not df.empty and "timestamp" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        df.set_index("timestamp", inplace=True)
                        historical_data[symbol] = df

            except Exception as e:
                logger.warning(f"Failed to get historical data for {symbol}: {e}")

        return historical_data

    async def get_market_timing_signal(self, symbol: str) -> MarketTimingResult:
        """
        Get market timing signal for a specific symbol.

        Combines technical analysis with ML predictions to generate timing signals.
        """
        try:
            # Check cache first
            cache_key = f"market_timing:{symbol}:{self.prediction_horizon}"
            if redis_client:
                try:
                    cached_result = redis_client.get(cache_key)
                    if cached_result:
                        data = json.loads(cached_result)
                        return MarketTimingResult(**data)
                except Exception as e:
                    logger.warning(f"Cache retrieval error for timing signal: {e}")

            # Get technical indicators
            technical_data = await self.market_data_processor.get_technical_indicators(
                symbol, timeframe="1day"
            )

            # Get ML prediction
            ml_prediction = await self.neural_network_service.predict_price(
                symbol, days_ahead=self.prediction_horizon
            )
            current_price = await self.market_data_service.get_current_price(symbol)

            # Calculate ML signal strength
            ml_signal_strength = 0.0
            if ml_prediction and current_price:
                price_change_pct = (ml_prediction - current_price) / current_price
                ml_signal_strength = np.tanh(price_change_pct * 5)  # Scale to [-1, 1]

            # Combine technical and ML signals
            technical_score = self._calculate_technical_score(technical_data)
            combined_score = 0.6 * technical_score + 0.4 * ml_signal_strength

            # Generate signal and confidence
            if combined_score > 0.5:
                signal = (
                    MarketTimingSignal.STRONG_BUY
                    if combined_score > 0.8
                    else MarketTimingSignal.BUY
                )
            elif combined_score < -0.5:
                signal = (
                    MarketTimingSignal.STRONG_SELL
                    if combined_score < -0.8
                    else MarketTimingSignal.SELL
                )
            else:
                signal = MarketTimingSignal.HOLD

            confidence = abs(combined_score)

            # Calculate optimal time window
            now = datetime.utcnow()
            optimal_start = now + timedelta(hours=6)  # Wait for market open
            optimal_end = now + timedelta(days=self.prediction_horizon)

            result = MarketTimingResult(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                recommendation=self._generate_timing_recommendation(signal, confidence),
                technical_indicators=technical_data or {},
                ml_prediction=ml_prediction or 0.0,
                optimal_time_window=(optimal_start, optimal_end),
                metadata={
                    "technical_score": technical_score,
                    "ml_signal_strength": ml_signal_strength,
                    "combined_score": combined_score,
                    "current_price": current_price,
                },
            )

            # Cache the result
            if redis_client:
                try:
                    # Convert datetime objects to strings for JSON serialization
                    cache_data = {
                        "symbol": result.symbol,
                        "signal": result.signal.value,
                        "confidence": result.confidence,
                        "recommendation": result.recommendation,
                        "technical_indicators": result.technical_indicators,
                        "ml_prediction": result.ml_prediction,
                        "optimal_time_window": [
                            result.optimal_time_window[0].isoformat(),
                            result.optimal_time_window[1].isoformat(),
                        ],
                        "metadata": result.metadata,
                    }
                    redis_client.setex(
                        cache_key, 300, json.dumps(cache_data)
                    )  # 5 minute TTL
                except Exception as e:
                    logger.warning(f"Cache storage error for timing signal: {e}")

            return result

        except Exception as e:
            logger.error(f"Failed to generate market timing signal for {symbol}: {e}")
            # Return neutral signal on error
            return MarketTimingResult(
                symbol=symbol,
                signal=MarketTimingSignal.HOLD,
                confidence=0.0,
                recommendation="Unable to generate timing signal",
                technical_indicators={},
                ml_prediction=0.0,
                optimal_time_window=(
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(days=1),
                ),
                metadata={"error": str(e)},
            )

    def _calculate_technical_score(
        self, technical_data: Optional[Dict[str, float]]
    ) -> float:
        """Calculate technical analysis score (-1 to 1)."""
        if not technical_data:
            return 0.0

        score = 0.0
        indicators_count = 0

        # RSI signal
        rsi = technical_data.get("rsi")
        if rsi is not None:
            if rsi < 30:
                score += 0.5  # Oversold, bullish
            elif rsi > 70:
                score -= 0.5  # Overbought, bearish
            indicators_count += 1

        # MACD signal
        macd = technical_data.get("macd")
        macd_signal = technical_data.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 0.3  # Bullish crossover
            else:
                score -= 0.3  # Bearish crossover
            indicators_count += 1

        # Bollinger Bands signal
        bb_upper = technical_data.get("bb_upper")
        bb_lower = technical_data.get("bb_lower")
        current_price = technical_data.get("close")
        if bb_upper and bb_lower and current_price:
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            if bb_position < 0.2:
                score += 0.2  # Near lower band, potential reversal
            elif bb_position > 0.8:
                score -= 0.2  # Near upper band, potential reversal
            indicators_count += 1

        return score / max(1, indicators_count) if indicators_count > 0 else 0.0

    def _generate_timing_recommendation(
        self, signal: MarketTimingSignal, confidence: float
    ) -> str:
        """Generate human-readable timing recommendation."""
        confidence_level = (
            "High" if confidence > 0.7 else "Medium" if confidence > 0.4 else "Low"
        )

        recommendations = {
            MarketTimingSignal.STRONG_BUY: f"Strong buy signal with {confidence_level.lower()} confidence. Consider increasing position size.",
            MarketTimingSignal.BUY: f"Buy signal with {confidence_level.lower()} confidence. Good entry opportunity.",
            MarketTimingSignal.HOLD: f"Hold signal with {confidence_level.lower()} confidence. Wait for clearer signals.",
            MarketTimingSignal.SELL: f"Sell signal with {confidence_level.lower()} confidence. Consider reducing position.",
            MarketTimingSignal.STRONG_SELL: f"Strong sell signal with {confidence_level.lower()} confidence. Consider exiting position.",
        }

        return recommendations.get(signal, "No clear timing signal available.")

    async def schedule_portfolio_optimization(
        self,
        user_id: int,
        method: OptimizationMethod = OptimizationMethod.EFFICIENT_FRONTIER,
        frequency_days: int = 7,
    ) -> bool:
        """
        Schedule recurring portfolio optimization.

        This would typically integrate with a task queue system like Celery.
        For now, we'll just log the scheduling request.
        """
        try:
            # Check minimum rebalance interval
            min_interval = getattr(settings, "MIN_REBALANCE_INTERVAL_DAYS", 7)
            if frequency_days < min_interval:
                raise ValueError(f"Minimum rebalance interval is {min_interval} days")

            # In a production system, this would create a scheduled task
            logger.info(
                f"Portfolio optimization scheduled for user {user_id} using {method} every {frequency_days} days"
            )

            # Store scheduling preference in user metadata (if user model supports it)
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                # This would require extending the User model with metadata field
                # user.metadata = user.metadata or {}
                # user.metadata['auto_rebalance'] = {
                #     'enabled': True,
                #     'method': method.value,
                #     'frequency_days': frequency_days,
                #     'last_scheduled': datetime.utcnow().isoformat()
                # }
                # self.db.commit()
                pass

            return True

        except Exception as e:
            logger.error(
                f"Failed to schedule portfolio optimization for user {user_id}: {e}"
            )
            return False

    async def execute_ai_rebalance(
        self,
        user_id: int,
        optimization_result: PortfolioOptimizationResult,
        dry_run: bool = True,
    ) -> List[str]:
        """
        Execute portfolio rebalancing based on optimization result.

        Args:
            user_id: User ID
            optimization_result: Result from portfolio optimization
            dry_run: If True, only simulate trades without executing

        Returns:
            List of trade IDs created
        """
        try:
            trade_ids = []

            # Check if market timing suggests good execution time
            if self.timing_enabled:
                # For major rebalancing, check market timing for each symbol
                timing_signals = {}
                for recommendation in optimization_result.trade_recommendations:
                    symbol = recommendation["symbol"]
                    timing = await self.get_market_timing_signal(symbol)
                    timing_signals[symbol] = timing

                # If majority of signals are negative, consider delaying
                negative_signals = sum(
                    1
                    for signal in timing_signals.values()
                    if signal.signal
                    in [MarketTimingSignal.SELL, MarketTimingSignal.STRONG_SELL]
                )

                if negative_signals > len(timing_signals) * 0.6:
                    logger.warning(
                        f"Market timing suggests delaying rebalance for user {user_id}"
                    )
                    if not dry_run:
                        return []  # Don't execute in poor market conditions

            # Execute trades based on recommendations
            max_trades = getattr(settings, "MAX_TRADES_PER_REBALANCE", 20)
            executed_trades = 0

            for recommendation in optimization_result.trade_recommendations:
                if executed_trades >= max_trades:
                    logger.warning(
                        f"Maximum trades per rebalance ({max_trades}) reached for user {user_id}"
                    )
                    break

                if recommendation["priority"] in ["HIGH", "MEDIUM"]:
                    trade_id = await self._create_rebalance_trade(
                        user_id, recommendation, optimization_result, dry_run
                    )

                    if trade_id:
                        trade_ids.append(trade_id)
                        executed_trades += 1

            logger.info(
                f"AI rebalance {'simulated' if dry_run else 'executed'} for user {user_id}: {len(trade_ids)} trades"
            )
            return trade_ids

        except Exception as e:
            logger.error(f"Failed to execute AI rebalance for user {user_id}: {e}")
            return []

    async def _create_rebalance_trade(
        self,
        user_id: int,
        recommendation: Dict[str, Any],
        optimization_result: PortfolioOptimizationResult,
        dry_run: bool,
    ) -> Optional[str]:
        """Create a trade for portfolio rebalancing."""
        try:
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            if not portfolio:
                return None

            trade_id = str(uuid.uuid4())

            # Create trade record
            trade = Trade(
                id=trade_id,
                symbol=recommendation["symbol"],
                trade_type=TradeType.BUY
                if recommendation["action"] == "BUY"
                else TradeType.SELL,
                side=TradeType.BUY
                if recommendation["action"] == "BUY"
                else TradeType.SELL,
                order_type=OrderType.MARKET,  # Use market orders for rebalancing
                quantity=recommendation["quantity"],
                portfolio_id=portfolio.id,
                status=TradeStatus.PENDING,
                strategy="ai_rebalancing",
                notes=f"AI rebalancing using {optimization_result.method.value}",
                is_paper_trade=dry_run,
                # Add metadata if Trade model supports it
                # metadata={
                #     'optimization_method': optimization_result.method.value,
                #     'target_weight': recommendation['target_weight'],
                #     'current_weight': recommendation['current_weight'],
                #     'confidence_score': optimization_result.confidence_score
                # }
            )

            if not dry_run:
                self.db.add(trade)
                self.db.commit()
                self.db.refresh(trade)

            logger.info(
                f"{'Simulated' if dry_run else 'Created'} rebalance trade {trade_id} for {recommendation['symbol']}"
            )
            return trade_id

        except Exception as e:
            logger.error(f"Failed to create rebalance trade: {e}")
            return None
