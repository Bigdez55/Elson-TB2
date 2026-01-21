import itertools
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...core.config import settings
from ...models.trade import OrderSide
from ...services.market_data import MarketDataService
from ..strategies.moving_average import MovingAverageStrategy

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service
        self.optimization_results = {}
        self.max_workers = 4

    async def optimize_strategy(
        self,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict,
    ) -> Dict:
        """Optimize strategy parameters using parallel backtesting"""
        try:
            # Get historical data for backtesting
            data = await self.market_data_service.get_historical_data(
                symbol, start_date, end_date
            )

            if data.empty:
                raise ValueError(f"No historical data available for {symbol}")

            # Generate parameter combinations
            param_combinations = self._generate_parameter_combinations(parameter_ranges)

            # Perform parallel optimization
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(
                    executor.map(
                        lambda params: self._backtest_parameters(
                            strategy_name, data, symbol, params
                        ),
                        param_combinations,
                    )
                )

            # Find best parameters
            best_result = max(results, key=lambda x: x["sharpe_ratio"])

            # Store optimization results
            self.optimization_results[symbol] = {
                "best_parameters": best_result["parameters"],
                "performance_metrics": best_result["metrics"],
                "optimization_time": datetime.utcnow().isoformat(),
                "data_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }

            return self.optimization_results[symbol]

        except Exception as e:
            logger.error(f"Strategy optimization error: {str(e)}")
            raise

    def _generate_parameter_combinations(self, parameter_ranges: Dict) -> List[Dict]:
        """Generate all possible parameter combinations within ranges"""
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())

        combinations = list(itertools.product(*param_values))
        return [dict(zip(param_names, combo)) for combo in combinations]

    def _backtest_parameters(
        self, strategy_name: str, data: pd.DataFrame, symbol: str, parameters: Dict
    ) -> Dict:
        """Backtest strategy with specific parameters"""
        try:
            if strategy_name == "MovingAverage":
                strategy = MovingAverageStrategy(
                    self.market_data_service, symbol, **parameters
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy_name}")

            # Run backtest
            results = self._run_backtest(strategy, data)

            return {
                "parameters": parameters,
                "metrics": results,
                "sharpe_ratio": results["sharpe_ratio"],
            }

        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return {"parameters": parameters, "metrics": {}, "sharpe_ratio": -np.inf}

    def _run_backtest(
        self, strategy: MovingAverageStrategy, data: pd.DataFrame
    ) -> Dict:
        """Run backtest simulation"""
        try:
            # Initialize metrics
            initial_capital = 100000
            position = 0
            portfolio_value = initial_capital
            trades = []
            daily_returns = []

            # Calculate indicators
            signals = strategy._calculate_indicators(data)

            # Simulate trading
            for i in range(len(signals) - 1):
                current_price = signals.iloc[i]["Close"]
                next_price = signals.iloc[i + 1]["Close"]
                signal = signals.iloc[i]["Signal"]

                # Generate trade based on signal
                if signal == 1 and position <= 0:  # Buy signal
                    position = (
                        portfolio_value * 0.95 / current_price
                    )  # Use 95% of portfolio
                    trade = {
                        "date": signals.index[i],
                        "type": "BUY",
                        "price": current_price,
                        "position": position,
                        "portfolio_value": portfolio_value,
                    }
                    trades.append(trade)

                elif signal == -1 and position > 0:  # Sell signal
                    portfolio_value = position * current_price
                    position = 0
                    trade = {
                        "date": signals.index[i],
                        "type": "SELL",
                        "price": current_price,
                        "position": position,
                        "portfolio_value": portfolio_value,
                    }
                    trades.append(trade)

                # Calculate daily return
                if position > 0:
                    daily_return = (next_price - current_price) / current_price
                    daily_returns.append(daily_return)
                else:
                    daily_returns.append(0)

            # Calculate performance metrics
            metrics = self._calculate_backtest_metrics(
                trades, daily_returns, initial_capital, portfolio_value
            )

            return metrics

        except Exception as e:
            logger.error(f"Backtest simulation error: {str(e)}")
            return {
                "sharpe_ratio": -np.inf,
                "total_return": -np.inf,
                "max_drawdown": 1,
                "win_rate": 0,
            }

    def _calculate_backtest_metrics(
        self,
        trades: List[Dict],
        daily_returns: List[float],
        initial_capital: float,
        final_portfolio_value: float,
    ) -> Dict:
        """Calculate comprehensive backtest performance metrics"""
        try:
            # Convert to numpy array for calculations
            returns_array = np.array(daily_returns)

            # Basic return metrics
            total_return = (final_portfolio_value - initial_capital) / initial_capital

            # Risk metrics
            daily_std = np.std(returns_array)
            annualized_std = daily_std * np.sqrt(252)

            # Sharpe Ratio (assuming risk-free rate from settings)
            excess_returns = returns_array - settings.RISK_FREE_RATE / 252
            sharpe_ratio = (
                np.mean(excess_returns) / daily_std * np.sqrt(252)
                if daily_std > 0
                else -np.inf
            )

            # Maximum Drawdown
            cumulative_returns = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (running_max - cumulative_returns) / running_max
            max_drawdown = np.max(drawdowns)

            # Trading metrics
            winning_trades = len(
                [
                    t
                    for t in trades
                    if t["type"] == "SELL"
                    and t["portfolio_value"] > t.get("previous_value", initial_capital)
                ]
            )
            total_trades = len([t for t in trades if t["type"] == "SELL"])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            return {
                "total_return": float(total_return),
                "annualized_return": float(total_return * 252 / len(daily_returns)),
                "sharpe_ratio": float(sharpe_ratio),
                "sortino_ratio": self._calculate_sortino_ratio(returns_array),
                "max_drawdown": float(max_drawdown),
                "win_rate": float(win_rate),
                "total_trades": total_trades,
                "profit_factor": self._calculate_profit_factor(trades),
                "volatility": float(annualized_std),
                "value_at_risk": float(np.percentile(returns_array, 5)),
                "avg_return_per_trade": (
                    float(total_return / total_trades) if total_trades > 0 else 0
                ),
                "metrics_version": "1.0",
            }

        except Exception as e:
            logger.error(f"Error calculating backtest metrics: {str(e)}")
            return {
                "sharpe_ratio": -np.inf,
                "total_return": -np.inf,
                "max_drawdown": 1,
                "win_rate": 0,
            }

    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio (sharpe ratio but only for negative returns)"""
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return np.inf

        downside_std = np.std(negative_returns)
        excess_return = np.mean(returns) - settings.RISK_FREE_RATE / 252

        return excess_return / downside_std * np.sqrt(252) if downside_std > 0 else 0

    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calculate profit factor (gross profits / gross losses)"""
        profits = sum(
            t["portfolio_value"] - t.get("previous_value", 0)
            for t in trades
            if t["type"] == "SELL" and t["portfolio_value"] > t.get("previous_value", 0)
        )
        losses = abs(
            sum(
                t["portfolio_value"] - t.get("previous_value", 0)
                for t in trades
                if t["type"] == "SELL"
                and t["portfolio_value"] < t.get("previous_value", 0)
            )
        )

        return profits / losses if losses > 0 else np.inf

    async def get_optimization_results(self, symbol: str) -> Optional[Dict]:
        """Get stored optimization results for a symbol"""
        return self.optimization_results.get(symbol)

    async def optimize_portfolio(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict,
    ) -> Dict:
        """Optimize strategies for multiple symbols"""
        portfolio_results = {}

        for symbol in symbols:
            try:
                result = await self.optimize_strategy(
                    "MovingAverage", symbol, start_date, end_date, parameter_ranges
                )
                portfolio_results[symbol] = result
            except Exception as e:
                logger.error(f"Error optimizing {symbol}: {str(e)}")

        return portfolio_results

    def get_recommended_parameters(self, symbol: str) -> Optional[Dict]:
        """Get recommended parameters based on optimization results"""
        if symbol in self.optimization_results:
            return self.optimization_results[symbol]["best_parameters"]
        return None
