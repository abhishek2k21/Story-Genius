"""
Structured Logging Configuration
"""
import logging
import sys
from typing import Optional

from src.core.settings import settings


class ColoredFormatter(logging.Formatter):
    """Formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name or "story_genius")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if settings.debug:
            handler.setFormatter(ColoredFormatter(
                "%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.setLevel(logging.DEBUG)
        else:
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.setLevel(logging.INFO)

        logger.addHandler(handler)
        logger.propagate = False

    return logger
