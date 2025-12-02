import logging
import sys
import os
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from pythonjsonlogger import jsonlogger
from functools import wraps

from .config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Enhanced JSON formatter for structured logging."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add additional fields to the log record."""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
            
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
            
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
            
        # Add environment information
        log_record['env'] = os.environ.get('ENVIRONMENT', 'development')
            
        # Track log retention info
        log_record['retention_category'] = getattr(record, 'retention_category', 'standard')


class LogRetentionManager:
    """Manages log retention and archiving processes."""
    
    def __init__(self, 
                 log_dir: Union[str, Path],
                 archive_dir: Optional[Union[str, Path]] = None,
                 default_retention_days: int = 90):
        """Initialize LogRetentionManager with paths and settings."""
        self.log_dir = Path(log_dir)
        self.archive_dir = Path(archive_dir) if archive_dir else self.log_dir / "archive"
        self.default_retention_days = default_retention_days
        
        # Ensure directories exist
        self.log_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        
        # Retention periods in days for different categories
        self.retention_periods = {
            'financial': 365 * 7,  # 7 years for financial records
            'security': 365 * 3,   # 3 years for security records
            'audit': 365 * 5,      # 5 years for audit records
            'standard': default_retention_days,  # Default retention period
            'debug': 30            # 30 days for debug logs
        }
        
    def archive_old_logs(self, older_than_days: Optional[int] = None):
        """Archive log files older than the specified number of days."""
        if older_than_days is None:
            older_than_days = 30  # Default to archiving logs older than 30 days
            
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        archive_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"logs_archive_{archive_timestamp}.zip"
        archive_path = self.archive_dir / archive_filename
        
        # Find log files to archive
        to_archive = []
        for log_file in self.log_dir.glob("*.log*"):
            if os.path.isfile(log_file) and os.path.getmtime(log_file) < cutoff_time:
                to_archive.append(log_file)
                
        if not to_archive:
            logging.info("No log files to archive")
            return
            
        # Create ZIP archive
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for log_file in to_archive:
                zipf.write(log_file, arcname=log_file.name)
                
        # Remove archived files
        for log_file in to_archive:
            try:
                os.remove(log_file)
                logging.info(f"Archived and removed log file: {log_file}")
            except Exception as e:
                logging.error(f"Failed to remove archived log file {log_file}: {e}")
                
        logging.info(f"Archived {len(to_archive)} log files to {archive_path}")
        
    def cleanup_expired_archives(self):
        """Delete archived logs that have exceeded their retention period."""
        now = time.time()
        
        for archive_file in self.archive_dir.glob("*.zip"):
            try:
                # Extract the retention category from the archive if possible
                category = 'standard'  # Default category
                
                # Get file modification time
                file_mtime = os.path.getmtime(archive_file)
                file_age_days = (now - file_mtime) / (24 * 60 * 60)
                
                # Check if the file has exceeded its retention period
                retention_days = self.retention_periods.get(category, self.default_retention_days)
                if file_age_days > retention_days:
                    os.remove(archive_file)
                    logging.info(f"Deleted expired log archive: {archive_file}")
            except Exception as e:
                logging.error(f"Failed to process archive file {archive_file}: {e}")
                
    def run_maintenance(self):
        """Run a complete maintenance cycle."""
        logging.info("Starting log maintenance")
        self.archive_old_logs()
        self.cleanup_expired_archives()
        logging.info("Log maintenance completed")


class PiiFilter(logging.Filter):
    """Filter to mask PII data in logs."""
    
    def __init__(self, patterns=None):
        """Initialize with patterns to mask."""
        super().__init__()
        # Default patterns to mask
        self.patterns = patterns or {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b': '[SSN]',
            r'\b\d{16}\b': '[CREDIT_CARD]',
            r'\b\d{3}\b': '[CVV]'
        }
        
    def filter(self, record):
        """Mask PII in log records."""
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in self.patterns.items():
                import re
                msg = re.sub(pattern, replacement, msg)
            record.msg = msg
            
        return True

def setup_logging():
    """Configure application logging with advanced features."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log retention manager
    retention_manager = LogRetentionManager(
        log_dir=log_dir,
        default_retention_days=settings.LOG_RETENTION_DAYS
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Standard log file handler with rotation
    file_handler = TimedRotatingFileHandler(
        log_dir / settings.LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add PII filter to mask sensitive data
    pii_filter = PiiFilter()
    file_handler.addFilter(pii_filter)
    
    root_logger.addHandler(file_handler)
    
    # Special handlers for different log categories
    
    # Financial logs (high retention)
    financial_handler = TimedRotatingFileHandler(
        log_dir / "financial.log",
        when='midnight',
        interval=1,
        backupCount=30  # Keep a month of daily backups
    )
    financial_handler.setLevel(logging.INFO)
    financial_handler.setFormatter(file_formatter)
    financial_handler.addFilter(pii_filter)
    
    financial_logger = logging.getLogger("financial")
    financial_logger.propagate = False  # Don't propagate to root logger
    financial_logger.addHandler(financial_handler)
    
    # Security logs
    security_handler = TimedRotatingFileHandler(
        log_dir / "security.log",
        when='midnight',
        interval=1,
        backupCount=30
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(file_formatter)
    security_handler.addFilter(pii_filter)
    
    security_logger = logging.getLogger("security")
    security_logger.propagate = False
    security_logger.addHandler(security_handler)
    
    # Audit logs
    audit_handler = TimedRotatingFileHandler(
        log_dir / "audit.log",
        when='midnight',
        interval=1,
        backupCount=30
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(file_formatter)
    audit_handler.addFilter(pii_filter)
    
    audit_logger = logging.getLogger("audit")
    audit_logger.propagate = False
    audit_logger.addHandler(audit_handler)

    # Set logging levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Run log retention maintenance
    try:
        retention_manager.run_maintenance()
    except Exception as e:
        logging.error(f"Failed to run log maintenance: {e}")
        
    logging.info("Logging configured with retention policies")
    
    return retention_manager

class RequestIdFilter(logging.Filter):
    """Add request ID to log records"""
    def __init__(self, request_id):
        super().__init__()
        self.request_id = request_id

    def filter(self, record):
        record.request_id = self.request_id
        return True

class TradeLogger:
    """Specialized logger for trade operations"""
    def __init__(self, logger_name="trade"):
        self.logger = logging.getLogger(logger_name)
        
    def log_trade_execution(self, trade_data: dict):
        """Log trade execution details"""
        self.logger.info(
            "Trade executed",
            extra={
                "trade_id": trade_data.get("id"),
                "symbol": trade_data.get("symbol"),
                "side": trade_data.get("side"),
                "quantity": trade_data.get("quantity"),
                "price": trade_data.get("price"),
                "status": trade_data.get("status")
            }
        )
        
    def log_trade_error(self, error: Exception, trade_data: dict = None):
        """Log trade execution errors"""
        extra = {"error_type": type(error).__name__}
        if trade_data:
            extra.update({
                "trade_id": trade_data.get("id"),
                "symbol": trade_data.get("symbol")
            })
        
        self.logger.error(
            f"Trade error: {str(error)}",
            extra=extra,
            exc_info=True
        )

class MarketDataLogger:
    """Specialized logger for market data operations"""
    def __init__(self, logger_name="market_data"):
        self.logger = logging.getLogger(logger_name)
        
    def log_market_data_request(self, symbol: str, data_type: str):
        """Log market data requests"""
        self.logger.info(
            "Market data requested",
            extra={
                "symbol": symbol,
                "data_type": data_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    def log_market_data_error(self, error: Exception, symbol: str = None):
        """Log market data errors"""
        extra = {
            "error_type": type(error).__name__,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.error(
            f"Market data error: {str(error)}",
            extra=extra,
            exc_info=True
        )

# Initialize specialized loggers
trade_logger = TradeLogger()
market_data_logger = MarketDataLogger()