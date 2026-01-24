"""
Billing and Monetization Service
Implements usage limits, credits, and monetization modes.
"""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List
from enum import Enum

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    AGENCY = "agency"
    ENTERPRISE = "enterprise"


class MonetizationMode(str, Enum):
    """Platform monetization modes."""
    CREDIT_BASED = "credit_based"           # Per-video credits
    CHANNEL_SERVICE = "channel_service"      # Managed channels
    BATCH_AGENCY = "batch_agency"           # Bulk agency orders
    API_PLATFORM = "api_platform"           # API access


@dataclass
class UsageLimits:
    """Usage limits for a plan."""
    videos_per_month: int
    videos_per_day: int
    max_duration: int
    max_retries: int
    ab_tests_per_month: int
    channels: int
    
    # Feature flags
    hook_engine: bool = True
    personas: bool = True
    visual_styles: bool = True
    metadata_engine: bool = True
    trend_injection: bool = False
    multi_channel: bool = False
    ab_testing: bool = False
    api_access: bool = False


# ============== PLAN DEFINITIONS ==============

PLANS: Dict[str, UsageLimits] = {
    PlanType.FREE: UsageLimits(
        videos_per_month=10,
        videos_per_day=2,
        max_duration=30,
        max_retries=1,
        ab_tests_per_month=0,
        channels=1,
        hook_engine=True,
        personas=True,
        visual_styles=False,
        metadata_engine=False,
        trend_injection=False,
        multi_channel=False,
        ab_testing=False,
        api_access=False
    ),
    
    PlanType.STARTER: UsageLimits(
        videos_per_month=50,
        videos_per_day=5,
        max_duration=35,
        max_retries=2,
        ab_tests_per_month=5,
        channels=2,
        hook_engine=True,
        personas=True,
        visual_styles=True,
        metadata_engine=True,
        trend_injection=False,
        multi_channel=False,
        ab_testing=True,
        api_access=False
    ),
    
    PlanType.PROFESSIONAL: UsageLimits(
        videos_per_month=200,
        videos_per_day=20,
        max_duration=60,
        max_retries=3,
        ab_tests_per_month=20,
        channels=5,
        hook_engine=True,
        personas=True,
        visual_styles=True,
        metadata_engine=True,
        trend_injection=True,
        multi_channel=True,
        ab_testing=True,
        api_access=False
    ),
    
    PlanType.AGENCY: UsageLimits(
        videos_per_month=1000,
        videos_per_day=100,
        max_duration=60,
        max_retries=3,
        ab_tests_per_month=100,
        channels=20,
        hook_engine=True,
        personas=True,
        visual_styles=True,
        metadata_engine=True,
        trend_injection=True,
        multi_channel=True,
        ab_testing=True,
        api_access=True
    ),
    
    PlanType.ENTERPRISE: UsageLimits(
        videos_per_month=10000,
        videos_per_day=1000,
        max_duration=180,
        max_retries=5,
        ab_tests_per_month=1000,
        channels=100,
        hook_engine=True,
        personas=True,
        visual_styles=True,
        metadata_engine=True,
        trend_injection=True,
        multi_channel=True,
        ab_testing=True,
        api_access=True
    )
}


@dataclass
class Account:
    """User/organization account."""
    id: str
    name: str
    email: str
    plan: PlanType
    
    # Credits
    credits_balance: int = 0
    credits_used_this_month: int = 0
    
    # Usage tracking
    videos_this_month: int = 0
    videos_today: int = 0
    last_video_date: datetime = None
    
    # Billing
    is_active: bool = True
    subscription_expires: datetime = None
    
    def get_limits(self) -> UsageLimits:
        """Get usage limits for this account's plan."""
        return PLANS.get(self.plan, PLANS[PlanType.FREE])
    
    def can_generate(self) -> tuple:
        """Check if account can generate a video."""
        limits = self.get_limits()
        
        # Check active
        if not self.is_active:
            return False, "Account is inactive"
        
        # Check monthly limit
        if self.videos_this_month >= limits.videos_per_month:
            return False, "Monthly video limit reached"
        
        # Check daily limit
        today = datetime.utcnow().date()
        if self.last_video_date and self.last_video_date.date() == today:
            if self.videos_today >= limits.videos_per_day:
                return False, "Daily video limit reached"
        
        return True, "OK"
    
    def record_generation(self):
        """Record a video generation."""
        today = datetime.utcnow().date()
        
        if self.last_video_date and self.last_video_date.date() == today:
            self.videos_today += 1
        else:
            self.videos_today = 1
        
        self.videos_this_month += 1
        self.last_video_date = datetime.utcnow()
        self.credits_used_this_month += 1


class BillingService:
    """
    Billing and monetization service.
    """
    
    def __init__(self):
        self._accounts: Dict[str, Account] = {}
        self.monetization_mode = MonetizationMode.CREDIT_BASED
    
    def create_account(
        self,
        name: str,
        email: str,
        plan: PlanType = PlanType.FREE
    ) -> Account:
        """Create a new account."""
        account_id = str(uuid.uuid4())
        
        account = Account(
            id=account_id,
            name=name,
            email=email,
            plan=plan,
            credits_balance=PLANS[plan].videos_per_month
        )
        
        self._accounts[account_id] = account
        logger.info(f"Created account: {name} ({plan.value})")
        
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID."""
        return self._accounts.get(account_id)
    
    def upgrade_plan(self, account_id: str, new_plan: PlanType) -> bool:
        """Upgrade account to new plan."""
        account = self.get_account(account_id)
        if not account:
            return False
        
        old_plan = account.plan
        account.plan = new_plan
        
        # Add credits difference
        old_credits = PLANS[old_plan].videos_per_month
        new_credits = PLANS[new_plan].videos_per_month
        account.credits_balance += (new_credits - old_credits)
        
        logger.info(f"Upgraded {account.name} from {old_plan} to {new_plan}")
        return True
    
    def add_credits(self, account_id: str, credits: int) -> int:
        """Add credits to account."""
        account = self.get_account(account_id)
        if not account:
            return 0
        
        account.credits_balance += credits
        logger.info(f"Added {credits} credits to {account.name}")
        return account.credits_balance
    
    def check_and_consume(self, account_id: str) -> tuple:
        """
        Check if account can generate and consume a credit.
        
        Returns:
            (can_generate: bool, message: str)
        """
        account = self.get_account(account_id)
        if not account:
            return False, "Account not found"
        
        can, message = account.can_generate()
        if not can:
            return False, message
        
        account.record_generation()
        return True, "OK"
    
    def get_usage_report(self, account_id: str) -> Dict:
        """Get usage report for account."""
        account = self.get_account(account_id)
        if not account:
            return {"error": "Account not found"}
        
        limits = account.get_limits()
        
        return {
            "account_id": account_id,
            "plan": account.plan.value,
            "usage": {
                "videos_this_month": account.videos_this_month,
                "videos_today": account.videos_today,
                "credits_balance": account.credits_balance
            },
            "limits": {
                "videos_per_month": limits.videos_per_month,
                "videos_per_day": limits.videos_per_day,
                "max_duration": limits.max_duration
            },
            "features": {
                "hook_engine": limits.hook_engine,
                "personas": limits.personas,
                "visual_styles": limits.visual_styles,
                "multi_channel": limits.multi_channel,
                "ab_testing": limits.ab_testing,
                "api_access": limits.api_access
            }
        }
    
    def get_pricing_table(self) -> Dict:
        """Get pricing table for all plans."""
        pricing = {
            PlanType.FREE.value: {"price": 0, "period": "month"},
            PlanType.STARTER.value: {"price": 29, "period": "month"},
            PlanType.PROFESSIONAL.value: {"price": 99, "period": "month"},
            PlanType.AGENCY.value: {"price": 299, "period": "month"},
            PlanType.ENTERPRISE.value: {"price": "custom", "period": "month"}
        }
        
        return {
            plan: {
                **pricing.get(plan, {}),
                "limits": asdict(PLANS[PlanType(plan)])
            }
            for plan in pricing
        }
