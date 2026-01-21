import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ...models.holding import Position
from ...models.portfolio import Portfolio
from ...models.trade import Trade
from ...services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class RiskManager:
    """
    The RiskManager handles all aspects of risk management for the trading system.
    This includes position sizing, correlation analysis, drawdown monitoring,
    and overall portfolio risk assessment.
    """

    def __init__(
        self,
        market_data_service: MarketDataService,
        max_position_size: float = 0.1,  # 10% of portfolio
        max_correlation: float = 0.7,
        max_daily_drawdown: float = 0.02,  # 2% daily drawdown limit
        max_total_drawdown: float = 0.1,  # 10% total drawdown limit
        risk_free_rate: float = 0.02,  # 2% annual risk-free rate
    ):
        self.market_data_service = market_data_service
        self.max_position_size = max_position_size
        self.max_correlation = max_correlation
        self.max_daily_drawdown = max_daily_drawdown
        self.max_total_drawdown = max_total_drawdown
        self.risk_free_rate = risk_free_rate

        # Risk metrics tracking
        self.portfolio_metrics = {}
        self.position_metrics = {}

    async def check_portfolio_risk(self, portfolio: Portfolio) -> Dict:
        """
        Perform comprehensive portfolio risk analysis and return risk metrics.
        """
        try:
            # Calculate current portfolio metrics
            metrics = await self._calculate_portfolio_metrics(portfolio)

            # Check risk limits
            risk_status = {"within_limits": True, "warnings": [], "metrics": metrics}

            # Check position concentration
            for position in portfolio.positions_detail:
                position_size = position.quantity * position.current_price
                position_pct = position_size / portfolio.total_value

                if position_pct > self.max_position_size:
                    risk_status["within_limits"] = False
                    risk_status["warnings"].append(
                        f"Position {position.symbol} exceeds maximum size"
                    )

            # Check drawdown limits
            if metrics["daily_drawdown"] > self.max_daily_drawdown:
                risk_status["within_limits"] = False
                risk_status["warnings"].append("Daily drawdown limit exceeded")

            if metrics["max_drawdown"] > self.max_total_drawdown:
                risk_status["within_limits"] = False
                risk_status["warnings"].append("Total drawdown limit exceeded")

            # Update tracking metrics
            self.portfolio_metrics = metrics

            return risk_status

        except Exception as e:
            logger.error(f"Error checking portfolio risk: {str(e)}")
            return {"within_limits": False, "warnings": [str(e)], "metrics": {}}

    async def calculate_position_size(
        self, portfolio: Portfolio, symbol: str, signal_strength: float
    ) -> Optional[float]:
        """
        Calculate appropriate position size based on portfolio value,
        current risk levels, and signal strength.
        """
        try:
            # Get current portfolio metrics
            metrics = self.portfolio_metrics or await self._calculate_portfolio_metrics(
                portfolio
            )

            # Base position size on portfolio value and max position size
            max_position_value = portfolio.total_value * self.max_position_size

            # Adjust based on current portfolio risk
            risk_adjustment = self._calculate_risk_adjustment(metrics)

            # Adjust based on signal strength (0 to 1)
            signal_adjustment = max(0.1, min(1.0, abs(signal_strength)))

            # Calculate final position size
            quote = await self.market_data_service.get_quote(symbol)
            price = Decimal(str(quote["price"]))

            position_value = (
                max_position_value
                * Decimal(str(risk_adjustment))
                * Decimal(str(signal_adjustment))
            )

            quantity = position_value / price
            return float(quantity)

        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return None

    def _calculate_risk_adjustment(self, metrics: Dict) -> float:
        """
        Calculate risk adjustment factor based on current portfolio metrics.
        """
        try:
            # Start with base factor
            adjustment = 1.0

            # Adjust based on volatility
            vol_ratio = metrics["current_volatility"] / metrics["historical_volatility"]
            if vol_ratio > 1:
                adjustment *= 1 / vol_ratio

            # Adjust based on drawdown
            drawdown_ratio = metrics["current_drawdown"] / self.max_total_drawdown
            adjustment *= 1 - drawdown_ratio

            # Adjust based on Sharpe ratio
            if metrics["sharpe_ratio"] < 1:
                adjustment *= metrics["sharpe_ratio"]

            return max(0.1, min(1.0, adjustment))

        except Exception as e:
            logger.error(f"Error calculating risk adjustment: {str(e)}")
            return 0.5

    async def _calculate_portfolio_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            # Get historical data for all positions
            position_returns = {}
            for position in portfolio.positions_detail:
                data = await self.market_data_service.get_historical_data(
                    position.symbol, start_date=datetime.now() - timedelta(days=252)
                )
                position_returns[position.symbol] = data["Close"].pct_change().dropna()

            # Calculate portfolio returns
            portfolio_returns = self._calculate_weighted_returns(
                position_returns, portfolio
            )

            # Calculate risk metrics
            volatility = float(portfolio_returns.std() * np.sqrt(252))  # Annualized
            sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)
            var = self._calculate_value_at_risk(portfolio_returns)

            return {
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "value_at_risk": var,
                "correlations": self._calculate_correlations(position_returns),
                "beta": self._calculate_portfolio_beta(position_returns, portfolio),
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
            return {}

    def _calculate_weighted_returns(
        self, position_returns: Dict[str, pd.Series], portfolio: Portfolio
    ) -> pd.Series:
        """Calculate weighted portfolio returns"""
        weights = {}
        for position in portfolio.positions_detail:
            weights[position.symbol] = (
                position.quantity * position.current_price / portfolio.total_value
            )

        weighted_returns = pd.Series(
            0, index=next(iter(position_returns.values())).index
        )
        for symbol, returns in position_returns.items():
            weighted_returns += returns * weights.get(symbol, 0)

        return weighted_returns

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate the Sharpe ratio"""
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        return float(np.sqrt(252) * excess_returns.mean() / excess_returns.std())

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.expanding().max()
        drawdowns = cum_returns / rolling_max - 1
        return float(drawdowns.min())

    def _calculate_value_at_risk(
        self, returns: pd.Series, confidence: float = 0.95
    ) -> float:
        """Calculate Value at Risk"""
        return float(np.percentile(returns, (1 - confidence) * 100))

    def _calculate_correlations(self, position_returns: Dict[str, pd.Series]) -> Dict:
        """Calculate correlation matrix between positions"""
        if not position_returns:
            return {}

        returns_df = pd.DataFrame(position_returns)
        correlation_matrix = returns_df.corr()

        return correlation_matrix.to_dict()

    async def _calculate_portfolio_beta(
        self, position_returns: Dict[str, pd.Series], portfolio: Portfolio
    ) -> float:
        """Calculate portfolio beta"""
        try:
            # Get market returns (using S&P 500 as proxy)
            market_data = await self.market_data_service.get_historical_data(
                "SPY", start_date=datetime.now() - timedelta(days=252)
            )
            market_returns = market_data["Close"].pct_change().dropna()

            # Calculate weighted portfolio returns
            portfolio_returns = self._calculate_weighted_returns(
                position_returns, portfolio
            )

            # Calculate beta
            covariance = np.cov(portfolio_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)

            return float(covariance / market_variance)

        except Exception as e:
            logger.error(f"Error calculating portfolio beta: {str(e)}")
            return 1.0

    async def check_correlation_limits(
        self, new_symbol: str, portfolio: Portfolio
    ) -> bool:
        """Check if adding a new position would exceed correlation limits"""
        try:
            # Get returns for existing positions and new symbol
            position_returns = {}
            for position in portfolio.positions_detail:
                data = await self.market_data_service.get_historical_data(
                    position.symbol, start_date=datetime.now() - timedelta(days=252)
                )
                position_returns[position.symbol] = data["Close"].pct_change().dropna()

            # Add new symbol
            new_data = await self.market_data_service.get_historical_data(
                new_symbol, start_date=datetime.now() - timedelta(days=252)
            )
            new_returns = new_data["Close"].pct_change().dropna()

            # Calculate correlations
            for symbol, returns in position_returns.items():
                correlation = returns.corr(new_returns)
                if abs(correlation) > self.max_correlation:
                    logger.warning(
                        f"High correlation ({correlation:.2f}) between {symbol} and {new_symbol}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking correlation limits: {str(e)}")
            return False

    def get_risk_report(self, portfolio: Portfolio) -> Dict:
        """Generate comprehensive risk report"""
        try:
            metrics = self.portfolio_metrics

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_value": float(portfolio.total_value),
                "risk_metrics": {
                    "volatility": metrics.get("volatility", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "value_at_risk": metrics.get("value_at_risk", 0),
                    "beta": metrics.get("beta", 1.0),
                },
                "position_metrics": self.position_metrics,
                "risk_limits": {
                    "max_position_size": self.max_position_size,
                    "max_correlation": self.max_correlation,
                    "max_daily_drawdown": self.max_daily_drawdown,
                    "max_total_drawdown": self.max_total_drawdown,
                },
                "warnings": self._generate_risk_warnings(portfolio, metrics),
            }

        except Exception as e:
            logger.error(f"Error generating risk report: {str(e)}")
            return {}
