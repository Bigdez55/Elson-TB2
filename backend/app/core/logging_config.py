"""
Enhanced logging configuration for personal trading platform.

This provides structured logging with trading-specific improvements without 
the complexity of enterprise systems like ELK stack.
"""
import structlog
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional
import threading
from collections import defaultdict, deque

# Trading-specific log levels
TRADE_EXECUTION = 25  # Between INFO (20) and WARNING (30)
RISK_ALERT = 35  # Between WARNING (30) and ERROR (40)

# Add custom log levels
logging.addLevelName(TRADE_EXECUTION, "TRADE")
logging.addLevelName(RISK_ALERT, "RISK")


class TradingLogFilter(logging.Filter):
    """Filter to add trading context to log records."""

    def filter(self, record):
        # Add trading session context if available
        if not hasattr(record, "session_id"):
            record.session_id = getattr(
                threading.current_thread(), "session_id", "default"
            )

        # Add request ID if available (for API requests)
        if not hasattr(record, "request_id"):
            record.request_id = getattr(threading.current_thread(), "request_id", None)

        return True


class PerformanceLogFilter(logging.Filter):
    """Filter to track slow operations and add performance context."""

    def __init__(self):
        super().__init__()
        self.slow_operations = deque(maxlen=100)
        self.operation_counts = defaultdict(int)

    def filter(self, record):
        # Track operations with duration
        if hasattr(record, "duration") and record.duration > 1.0:
            self.slow_operations.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": getattr(record, "operation", "unknown"),
                    "duration": record.duration,
                    "function": record.funcName,
                    "module": record.module,
                }
            )

        # Count operations by type
        if hasattr(record, "operation"):
            self.operation_counts[record.operation] += 1

        return True


class TradingJSONFormatter(structlog.processors.JSONRenderer):
    """Enhanced JSON formatter with trading-specific fields."""

    def __call__(self, logger, method_name, event_dict):
        # Add standard trading fields
        if "trade_id" in event_dict:
            event_dict["log_type"] = "trade_execution"
        elif "portfolio_id" in event_dict:
            event_dict["log_type"] = "portfolio_operation"
        elif "symbol" in event_dict:
            event_dict["log_type"] = "market_data"
        elif "risk_score" in event_dict or "violation" in event_dict:
            event_dict["log_type"] = "risk_management"
        else:
            event_dict["log_type"] = "system"

        # Add performance indicators
        if "duration" in event_dict:
            if event_dict["duration"] > 5.0:
                event_dict["performance_flag"] = "very_slow"
            elif event_dict["duration"] > 1.0:
                event_dict["performance_flag"] = "slow"
            else:
                event_dict["performance_flag"] = "normal"

        return super().__call__(logger, method_name, event_dict)


def configure_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Configure enhanced structlog for trading platform."""

    # Create log directory structure
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create subdirectories for different log types
    (log_path / "trades").mkdir(exist_ok=True)
    (log_path / "errors").mkdir(exist_ok=True)
    (log_path / "performance").mkdir(exist_ok=True)
    (log_path / "risk").mkdir(exist_ok=True)

    # Configure structlog with enhanced processors
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.dict_tracebacks,
            TradingJSONFormatter(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with enhanced format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(TradingLogFilter())
    root_logger.addHandler(console_handler)

    # Main application log with rotation
    main_handler = RotatingFileHandler(
        log_path / "trading_main.log", maxBytes=50 * 1024 * 1024, backupCount=10  # 50MB
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(logging.Formatter("%(message)s"))  # JSON from structlog
    main_handler.addFilter(TradingLogFilter())
    root_logger.addHandler(main_handler)

    # Trade execution logs (separate file, daily rotation)
    trade_handler = TimedRotatingFileHandler(
        log_path / "trades" / "executions.log", when="midnight", backupCount=30
    )
    trade_handler.setLevel(TRADE_EXECUTION)
    trade_handler.setFormatter(logging.Formatter("%(message)s"))
    trade_handler.addFilter(lambda record: "trade_id" in getattr(record, "msg", "{}"))
    root_logger.addHandler(trade_handler)

    # Error logs (separate file)
    error_handler = RotatingFileHandler(
        log_path / "errors" / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(error_handler)

    # Risk management logs
    risk_handler = TimedRotatingFileHandler(
        log_path / "risk" / "risk_events.log",
        when="midnight",
        backupCount=90,  # Keep 3 months
    )
    risk_handler.setLevel(RISK_ALERT)
    risk_handler.setFormatter(logging.Formatter("%(message)s"))
    risk_handler.addFilter(
        lambda record: any(
            keyword in str(record.msg).lower()
            for keyword in ["risk", "violation", "circuit", "limit"]
        )
    )
    root_logger.addHandler(risk_handler)

    # Performance monitoring logs
    perf_filter = PerformanceLogFilter()
    perf_handler = TimedRotatingFileHandler(
        log_path / "performance" / "performance.log", when="midnight", backupCount=7
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(logging.Formatter("%(message)s"))
    perf_handler.addFilter(perf_filter)
    perf_handler.addFilter(
        lambda record: hasattr(record, "duration")
        or "performance" in str(record.msg).lower()
    )
    root_logger.addHandler(perf_handler)

    # Reduce noise from third-party libraries
    for logger_name in [
        "uvicorn",
        "sqlalchemy",
        "httpx",
        "asyncio",
        "urllib3",
        "requests",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Set specific levels for trading-related loggers
    logging.getLogger("trading").setLevel(logging.DEBUG)
    logging.getLogger("risk").setLevel(logging.DEBUG)
    logging.getLogger("portfolio").setLevel(logging.DEBUG)
    logging.getLogger("market_data").setLevel(logging.INFO)


# Enhanced trading-specific log categories with structured logging
def get_trade_logger():
    """Get a logger specifically for trade operations."""
    return structlog.get_logger("trading.trades")


def get_portfolio_logger():
    """Get a logger specifically for portfolio operations."""
    return structlog.get_logger("trading.portfolio")


def get_market_logger():
    """Get a logger specifically for market data operations."""
    return structlog.get_logger("trading.market")


def get_risk_logger():
    """Get a logger specifically for risk management."""
    return structlog.get_logger("trading.risk")


def get_performance_logger():
    """Get a logger specifically for performance monitoring."""
    return structlog.get_logger("trading.performance")


def get_ai_logger():
    """Get a logger specifically for AI/ML operations."""
    return structlog.get_logger("trading.ai")


# Enhanced logging helper functions
def log_trade_execution(
    trade_id: str,
    symbol: str,
    action: str,
    quantity: float,
    price: float,
    status: str,
    execution_time: Optional[float] = None,
    slippage: Optional[float] = None,
    **kwargs,
):
    """Log trade execution with standardized format."""
    logger = get_trade_logger()

    log_data = {
        "trade_id": trade_id,
        "symbol": symbol,
        "action": action,
        "quantity": float(quantity),
        "price": float(price),
        "status": status,
        "total_value": float(quantity * price),
    }

    if execution_time is not None:
        log_data["execution_time"] = float(execution_time)

    if slippage is not None:
        log_data["slippage"] = float(slippage)

    # Add any additional context
    log_data.update(kwargs)

    # Use INFO level for trade executions (structlog doesn't handle custom levels well)
    logger.info(f"TRADE: {action} {quantity} {symbol} @ ${price:.2f}", **log_data)


def log_risk_event(
    event_type: str,
    severity: str,
    message: str,
    user_id: Optional[int] = None,
    portfolio_id: Optional[int] = None,
    trade_id: Optional[str] = None,
    risk_score: Optional[float] = None,
    **kwargs,
):
    """Log risk management events with standardized format."""
    logger = get_risk_logger()

    log_data = {
        "event_type": event_type,
        "severity": severity,
        "message": message,
    }

    if user_id is not None:
        log_data["user_id"] = user_id

    if portfolio_id is not None:
        log_data["portfolio_id"] = portfolio_id

    if trade_id is not None:
        log_data["trade_id"] = trade_id

    if risk_score is not None:
        log_data["risk_score"] = float(risk_score)

    # Add any additional context
    log_data.update(kwargs)

    # Use WARNING level for risk events (structlog doesn't handle custom levels well)
    logger.warning(f"RISK: {event_type} - {message}", **log_data)


def log_portfolio_update(
    portfolio_id: int,
    user_id: int,
    total_value: float,
    change_amount: float,
    change_percent: float,
    operation: str = "update",
    **kwargs,
):
    """Log portfolio updates with standardized format."""
    logger = get_portfolio_logger()

    log_data = {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_value": float(total_value),
        "change_amount": float(change_amount),
        "change_percent": float(change_percent),
        "operation": operation,
    }

    # Add any additional context
    log_data.update(kwargs)

    logger.info(
        f"Portfolio {operation}: ${total_value:,.2f} ({change_percent:+.2f}%)",
        **log_data,
    )


def log_market_data_event(
    symbol: str,
    event_type: str,
    source: str,
    latency_ms: Optional[float] = None,
    price: Optional[float] = None,
    **kwargs,
):
    """Log market data events with standardized format."""
    logger = get_market_logger()

    log_data = {
        "symbol": symbol,
        "event_type": event_type,
        "source": source,
    }

    if latency_ms is not None:
        log_data["latency_ms"] = float(latency_ms)

    if price is not None:
        log_data["price"] = float(price)

    # Add any additional context
    log_data.update(kwargs)

    logger.info(f"Market data {event_type}: {symbol} from {source}", **log_data)


def log_performance_metric(
    operation: str,
    duration: float,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs,
):
    """Log performance metrics with standardized format."""
    logger = get_performance_logger()

    log_data = {
        "operation": operation,
        "duration": float(duration),
        "success": success,
    }

    if error:
        log_data["error"] = error

    # Add any additional context
    log_data.update(kwargs)

    level = logging.WARNING if duration > 5.0 else logging.INFO
    logger.log(level, f"Performance: {operation} took {duration:.3f}s", **log_data)


def log_ai_operation(
    operation: str,
    model_type: str,
    symbol: Optional[str] = None,
    confidence: Optional[float] = None,
    prediction: Optional[Dict[str, Any]] = None,
    execution_time: Optional[float] = None,
    **kwargs,
):
    """Log AI/ML operations with standardized format."""
    logger = get_ai_logger()

    log_data = {
        "operation": operation,
        "model_type": model_type,
    }

    if symbol:
        log_data["symbol"] = symbol

    if confidence is not None:
        log_data["confidence"] = float(confidence)

    if prediction:
        log_data["prediction"] = prediction

    if execution_time is not None:
        log_data["execution_time"] = float(execution_time)

    # Add any additional context
    log_data.update(kwargs)

    logger.info(f"AI operation: {operation} using {model_type}", **log_data)


def log_system_error(
    error: Exception,
    context: str,
    user_id: Optional[int] = None,
    trade_id: Optional[str] = None,
    recovery_action: Optional[str] = None,
    **kwargs,
):
    """Log system errors with standardized format and full context."""
    logger = structlog.get_logger("system.errors")

    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exc(),
    }

    if user_id is not None:
        log_data["user_id"] = user_id

    if trade_id:
        log_data["trade_id"] = trade_id

    if recovery_action:
        log_data["recovery_action"] = recovery_action

    # Add any additional context
    log_data.update(kwargs)

    logger.error(f"System error in {context}: {str(error)}", **log_data)


# Context managers for operation logging
class LogOperationContext:
    """Context manager for logging operation duration and outcome."""

    def __init__(
        self, operation: str, logger_name: str = "trading.performance", **context
    ):
        self.operation = operation
        self.logger = structlog.get_logger(logger_name)
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            log_performance_metric(
                operation=self.operation,
                duration=duration,
                success=True,
                **self.context,
            )
        else:
            log_performance_metric(
                operation=self.operation,
                duration=duration,
                success=False,
                error=str(exc_val),
                **self.context,
            )
            log_system_error(
                error=exc_val, context=f"Operation: {self.operation}", **self.context
            )


# Utility function to configure session context
def set_session_context(
    session_id: str, user_id: Optional[int] = None, request_id: Optional[str] = None
):
    """Set session context for current thread."""
    thread = threading.current_thread()
    thread.session_id = session_id
    if user_id:
        thread.user_id = user_id
    if request_id:
        thread.request_id = request_id


def clear_session_context():
    """Clear session context for current thread."""
    thread = threading.current_thread()
    if hasattr(thread, "session_id"):
        delattr(thread, "session_id")
    if hasattr(thread, "user_id"):
        delattr(thread, "user_id")
    if hasattr(thread, "request_id"):
        delattr(thread, "request_id")
