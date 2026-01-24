"""
Structured Logging Module for the Creative AI Shorts Platform.
Provides consistent logging format across all services.
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


class JobLogger:
    """
    Job-specific logger that prefixes messages with job_id.
    """
    
    def __init__(self, job_id: str, logger: Optional[logging.Logger] = None):
        self.job_id = job_id
        self.logger = logger or get_logger(f"job.{job_id[:8]}")
    
    def _format(self, msg: str) -> str:
        return f"[Job {self.job_id[:8]}] {msg}"
    
    def info(self, msg: str):
        self.logger.info(self._format(msg))
    
    def debug(self, msg: str):
        self.logger.debug(self._format(msg))
    
    def warning(self, msg: str):
        self.logger.warning(self._format(msg))
    
    def error(self, msg: str):
        self.logger.error(self._format(msg))
    
    def step(self, step_num: int, total_steps: int, msg: str):
        """Log a step in the job execution."""
        self.info(f"Step {step_num}/{total_steps}: {msg}")


# Default application logger
app_logger = get_logger("shorts_platform")
