"""
Performance Analysis for Backtesting

Calculates comprehensive performance metrics including returns,
risk-adjusted metrics, drawdowns, and trade statistics.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""

    # Returns
    total_return: float = 0.0
    annualized_return: float = 0.0
    monthly_return: float = 0.0

    # Risk
    volatility: float = 0.0
    annualized_volatility: float = 0.0
    downside_volatility: float = 0.0

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0

    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    avg_drawdown: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade: float = 0.0
    expectancy: float = 0.0

    # Exposure
    avg_exposure: float = 0.0
    max_exposure: float = 0.0

    # Time
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    trading_days: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "returns": {
                "total_return_pct": self.total_return * 100,
                "annualized_return_pct": self.annualized_return * 100,
                "monthly_return_pct": self.monthly_return * 100,
            },
            "risk": {
                "volatility_pct": self.volatility * 100,
                "annualized_volatility_pct": self.annualized_volatility * 100,
                "downside_volatility_pct": self.downside_volatility * 100,
            },
            "risk_adjusted": {
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "calmar_ratio": self.calmar_ratio,
            },
            "drawdown": {
                "max_drawdown_pct": self.max_drawdown * 100,
                "max_drawdown_duration_days": self.max_drawdown_duration,
                "avg_drawdown_pct": self.avg_drawdown * 100,
            },
            "trades": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate_pct": self.win_rate * 100,
                "profit_factor": self.profit_factor,
                "avg_win": self.avg_win,
                "avg_loss": self.avg_loss,
                "largest_win": self.largest_win,
                "largest_loss": self.largest_loss,
                "expectancy": self.expectancy,
            },
            "exposure": {
                "avg_exposure_pct": self.avg_exposure * 100,
                "max_exposure_pct": self.max_exposure * 100,
            },
            "period": {
                "start_date": str(self.start_date) if self.start_date else None,
                "end_date": str(self.end_date) if self.end_date else None,
                "trading_days": self.trading_days,
            },
        }


class PerformanceAnalyzer:
    """
    Analyzes backtest performance and generates comprehensive reports.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize analyzer.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.risk_free_rate = risk_free_rate
        self.daily_risk_free = (1 + risk_free_rate) ** (1 / 252) - 1

    def analyze(
        self,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        initial_capital: float,
    ) -> PerformanceMetrics:
        """
        Perform comprehensive performance analysis.

        Args:
            equity_curve: List of equity snapshots with 'timestamp' and 'total_value'
            trades: List of trade dictionaries
            initial_capital: Starting capital

        Returns:
            PerformanceMetrics object
        """
        metrics = PerformanceMetrics()

        if not equity_curve:
            return metrics

        # Convert to DataFrame
        df = pd.DataFrame(equity_curve)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Calculate returns
        df["returns"] = df["total_value"].pct_change()
        df["cumulative_returns"] = (1 + df["returns"]).cumprod() - 1

        # Time period
        metrics.start_date = df["timestamp"].iloc[0]
        metrics.end_date = df["timestamp"].iloc[-1]
        metrics.trading_days = len(df)

        # Calculate return metrics
        metrics.total_return = (df["total_value"].iloc[-1] / initial_capital) - 1

        years = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).days / 365.25
        if years > 0:
            metrics.annualized_return = (1 + metrics.total_return) ** (1 / years) - 1
            metrics.monthly_return = (1 + metrics.annualized_return) ** (1 / 12) - 1

        # Calculate risk metrics
        returns = df["returns"].dropna()
        if len(returns) > 1:
            metrics.volatility = returns.std()
            metrics.annualized_volatility = metrics.volatility * np.sqrt(252)

            # Downside volatility
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                metrics.downside_volatility = negative_returns.std() * np.sqrt(252)

        # Calculate risk-adjusted metrics
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(
            metrics.annualized_return, metrics.annualized_volatility
        )

        metrics.sortino_ratio = self._calculate_sortino_ratio(
            metrics.annualized_return, metrics.downside_volatility
        )

        # Calculate drawdown metrics
        dd_info = self._calculate_drawdown(df["total_value"])
        metrics.max_drawdown = dd_info["max_drawdown"]
        metrics.max_drawdown_duration = dd_info["max_duration"]
        metrics.avg_drawdown = dd_info["avg_drawdown"]

        metrics.calmar_ratio = self._calculate_calmar_ratio(
            metrics.annualized_return, metrics.max_drawdown
        )

        # Calculate trade statistics
        trade_stats = self._calculate_trade_stats(trades)
        metrics.total_trades = trade_stats["total_trades"]
        metrics.winning_trades = trade_stats["winning_trades"]
        metrics.losing_trades = trade_stats["losing_trades"]
        metrics.win_rate = trade_stats["win_rate"]
        metrics.profit_factor = trade_stats["profit_factor"]
        metrics.avg_win = trade_stats["avg_win"]
        metrics.avg_loss = trade_stats["avg_loss"]
        metrics.largest_win = trade_stats["largest_win"]
        metrics.largest_loss = trade_stats["largest_loss"]
        metrics.avg_trade = trade_stats["avg_trade"]
        metrics.expectancy = trade_stats["expectancy"]

        # Calculate exposure
        if "positions_value" in df.columns:
            exposure = df["positions_value"] / df["total_value"]
            metrics.avg_exposure = exposure.mean()
            metrics.max_exposure = exposure.max()

        return metrics

    def _calculate_sharpe_ratio(
        self, annualized_return: float, annualized_volatility: float
    ) -> float:
        """Calculate Sharpe ratio"""
        if annualized_volatility == 0:
            return 0.0
        return (annualized_return - self.risk_free_rate) / annualized_volatility

    def _calculate_sortino_ratio(
        self, annualized_return: float, downside_volatility: float
    ) -> float:
        """Calculate Sortino ratio"""
        if downside_volatility == 0:
            return 0.0
        return (annualized_return - self.risk_free_rate) / downside_volatility

    def _calculate_calmar_ratio(
        self, annualized_return: float, max_drawdown: float
    ) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / abs(max_drawdown)

    def _calculate_drawdown(self, equity: pd.Series) -> Dict[str, float]:
        """Calculate drawdown metrics"""
        # Running maximum
        running_max = equity.expanding().max()

        # Drawdown
        drawdown = (equity - running_max) / running_max

        # Max drawdown
        max_drawdown = drawdown.min()

        # Drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0

        for in_dd in is_drawdown:
            if in_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0

        if current_period > 0:
            drawdown_periods.append(current_period)

        max_duration = max(drawdown_periods) if drawdown_periods else 0
        avg_drawdown = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0

        return {
            "max_drawdown": abs(max_drawdown),
            "max_duration": max_duration,
            "avg_drawdown": abs(avg_drawdown) if avg_drawdown else 0,
        }

    def _calculate_trade_stats(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate trade statistics"""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "avg_trade": 0,
                "expectancy": 0,
            }

        # Get P&L for each trade
        pnls = [t.get("realized_pnl", 0) for t in trades if t.get("side") == "sell"]

        if not pnls:
            pnls = [t.get("realized_pnl", 0) for t in trades]

        total_trades = len(pnls)
        winning_trades = len([p for p in pnls if p > 0])
        losing_trades = len([p for p in pnls if p < 0])

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0

        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else float("inf") if gross_profit > 0 else 0
        )

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0

        avg_trade = np.mean(pnls) if pnls else 0
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_trade": avg_trade,
            "expectancy": expectancy,
        }

    def generate_report(
        self, metrics: PerformanceMetrics, include_charts: bool = False
    ) -> str:
        """Generate a text report of performance"""
        report = []
        report.append("=" * 60)
        report.append("BACKTEST PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")

        # Period
        report.append("PERIOD")
        report.append("-" * 40)
        report.append(f"Start Date:       {metrics.start_date}")
        report.append(f"End Date:         {metrics.end_date}")
        report.append(f"Trading Days:     {metrics.trading_days}")
        report.append("")

        # Returns
        report.append("RETURNS")
        report.append("-" * 40)
        report.append(f"Total Return:     {metrics.total_return * 100:>10.2f}%")
        report.append(f"Annualized:       {metrics.annualized_return * 100:>10.2f}%")
        report.append(f"Monthly:          {metrics.monthly_return * 100:>10.2f}%")
        report.append("")

        # Risk
        report.append("RISK METRICS")
        report.append("-" * 40)
        report.append(
            f"Volatility (Ann): {metrics.annualized_volatility * 100:>10.2f}%"
        )
        report.append(f"Downside Vol:     {metrics.downside_volatility * 100:>10.2f}%")
        report.append(f"Max Drawdown:     {metrics.max_drawdown * 100:>10.2f}%")
        report.append(f"Max DD Duration:  {metrics.max_drawdown_duration:>10d} days")
        report.append("")

        # Risk-Adjusted
        report.append("RISK-ADJUSTED RETURNS")
        report.append("-" * 40)
        report.append(f"Sharpe Ratio:     {metrics.sharpe_ratio:>10.2f}")
        report.append(f"Sortino Ratio:    {metrics.sortino_ratio:>10.2f}")
        report.append(f"Calmar Ratio:     {metrics.calmar_ratio:>10.2f}")
        report.append("")

        # Trade Stats
        report.append("TRADE STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Trades:     {metrics.total_trades:>10d}")
        report.append(f"Winning Trades:   {metrics.winning_trades:>10d}")
        report.append(f"Losing Trades:    {metrics.losing_trades:>10d}")
        report.append(f"Win Rate:         {metrics.win_rate * 100:>10.2f}%")
        report.append(f"Profit Factor:    {metrics.profit_factor:>10.2f}")
        report.append(f"Avg Win:          ${metrics.avg_win:>9.2f}")
        report.append(f"Avg Loss:         ${metrics.avg_loss:>9.2f}")
        report.append(f"Largest Win:      ${metrics.largest_win:>9.2f}")
        report.append(f"Largest Loss:     ${metrics.largest_loss:>9.2f}")
        report.append(f"Expectancy:       ${metrics.expectancy:>9.2f}")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def compare_strategies(
        self, results: Dict[str, PerformanceMetrics]
    ) -> pd.DataFrame:
        """
        Compare multiple strategy results.

        Args:
            results: Dictionary of strategy name -> PerformanceMetrics

        Returns:
            DataFrame with comparison
        """
        comparison = []

        for name, metrics in results.items():
            comparison.append(
                {
                    "Strategy": name,
                    "Total Return %": metrics.total_return * 100,
                    "Ann. Return %": metrics.annualized_return * 100,
                    "Volatility %": metrics.annualized_volatility * 100,
                    "Sharpe": metrics.sharpe_ratio,
                    "Sortino": metrics.sortino_ratio,
                    "Max DD %": metrics.max_drawdown * 100,
                    "Win Rate %": metrics.win_rate * 100,
                    "Profit Factor": metrics.profit_factor,
                    "Trades": metrics.total_trades,
                }
            )

        df = pd.DataFrame(comparison)
        df = df.set_index("Strategy")

        return df
