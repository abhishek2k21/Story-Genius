"""
Observability Module
Request tracing, metrics, and structured logging.
"""
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)

# Context variables for request tracing
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_ctx.get()


def get_user_id() -> Optional[str]:
    """Get current user ID from context."""
    return user_id_ctx.get()


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for tracing."""
    request_id_ctx.set(request_id)
    if user_id:
        user_id_ctx.set(user_id)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]


# ========================
# Metrics Collection
# ========================

class Metrics:
    """Simple in-memory metrics collection."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._timings: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + value

    def timing(self, name: str, duration_ms: float) -> None:
        """Record a timing."""
        if name not in self._timings:
            self._timings[name] = []
        self._timings[name].append(duration_ms)
        # Keep only last 1000 timings
        self._timings[name] = self._timings[name][-1000:]

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)

    def get_timing_stats(self, name: str) -> dict:
        """Get timing statistics."""
        timings = self._timings.get(name, [])
        if not timings:
            return {"count": 0}

        return {
            "count": len(timings),
            "avg_ms": sum(timings) / len(timings),
            "min_ms": min(timings),
            "max_ms": max(timings),
        }

    def get_all(self) -> dict:
        """Get all metrics."""
        return {
            "counters": self._counters.copy(),
            "timings": {k: self.get_timing_stats(k) for k in self._timings},
        }


# Singleton metrics instance
_metrics = Metrics()


def get_metrics() -> Metrics:
    """Get metrics singleton."""
    return _metrics


# ========================
# Decorators
# ========================

def trace(
    operation: str,
    log_args: bool = False,
    log_result: bool = False,
):
    """
    Decorator to trace function execution.

    Args:
        operation: Name of the operation for logging
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request_id = get_request_id() or generate_request_id()
            start_time = time.perf_counter()

            extra = {"request_id": request_id, "operation": operation}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Starting {operation}", extra=extra)

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                _metrics.increment(f"{operation}.success")
                _metrics.timing(operation, duration_ms)

                log_extra = {**extra, "duration_ms": round(duration_ms, 2)}
                if log_result:
                    log_extra["result"] = str(result)[:200]

                logger.info(f"Completed {operation}", extra=log_extra)
                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _metrics.increment(f"{operation}.error")

                logger.error(
                    f"Failed {operation}: {e}",
                    extra={**extra, "duration_ms": round(duration_ms, 2), "error": str(e)},
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request_id = get_request_id() or generate_request_id()
            start_time = time.perf_counter()

            extra = {"request_id": request_id, "operation": operation}

            logger.debug(f"Starting {operation}", extra=extra)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                _metrics.increment(f"{operation}.success")
                _metrics.timing(operation, duration_ms)

                logger.info(f"Completed {operation}", extra={"duration_ms": round(duration_ms, 2)})
                return result

            except Exception as e:
                _metrics.increment(f"{operation}.error")
                logger.error(f"Failed {operation}: {e}")
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def timed(name: str):
    """Simple timing decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                _metrics.timing(name, duration_ms)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                _metrics.timing(name, duration_ms)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
