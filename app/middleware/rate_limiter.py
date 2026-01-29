"""
Advanced Rate Limiting Middleware.
Token bucket algorithm with per-endpoint limits.
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.cache import cache_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """
    Token bucket rate limiter.
    
    Features:
    - Per-IP rate limiting
    - Per-endpoint custom limits
    - Sliding window
    - Redis-backed (distributed)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.burst = burst_size
        self.window = 60  # seconds
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Get applicable rate limit for this endpoint
        limit, window = self._get_rate_limit(request.url.path)
        
        # Check rate limit
        allowed = await self._check_rate_limit(
            client_ip,
            request.url.path,
            limit,
            window
        )
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {request.url.path}"
            )
            
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = await self._get_remaining(client_ip, request.url.path)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self._get_reset_time(window))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address.
        
        Checks X-Forwarded-For header first (for proxies/load balancers).
        
        Args:
            request: FastAPI request
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For (set by load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (original client)
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit(self, path: str) -> tuple[int, int]:
        """
        Get rate limit for endpoint.
        
        Different endpoints have different limits:
        - Auth endpoints: Stricter (prevent brute force)
        - API endpoints: Normal
        - Public endpoints: Lenient
        
        Args:
            path: Request path
            
        Returns:
            Tuple of (requests_per_window, window_seconds)
        """
        # Endpoint-specific limits
        limits = {
            # Authentication (very strict - prevent brute force)
            "/oauth/token": (5, 60),  # 5 req/min
            "/api/login": (5, 60),
            "/api/register": (3, 60),
            
            # Password reset (strict)
            "/api/password/reset": (3, 300),  # 3 req/5min
            
            # GDPR endpoints (moderate)
            "/gdpr/data-export": (10, 60),
            "/gdpr/delete-account": (2, 60),
            
            # API endpoints (normal)
            "/api/": (60, 60),  # 60 req/min
            
            # Public endpoints (lenient)
            "/health": (120, 60),
            "/metrics": (120, 60),
        }
        
        # Find most specific match
        for endpoint, (limit, window) in limits.items():
            if path.startswith(endpoint):
                return (limit, window)
        
        # Default limit
        return (self.rpm, self.window)
    
    async def _check_rate_limit(
        self,
        client_id: str,
        path: str,
        limit: int,
        window: int
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Uses sliding window counter in Redis.
        
        Args:
            client_id: Client identifier (IP)
            path: Request path
            limit: Max requests per window
            window: Window size in seconds
            
        Returns:
            True if allowed, False if rate limited
        """
        # Redis key for this client + path
        key = f"ratelimit:{client_id}:{path}:{window}"
        
        try:
            # Get current count
            current = await cache_manager.get(key)
            
            if current is None:
                # First request in window
                await cache_manager.set(key, 1, expire=window)
                return True
            
            current_count = int(current)
            
            if current_count >= limit:
                # Rate limit exceeded
                return False
            
            # Increment counter
            await cache_manager.incr(key)
            return True
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request (fail open)
            return True
    
    async def _get_remaining(self, client_id: str, path: str) -> int:
        """Get remaining requests in current window."""
        limit, window = self._get_rate_limit(path)
        key = f"ratelimit:{client_id}:{path}:{window}"
        
        try:
            current = await cache_manager.get(key)
            if current is None:
                return limit
            
            return max(0, limit - int(current))
        except Exception:
            return limit
    
    def _get_reset_time(self, window: int) -> int:
        """Get timestamp when rate limit resets."""
        reset_time = datetime.utcnow() + timedelta(seconds=window)
        return int(reset_time.timestamp())


# Integration with FastAPI
# Add to main.py:
# from app.middleware.rate_limiter import RateLimiter
# app.add_middleware(RateLimiter, requests_per_minute=60)
