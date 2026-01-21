import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ...core.config import settings
from ...models.portfolio import Portfolio
from ...models.trade import Trade

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    def __init__(self, db: Session):
        self.db = db
        self.metrics_cache = {}
        self.last_update = datetime.now()
        self.update_interval = timedelta(minutes=5)

    async def record_trade(self, trade: Trade):
        """Record and analyze a completed trade"""
        try:
            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.user_id == trade.user_id)
                .first()
            )

            if not portfolio:
                logger.error(f"Portfolio not found for user {trade.user_id}")
                return

            # Calculate trade metrics
            profit_loss = self._calculate_trade_pl(trade)
            roi = self._calculate_roi(trade)

            # Update portfolio metrics
            self._update_portfolio_metrics(portfolio, trade, profit_loss)

            # Store trade metrics
            trade_metrics = {
                "trade_id": trade.id,
                "profit_loss": float(profit_loss),
                "roi": float(roi),
                "execution_time": (trade.filled_at - trade.created_at).total_seconds(),
                "slippage": self._calculate_slippage(trade),
            }

            self.metrics_cache[trade.id] = trade_metrics

            # Trigger metrics update if needed
            await self._check_metrics_update()

        except Exception as e:
            logger.error(f"Error recording trade metrics: {str(e)}")

    async def get_performance_metrics(
        self, user_id: int, timeframe: str = "daily"
    ) -> Dict:
        """Get performance metrics for a specific timeframe"""
        try:
            # Get user's portfolio
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
            )

            if not portfolio:
                raise ValueError(f"Portfolio not found for user {user_id}")

            # Calculate metrics based on timeframe
            if timeframe == "daily":
                return await self._calculate_daily_metrics(portfolio)
            elif timeframe == "weekly":
                return await self._calculate_weekly_metrics(portfolio)
            elif timeframe == "monthly":
                return await self._calculate_monthly_metrics(portfolio)
            else:
                raise ValueError(f"Invalid timeframe: {timeframe}")

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

    def _calculate_trade_pl(self, trade: Trade) -> Decimal:
        """Calculate profit/loss for a trade"""
        if trade.side == "BUY":
            return -(trade.quantity * trade.price + trade.commission)
        else:
            return trade.quantity * trade.price - trade.commission

    def _calculate_roi(self, trade: Trade) -> Decimal:
        """Calculate ROI for a trade"""
        cost_basis = trade.quantity * trade.price
        if cost_basis == 0:
            return Decimal("0")
        return (self._calculate_trade_pl(trade) / cost_basis) * 100

    def _calculate_slippage(self, trade: Trade) -> Decimal:
        """Calculate price slippage"""
        if trade.order_type == "MARKET":
            expected_price = trade.price
            executed_price = trade.filled_price
            return abs(executed_price - expected_price) / expected_price * 100
        return Decimal("0")

    def _update_portfolio_metrics(
        self, portfolio: Portfolio, trade: Trade, profit_loss: Decimal
    ):
        """Update portfolio performance metrics"""
        portfolio.total_value += profit_loss
        portfolio.updated_at = datetime.utcnow()

        # Update positions JSON
        positions = json.loads(portfolio.positions or "{}")
        symbol = trade.symbol

        if symbol not in positions:
            positions[symbol] = {"quantity": 0, "average_price": 0, "realized_pl": 0}

        position = positions[symbol]

        if trade.side == "BUY":
            # Update average price and quantity for buys
            old_value = Decimal(str(position["quantity"])) * Decimal(
                str(position["average_price"])
            )
            new_value = trade.quantity * trade.price
            new_quantity = Decimal(str(position["quantity"])) + trade.quantity

            if new_quantity > 0:
                position["average_price"] = float(
                    (old_value + new_value) / new_quantity
                )
            position["quantity"] = float(new_quantity)
        else:
            # Update realized P/L for sells
            position["realized_pl"] = float(
                Decimal(str(position["realized_pl"])) + profit_loss
            )
            position["quantity"] = float(
                Decimal(str(position["quantity"])) - trade.quantity
            )

        portfolio.positions = json.dumps(positions)
        self.db.commit()

    async def _check_metrics_update(self):
        """Check and update cached metrics if needed"""
        if datetime.now() - self.last_update > self.update_interval:
            await self._update_metrics()
            self.last_update = datetime.now()

    async def _update_metrics(self):
        """Update all performance metrics"""
        try:
            # Calculate aggregate metrics
            for user_id in set(trade.user_id for trade in self.metrics_cache.values()):
                portfolio = (
                    self.db.query(Portfolio)
                    .filter(Portfolio.user_id == user_id)
                    .first()
                )

                if portfolio:
                    metrics = await self._calculate_portfolio_metrics(portfolio)
                    # Store updated metrics
                    portfolio.metrics = json.dumps(metrics)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")

    async def _calculate_portfolio_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate comprehensive portfolio metrics"""
        metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_profit_loss": 0,
            "largest_gain": 0,
            "largest_loss": 0,
            "average_roi": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
        }

        # Get all trades for portfolio
        trades = (
            self.db.query(Trade)
            .filter(Trade.user_id == portfolio.user_id, Trade.status == "FILLED")
            .order_by(Trade.filled_at)
            .all()
        )

        if not trades:
            return metrics

        # Calculate metrics
        daily_returns = []
        running_pl = 0
        peak_value = portfolio.total_value
        max_drawdown = 0

        for trade in trades:
            pl = self._calculate_trade_pl(trade)
            running_pl += pl

            # Update metrics
            metrics["total_trades"] += 1
            if pl > 0:
                metrics["winning_trades"] += 1
                metrics["largest_gain"] = max(metrics["largest_gain"], float(pl))
            else:
                metrics["losing_trades"] += 1
                metrics["largest_loss"] = min(metrics["largest_loss"], float(pl))

            # Calculate drawdown
            peak_value = max(peak_value, portfolio.total_value + running_pl)
            drawdown = (peak_value - (portfolio.total_value + running_pl)) / peak_value
            max_drawdown = max(max_drawdown, drawdown)

            # Record daily return
            daily_returns.append(float(self._calculate_roi(trade)))

        # Calculate aggregate metrics
        metrics["total_profit_loss"] = float(running_pl)
        metrics["win_rate"] = (
            metrics["winning_trades"] / metrics["total_trades"]
            if metrics["total_trades"] > 0
            else 0
        )
        metrics["average_roi"] = np.mean(daily_returns) if daily_returns else 0
        metrics["max_drawdown"] = float(max_drawdown)

        # Calculate Sharpe Ratio
        if len(daily_returns) > 1:
            returns_std = np.std(daily_returns)
            if returns_std > 0:
                metrics["sharpe_ratio"] = (
                    np.mean(daily_returns) - settings.RISK_FREE_RATE
                ) / returns_std

        return metrics

    async def _calculate_daily_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate daily performance metrics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        return await self._calculate_metrics_for_timeframe(
            portfolio, start_date, end_date
        )

    async def _calculate_weekly_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate weekly performance metrics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=1)
        return await self._calculate_metrics_for_timeframe(
            portfolio, start_date, end_date
        )

    async def _calculate_monthly_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate monthly performance metrics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return await self._calculate_metrics_for_timeframe(
            portfolio, start_date, end_date
        )

    async def _calculate_metrics_for_timeframe(
        self, portfolio: Portfolio, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Calculate metrics for a specific timeframe"""
        trades = (
            self.db.query(Trade)
            .filter(
                Trade.user_id == portfolio.user_id,
                Trade.filled_at.between(start_date, end_date),
                Trade.status == "FILLED",
            )
            .all()
        )

        metrics = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_trades": len(trades),
            "total_volume": sum(float(t.quantity * t.price) for t in trades),
            "profit_loss": sum(float(self._calculate_trade_pl(t)) for t in trades),
            "fees": sum(float(t.commission) for t in trades),
        }

        # Calculate additional metrics
        if trades:
            roi_values = [float(self._calculate_roi(t)) for t in trades]
            metrics.update(
                {
                    "average_roi": np.mean(roi_values),
                    "roi_volatility": np.std(roi_values),
                    "best_trade": max(roi_values),
                    "worst_trade": min(roi_values),
                }
            )

        return metrics
