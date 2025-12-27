"""Metrics collection utilities.

This module provides utilities for collecting and recording application metrics.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self, max_history: int = 1000):
        """Initialize the metrics collector.

        Args:
            max_history: Maximum number of metric entries to keep in memory
        """
        self.max_history = max_history
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = Lock()

    def increment(
        self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric.

        Args:
            metric_name: Name of the metric
            value: Value to increment by (default: 1)
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            self._counters[key] += value
            logger.debug(f"Incremented counter {key} by {value}")

    def gauge(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric value.

        Args:
            metric_name: Name of the metric
            value: Value to set
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            self._gauges[key] = value
            logger.debug(f"Set gauge {key} to {value}")

    def timing(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timing metric.

        Args:
            metric_name: Name of the metric
            value: Timing value in milliseconds
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            self._timings[key].append({"value": value, "timestamp": time.time()})
            logger.debug(f"Recorded timing {key}: {value}ms")

    def histogram(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric (alias for timing).

        Args:
            metric_name: Name of the metric
            value: Value to record
            tags: Optional tags for the metric
        """
        self.timing(metric_name, value, tags)

    def get_counter(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> int:
        """Get current counter value.

        Args:
            metric_name: Name of the metric
            tags: Optional tags for the metric

        Returns:
            Current counter value
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            return self._counters.get(key, 0)

    def get_gauge(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> float:
        """Get current gauge value.

        Args:
            metric_name: Name of the metric
            tags: Optional tags for the metric

        Returns:
            Current gauge value
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            return self._gauges.get(key, 0.0)

    def get_timings(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Get timing history.

        Args:
            metric_name: Name of the metric
            tags: Optional tags for the metric

        Returns:
            List of timing measurements
        """
        with self._lock:
            key = self._build_key(metric_name, tags)
            return list(self._timings.get(key, []))

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": {k: list(v) for k, v in self._timings.items()},
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timings.clear()
            logger.info("Reset all metrics")

    def _build_key(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Build a metric key from name and tags.

        Args:
            metric_name: Name of the metric
            tags: Optional tags for the metric

        Returns:
            Formatted metric key
        """
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{metric_name}[{tag_str}]"
        return metric_name


class TimingContext:
    """Context manager for timing operations."""

    def __init__(
        self,
        metrics: MetricsCollector,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Initialize timing context.

        Args:
            metrics: Metrics collector instance
            metric_name: Name of the timing metric
            tags: Optional tags for the metric
        """
        self.metrics = metrics
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record the duration."""
        if self.start_time is not None:
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.metrics.timing(self.metric_name, duration, self.tags)


# Global metrics instance
_global_metrics = MetricsCollector()


def increment(
    metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
) -> None:
    """Increment a counter metric using the global collector."""
    _global_metrics.increment(metric_name, value, tags)


def gauge(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Set a gauge metric using the global collector."""
    _global_metrics.gauge(metric_name, value, tags)


def timing(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a timing metric using the global collector."""
    _global_metrics.timing(metric_name, value, tags)


def histogram(
    metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a histogram metric using the global collector."""
    _global_metrics.histogram(metric_name, value, tags)


def time_operation(
    metric_name: str, tags: Optional[Dict[str, str]] = None
) -> TimingContext:
    """Create a timing context manager.

    Args:
        metric_name: Name of the timing metric
        tags: Optional tags for the metric

    Returns:
        Timing context manager
    """
    return TimingContext(_global_metrics, metric_name, tags)


def get_metrics() -> Dict[str, Any]:
    """Get all current metrics from the global collector."""
    return _global_metrics.get_all_metrics()


def reset_metrics() -> None:
    """Reset all metrics in the global collector."""
    _global_metrics.reset()


# Create a metrics object that matches the expected interface
class Metrics:
    """Metrics interface that matches the expected API."""

    @staticmethod
    def increment(
        metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        _global_metrics.increment(metric_name, value, tags)

    @staticmethod
    def gauge(
        metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        _global_metrics.gauge(metric_name, value, tags)

    @staticmethod
    def timing(
        metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timing metric."""
        _global_metrics.timing(metric_name, value, tags)

    @staticmethod
    def histogram(
        metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric."""
        _global_metrics.histogram(metric_name, value, tags)


# Global metrics instance that matches the expected interface
metrics = Metrics()
