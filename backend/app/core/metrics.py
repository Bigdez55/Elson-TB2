"""Metrics module - provides centralized metrics tracking.

This module provides a unified metrics interface used throughout the trading platform.
"""

from typing import Any, Dict, Optional

from app.core.monitoring import metrics_collector, performance_tracker, trading_monitor


class MetricsInterface:
    """Unified metrics interface for the trading platform."""

    def __init__(self):
        self._collector = metrics_collector
        self._trading_monitor = trading_monitor
        self._tracker = performance_tracker

    def increment(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        self._collector.increment_counter(name, value, labels)

    def gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        self._collector.set_gauge(name, value, labels)

    def histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        self._collector.record_histogram(name, value, labels)

    def record_trade(self, trade_data: Dict[str, Any]) -> None:
        """Record a trade execution."""
        self._trading_monitor.record_trade(trade_data)

    def record_latency(self, source: str, latency_ms: float) -> None:
        """Record market data latency."""
        self._trading_monitor.record_market_data_latency(source, latency_ms)

    def update_portfolio(self, portfolio_data: Dict[str, Any]) -> None:
        """Update portfolio metrics."""
        self._trading_monitor.update_portfolio_metrics(portfolio_data)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self._collector.get_metrics_summary()

    # Convenience methods for common patterns
    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Alias for increment."""
        self.increment(name, value, labels)

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Alias for gauge."""
        self.gauge(name, value, labels)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Alias for histogram."""
        self.histogram(name, value, labels)


# Global metrics instance
metrics = MetricsInterface()


def record_metric(
    name: str,
    value: float,
    metric_type: str = "counter",
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """Record a metric by type.

    Args:
        name: Metric name
        value: Metric value
        metric_type: One of 'counter', 'gauge', 'histogram'
        labels: Optional labels for the metric
    """
    if metric_type == "counter":
        metrics.increment(name, value, labels)
    elif metric_type == "gauge":
        metrics.gauge(name, value, labels)
    elif metric_type == "histogram":
        metrics.histogram(name, value, labels)
    else:
        # Default to counter
        metrics.increment(name, value, labels)


__all__ = ["metrics", "record_metric", "MetricsInterface"]
