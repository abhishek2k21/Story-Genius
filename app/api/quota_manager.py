"""
Quota Manager
Per-user quota tracking and enforcement.
"""
import threading
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.core.exceptions import RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Plan(str, Enum):
    """User subscription plans"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class QuotaConfig:
    """Quota configuration per plan"""
    videos_per_month: Optional[int]  # None = unlimited
    batch_size_limit: int
    priority: int  # 1=highest, 3=lowest


# Plan quota configurations
PLAN_QUOTAS = {
    Plan.FREE: QuotaConfig(videos_per_month=10, batch_size_limit=5, priority=3),
    Plan.PRO: QuotaConfig(videos_per_month=100, batch_size_limit=20, priority=2),
    Plan.ENTERPRISE: QuotaConfig(videos_per_month=None, batch_size_limit=100, priority=1),
}


@dataclass
class UserQuota:
    """Per-user quota tracking"""
    user_id: str
    plan: Plan
    videos_used_this_month: int = 0
    billing_cycle_start: datetime = None
    
    def __post_init__(self):
        if self.billing_cycle_start is None:
            self.billing_cycle_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class QuotaManager:
    """
    Quota manager for tracking and enforcing usage limits.
    In production, store in database for persistence.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._user_quotas: Dict[str, UserQuota] = {}
                    cls._instance._mutex = threading.RLock()
        return cls._instance
    
    def get_user_quota(self, user_id: str, plan: str = "free") -> UserQuota:
        """Get or create user quota"""
        with self._mutex:
            if user_id not in self._user_quotas:
                self._user_quotas[user_id] = UserQuota(
                    user_id=user_id,
                    plan=Plan(plan)
                )
            return self._user_quotas[user_id]
    
    def check_quota(self, user_id: str, plan: str = "free", videos_to_create: int = 1) -> bool:
        """
        Check if user has quota for video creation.
        
        Args:
            user_id: User identifier
            plan: User's plan
            videos_to_create: Number of videos to create
            
        Returns:
            True if quota available
            
        Raises:
            RateLimitError if quota exceeded
        """
        quota = self.get_user_quota(user_id, plan)
        config = PLAN_QUOTAS[Plan(plan)]
        
        # Check if billing cycle needs reset
        self._check_billing_cycle(quota)
        
        # Enterprise has unlimited
        if config.videos_per_month is None:
            return True
        
        # Check if quota exceeded
        if quota.videos_used_this_month + videos_to_create > config.videos_per_month:
            raise RateLimitError(
                "Monthly quota exceeded",
                details={
                    "quota": config.videos_per_month,
                    "used": quota.videos_used_this_month,
                    "requested": videos_to_create,
                    "reset_at": self._get_next_billing_cycle(quota).isoformat()
                }
            )
        
        return True
    
    def consume_quota(self, user_id: str, plan: str = "free", videos_count: int = 1):
        """Consume quota for video creation"""
        quota = self.get_user_quota(user_id, plan)
        
        with self._mutex:
            quota.videos_used_this_month += videos_count
            logger.info(
                f"Quota consumed for user {user_id}: {videos_count} videos",
                extra={"user_id": user_id, "videos_count": videos_count}
            )
    
    def get_quota_status(self, user_id: str, plan: str = "free") -> Dict:
        """Get quota status for user"""
        quota = self.get_user_quota(user_id, plan)
        config = PLAN_QUOTAS[Plan(plan)]
        
        self._check_billing_cycle(quota)
        
        if config.videos_per_month is None:
            return {
                "plan": plan,
                "quota": "unlimited",
                "used": quota.videos_used_this_month,
                "remaining": "unlimited",
                "reset_at": self._get_next_billing_cycle(quota).isoformat()
            }
        
        return {
            "plan": plan,
            "quota": config.videos_per_month,
            "used": quota.videos_used_this_month,
            "remaining": config.videos_per_month - quota.videos_used_this_month,
            "reset_at": self._get_next_billing_cycle(quota).isoformat(),
            "batch_size_limit": config.batch_size_limit
        }
    
    def _check_billing_cycle(self, quota: UserQuota):
        """Check if billing cycle needs reset"""
        next_cycle = self._get_next_billing_cycle(quota)
        
        if datetime.utcnow() >= next_cycle:
            with self._mutex:
                quota.videos_used_this_month = 0
                quota.billing_cycle_start = next_cycle
                logger.info(f"Reset quota for user {quota.user_id} - new billing cycle")
    
    def _get_next_billing_cycle(self, quota: UserQuota) -> datetime:
        """Get next billing cycle start date"""
        current = quota.billing_cycle_start
        
        # Next month, same day
        if current.month == 12:
            return current.replace(year=current.year + 1, month=1)
        else:
            return current.replace(month=current.month + 1)
    
    def reset_user_quota(self, user_id: str):
        """Reset quota for a user (admin operation)"""
        quota = self.get_user_quota(user_id)
        
        with self._mutex:
            quota.videos_used_this_month = 0
            logger.info(f"Admin reset quota for user {user_id}")


# Singleton instance
quota_manager = QuotaManager()
