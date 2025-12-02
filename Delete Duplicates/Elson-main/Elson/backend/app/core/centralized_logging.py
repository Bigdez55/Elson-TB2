"""
Centralized logging module for the Elson Wealth App.

This module configures Python logging to send logs to a centralized ELK 
(Elasticsearch, Logstash, Kibana) stack via Fluentd.
"""

import logging
import socket
import os
import sys
import json
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import fluent.handler
import fluent.sender

from .config import settings

# Configure module-level logger
logger = logging.getLogger(__name__)

# Define custom JSON formatter
class ElsonJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        super(ElsonJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add environment info
        log_record['environment'] = settings.ENVIRONMENT
        log_record['version'] = settings.VERSION
        log_record['hostname'] = socket.gethostname()
        
        # Add process/thread info
        log_record['pid'] = os.getpid()
        log_record['thread'] = record.threadName
        
        # Include exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }

# Custom Fluent handler with enhanced error handling
class EnhancedFluentHandler(fluent.handler.FluentHandler):
    """Fluent handler with better error handling and retry logic."""
    
    def __init__(self, *args, **kwargs):
        self.fallback_file = kwargs.pop('fallback_file', None)
        super(EnhancedFluentHandler, self).__init__(*args, **kwargs)
        
        # Configure local file fallback
        if self.fallback_file:
            self.file_handler = RotatingFileHandler(
                self.fallback_file,
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5
            )
            self.file_handler.setFormatter(ElsonJsonFormatter())
    
    def emit(self, record):
        """Override emit to handle connection failures."""
        try:
            super(EnhancedFluentHandler, self).emit(record)
        except Exception as e:
            # Log error but don't crash
            sys.stderr.write(f"Error sending log to Fluentd: {str(e)}\n")
            
            # Use file fallback if configured
            if hasattr(self, 'file_handler'):
                try:
                    self.file_handler.emit(record)
                except Exception as file_error:
                    sys.stderr.write(f"Error writing to fallback log: {str(file_error)}\n")

def setup_centralized_logging():
    """
    Setup centralized logging for the application.
    
    This configures Python's logging system to send logs to Fluentd,
    which forwards them to Elasticsearch for centralized storage and 
    visualization in Kibana.
    """
    # Skip setup if not enabled
    if not settings.ELK_LOGGING_ENABLED:
        logger.info("Centralized logging is disabled. Using standard logging.")
        return
    
    try:
        # Set global log level
        root_logger = logging.getLogger()
        root_logger.setLevel(settings.LOG_LEVEL)
        
        # Configure Fluent handler
        fluent_handler = EnhancedFluentHandler(
            'elson.backend',
            host=settings.FLUENTD_HOST,
            port=int(settings.FLUENTD_PORT),
            fallback_file=settings.LOG_FILE_PATH,
            nanosecond_precision=True
        )
        
        # Setup formatter 
        fluent_formatter = fluent.handler.FluentRecordFormatter({
            'level': '%(levelname)s',
            'logger': '%(name)s',
            'message': '%(message)s',
            'module': '%(module)s',
            'function': '%(funcName)s',
            'line': '%(lineno)d',
            'timestamp': '%(created)f'
        })
        fluent_handler.setFormatter(fluent_formatter)
        
        # Add handler to root logger
        root_logger.addHandler(fluent_handler)
        
        # Configure console logging for local development
        if settings.ENVIRONMENT in ['development', 'local']:
            console_handler = logging.StreamHandler()
            console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            console_formatter = logging.Formatter(console_format)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Setup JSON file logging as backup
        file_handler = RotatingFileHandler(
            settings.LOG_FILE_PATH or '/tmp/elson-backend.log',
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(ElsonJsonFormatter())
        root_logger.addHandler(file_handler)
        
        # Configure sensitive loggers
        for logger_name in [
            'sqlalchemy.engine',
            'urllib3',
            'requests',
            'werkzeug',
            'stripe',
            'pandas',
            'elasticsearch'
        ]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
        
        logger.info(
            "Centralized logging configured successfully", 
            extra={
                "fluentd_host": settings.FLUENTD_HOST,
                "environment": settings.ENVIRONMENT,
                "service": "backend"
            }
        )
    except Exception as e:
        # Don't fail application startup if logging setup fails
        logger.error(f"Failed to configure centralized logging: {str(e)}")
        traceback.print_exc()

def shutdown_logging():
    """Properly close all logging handlers."""
    for handler in logging.getLogger().handlers:
        try:
            handler.close()
        except Exception as e:
            sys.stderr.write(f"Error closing log handler: {str(e)}\n")

# Custom handler for request logs
class RequestLoggingHandler:
    """Handler for API request logging."""
    
    @staticmethod
    def log_request(request, response=None, error=None):
        """Log API request details."""
        try:
            # Basic request info
            request_data = {
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "request_id": request.headers.get("x-request-id", "none"),
                "query_params": dict(request.query_params),
            }
            
            # User/auth info if available
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                request_data["user_id"] = user_id
                
            # Response info if available
            if response:
                request_data["status_code"] = response.status_code
                request_data["response_time_ms"] = getattr(
                    request.state, "response_time", 0
                )
            
            # Error info if available
            if error:
                request_data["error"] = str(error)
                if isinstance(error, Exception) and hasattr(error, "__traceback__"):
                    request_data["traceback"] = "".join(
                        traceback.format_exception(
                            type(error), error, error.__traceback__
                        )
                    )
            
            # Log level depends on status code or error
            log_level = logging.INFO
            if response and response.status_code >= 400:
                log_level = logging.WARNING
            if response and response.status_code >= 500 or error:
                log_level = logging.ERROR
                
            logger.log(
                log_level,
                f"API request: {request.method} {request.url.path}",
                extra={"request": request_data}
            )
        except Exception as e:
            # Never fail because of logging
            logger.error(f"Error in request logging: {str(e)}")
            
# EOF