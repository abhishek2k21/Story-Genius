"""
Structured Logging Module for the Creative AI Shorts Platform.
Provides consistent logging format across all services with context propagation and rotation.
"""
import json
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum

from app.core.context import get_context

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
        
        # Add trace context if available
        try:
            from app.core.tracing import get_trace_context
            trace_ctx = get_trace_context()
            if trace_ctx:
                log_entry["trace_id"] = trace_ctx.trace_id
                log_entry["request_id"] = trace_ctx.request_id
                if trace_ctx.user_id:
                    log_entry["user_id"] = trace_ctx.user_id
                if trace_ctx.job_id:
                    log_entry["job_id"] = trace_ctx.job_id
                if trace_ctx.batch_id:
                    log_entry["batch_id"] = trace_ctx.batch_id
        except ImportError:
            pass
        
        # Fallback to old context system
        ctx = get_context()
        if ctx:
            if "request_id" not in log_entry:
                log_entry["request_id"] = ctx.request_id
            if ctx.job_id and "job_id" not in log_entry:
                log_entry["job_id"] = ctx.job_id
            if ctx.batch_id and "batch_id" not in log_entry:
                log_entry["batch_id"] = ctx.batch_id
            if ctx.user_id and "user_id" not in log_entry:
                log_entry["user_id"] = ctx.user_id
        
        # Add duration if provided
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        # Add status code if provided
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
        
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
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get context info
        ctx = get_context()
        ctx_str = ""
        if ctx:
            ctx_str = f" [{ctx.request_id[:8]}]"
            if ctx.job_id:
                ctx_str += f" job:{ctx.job_id[:8]}"
        
        msg = f"{color}{timestamp}{reset} {color}{record.levelname:8}{reset} {record.name}{ctx_str}: {record.getMessage()}"
        
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
    
    def warning(self, message: str, **extra):
        self._log(logging.WARNING, message, **extra)
    
    def error(self, message: str, exc_info: bool = False, **extra):
        if exc_info:
            self.logger.error(message, exc_info=True, extra={"extra_data": extra} if extra else None)
        else:
            self._log(logging.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        self._log(logging.CRITICAL, message, **extra)

    # Alias for warning to match standard logging
    warn = warning


# Logger registry
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


class JobLogger:
    """
    Job-specific logger compatibility wrapper.
    Ensures backward compatibility while using structured logging.
    """
    
    def __init__(self, job_id: str, logger: Optional[Union[logging.Logger, StructuredLogger]] = None):
        self.job_id = job_id
        # Use StructuredLogger if possible, but handle if a standard Logger is passed
        if logger:
             # If it's a standard logger, wrap it roughly or just store it. 
             # Ideally we want a StructuredLogger.
             if isinstance(logger, logging.Logger):
                 self.logger = get_logger(logger.name)
             else:
                 self.logger = logger
        else:
            self.logger = get_logger(f"job.{job_id[:8]}")
    
    def _format(self, msg: str) -> str:
        # We don't need to prefix with [Job ID] if we are using structural context,
        # but for message backward compatibility we'll keep it simple or rely on context.
        # However, this class explicitly asks for a job_id logger. 
        # We can add job_id to extra context if not already present.
        return msg
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, job_id=self.job_id, **kwargs)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, job_id=self.job_id, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, job_id=self.job_id, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, job_id=self.job_id, **kwargs)
    
    def step(self, step_num: int, total_steps: int, msg: str):
        """Log a step in the job execution."""
        self.info(f"Step {step_num}/{total_steps}: {msg}")


def configure_logging(
    level: str = "INFO",
    format_type: str = "pretty",
    log_file: Optional[str] = None,
    rotation_max_bytes: int = 10 * 1024 * 1024,  # 10MB
    rotation_backup_count: int = 5
):
    """
    Configure logging for the application.
    
    Args:
        level: Log level (INFO, DEBUG, etc.)
        format_type: 'json' or 'pretty'
        log_file: Path to log file for output. If set, logs to file with rotation.
                  If explicitly 'console' or None, logs to stdout.
    """
    root = logging.getLogger()
    log_level = getattr(logging, level.upper())
    root.setLevel(log_level)
    
    # Clear existing handlers
    root.handlers.clear()
    
    handlers = []
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # File Handler (Rotating)
    if log_file and log_file.lower() != "console":
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=rotation_max_bytes,
            backupCount=rotation_backup_count
        )
        handlers.append(file_handler)
        
    # Set formatter for all handlers
    formatter = StructuredFormatter() if format_type == "json" else PrettyFormatter()
    
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        root.addHandler(handler)

# Initialize with development defaults
# Check env vars for config or default to pretty
configure_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format_type=os.getenv("LOG_FORMAT", "pretty")
)
