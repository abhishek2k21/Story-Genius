"""
Retry Utilities
Retry logic with exponential backoff for external services.
"""
import asyncio
import random
from functools import wraps
from typing import Callable, Optional, Sequence, Type

from src.core.logging import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Sequence[Type[Exception]]] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = tuple(retryable_exceptions or [Exception])


DEFAULT_RETRY = RetryConfig()

# Service-specific configurations
GEMINI_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[ConnectionError, TimeoutError],
)

VEO_RETRY = RetryConfig(
    max_attempts=5,
    base_delay=5.0,
    max_delay=120.0,
    retryable_exceptions=[ConnectionError, TimeoutError],
)

TTS_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=15.0,
)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for next retry attempt."""
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add random jitter (0.5 to 1.5 of calculated delay)
        delay = delay * (0.5 + random.random())

    return delay


def retry(
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None,
):
    """
    Retry decorator with exponential backoff.

    Args:
        config: Retry configuration
        operation_name: Name for logging
    """
    cfg = config or DEFAULT_RETRY

    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, cfg.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except cfg.retryable_exceptions as e:
                    last_exception = e

                    if attempt < cfg.max_attempts:
                        delay = calculate_delay(attempt, cfg)
                        logger.warning(
                            f"Retry {attempt}/{cfg.max_attempts} for {name}: {e}. "
                            f"Waiting {delay:.1f}s before retry."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {cfg.max_attempts} attempts failed for {name}: {e}"
                        )

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None

            for attempt in range(1, cfg.max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except cfg.retryable_exceptions as e:
                    last_exception = e

                    if attempt < cfg.max_attempts:
                        delay = calculate_delay(attempt, cfg)
                        logger.warning(
                            f"Retry {attempt}/{cfg.max_attempts} for {name}: {e}. "
                            f"Waiting {delay:.1f}s before retry."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {cfg.max_attempts} attempts failed for {name}: {e}"
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation",
    **kwargs,
):
    """
    Retry an async function with configuration.

    Args:
        func: Async function to retry
        *args: Function arguments
        config: Retry configuration
        operation_name: Name for logging
        **kwargs: Function keyword arguments
    """
    cfg = config or DEFAULT_RETRY
    last_exception = None

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return await func(*args, **kwargs)

        except cfg.retryable_exceptions as e:
            last_exception = e

            if attempt < cfg.max_attempts:
                delay = calculate_delay(attempt, cfg)
                logger.warning(
                    f"Retry {attempt}/{cfg.max_attempts} for {operation_name}: {e}. "
                    f"Waiting {delay:.1f}s before retry."
                )
                await asyncio.sleep(delay)

    raise last_exception
