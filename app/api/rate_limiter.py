"""
Rate Limiter
Per-user rate limiting with sliding window algorithm.
"""
import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque

from app.core.exceptions import RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    

@dataclass
class UserRateLimit:
    """Per-user rate limit tracking"""
    user_id: str
    requests: deque = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.
    In production, use Redis for distributed rate limiting.
    """
    
    # Default rate limits
    DEFAULT_LIMITS = {
        "api": RateLimitConfig(max_requests=100, window_seconds=3600),  # 100/hour
        "batch_create": RateLimitConfig(max_requests=5, window_seconds=3600),  # 5/hour
        "video_generate": RateLimitConfig(max_requests=20, window_seconds=3600),  # 20/hour
    }
    
    # Plan-based multipliers
    PLAN_MULTIPLIERS = {
        "free": 1.0,
        "pro": 3.0,
        "enterprise": 10.0
    }
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._user_limits: Dict[str, Dict[str, UserRateLimit]] = {}
                    cls._instance._mutex = threading.RLock()
        return cls._instance
    
    def check_rate_limit(
        self,
        user_id: str,
        limit_type: str = "api",
        plan: str = "free"
    ) -> bool:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: User identifier
            limit_type: Type of limit (api, batch_create, video_generate)
            plan: User's plan (free, pro, enterprise)
            
        Returns:
            True if within limit, False otherwise
            
        Raises:
            RateLimitError if limit exceeded
        """
        config = self.DEFAULT_LIMITS.get(limit_type, self.DEFAULT_LIMITS["api"])
        multiplier = self.PLAN_MULTIPLIERS.get(plan, 1.0)
        max_requests = int(config.max_requests * multiplier)
        
        with self._mutex:
            # Get or create user limit tracker
            if user_id not in self._user_limits:
                self._user_limits[user_id] = {}
            
            if limit_type not in self._user_limits[user_id]:
                self._user_limits[user_id][limit_type] = UserRateLimit(user_id=user_id)
            
            user_limit = self._user_limits[user_id][limit_type]
        
        with user_limit.lock:
            now = time.time()
            window_start = now - config.window_seconds
            
            # Remove old requests outside window
            while user_limit.requests and user_limit.requests[0] < window_start:
                user_limit.requests.popleft()
            
            # Check if limit exceeded
            if len(user_limit.requests) >= max_requests:
                # Calculate retry_after
                oldest_request = user_limit.requests[0]
                retry_after = int(oldest_request + config.window_seconds - now)
                
                logger.warning(
                    f"Rate limit exceeded for user {user_id}, limit_type={limit_type}",
                    extra={"user_id": user_id, "limit_type": limit_type, "plan": plan}
                )
                
                raise RateLimitError(
                    f"Rate limit exceeded for {limit_type}",
                    details={
                        "limit": max_requests,
                        "window_seconds": config.window_seconds,
                        "retry_after": retry_after
                    }
                )
            
            # Add current request
            user_limit.requests.append(now)
            return True
    
    def get_rate_limit_status(
        self,
        user_id: str,
        limit_type: str = "api",
        plan: str = "free"
    ) -> Dict:
        """Get current rate limit status for user"""
        config = self.DEFAULT_LIMITS.get(limit_type, self.DEFAULT_LIMITS["api"])
        multiplier = self.PLAN_MULTIPLIERS.get(plan, 1.0)
        max_requests = int(config.max_requests * multiplier)
        
        with self._mutex:
            if user_id not in self._user_limits or limit_type not in self._user_limits[user_id]:
                return {
                    "limit": max_requests,
                    "remaining": max_requests,
                    "reset_at": datetime.utcnow() + timedelta(seconds=config.window_seconds)
                }
            
            user_limit = self._user_limits[user_id][limit_type]
        
        with user_limit.lock:
            now = time.time()
            window_start = now - config.window_seconds
            
            # Clean old requests
            while user_limit.requests and user_limit.requests[0] < window_start:
                user_limit.requests.popleft()
            
            remaining = max(0, max_requests - len(user_limit.requests))
            
            # Calculate reset time
            if user_limit.requests:
                reset_time = user_limit.requests[0] + config.window_seconds
                reset_at = datetime.fromtimestamp(reset_time)
            else:
                reset_at = datetime.utcnow() + timedelta(seconds=config.window_seconds)
            
            return {
                "limit": max_requests,
                "remaining": remaining,
                "reset_at": reset_at.isoformat()
            }
    
    def reset_user_limits(self, user_id: str):
        """Reset all limits for a user (admin operation)"""
        with self._mutex:
            if user_id in self._user_limits:
                del self._user_limits[user_id]
                logger.info(f"Reset rate limits for user {user_id}")


# Singleton instance
rate_limiter = RateLimiter()
