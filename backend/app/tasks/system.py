"""System maintenance and monitoring tasks.

This module contains system-level background tasks for monitoring, 
maintenance, and health checks.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil

from app.core.alerts import alert_manager
from app.core.config import settings
from app.core.metrics import metrics
from app.core.redis_service import redis_service
from app.core.task_queue import TaskQueueError, task
from app.db.database import get_db

logger = logging.getLogger(__name__)


@task(max_retries=2, queue="high_priority")
def check_market_status(self) -> Dict[str, Any]:
    """Check the status of market data providers and services.

    This task runs periodically to ensure market data services are
    functioning correctly and reports any issues.

    Returns:
        Status information about market data services
    """
    logger.info("Running market status check")
    start_time = time.time()

    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": [],
        "overall_status": "healthy",
    }

    # Check market data providers
    try:
        from app.services.market_data import MarketDataService

        market_service = MarketDataService()

        # Check if we can get a quote for a common symbol
        test_symbol = "AAPL"
        quote = market_service.get_latest_price(test_symbol)

        status["checks"].append(
            {
                "name": "market_data_service",
                "status": "healthy" if quote else "degraded",
                "details": {
                    "test_symbol": test_symbol,
                    "quote_received": bool(quote),
                    "quote_value": quote if quote else None,
                },
            }
        )

        if not quote:
            status["overall_status"] = "degraded"
            alert_manager.send_alert(
                "Market Data Service Degraded",
                f"Unable to retrieve quote for {test_symbol}",
                level="warning",
            )
    except Exception as e:
        logger.error(f"Market data service check failed: {e}")
        status["checks"].append(
            {"name": "market_data_service", "status": "unhealthy", "error": str(e)}
        )
        status["overall_status"] = "unhealthy"
        alert_manager.send_alert(
            "Market Data Service Unhealthy",
            f"Market data check failed: {e}",
            level="error",
        )

    # Check streaming service status
    try:
        from app.services.market_data_streaming import get_streaming_service

        streaming_service = get_streaming_service()

        connection_status = streaming_service.connection_status
        active_connections = len(streaming_service.websocket_manager.active_connections)

        streaming_status = "healthy"
        if not streaming_service.stream_active:
            streaming_status = "inactive"
        elif sum(connection_status.values()) == 0:
            streaming_status = "degraded"

        status["checks"].append(
            {
                "name": "streaming_service",
                "status": streaming_status,
                "details": {
                    "active": streaming_service.stream_active,
                    "connections": connection_status,
                    "client_count": active_connections,
                },
            }
        )

        if streaming_status != "healthy":
            status["overall_status"] = "degraded"
            alert_manager.send_alert(
                "Market Streaming Service Degraded",
                f"Streaming service status: {streaming_status}",
                level="warning",
            )
    except Exception as e:
        logger.error(f"Streaming service check failed: {e}")
        status["checks"].append(
            {"name": "streaming_service", "status": "unhealthy", "error": str(e)}
        )
        status["overall_status"] = "unhealthy"

    # Check database connectivity
    try:
        db = next(get_db())
        # Simple query to test connection
        result = db.execute("SELECT 1").fetchone()
        db.close()

        status["checks"].append(
            {
                "name": "database",
                "status": "healthy" if result else "unhealthy",
                "details": {"connection_successful": bool(result)},
            }
        )

        if not result:
            status["overall_status"] = "unhealthy"
            alert_manager.send_alert(
                "Database Connectivity Issue",
                "Database connection test failed",
                level="critical",
            )
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        status["checks"].append(
            {"name": "database", "status": "unhealthy", "error": str(e)}
        )
        status["overall_status"] = "unhealthy"
        alert_manager.send_alert(
            "Database Connection Failed", f"Database check error: {e}", level="critical"
        )

    # Check Redis connectivity
    try:
        redis_ping = redis_service.ping()

        status["checks"].append(
            {
                "name": "redis",
                "status": "healthy" if redis_ping else "unhealthy",
                "details": {
                    "ping_successful": bool(redis_ping),
                    "is_mock": redis_service.is_mock,
                },
            }
        )

        if not redis_ping and not redis_service.is_mock:
            status["overall_status"] = "unhealthy"
            alert_manager.send_alert(
                "Redis Connectivity Issue", "Redis ping test failed", level="error"
            )
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        status["checks"].append(
            {"name": "redis", "status": "unhealthy", "error": str(e)}
        )
        status["overall_status"] = "unhealthy"

    # Check system resources
    try:
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=1)
        memory_info = process.memory_info()

        # Check if resources are within acceptable limits
        cpu_status = "healthy"
        if cpu_percent > 80:
            cpu_status = "warning"
        if cpu_percent > 95:
            cpu_status = "critical"

        mem_status = "healthy"
        memory_mb = memory_info.rss / (1024 * 1024)
        if memory_mb > 1024:  # >1GB
            mem_status = "warning"
        if memory_mb > 1536:  # >1.5GB
            mem_status = "critical"

        resource_status = "healthy"
        if cpu_status == "critical" or mem_status == "critical":
            resource_status = "unhealthy"
        elif cpu_status == "warning" or mem_status == "warning":
            resource_status = "degraded"

        status["checks"].append(
            {
                "name": "system_resources",
                "status": resource_status,
                "details": {
                    "cpu_percent": cpu_percent,
                    "cpu_status": cpu_status,
                    "memory_mb": memory_mb,
                    "memory_status": mem_status,
                    "open_files": len(process.open_files()),
                    "threads": len(process.threads()),
                },
            }
        )

        if resource_status != "healthy":
            if resource_status == "unhealthy":
                status["overall_status"] = "unhealthy"
                alert_manager.send_alert(
                    "System Resource Critical",
                    f"CPU: {cpu_percent}%, Memory: {memory_mb:.2f}MB",
                    level="critical",
                )
            elif status["overall_status"] == "healthy":
                status["overall_status"] = "degraded"
                alert_manager.send_alert(
                    "System Resource Warning",
                    f"CPU: {cpu_percent}%, Memory: {memory_mb:.2f}MB",
                    level="warning",
                )
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        status["checks"].append(
            {"name": "system_resources", "status": "unknown", "error": str(e)}
        )

    # Record execution time
    execution_time = time.time() - start_time
    status["execution_time"] = execution_time

    # Log and store the results
    logger.info(
        f"Market status check completed in {execution_time:.2f}s: {status['overall_status']}"
    )

    # Store status in Redis with TTL
    redis_service.set("market_status:latest", status, ttl=600)  # 10 minutes

    # Record status in metrics
    metrics.gauge(
        "market_status",
        1 if status["overall_status"] == "healthy" else 0,
        tags={"status": status["overall_status"]},
    )

    return status


@task(max_retries=1, queue="low_priority")
def cleanup_old_tasks(self) -> Dict[str, Any]:
    """Clean up old task results and temporary files.

    This task runs periodically to prevent result backend bloat and
    clean up temporary files created by tasks.

    Returns:
        Cleanup statistics
    """
    logger.info("Running task cleanup")
    start_time = time.time()

    stats = {"task_results_cleaned": 0, "temp_files_removed": 0, "errors": []}

    # Clean up old task results from Redis
    try:
        # Get task result keys older than 3 days
        cutoff_time = datetime.utcnow() - timedelta(days=3)
        cutoff_timestamp = int(cutoff_time.timestamp())

        # Get keys with task result pattern
        task_keys = redis_service.keys("celery-task-meta-*")

        # Check each key's timestamp
        for key in task_keys:
            try:
                result_data = redis_service.get(key)
                if (
                    result_data
                    and isinstance(result_data, dict)
                    and "date_done" in result_data
                ):
                    # Check if this result is older than cutoff
                    task_time = result_data.get("date_done")
                    if task_time and task_time < cutoff_timestamp:
                        redis_service.delete(key)
                        stats["task_results_cleaned"] += 1
            except Exception as e:
                error_msg = f"Error cleaning key {key}: {e}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)
    except Exception as e:
        error_msg = f"Error cleaning task results: {e}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)

    # Clean up temporary files
    try:
        temp_dir = settings.TEMP_DIR
        if temp_dir and os.path.exists(temp_dir):
            cutoff_time = time.time() - (3 * 86400)  # 3 days ago

            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)

                # Skip if not a regular file
                if not os.path.isfile(filepath):
                    continue

                # Check file age
                file_time = os.path.getmtime(filepath)
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        stats["temp_files_removed"] += 1
                    except Exception as e:
                        error_msg = f"Error removing temp file {filepath}: {e}"
                        logger.warning(error_msg)
                        stats["errors"].append(error_msg)
    except Exception as e:
        error_msg = f"Error cleaning temporary files: {e}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)

    # Log and return results
    execution_time = time.time() - start_time
    stats["execution_time"] = execution_time

    logger.info(
        f"Task cleanup completed in {execution_time:.2f}s: "
        f"Cleaned {stats['task_results_cleaned']} task results, "
        f"removed {stats['temp_files_removed']} temp files"
    )

    # Record metrics
    metrics.gauge("task_cleanup.results_cleaned", stats["task_results_cleaned"])
    metrics.gauge("task_cleanup.files_removed", stats["temp_files_removed"])

    return stats


@task(queue="normal_priority")
def generate_system_report(self) -> Dict[str, Any]:
    """Generate a comprehensive system health report.

    This task produces a detailed report on system health, performance,
    and resource utilization for monitoring and diagnostics.

    Returns:
        Complete system health report
    """
    logger.info("Generating system health report")
    start_time = time.time()

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "system": {},
        "services": {},
        "database": {},
        "tasks": {},
        "metrics": {},
    }

    # System information
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        report["system"] = {
            "boot_time": boot_time,
            "uptime_seconds": time.time() - psutil.boot_time(),
            "cpu": {"percent": cpu_percent, "count": psutil.cpu_count()},
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "percent": disk.percent,
            },
        }
    except Exception as e:
        logger.error(f"Error collecting system info: {e}")
        report["system"]["error"] = str(e)

    # Service status
    try:
        # Get latest market status from Redis
        market_status = redis_service.get("market_status:latest")
        if market_status:
            report["services"]["market"] = market_status

        # Check Redis
        report["services"]["redis"] = {
            "connected": bool(redis_service.ping()),
            "is_mock": redis_service.is_mock,
            "info": redis_service.info() if hasattr(redis_service, "info") else None,
        }

        # Check task queue workers
        inspector = self.app.control.inspect()
        report["services"]["task_queue"] = {
            "registered_tasks": len(self.app.tasks),
            "workers": inspector.active_queues() or {},
            "stats": inspector.stats() or {},
        }
    except Exception as e:
        logger.error(f"Error collecting service status: {e}")
        report["services"]["error"] = str(e)

    # Database statistics
    try:
        db = next(get_db())

        # Get basic table statistics
        tables = [
            "users",
            "trades",
            "positions",
            "accounts",
            "portfolios",
            "subscriptions",
            "notifications",
        ]

        table_stats = {}
        for table in tables:
            try:
                count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                table_stats[table] = {"count": count}
            except Exception as table_e:
                table_stats[table] = {"error": str(table_e)}

        report["database"]["tables"] = table_stats

        # Get active connections
        conn_count = db.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
        ).scalar()

        report["database"]["connections"] = conn_count
        db.close()
    except Exception as e:
        logger.error(f"Error collecting database stats: {e}")
        report["database"]["error"] = str(e)

    # Task statistics
    try:
        report["tasks"]["active"] = len(list_active_tasks())

        # Error rates
        task_errors = redis_service.lrange("task_error_list", 0, -1)
        report["tasks"]["recent_errors"] = len(task_errors)

        # Recent task completions from metrics
        # (This would normally come from metrics store)
        report["tasks"]["metrics"] = {
            "success_rate": 0.95,  # Placeholder
            "avg_duration_ms": 150,  # Placeholder
        }
    except Exception as e:
        logger.error(f"Error collecting task stats: {e}")
        report["tasks"]["error"] = str(e)

    # Overall metrics (normally from Prometheus)
    report["metrics"] = {
        "api": {
            "requests_per_minute": 120,  # Placeholder
            "avg_response_time_ms": 85,  # Placeholder
            "error_rate": 0.02,  # Placeholder
        },
        "orders": {
            "executions_per_hour": 25,  # Placeholder
            "success_rate": 0.99,  # Placeholder
        },
    }

    # Calculate execution time
    execution_time = time.time() - start_time
    report["execution_time"] = execution_time

    # Store the report in Redis
    redis_service.set(
        f"system_report:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        report,
        ttl=86400 * 7,  # Store for 7 days
    )

    # Keep only the last 10 reports
    report_keys = redis_service.keys("system_report:*")
    report_keys.sort()
    if len(report_keys) > 10:
        for old_key in report_keys[:-10]:
            redis_service.delete(old_key)

    logger.info(f"System report generated in {execution_time:.2f}s")
    return report


def list_active_tasks() -> List[Dict[str, Any]]:
    """List all active tasks from the task queue."""
    from app.core.task_queue import list_active_tasks as list_tasks

    try:
        return list_tasks()
    except Exception as e:
        logger.error(f"Error listing active tasks: {e}")
        return []
