"""
Sliding Window Rate Limiter
Implements per-user and per-endpoint rate limiting with sliding time windows.
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


class UserTier(str, Enum):
    """User tier enumeration"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int = 0  # Allowed burst above limit
    
    def __post_init__(self):
        if self.burst_size == 0:
            self.burst_size = self.requests_per_minute // 2


# Tier-based rate limits
TIER_LIMITS = {
    UserTier.FREE: RateLimit(
        requests_per_minute=10,
        requests_per_hour=100
    ),
    UserTier.PRO: RateLimit(
        requests_per_minute=100,
        requests_per_hour=10000
    ),
    UserTier.ENTERPRISE: RateLimit(
        requests_per_minute=1000,
        requests_per_hour=100000
    )
}


@dataclass
class RequestRecord:
    """Single request record"""
    timestamp: float
    endpoint: str
    user_id: str


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    More accurate than fixed window as it doesn't reset at boundaries.
    """
    
    def __init__(self):
        # Store request records per user
        self._user_requests: Dict[str, List[RequestRecord]] = {}
        logger.info("SlidingWindowRateLimiter initialized")
    
    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        tier: UserTier = UserTier.FREE
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            user_id: User ID
            endpoint: API endpoint
            tier: User tier
        
        Returns:
            (allowed: bool, retry_after_seconds: Optional[int])
        """
        now = time.time()
        limits = TIER_LIMITS[tier]
        
        # Initialize user if not exists
        if user_id not in self._user_requests:
            self._user_requests[user_id] = []
        
        # Clean up old requests
        self._cleanup_old_requests(user_id, now)
        
        # Count requests in sliding windows
        minute_ago = now - 60
        hour_ago = now - 3600
        
        requests = self._user_requests[user_id]
        
        requests_last_minute = sum(
            1 for r in requests if r.timestamp > minute_ago
        )
        requests_last_hour = sum(
            1 for r in requests if r.timestamp > hour_ago
        )
        
        # Check limits
        if requests_last_minute >= limits.requests_per_minute + limits.burst_size:
            retry_after = int(60 - (now - requests[0].timestamp))
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{requests_last_minute}/{limits.requests_per_minute} per minute"
            )
            return False, retry_after
        
        if requests_last_hour >= limits.requests_per_hour:
            retry_after = int(3600 - (now - requests[0].timestamp))
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{requests_last_hour}/{limits.requests_per_hour} per hour"
            )
            return False, retry_after
        
        # Record request
        self._user_requests[user_id].append(
            RequestRecord(timestamp=now, endpoint=endpoint, user_id=user_id)
        )
        
        logger.debug(
            f"Request allowed for user {user_id}: "
            f"{requests_last_minute + 1}/{limits.requests_per_minute} per minute"
        )
        
        return True, None
    
    def get_usage(self, user_id: str, tier: UserTier = UserTier.FREE) -> Dict:
        """
        Get current usage for user.
        
        Args:
            user_id: User ID
            tier: User tier
        
        Returns:
            Usage statistics
        """
        if user_id not in self._user_requests:
            return {
                "requests_last_minute": 0,
                "requests_last_hour": 0,
                "limit_per_minute": TIER_LIMITS[tier].requests_per_minute,
                "limit_per_hour": TIER_LIMITS[tier].requests_per_hour
            }
        
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        requests = self._user_requests[user_id]
        
        return {
            "requests_last_minute": sum(1 for r in requests if r.timestamp > minute_ago),
            "requests_last_hour": sum(1 for r in requests if r.timestamp > hour_ago),
            "limit_per_minute": TIER_LIMITS[tier].requests_per_minute,
            "limit_per_hour": TIER_LIMITS[tier].requests_per_hour
        }
    
    def reset_user(self, user_id: str):
        """Reset rate limits for user"""
        if user_id in self._user_requests:
            del self._user_requests[user_id]
            logger.info(f"Rate limits reset for user {user_id}")
    
    def _cleanup_old_requests(self, user_id: str, now: float):
        """Remove requests older than 1 hour"""
        hour_ago = now - 3600
        
        self._user_requests[user_id] = [
            r for r in self._user_requests[user_id]
            if r.timestamp > hour_ago
        ]


# Decorator for rate limiting
def rate_limited(tier: UserTier = UserTier.FREE, endpoint: Optional[str] = None):
    """
    Decorator to apply rate limiting to functions.
    
    Usage:
        @rate_limited(tier=UserTier.PRO, endpoint="/api/generate")
        def generate_content(user_id: str):
            # Function logic
            pass
    """
    def decorator(func):
        def wrapper(user_id: str, *args, **kwargs):
            endpoint_name = endpoint or func.__name__
            
            allowed, retry_after = rate_limiter.check_rate_limit(
                user_id=user_id,
                endpoint=endpoint_name,
                tier=tier
            )
            
            if not allowed:
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    retry_after=retry_after
                )
            
            return func(user_id, *args, **kwargs)
        
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


# Global instance
rate_limiter = SlidingWindowRateLimiter()
