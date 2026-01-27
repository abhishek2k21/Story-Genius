"""
Structured Logging
Production-ready structured logging with context propagation.
"""
import json
import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.observability.context import get_context


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context if available
        ctx = get_context()
        if ctx:
            log_entry["request_id"] = ctx.request_id
            if ctx.job_id:
                log_entry["job_id"] = ctx.job_id
            if ctx.batch_id:
                log_entry["batch_id"] = ctx.batch_id
            if ctx.user_id:
                log_entry["user_id"] = ctx.user_id
        
        # Add duration if provided
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        # Add extra data
        if hasattr(record, 'extra_data') and record.extra_data:
            log_entry["extra"] = record.extra_data
        
        # Add exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class PrettyFormatter(logging.Formatter):
    """Human-readable formatter for development"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m"
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        
        # Get context info
        ctx = get_context()
        ctx_str = ""
        if ctx:
            ctx_str = f" [{ctx.request_id[:8]}]"
            if ctx.job_id:
                ctx_str += f" job:{ctx.job_id[:8]}"
        
        msg = f"{color}{timestamp}{reset} {color}{record.levelname:8}{reset}{ctx_str} {record.name}: {record.getMessage()}"
        
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


class StructuredLogger:
    """Logger wrapper with structured data support"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log(self, level: int, message: str, duration_ms: int = None, **extra):
        record = self.logger.makeRecord(
            self.name, level, "", 0, message, None, None
        )
        if duration_ms is not None:
            record.duration_ms = duration_ms
        if extra:
            record.extra_data = extra
        self.logger.handle(record)
    
    def debug(self, message: str, **extra):
        self._log(logging.DEBUG, message, **extra)
    
    def info(self, message: str, duration_ms: int = None, **extra):
        self._log(logging.INFO, message, duration_ms=duration_ms, **extra)
    
    def warn(self, message: str, **extra):
        self._log(logging.WARNING, message, **extra)
    
    def error(self, message: str, exc_info: bool = False, **extra):
        if exc_info:
            self.logger.error(message, exc_info=True, extra={"extra_data": extra} if extra else None)
        else:
            self._log(logging.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        self._log(logging.CRITICAL, message, **extra)


# Logger registry
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def configure_logging(
    level: str = "INFO",
    format_type: str = "pretty",
    output: str = "console"
):
    """Configure logging for the application"""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root.handlers.clear()
    
    # Create handler
    if output == "console":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(output)
    
    # Set formatter
    if format_type == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(PrettyFormatter())
    
    handler.setLevel(getattr(logging, level.upper()))
    root.addHandler(handler)


# Initialize with development defaults
configure_logging(level="INFO", format_type="pretty")
