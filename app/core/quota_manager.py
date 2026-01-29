"""
Token Bucket Quota Manager
Implements token bucket algorithm for quota management.
"""
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class QuotaType(str, Enum):
    """Quota type enumeration"""
    LLM_TOKENS = "llm_tokens"
    VIDEO_GENERATION = "video_generation"
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"


@dataclass
class QuotaConfig:
    """Quota configuration"""
    capacity: int  # Max tokens in bucket
    refill_rate: float  # Tokens per second
    refill_period: str = "daily"  # daily, hourly, constant
    
    def tokens_per_second(self) -> float:
        """Calculate refill tokens per second"""
        if self.refill_period == "constant":
            return self.refill_rate
        elif self.refill_period == "hourly":
            return self.capacity / 3600
        else:  # daily
            return self.capacity / 86400


# Default quotas per tier
DEFAULT_QUOTAS = {
    "free": {
        QuotaType.LLM_TOKENS: QuotaConfig(capacity=10000, refill_rate=0, refill_period="daily"),
        QuotaType.VIDEO_GENERATION: QuotaConfig(capacity=10, refill_rate=0, refill_period="daily"),
        QuotaType.API_CALLS: QuotaConfig(capacity=1000, refill_rate=0, refill_period="daily"),
        QuotaType.STORAGE_GB: QuotaConfig(capacity=5, refill_rate=0, refill_period="daily")
    },
    "pro": {
        QuotaType.LLM_TOKENS: QuotaConfig(capacity=100000, refill_rate=0, refill_period="daily"),
        QuotaType.VIDEO_GENERATION: QuotaConfig(capacity=100, refill_rate=0, refill_period="daily"),
        QuotaType.API_CALLS: QuotaConfig(capacity=10000, refill_rate=0, refill_period="daily"),
        QuotaType.STORAGE_GB: QuotaConfig(capacity=100, refill_rate=0, refill_period="daily")
    },
    "enterprise": {
        QuotaType.LLM_TOKENS: QuotaConfig(capacity=1000000, refill_rate=0, refill_period="daily"),
        QuotaType.VIDEO_GENERATION: QuotaConfig(capacity=1000, refill_rate=0, refill_period="daily"),
        QuotaType.API_CALLS: QuotaConfig(capacity=100000, refill_rate=0, refill_period="daily"),
        QuotaType.STORAGE_GB: QuotaConfig(capacity=1000, refill_rate=0, refill_period="daily")
    }
}


@dataclass
class TokenBucket:
    """Token bucket for quota enforcement"""
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float
    
    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on refill rate
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def consume(self, amount: int) -> bool:
        """
        Attempt to consume tokens.
        
        Args:
            amount: Number of tokens to consume
        
        Returns:
            True if consumed, False if insufficient
        """
        self.refill()
        
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
    
    def available(self) -> int:
        """Get available tokens"""
        self.refill()
        return int(self.tokens)


class QuotaManager:
    """
    Manages quotas using token bucket algorithm.
    """
    
    def __init__(self):
        # Store buckets per user and quota type
        self._buckets: Dict[str, Dict[QuotaType, TokenBucket]] = {}
        self._user_tiers: Dict[str, str] = {}  # user_id -> tier
        logger.info("QuotaManager initialized")
    
    def set_user_tier(self, user_id: str, tier: str):
        """Set user tier"""
        self._user_tiers[user_id] = tier
        logger.info(f"User {user_id} tier set to {tier}")
    
    def consume_quota(
        self,
        user_id: str,
        quota_type: QuotaType,
        amount: int
    ) -> tuple[bool, Optional[int]]:
        """
        Consume quota for user.
        
        Args:
            user_id: User ID
            quota_type: Type of quota
            amount: Amount to consume
        
        Returns:
            (success: bool, retry_after_seconds: Optional[int])
        """
        # Initialize bucket if needed
        if user_id not in self._buckets:
            self._initialize_buckets(user_id)
        
        bucket = self._buckets[user_id][quota_type]
        
        if bucket.consume(amount):
            logger.debug(
                f"Quota consumed for user {user_id}: "
                f"{amount} {quota_type.value} "
                f"({bucket.available()} remaining)"
            )
            return True, None
        else:
            # Calculate retry time
            tokens_needed = amount - bucket.available()
            retry_after = int(tokens_needed / bucket.refill_rate) if bucket.refill_rate > 0 else 86400
            
            logger.warning(
                f"Quota exceeded for user {user_id}: "
                f"{quota_type.value} (needed {amount}, available {bucket.available()})"
            )
            return False, retry_after
    
    def get_quota_status(
        self,
        user_id: str,
        quota_type: QuotaType
    ) -> Dict:
        """
        Get quota status for user.
        
        Args:
            user_id: User ID
            quota_type: Type of quota
        
        Returns:
            Quota status
        """
        if user_id not in self._buckets:
            self._initialize_buckets(user_id)
        
        bucket = self._buckets[user_id][quota_type]
        available = bucket.available()
        
        return {
            "quota_type": quota_type.value,
            "available": available,
            "capacity": bucket.capacity,
            "used": bucket.capacity - available,
            "usage_percent": ((bucket.capacity - available) / bucket.capacity) * 100,
            "refill_rate": bucket.refill_rate
        }
    
    def reset_quota(
        self,
        user_id: str,
        quota_type: Optional[QuotaType] = None
    ):
        """
        Reset quota for user.
        
        Args:
            user_id: User ID
            quota_type: Type of quota to reset (None = all)
        """
        if user_id not in self._buckets:
            return
        
        if quota_type:
            # Reset specific quota
            tier = self._user_tiers.get(user_id, "free")
            config = DEFAULT_QUOTAS[tier][quota_type]
            self._buckets[user_id][quota_type] = self._create_bucket(config)
            logger.info(f"Reset quota {quota_type.value} for user {user_id}")
        else:
            # Reset all quotas
            self._initialize_buckets(user_id)
            logger.info(f"Reset all quotas for user {user_id}")
    
    def _initialize_buckets(self, user_id: str):
        """Initialize token buckets for user"""
        tier = self._user_tiers.get(user_id, "free")
        quotas = DEFAULT_QUOTAS[tier]
        
        self._buckets[user_id] = {
            quota_type: self._create_bucket(config)
            for quota_type, config in quotas.items()
        }
        
        logger.debug(f"Initialized buckets for user {user_id} (tier: {tier})")
    
    def _create_bucket(self, config: QuotaConfig) -> TokenBucket:
        """Create token bucket from config"""
        return TokenBucket(
            capacity=config.capacity,
            tokens=float(config.capacity),  # Start full
            refill_rate=config.tokens_per_second(),
            last_refill=time.time()
        )


class QuotaExceeded(Exception):
    """Quota exceeded exception"""
    
    def __init__(self, message: str, quota_type: QuotaType, retry_after: int):
        super().__init__(message)
        self.quota_type = quota_type
        self.retry_after = retry_after


# Global instance
quota_manager = QuotaManager()
