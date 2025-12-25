"""
Portfolio Optimization Service for Personal Trading Platform

Advanced portfolio optimization using Modern Portfolio Theory,
risk management, and personalized rebalancing strategies.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import structlog
from scipy.optimize import minimize
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.services.enhanced_market_data import enhanced_market_data_service

logger = structlog.get_logger()


class PortfolioOptimizer:
    """
    Advanced portfolio optimization for personal trading.

    Implements Modern Portfolio Theory with personal risk preferences
    and practical constraints.
    """

    def __init__(self):
        self.risk_free_rate = 0.02  # 2% risk-free rate assumption
        self.trading_cost = 0.001  # 0.1% trading cost assumption

    async def analyze_portfolio_performance(self, portfolio: Portfolio, db: Session) -> Dict[str, Any]:
        """
        Comprehensive portfolio performance analysis.

        Args:
            portfolio: Portfolio to analyze
            db: Database session

        Returns:
            Detailed performance metrics and analysis
        """
        try:
            holdings = portfolio.holdings
            if not holdings:
                return {"error": "No holdings to analyze"}

            # Get historical data for all holdings
            symbols = [h.symbol for h in holdings]
            historical_data = {}

            for symbol in symbols:
                data = await enhanced_market_data_service.get_historical_data(symbol, period="1y")
                if data:
                    historical_data[symbol] = data

            if not historical_data:
                return {"error": "Unable to retrieve historical data"}

            # Calculate portfolio metrics
            performance_metrics = await self._calculate_performance_metrics(portfolio, historical_data)

            # Risk analysis
            risk_metrics = await self._calculate_risk_metrics(portfolio, historical_data)

            # Diversification analysis
            diversification_metrics = self._calculate_diversification_metrics(portfolio)

            # Generate recommendations
            recommendations = await self._generate_performance_recommendations(
                portfolio, performance_metrics, risk_metrics
            )

            return {
                "portfolio_id": portfolio.id,
                "portfolio_name": portfolio.name,
                "analysis_date": datetime.utcnow().isoformat(),
                "total_value": portfolio.total_value,
                "performance": performance_metrics,
                "risk": risk_metrics,
                "diversification": diversification_metrics,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error("Error in portfolio performance analysis", error=str(e))
            return {"error": "Failed to analyze portfolio performance"}

    async def optimize_allocation(
        self,
        portfolio: Portfolio,
        target_return: Optional[float] = None,
        max_risk: Optional[float] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using Modern Portfolio Theory.

        Args:
            portfolio: Portfolio to optimize
            target_return: Target annual return (optional)
            max_risk: Maximum acceptable volatility (optional)
            user_preferences: User preferences and constraints

        Returns:
            Optimal allocation recommendations
        """
        try:
            holdings = portfolio.holdings
            if len(holdings) < 2:
                return {
                    "error": "Need at least 2 holdings for optimization",
                    "recommendation": "Add more holdings to enable optimization",
                }

            # Get historical data for covariance matrix
            symbols = [h.symbol for h in holdings]
            returns_data = await self._get_returns_data(symbols)

            if not returns_data or len(returns_data.columns) < 2:
                return {"error": "Insufficient data for optimization"}

            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean() * 252  # Annualized
            cov_matrix = returns_data.cov() * 252  # Annualized

            # Current allocations
            total_value = sum(h.market_value for h in holdings)
            current_weights = np.array([h.market_value / total_value for h in holdings])

            # Optimization constraints
            constraints = self._build_optimization_constraints(len(holdings), user_preferences)

            # Objective function (maximize Sharpe ratio or minimize risk)
            if target_return:
                # Minimize risk for target return
                optimal_weights = self._minimize_risk_for_return(
                    expected_returns, cov_matrix, target_return, constraints
                )
                optimization_type = "risk_minimization"
            else:
                # Maximize Sharpe ratio
                optimal_weights = self._maximize_sharpe_ratio(expected_returns, cov_matrix, constraints)
                optimization_type = "sharpe_maximization"

            if optimal_weights is None:
                return {"error": "Optimization failed to converge"}

            # Calculate rebalancing actions
            rebalancing_actions = self._calculate_rebalancing_actions(
                holdings, current_weights, optimal_weights, total_value
            )

            # Calculate expected portfolio metrics
            portfolio_return = np.dot(optimal_weights, expected_returns)
            portfolio_risk = np.sqrt(np.dot(optimal_weights, np.dot(cov_matrix, optimal_weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk

            return {
                "optimization_type": optimization_type,
                "portfolio_metrics": {
                    "expected_return": round(portfolio_return * 100, 2),
                    "expected_risk": round(portfolio_risk * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 3),
                },
                "current_allocation": {symbols[i]: round(current_weights[i] * 100, 2) for i in range(len(symbols))},
                "optimal_allocation": {symbols[i]: round(optimal_weights[i] * 100, 2) for i in range(len(symbols))},
                "rebalancing_actions": rebalancing_actions,
                "total_rebalancing_cost": sum(action["cost"] for action in rebalancing_actions),
                "optimization_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error in portfolio optimization", error=str(e))
            return {"error": "Failed to optimize portfolio allocation"}

    async def generate_rebalancing_plan(self, portfolio: Portfolio, threshold: float = 0.05) -> Dict[str, Any]:
        """
        Generate automatic rebalancing plan based on target allocations.

        Args:
            portfolio: Portfolio to rebalance
            threshold: Rebalancing threshold (default 5%)

        Returns:
            Rebalancing plan with specific actions
        """
        try:
            holdings = portfolio.holdings
            if not holdings:
                return {"error": "No holdings to rebalance"}

            total_value = sum(h.market_value for h in holdings)

            rebalancing_needed = []
            for holding in holdings:
                current_allocation = holding.market_value / total_value
                target_allocation = holding.target_allocation_percentage or 0

                if target_allocation > 0:
                    deviation = abs(current_allocation - target_allocation / 100)

                    if deviation > threshold:
                        action_type = "BUY" if current_allocation < target_allocation / 100 else "SELL"

                        target_value = total_value * (target_allocation / 100)
                        amount_needed = abs(target_value - holding.market_value)

                        rebalancing_needed.append(
                            {
                                "symbol": holding.symbol,
                                "action": action_type,
                                "current_allocation": round(current_allocation * 100, 2),
                                "target_allocation": target_allocation,
                                "deviation": round(deviation * 100, 2),
                                "current_value": holding.market_value,
                                "target_value": round(target_value, 2),
                                "amount_needed": round(amount_needed, 2),
                                "shares_to_trade": round(amount_needed / holding.current_price, 4)
                                if holding.current_price > 0
                                else 0,
                            }
                        )

            # Calculate total trading costs
            total_cost = sum(action["amount_needed"] * self.trading_cost for action in rebalancing_needed)

            return {
                "rebalancing_needed": len(rebalancing_needed) > 0,
                "threshold_used": threshold * 100,
                "total_portfolio_value": total_value,
                "actions": rebalancing_needed,
                "estimated_cost": round(total_cost, 2),
                "cost_percentage": round(total_cost / total_value * 100, 4),
                "plan_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error generating rebalancing plan", error=str(e))
            return {"error": "Failed to generate rebalancing plan"}

    async def suggest_diversification_improvements(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Suggest improvements to portfolio diversification.

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Diversification analysis and improvement suggestions
        """
        try:
            holdings = portfolio.holdings
            if not holdings:
                return {"error": "No holdings to analyze"}

            # Asset type analysis
            asset_types = {}
            for holding in holdings:
                asset_type = holding.asset_type
                if asset_type not in asset_types:
                    asset_types[asset_type] = {
                        "count": 0,
                        "total_value": 0,
                        "symbols": [],
                    }
                asset_types[asset_type]["count"] += 1
                asset_types[asset_type]["total_value"] += holding.market_value
                asset_types[asset_type]["symbols"].append(holding.symbol)

            total_value = sum(h.market_value for h in holdings)

            # Calculate asset type allocations
            for asset_type in asset_types:
                asset_types[asset_type]["allocation"] = asset_types[asset_type]["total_value"] / total_value * 100

            # Concentration analysis
            concentrations = []
            for holding in holdings:
                allocation = holding.market_value / total_value
                if allocation > 0.25:  # More than 25%
                    concentrations.append(
                        {
                            "symbol": holding.symbol,
                            "allocation": round(allocation * 100, 2),
                            "value": holding.market_value,
                            "risk_level": "high",
                        }
                    )
                elif allocation > 0.15:  # More than 15%
                    concentrations.append(
                        {
                            "symbol": holding.symbol,
                            "allocation": round(allocation * 100, 2),
                            "value": holding.market_value,
                            "risk_level": "medium",
                        }
                    )

            # Generate suggestions
            suggestions = []

            # Asset type diversification
            if len(asset_types) < 3:
                suggestions.append(
                    {
                        "type": "asset_diversification",
                        "priority": "high",
                        "description": "Consider adding different asset types",
                        "recommendation": "Add bonds, REITs, or international stocks",
                    }
                )

            # Concentration risk
            if concentrations:
                suggestions.append(
                    {
                        "type": "concentration_risk",
                        "priority": "high",
                        "description": "High concentration in individual positions",
                        "recommendation": "Consider reducing position sizes above 20%",
                    }
                )

            # Number of holdings
            if len(holdings) < 10:
                suggestions.append(
                    {
                        "type": "holding_count",
                        "priority": "medium",
                        "description": "Consider adding more holdings for better diversification",
                        "recommendation": "Target 15-25 holdings for optimal diversification",
                    }
                )
            elif len(holdings) > 30:
                suggestions.append(
                    {
                        "type": "holding_count",
                        "priority": "low",
                        "description": "Large number of holdings may be difficult to manage",
                        "recommendation": "Consider consolidating similar positions",
                    }
                )

            return {
                "diversification_score": self._calculate_diversification_score(
                    len(holdings), len(asset_types), concentrations
                ),
                "asset_type_breakdown": asset_types,
                "concentration_risks": concentrations,
                "total_holdings": len(holdings),
                "suggestions": suggestions,
                "analysis_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error in diversification analysis", error=str(e))
            return {"error": "Failed to analyze diversification"}

    async def _get_returns_data(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """Get returns data for portfolio optimization."""
        try:
            returns_data = {}

            for symbol in symbols:
                historical_data = await enhanced_market_data_service.get_historical_data(symbol, period="1y")

                if historical_data:
                    prices = [float(d["close"]) for d in historical_data if d["close"] is not None]

                    if len(prices) > 20:  # Need sufficient data
                        price_series = pd.Series(prices)
                        returns = price_series.pct_change().dropna()
                        returns_data[symbol] = returns

            if len(returns_data) < 2:
                return None

            # Align data (use minimum length)
            min_length = min(len(data) for data in returns_data.values())
            aligned_data = {
                symbol: data.tail(min_length).reset_index(drop=True) for symbol, data in returns_data.items()
            }

            return pd.DataFrame(aligned_data)

        except Exception as e:
            logger.error("Error getting returns data", error=str(e))
            return None

    def _maximize_sharpe_ratio(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: List[Dict],
    ) -> Optional[np.ndarray]:
        """Maximize Sharpe ratio optimization."""
        try:
            n_assets = len(expected_returns)

            def negative_sharpe_ratio(weights):
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_std = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                return -(portfolio_return - self.risk_free_rate) / portfolio_std

            # Initial guess: equal weights
            initial_guess = np.array([1.0 / n_assets] * n_assets)

            # Bounds: 0% to 50% per asset
            bounds = tuple((0, 0.5) for _ in range(n_assets))

            result = minimize(
                negative_sharpe_ratio,
                initial_guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            return result.x if result.success else None

        except Exception as e:
            logger.error("Error in Sharpe ratio optimization", error=str(e))
            return None

    def _minimize_risk_for_return(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: float,
        constraints: List[Dict],
    ) -> Optional[np.ndarray]:
        """Minimize risk for target return optimization."""
        try:
            n_assets = len(expected_returns)

            def portfolio_variance(weights):
                return np.dot(weights, np.dot(cov_matrix, weights))

            # Add return constraint
            return_constraint = {
                "type": "eq",
                "fun": lambda weights: np.dot(weights, expected_returns) - target_return,
            }
            constraints.append(return_constraint)

            # Initial guess: equal weights
            initial_guess = np.array([1.0 / n_assets] * n_assets)

            # Bounds: 0% to 50% per asset
            bounds = tuple((0, 0.5) for _ in range(n_assets))

            result = minimize(
                portfolio_variance,
                initial_guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            return result.x if result.success else None

        except Exception as e:
            logger.error("Error in risk minimization", error=str(e))
            return None

    def _build_optimization_constraints(
        self, n_assets: int, user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Build optimization constraints."""
        constraints = []

        # Weights must sum to 1
        constraints.append({"type": "eq", "fun": lambda weights: np.sum(weights) - 1})

        # User-defined constraints
        if user_preferences:
            max_position_size = user_preferences.get("max_position_size", 0.5)
            min_position_size = user_preferences.get("min_position_size", 0.0)

            # Maximum position size constraint
            for i in range(n_assets):
                constraints.append(
                    {
                        "type": "ineq",
                        "fun": lambda weights, i=i: max_position_size - weights[i],
                    }
                )

            # Minimum position size constraint (if specified)
            if min_position_size > 0:
                for i in range(n_assets):
                    constraints.append(
                        {
                            "type": "ineq",
                            "fun": lambda weights, i=i: weights[i] - min_position_size,
                        }
                    )

        return constraints

    def _calculate_rebalancing_actions(
        self,
        holdings: List[Holding],
        current_weights: np.ndarray,
        optimal_weights: np.ndarray,
        total_value: float,
    ) -> List[Dict[str, Any]]:
        """Calculate specific rebalancing actions."""
        actions = []

        for i, holding in enumerate(holdings):
            current_value = current_weights[i] * total_value
            optimal_value = optimal_weights[i] * total_value
            difference = optimal_value - current_value

            if abs(difference) > total_value * 0.01:  # 1% minimum threshold
                action_type = "BUY" if difference > 0 else "SELL"
                shares_to_trade = abs(difference) / holding.current_price
                cost = abs(difference) * self.trading_cost

                actions.append(
                    {
                        "symbol": holding.symbol,
                        "action": action_type,
                        "current_weight": round(current_weights[i] * 100, 2),
                        "optimal_weight": round(optimal_weights[i] * 100, 2),
                        "dollar_amount": round(abs(difference), 2),
                        "shares": round(shares_to_trade, 4),
                        "cost": round(cost, 2),
                    }
                )

        return actions

    async def _calculate_performance_metrics(
        self, portfolio: Portfolio, historical_data: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics."""
        # Placeholder implementation
        return {
            "total_return": portfolio.total_return,
            "total_return_percentage": portfolio.total_return_percentage,
            "annualized_return": 0.0,  # To be calculated from historical data
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
        }

    async def _calculate_risk_metrics(self, portfolio: Portfolio, historical_data: Dict[str, List]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics."""
        # Placeholder implementation
        return {
            "portfolio_beta": 1.0,
            "value_at_risk_95": 0.0,
            "expected_shortfall": 0.0,
            "correlation_with_market": 0.0,
        }

    def _calculate_diversification_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Calculate diversification metrics."""
        holdings = portfolio.holdings
        total_value = sum(h.market_value for h in holdings)

        # Herfindahl-Hirschman Index (concentration measure)
        hhi = sum((h.market_value / total_value) ** 2 for h in holdings)

        return {
            "number_of_holdings": len(holdings),
            "herfindahl_index": round(hhi, 4),
            "effective_number_of_stocks": round(1 / hhi, 2) if hhi > 0 else 0,
            "diversification_ratio": round(1 - hhi, 4),
        }

    def _calculate_diversification_score(
        self,
        num_holdings: int,
        num_asset_types: int,
        concentrations: List[Dict],
    ) -> int:
        """Calculate overall diversification score (0-100)."""
        score = 100

        # Penalize for too few holdings
        if num_holdings < 5:
            score -= 30
        elif num_holdings < 10:
            score -= 15

        # Penalize for lack of asset type diversity
        if num_asset_types < 2:
            score -= 25
        elif num_asset_types < 3:
            score -= 10

        # Penalize for concentration risk
        score -= len(concentrations) * 10

        return max(0, min(100, score))

    async def _generate_performance_recommendations(
        self,
        portfolio: Portfolio,
        performance_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
    ) -> List[str]:
        """Generate performance-based recommendations."""
        recommendations = []

        # Example recommendations based on metrics
        if performance_metrics.get("sharpe_ratio", 0) < 0.5:
            recommendations.append("Consider rebalancing to improve risk-adjusted returns")

        if risk_metrics.get("portfolio_beta", 1) > 1.5:
            recommendations.append("Portfolio is highly correlated with market - consider diversification")

        return recommendations


# Singleton instance
portfolio_optimizer = PortfolioOptimizer()
