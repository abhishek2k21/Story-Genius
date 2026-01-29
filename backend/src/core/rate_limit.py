"""
Rate Limiting Middleware
Request throttling to prevent abuse.
"""
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class RateLimitConfig:
    """Rate limit configuration."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit


# Default configs by endpoint type
RATE_LIMITS = {
    "default": RateLimitConfig(60, 1000, 10),
    "generate": RateLimitConfig(10, 100, 3),  # AI generation endpoints
    "auth": RateLimitConfig(10, 50, 5),  # Auth endpoints
}


class TokenBucket:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # Tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Add tokens based on time elapsed
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """In-memory rate limiter."""

    def __init__(self):
        # client_id -> TokenBucket
        self._buckets: dict[str, TokenBucket] = {}
        # client_id -> minute_count
        self._minute_counts: dict[str, list[float]] = defaultdict(list)
        # client_id -> hour_count
        self._hour_counts: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key[:8]}"

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _get_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for path."""
        if "generate" in path or "video" in path:
            return RATE_LIMITS["generate"]
        if "auth" in path or "login" in path:
            return RATE_LIMITS["auth"]
        return RATE_LIMITS["default"]

    def _clean_old_entries(self, entries: list[float], max_age: float) -> list[float]:
        """Remove entries older than max_age."""
        cutoff = time.time() - max_age
        return [t for t in entries if t > cutoff]

    def is_allowed(self, request: Request) -> tuple[bool, Optional[dict]]:
        """Check if request is allowed."""
        client_id = self._get_client_id(request)
        config = self._get_config(request.url.path)
        now = time.time()

        # Check minute limit
        self._minute_counts[client_id] = self._clean_old_entries(
            self._minute_counts[client_id], 60
        )
        if len(self._minute_counts[client_id]) >= config.requests_per_minute:
            return False, {
                "error": "Rate limit exceeded",
                "limit": "per_minute",
                "retry_after": 60,
            }

        # Check hour limit
        self._hour_counts[client_id] = self._clean_old_entries(
            self._hour_counts[client_id], 3600
        )
        if len(self._hour_counts[client_id]) >= config.requests_per_hour:
            return False, {
                "error": "Rate limit exceeded",
                "limit": "per_hour",
                "retry_after": 3600,
            }

        # Check burst using token bucket
        if client_id not in self._buckets:
            self._buckets[client_id] = TokenBucket(
                rate=config.requests_per_minute / 60,
                capacity=config.burst_limit,
            )

        if not self._buckets[client_id].consume():
            return False, {
                "error": "Burst limit exceeded",
                "limit": "burst",
                "retry_after": 1,
            }

        # Record request
        self._minute_counts[client_id].append(now)
        self._hour_counts[client_id].append(now)

        return True, None


# Singleton limiter
_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        # Skip in debug mode (optional)
        if settings.debug:
            return await call_next(request)

        allowed, error_info = _limiter.is_allowed(request)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {request.url.path}",
                extra={"client": _limiter._get_client_id(request)},
            )
            raise HTTPException(
                status_code=429,
                detail=error_info,
                headers={"Retry-After": str(error_info.get("retry_after", 60))},
            )

        return await call_next(request)


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter singleton."""
    return _limiter
