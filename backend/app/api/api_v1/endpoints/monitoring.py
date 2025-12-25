"""
Monitoring endpoints for the personal trading platform.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from datetime import datetime

from app.core.monitoring import (
    get_monitoring_summary,
    metrics_collector,
    trading_monitor,
    performance_tracker,
)
from app.api.deps import get_current_active_user as get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "elson-trading-platform",
    }


@router.get("/metrics")
async def get_metrics(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current metrics summary."""
    return get_monitoring_summary()


@router.get("/metrics/detailed")
async def get_detailed_metrics(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed metrics breakdown."""
    return {
        "metrics": metrics_collector.get_metrics_summary(),
        "trading": trading_monitor.get_trading_summary(),
        "performance": performance_tracker.get_performance_summary(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/trading/summary")
async def get_trading_summary(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get trading activity summary."""
    summary = trading_monitor.get_trading_summary()

    # Add recent trade history
    summary["recent_trades"] = list(trading_monitor.trade_history)[
        -10:
    ]  # Last 10 trades

    return summary


@router.get("/performance")
async def get_performance_summary(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get performance metrics summary."""
    perf_summary = performance_tracker.get_performance_summary()

    # Add threshold warnings
    warnings = []
    for operation, stats in perf_summary.items():
        if stats["avg"] > 1.0:
            warnings.append(
                {
                    "operation": operation,
                    "avg_duration": stats["avg"],
                    "message": f"{operation} is running slow (avg: {stats['avg']:.2f}s)",
                }
            )

    return {
        "performance": perf_summary,
        "warnings": warnings,
        "timestamp": datetime.now().isoformat(),
    }
