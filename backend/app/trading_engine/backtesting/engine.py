"""
Backtesting Engine

Main engine for running strategy backtests with historical data.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

import pandas as pd

from ..strategies.base import TradingStrategy
from .data_handler import Bar, DataHandler
from .order import Order, OrderSide, OrderStatus, OrderType
from .performance import PerformanceAnalyzer, PerformanceMetrics
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest"""

    initial_capital: float = 100000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    position_sizing: str = "fixed"  # fixed, percent, kelly
    position_size: float = 0.02  # 2% of portfolio per trade
    max_positions: int = 10
    warmup_bars: int = 50
    use_stops: bool = True
    use_take_profit: bool = True
    allow_short: bool = False
    margin_requirement: float = 1.0


@dataclass
class BacktestResult:
    """Results from a backtest run"""

    strategy_name: str
    config: BacktestConfig
    metrics: PerformanceMetrics
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    orders: List[Dict[str, Any]]
    final_portfolio: Dict[str, Any]
    execution_time: float = 0.0
    bars_processed: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "strategy_name": self.strategy_name,
            "config": {
                "initial_capital": self.config.initial_capital,
                "commission_rate": self.config.commission_rate,
                "slippage_rate": self.config.slippage_rate,
                "position_sizing": self.config.position_sizing,
                "position_size": self.config.position_size,
            },
            "metrics": self.metrics.to_dict(),
            "summary": {
                "total_return_pct": self.metrics.total_return * 100,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "max_drawdown_pct": self.metrics.max_drawdown * 100,
                "total_trades": self.metrics.total_trades,
                "win_rate_pct": self.metrics.win_rate * 100,
            },
            "execution": {
                "bars_processed": self.bars_processed,
                "execution_time_seconds": self.execution_time,
            },
        }


class BacktestEngine:
    """
    Main backtesting engine.

    Runs trading strategies against historical data with realistic
    simulation of market conditions, order execution, and portfolio management.
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()
        self.data_handler = DataHandler()
        self.portfolio: Optional[Portfolio] = None
        self.analyzer = PerformanceAnalyzer()

        self._strategies: List[TradingStrategy] = []
        self._signals: List[Dict[str, Any]] = []
        self._current_bar: Optional[Dict[str, Bar]] = None

    def add_data(
        self, symbol: str, data: Union[pd.DataFrame, List[Dict], str], **kwargs
    ) -> None:
        """
        Add data for backtesting.

        Args:
            symbol: Symbol identifier
            data: DataFrame, list of dicts, or CSV filepath
            **kwargs: Additional arguments for data loading
        """
        if isinstance(data, pd.DataFrame):
            self.data_handler.load_dataframe(symbol, data, **kwargs)
        elif isinstance(data, list):
            self.data_handler.load_dict(symbol, data)
        elif isinstance(data, str):
            self.data_handler.load_csv(symbol, data, **kwargs)

    def add_strategy(self, strategy: TradingStrategy) -> None:
        """
        Add a strategy to backtest.

        Args:
            strategy: Strategy instance to test
        """
        self._strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")

    def run(self) -> BacktestResult:
        """
        Run the backtest synchronously.

        Returns:
            BacktestResult with performance metrics
        """
        return asyncio.run(self.run_async())

    async def run_async(self) -> BacktestResult:
        """
        Run the backtest asynchronously.

        Returns:
            BacktestResult with performance metrics
        """
        start_time = datetime.utcnow()

        # Initialize
        self._initialize()

        # Preprocess data
        self.data_handler.preprocess()

        if len(self.data_handler.symbols) > 1:
            self.data_handler.align_data()

        # Run simulation
        bars_processed = await self._run_simulation()

        # Calculate performance
        metrics = self.analyzer.analyze(
            self.portfolio.get_equity_curve(),
            self.portfolio.trades,
            self.config.initial_capital,
        )

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # Build result
        result = BacktestResult(
            strategy_name=self._strategies[0].name if self._strategies else "Unknown",
            config=self.config,
            metrics=metrics,
            equity_curve=self.portfolio.get_equity_curve(),
            trades=self.portfolio.trades,
            signals=self._signals,
            orders=[o.to_dict() for o in self.portfolio.filled_orders],
            final_portfolio=self.portfolio.get_summary(),
            execution_time=execution_time,
            bars_processed=bars_processed,
        )

        logger.info(
            f"Backtest complete: {bars_processed} bars, "
            f"{metrics.total_trades} trades, "
            f"{metrics.total_return * 100:.2f}% return"
        )

        return result

    def _initialize(self) -> None:
        """Initialize backtest state"""
        self.portfolio = Portfolio(
            initial_capital=self.config.initial_capital,
            commission_rate=self.config.commission_rate,
            slippage_rate=self.config.slippage_rate,
            margin_requirement=self.config.margin_requirement,
        )
        self._signals = []
        self._current_bar = None

    async def _run_simulation(self) -> int:
        """
        Run the main simulation loop.

        Returns:
            Number of bars processed
        """
        bars_processed = 0

        for bars in self.data_handler.iterate_bars(warmup=self.config.warmup_bars):
            self._current_bar = bars

            # Update prices in portfolio
            prices = {symbol: bar.close for symbol, bar in bars.items()}
            self.portfolio.update_prices(prices)

            # Process pending orders
            self._process_pending_orders(bars)

            # Generate signals from strategies
            for strategy in self._strategies:
                await self._process_strategy(strategy, bars)

            # Check stops and take profits
            if self.config.use_stops or self.config.use_take_profit:
                self._check_exit_conditions(bars)

            # Take snapshot
            timestamp = next(iter(bars.values())).timestamp
            self.portfolio.take_snapshot(timestamp)

            bars_processed += 1

        return bars_processed

    async def _process_strategy(
        self, strategy: TradingStrategy, bars: Dict[str, Bar]
    ) -> None:
        """Process a single strategy for current bars"""
        # Check if strategy symbol is in current data
        if strategy.symbol not in bars:
            return

        bar = bars[strategy.symbol]

        # Prepare market data for strategy
        market_data = self.data_handler.get_market_data(
            strategy.symbol, self.data_handler.current_index
        )

        # Add lookback data if available
        lookback_df = self.data_handler.get_lookback(
            strategy.symbol, self.data_handler.current_index, 100  # Default lookback
        )
        if not lookback_df.empty:
            market_data["historical"] = lookback_df.to_dict("records")

        # Generate signal
        try:
            signal = await strategy.generate_signal(market_data)

            if signal:
                signal["bar_index"] = self.data_handler.current_index
                signal["strategy"] = strategy.name
                self._signals.append(signal)

                # Process signal if actionable
                if signal.get("action") in ["buy", "sell"]:
                    self._process_signal(signal, bar, strategy)

        except Exception as e:
            logger.error(f"Error processing strategy {strategy.name}: {e}")

    def _process_signal(
        self, signal: Dict[str, Any], bar: Bar, strategy: TradingStrategy
    ) -> None:
        """Process a trading signal"""
        action = signal.get("action")
        confidence = signal.get("confidence", 0)
        symbol = bar.symbol

        # Check minimum confidence
        min_confidence = strategy.parameters.get("min_confidence", 0.5)
        if confidence < min_confidence:
            return

        # Calculate position size
        position_size = self._calculate_position_size(signal, bar.close, strategy)

        if position_size <= 0:
            return

        # Check position limits
        if action == "buy":
            current_positions = len(
                [p for p in self.portfolio.positions.values() if p.quantity > 0]
            )
            if current_positions >= self.config.max_positions:
                logger.debug("Max positions reached, skipping buy signal")
                return

        # Check if we can trade (position for sells)
        if action == "sell":
            position = self.portfolio.get_position(symbol)
            if not position or position.quantity <= 0:
                if not self.config.allow_short:
                    return
            position_size = min(position_size, position.quantity if position else 0)

        # Create order
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY if action == "buy" else OrderSide.SELL,
            quantity=position_size,
            order_type=OrderType.MARKET,
            stop_loss=signal.get("stop_loss"),
            take_profit=signal.get("take_profit"),
            strategy_name=strategy.name,
        )

        # Submit and execute immediately (market order)
        if self.portfolio.submit_order(order):
            fill_price = order.get_fill_price(bar.close, self.config.slippage_rate)
            self.portfolio.execute_order(order, fill_price, bar.timestamp)

    def _calculate_position_size(
        self, signal: Dict[str, Any], price: float, strategy: TradingStrategy
    ) -> float:
        """Calculate position size based on sizing method"""
        portfolio_value = self.portfolio.total_value

        if self.config.position_sizing == "fixed":
            # Fixed percentage of portfolio
            allocation = portfolio_value * self.config.position_size
            return allocation / price

        elif self.config.position_sizing == "percent":
            # Use strategy's position percentage
            position_pct = strategy.parameters.get(
                "base_position_pct", self.config.position_size
            )
            allocation = portfolio_value * position_pct
            return allocation / price

        elif self.config.position_sizing == "kelly":
            # Kelly criterion sizing
            win_rate = signal.get("indicators", {}).get("win_rate", 0.5)
            avg_win = signal.get("indicators", {}).get("avg_win_pct", 0.02)
            avg_loss = signal.get("indicators", {}).get("avg_loss_pct", 0.01)

            if avg_loss == 0:
                kelly_fraction = 0
            else:
                kelly_fraction = (
                    win_rate * avg_win - (1 - win_rate) * avg_loss
                ) / avg_win

            # Use half Kelly for safety
            kelly_fraction = max(0, min(kelly_fraction * 0.5, 0.25))

            allocation = portfolio_value * kelly_fraction
            return allocation / price

        else:
            # Default to fixed
            allocation = portfolio_value * self.config.position_size
            return allocation / price

    def _process_pending_orders(self, bars: Dict[str, Bar]) -> None:
        """Process pending limit and stop orders"""
        for order in self.portfolio.get_pending_orders():
            if order.symbol not in bars:
                continue

            bar = bars[order.symbol]

            # Check if order can be filled
            if order.can_fill_at_price(bar.close, bar.high, bar.low):
                fill_price = order.get_fill_price(bar.close, self.config.slippage_rate)
                self.portfolio.execute_order(order, fill_price, bar.timestamp)

    def _check_exit_conditions(self, bars: Dict[str, Bar]) -> None:
        """Check stop loss and take profit for open positions"""
        for symbol, position in list(self.portfolio.positions.items()):
            if position.quantity <= 0 or symbol not in bars:
                continue

            bar = bars[symbol]

            # Find the original order for stops
            entry_order = None
            for order in reversed(self.portfolio.filled_orders):
                if order.symbol == symbol and order.side == OrderSide.BUY:
                    entry_order = order
                    break

            if not entry_order:
                continue

            should_exit = False
            exit_reason = ""

            # Check stop loss
            if self.config.use_stops and entry_order.stop_loss:
                if bar.low <= entry_order.stop_loss:
                    should_exit = True
                    exit_reason = "stop_loss"

            # Check take profit
            if self.config.use_take_profit and entry_order.take_profit:
                if bar.high >= entry_order.take_profit:
                    should_exit = True
                    exit_reason = "take_profit"

            if should_exit:
                # Create exit order
                exit_order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET,
                    strategy_name=entry_order.strategy_name,
                )

                if self.portfolio.submit_order(exit_order):
                    exit_price = (
                        entry_order.stop_loss
                        if exit_reason == "stop_loss"
                        else entry_order.take_profit
                    )
                    self.portfolio.execute_order(exit_order, exit_price, bar.timestamp)
                    logger.debug(
                        f"Exit triggered: {exit_reason} for {symbol} @ {exit_price:.2f}"
                    )

    def get_report(self, result: BacktestResult) -> str:
        """Generate performance report"""
        return self.analyzer.generate_report(result.metrics)

    def reset(self) -> None:
        """Reset engine for new backtest"""
        if self.portfolio:
            self.portfolio.reset()
        self._signals = []
        self._current_bar = None


def run_backtest(
    strategy: TradingStrategy,
    data: Union[pd.DataFrame, List[Dict], str],
    symbol: str,
    config: Optional[BacktestConfig] = None,
    **kwargs,
) -> BacktestResult:
    """
    Convenience function to run a backtest.

    Args:
        strategy: Strategy to test
        data: Historical data
        symbol: Trading symbol
        config: Backtest configuration
        **kwargs: Additional data loading arguments

    Returns:
        BacktestResult
    """
    engine = BacktestEngine(config)
    engine.add_data(symbol, data, **kwargs)
    engine.add_strategy(strategy)
    return engine.run()
