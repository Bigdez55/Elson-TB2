from prometheus_client import Counter, Gauge, Histogram, Summary
import logging
import time
from typing import Dict, Optional, Any, List, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

# System metrics
http_requests_total = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, 75.0, 100.0, float("inf"))
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_name']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_name']
)

# Trading metrics
trades_executed_total = Counter(
    'trades_executed_total',
    'Total number of trades executed',
    ['status', 'strategy', 'symbol']
)

trade_execution_duration_seconds = Histogram(
    'trade_execution_duration_seconds',
    'Trade execution duration in seconds',
    ['strategy', 'symbol']
)

trade_execution_slippage = Histogram(
    'trade_execution_slippage',
    'Trade execution slippage as percentage',
    ['strategy', 'symbol'],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, float("inf"))
)

order_fill_rate = Gauge(
    'order_fill_rate',
    'Percentage of orders successfully filled',
    ['strategy']
)

market_data_latency_seconds = Histogram(
    'market_data_latency_seconds',
    'Market data latency in seconds',
    ['source'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, float("inf"))
)

market_data_errors_total = Counter(
    'market_data_errors_total',
    'Total number of market data errors',
    ['source', 'error_type']
)

# Portfolio metrics
portfolio_value = Gauge(
    'portfolio_value',
    'Current portfolio value',
    ['user_id', 'portfolio_id']
)

portfolio_cash_balance = Gauge(
    'portfolio_cash_balance',
    'Current portfolio cash balance',
    ['user_id', 'portfolio_id']
)

portfolio_return = Gauge(
    'portfolio_return',
    'Portfolio return as percentage',
    ['user_id', 'portfolio_id', 'time_period']
)

portfolio_drawdown = Gauge(
    'portfolio_drawdown',
    'Portfolio drawdown as percentage',
    ['user_id', 'portfolio_id']
)

position_count = Gauge(
    'position_count',
    'Number of positions in portfolio',
    ['user_id', 'portfolio_id']
)

position_allocation = Gauge(
    'position_allocation',
    'Position allocation as percentage of portfolio',
    ['user_id', 'portfolio_id', 'symbol']
)

# Risk metrics
circuit_breakers_active = Gauge(
    'circuit_breakers_active',
    'Number of active circuit breakers',
    ['type']
)

risk_limit_violations_total = Counter(
    'risk_limit_violations_total',
    'Total number of risk limit violations',
    ['limit_type', 'severity']
)

portfolio_volatility = Gauge(
    'portfolio_volatility',
    'Portfolio volatility (annualized)',
    ['user_id', 'portfolio_id']
)

portfolio_sharpe_ratio = Gauge(
    'portfolio_sharpe_ratio',
    'Portfolio Sharpe ratio',
    ['user_id', 'portfolio_id']
)

portfolio_correlation = Gauge(
    'portfolio_correlation',
    'Average correlation between portfolio positions',
    ['user_id', 'portfolio_id']
)

sector_exposure = Gauge(
    'sector_exposure',
    'Sector exposure as percentage of portfolio',
    ['user_id', 'portfolio_id', 'sector']
)

class MetricsMiddleware:
    """Middleware for collecting HTTP request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Extract method and path
        method = scope.get("method", "UNKNOWN")
        path = scope["path"]
        
        # Create a wrapper for send that captures the status code
        original_send = send
        status_code = "UNKNOWN"
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await original_send(message)
        
        # Process the request
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            http_requests_total.labels(method=method, endpoint=path, status=status_code).inc()
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
            
def track_db_query(operation: str, table: str) -> Callable:
    """Decorator for tracking database query duration."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
        return wrapper
    return decorator

def track_trade_execution(strategy: str, symbol: str, status: str) -> None:
    """
    Track trade execution metrics.
    
    Args:
        strategy: The trading strategy used
        symbol: The traded symbol
        status: The trade status (e.g., "filled", "rejected")
    """
    trades_executed_total.labels(status=status, strategy=strategy, symbol=symbol).inc()

def track_trade_duration(strategy: str, symbol: str, duration: float) -> None:
    """
    Track trade execution duration.
    
    Args:
        strategy: The trading strategy used
        symbol: The traded symbol
        duration: The execution duration in seconds
    """
    trade_execution_duration_seconds.labels(strategy=strategy, symbol=symbol).observe(duration)

def track_trade_slippage(strategy: str, symbol: str, slippage: float) -> None:
    """
    Track trade execution slippage.
    
    Args:
        strategy: The trading strategy used
        symbol: The traded symbol
        slippage: The execution slippage as percentage
    """
    trade_execution_slippage.labels(strategy=strategy, symbol=symbol).observe(slippage)

def update_portfolio_metrics(
    user_id: str,
    portfolio_id: str,
    total_value: float,
    cash_balance: float,
    positions: List[Dict[str, Any]]
) -> None:
    """
    Update portfolio metrics.
    
    Args:
        user_id: The user ID
        portfolio_id: The portfolio ID
        total_value: The total portfolio value
        cash_balance: The cash balance
        positions: The list of positions
    """
    portfolio_value.labels(user_id=user_id, portfolio_id=portfolio_id).set(total_value)
    portfolio_cash_balance.labels(user_id=user_id, portfolio_id=portfolio_id).set(cash_balance)
    position_count.labels(user_id=user_id, portfolio_id=portfolio_id).set(len(positions))
    
    # Update position allocations
    for position in positions:
        symbol = position.get("symbol")
        allocation = position.get("value", 0) / total_value if total_value > 0 else 0
        position_allocation.labels(user_id=user_id, portfolio_id=portfolio_id, symbol=symbol).set(allocation)

def update_risk_metrics(
    user_id: str,
    portfolio_id: str,
    volatility: float,
    sharpe_ratio: float,
    drawdown: float,
    sector_exposures: Dict[str, float]
) -> None:
    """
    Update risk metrics.
    
    Args:
        user_id: The user ID
        portfolio_id: The portfolio ID
        volatility: The portfolio volatility
        sharpe_ratio: The portfolio Sharpe ratio
        drawdown: The portfolio drawdown
        sector_exposures: The sector exposures
    """
    portfolio_volatility.labels(user_id=user_id, portfolio_id=portfolio_id).set(volatility)
    portfolio_sharpe_ratio.labels(user_id=user_id, portfolio_id=portfolio_id).set(sharpe_ratio)
    portfolio_drawdown.labels(user_id=user_id, portfolio_id=portfolio_id).set(drawdown)
    
    # Update sector exposures
    for sector, exposure in sector_exposures.items():
        sector_exposure.labels(user_id=user_id, portfolio_id=portfolio_id, sector=sector).set(exposure)

def update_circuit_breaker_metrics(breaker_counts: Dict[str, int]) -> None:
    """
    Update circuit breaker metrics.
    
    Args:
        breaker_counts: Dictionary of breaker type counts
    """
    for breaker_type, count in breaker_counts.items():
        circuit_breakers_active.labels(type=breaker_type).set(count)

def track_risk_limit_violation(limit_type: str, severity: str) -> None:
    """
    Track risk limit violation.
    
    Args:
        limit_type: The type of risk limit (e.g., "position_size", "drawdown")
        severity: The severity level (e.g., "warning", "critical")
    """
    risk_limit_violations_total.labels(limit_type=limit_type, severity=severity).inc()

def track_market_data_metrics(source: str, latency: float, error_type: Optional[str] = None) -> None:
    """
    Track market data metrics.
    
    Args:
        source: The market data source
        latency: The data retrieval latency in seconds
        error_type: Optional error type if an error occurred
    """
    market_data_latency_seconds.labels(source=source).observe(latency)
    
    if error_type:
        market_data_errors_total.labels(source=source, error_type=error_type).inc()

def record_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """
    Record a metric with a given name and value.
    
    This function provides a simpler interface to record metrics without having to
    worry about which specific type of metric (Counter, Gauge, etc.) should be used.
    
    Args:
        name: The name of the metric
        value: The metric value
        labels: Optional dictionary of labels
    """
    labels = labels or {}
    
    # In development/testing, we can just log metrics
    # as we might not have prometheus running
    if settings.ENVIRONMENT in ["development", "testing"]:
        labels_str = ", ".join(f"{k}={v}" for k, v in labels.items()) if labels else ""
        logger.debug(f"Metric: {name}={value} {labels_str}")
        return
    
    # Only use Prometheus in production/staging
    try:
        # Import here to avoid circular imports
        from prometheus_client import REGISTRY, Counter, Gauge, Histogram
        
        # Find registered metrics with matching name
        for metric in REGISTRY._names_to_collectors.values():
            if getattr(metric, "_name", None) == name:
                # Use the appropriate method based on metric type
                if hasattr(metric, 'inc'):
                    # For Counter
                    if labels:
                        metric.labels(**labels).inc(value)
                    else:
                        metric.inc(value)
                    return
                elif hasattr(metric, 'set'):
                    # For Gauge
                    if labels:
                        metric.labels(**labels).set(value)
                    else:
                        metric.set(value)
                    return
                elif hasattr(metric, 'observe'):
                    # For Histogram or Summary
                    if labels:
                        metric.labels(**labels).observe(value)
                    else:
                        metric.observe(value)
                    return
        
        # If no matching metric found, create a new one (defaults to Gauge)
        label_names = list(labels.keys()) if labels else []
        new_metric = Gauge(name, f'Auto-created metric: {name}', label_names)
        
        if labels:
            new_metric.labels(**labels).set(value)
        else:
            new_metric.set(value)
            
    except Exception as e:
        logger.error(f"Error recording metric {name}: {str(e)}")
        # Fall back to logging the metric if recording fails
        labels_str = ", ".join(f"{k}={v}" for k, v in labels.items()) if labels else ""
        logger.info(f"Metric: {name}={value} {labels_str}")