"""
Lightweight monitoring system for personal trading platform.

This module provides essential monitoring capabilities without the overhead
of enterprise-grade systems like Prometheus or ELK stack.
"""

import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Simple in-memory metrics collector for personal trading."""

    def __init__(self, max_history_hours: int = 24):
        self.max_history = max_history_hours * 3600  # Convert to seconds
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self._lock = threading.Lock()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self.counters[key] += value

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self.gauges[key] = value

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric (stores recent values)."""
        key = self._make_key(name, labels)
        with self._lock:
            self.metrics[key].append({"timestamp": time.time(), "value": value})

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        with self._lock:
            # Clean old histogram entries
            cutoff_time = time.time() - self.max_history
            for key in self.metrics:
                while (
                    self.metrics[key]
                    and self.metrics[key][0]["timestamp"] < cutoff_time
                ):
                    self.metrics[key].popleft()

            # Calculate summaries
            summary = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {},
            }

            for key, values in self.metrics.items():
                if values:
                    value_list = [v["value"] for v in values]
                    summary["histograms"][key] = {
                        "count": len(value_list),
                        "min": min(value_list),
                        "max": max(value_list),
                        "avg": sum(value_list) / len(value_list),
                        "last": value_list[-1],
                    }

            return summary

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"


class TradingMonitor:
    """Monitor specifically for trading operations."""

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.trade_history = deque(maxlen=100)  # Keep last 100 trades

    def record_trade(self, trade_data: Dict[str, Any]):
        """Record a trade execution."""
        self.trade_history.append(
            {"timestamp": datetime.now().isoformat(), **trade_data}
        )

        # Update metrics
        status = trade_data.get("status", "unknown")
        symbol = trade_data.get("symbol", "unknown")

        self.metrics.increment_counter(
            "trades_total", labels={"status": status, "symbol": symbol}
        )

        if "execution_time" in trade_data:
            self.metrics.record_histogram(
                "trade_execution_seconds",
                trade_data["execution_time"],
                labels={"symbol": symbol},
            )

        if "slippage" in trade_data:
            self.metrics.record_histogram(
                "trade_slippage_percent",
                trade_data["slippage"],
                labels={"symbol": symbol},
            )

    def record_market_data_latency(self, source: str, latency_ms: float):
        """Record market data feed latency."""
        self.metrics.record_histogram(
            "market_data_latency_ms", latency_ms, labels={"source": source}
        )

    def update_portfolio_metrics(self, portfolio_data: Dict[str, Any]):
        """Update portfolio metrics."""
        self.metrics.set_gauge("portfolio_value", portfolio_data.get("total_value", 0))
        self.metrics.set_gauge("portfolio_cash", portfolio_data.get("cash_balance", 0))
        self.metrics.set_gauge(
            "portfolio_positions", portfolio_data.get("position_count", 0)
        )

        if "daily_return" in portfolio_data:
            self.metrics.set_gauge(
                "portfolio_daily_return_percent", portfolio_data["daily_return"]
            )

        if "positions" in portfolio_data:
            for position in portfolio_data["positions"]:
                symbol = position.get("symbol")
                if symbol:
                    self.metrics.set_gauge(
                        "position_value",
                        position.get("value", 0),
                        labels={"symbol": symbol},
                    )

    def get_trading_summary(self) -> Dict[str, Any]:
        """Get a summary of trading activity."""
        metrics_summary = self.metrics.get_metrics_summary()

        # Calculate additional trading-specific metrics
        recent_trades = list(self.trade_history)
        success_count = sum(1 for t in recent_trades if t.get("status") == "filled")
        total_trades = len(recent_trades)

        return {
            "metrics": metrics_summary,
            "trading": {
                "recent_trade_count": total_trades,
                "success_rate": success_count / total_trades if total_trades > 0 else 0,
                "last_trade": recent_trades[-1] if recent_trades else None,
            },
        }


class PerformanceTracker:
    """Track performance with minimal overhead."""

    def __init__(self):
        self.timings = defaultdict(list)

    def track_duration(self, operation: str):
        """Decorator to track operation duration."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.timings[operation].append(duration)
                    if duration > 1.0:  # Log slow operations
                        logger.warning(
                            f"Slow operation: {operation}", duration=duration
                        )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"Operation failed: {operation}",
                        duration=duration,
                        error=str(e),
                    )
                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.timings[operation].append(duration)
                    if duration > 1.0:  # Log slow operations
                        logger.warning(
                            f"Slow operation: {operation}", duration=duration
                        )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"Operation failed: {operation}",
                        duration=duration,
                        error=str(e),
                    )
                    raise

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        for operation, durations in self.timings.items():
            if durations:
                summary[operation] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "max": max(durations),
                    "min": min(durations),
                }
        return summary


class SimpleFileLogger:
    """Simple file-based logging for important events."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_trade(self, trade_data: Dict[str, Any]):
        """Log trade to a dedicated file."""
        log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "type": "trade",
                        **trade_data,
                    }
                )
                + "\n"
            )

    def log_error(self, error_data: Dict[str, Any]):
        """Log errors to a dedicated file."""
        log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "type": "error",
                        **error_data,
                    }
                )
                + "\n"
            )

    def log_performance(self, perf_data: Dict[str, Any]):
        """Log daily performance snapshot."""
        log_file = self.log_dir / f"performance_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "type": "performance",
                        **perf_data,
                    }
                )
                + "\n"
            )


# Global instances
metrics_collector = MetricsCollector()
trading_monitor = TradingMonitor(metrics_collector)
performance_tracker = PerformanceTracker()
file_logger = SimpleFileLogger()


# Convenience functions
def track_trade(trade_data: Dict[str, Any]):
    """Track a trade execution."""
    trading_monitor.record_trade(trade_data)
    file_logger.log_trade(trade_data)


def track_market_latency(source: str, latency_ms: float):
    """Track market data latency."""
    trading_monitor.record_market_data_latency(source, latency_ms)


def update_portfolio(portfolio_data: Dict[str, Any]):
    """Update portfolio metrics."""
    trading_monitor.update_portfolio_metrics(portfolio_data)


def get_monitoring_summary() -> Dict[str, Any]:
    """Get complete monitoring summary."""
    return {
        "trading": trading_monitor.get_trading_summary(),
        "performance": performance_tracker.get_performance_summary(),
        "timestamp": datetime.now().isoformat(),
    }
