"""
A/B Testing Framework.
Manages experiments for conversion optimization.
"""
from typing import Dict, Optional, List
from datetime import datetime
import hashlib
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class VariantType(str, Enum):
    """Variant type enum."""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class ABTest:
    """Represents an A/B test configuration."""
    
    def __init__(
        self,
        name: str,
        description: str,
        variants: Dict[str, int],
        goal_event: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ):
        self.name = name
        self.description = description
        self.variants = variants  # {"control": 50, "variant_a": 50}
        self.goal_event = goal_event
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = True
    
    def validate(self) -> bool:
        """Validate test configuration."""
        # Check percentages sum to 100
        total = sum(self.variants.values())
        if total != 100:
            logger.error(f"Variant percentages must sum to 100, got {total}")
            return False
        
        return True


class ABTestManager:
    """Manage A/B tests for conversion optimization."""
    
    def __init__(self):
        self.active_tests: Dict[str, ABTest] = {}
        self.results_cache = {}
    
    def create_test(
        self,
        name: str,
        description: str,
        variants: Dict[str, int],
        goal_event: str,
        start_date: Optional[datetime] = None
    ) -> ABTest:
        """
        Create a new A/B test.
        
        Args:
            name: Unique test name
            description: Test description
            variants: Variant distribution {"control": 50, "variant_a": 50}
            goal_event: Goal event to track (e.g., "signup_completed")
            start_date: When to start test (default: now)
            
        Returns:
            Created ABTest instance
        """
        test = ABTest(
            name=name,
            description=description,
            variants=variants,
            goal_event=goal_event,
            start_date=start_date or datetime.now()
        )
        
        if not test.validate():
            raise ValueError("Invalid test configuration")
        
        self.active_tests[name] = test
        logger.info(f"Created A/B test: {name}")
        
        return test
    
    def assign_variant(self, user_id: str, test_name: str) -> str:
        """
        Assign user to a test variant.
        
        Uses consistent hashing to ensure same user always gets same variant.
        
        Args:
            user_id: Unique user identifier
            test_name: Name of the test
            
        Returns:
            Variant name (e.g., "control", "variant_a")
        """
        test = self.active_tests.get(test_name)
        if not test or not test.is_active:
            return "control"  # Default to control if test not found
        
        # Consistent hashing
        hash_input = f"{user_id}:{test_name}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        bucket = hash_value % 100
        
        # Assign based on bucket
        cumulative = 0
        for variant, percentage in test.variants.items():
            cumulative += percentage
            if bucket < cumulative:
                return variant
        
        # Fallback
        return "control"
    
    def track_event(
        self,
        user_id: str,
        test_name: str,
        event: str,
        properties: Optional[Dict] = None
    ):
        """
        Track an event for A/B test analysis.
        
        Args:
            user_id: User identifier
            test_name: Test name
            event: Event name
            properties: Additional event properties
        """
        test = self.active_tests.get(test_name)
        if not test or not test.is_active:
            return
        
        variant = self.assign_variant(user_id, test_name)
        
        # Log event
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "test_name": test_name,
            "variant": variant,
            "event": event,
            "properties": properties or {}
        }
        
        # Send to analytics system
        # In production, this would send to analytics platform
        # For now, just log
        logger.info(f"AB Test Event: {event_data}")
        
        # Check if this is the goal event
        if event == test.goal_event:
            self._record_conversion(test_name, variant, user_id)
    
    def _record_conversion(self, test_name: str, variant: str, user_id: str):
        """Record a conversion for the test."""
        key = f"{test_name}:{variant}"
        if key not in self.results_cache:
            self.results_cache[key] = {
                "conversions": set(),
                "impressions": set()
            }
        
        self.results_cache[key]["conversions"].add(user_id)
    
    def get_results(self, test_name: str) -> Dict:
        """
        Get test results.
        
        Args:
            test_name: Test name
            
        Returns:
            Results by variant with conversion rates
        """
        test = self.active_tests.get(test_name)
        if not test:
            return {}
        
        results = {}
        
        for variant in test.variants.keys():
            key = f"{test_name}:{variant}"
            data = self.results_cache.get(key, {
                "conversions": set(),
                "impressions": set()
            })
            
            conversions = len(data["conversions"])
            impressions = len(data["impressions"])
            conversion_rate = (conversions / impressions * 100) if impressions > 0 else 0
            
            results[variant] = {
                "impressions": impressions,
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 2)
            }
        
        # Calculate statistical significance (simplified)
        # In production, use proper statistical tests
        if "control" in results and len(results) > 1:
            control_rate = results["control"]["conversion_rate"]
            
            for variant, data in results.items():
                if variant != "control":
                    lift = ((data["conversion_rate"] - control_rate) / control_rate * 100) if control_rate > 0 else 0
                    data["lift"] = round(lift, 2)
                    
                    # Simple significance check (needs proper statistical test in production)
                    data["is_significant"] = abs(lift) > 10 and data["impressions"] > 100
        
        return results
    
    def stop_test(self, test_name: str):
        """Stop an A/B test."""
        if test_name in self.active_tests:
            self.active_tests[test_name].is_active = False
            self.active_tests[test_name].end_date = datetime.now()
            logger.info(f"Stopped A/B test: {test_name}")
    
    def get_active_tests_for_user(self, user_id: str) -> List[Dict]:
        """
        Get all active tests and variants for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of tests with assigned variants
        """
        user_tests = []
        
        for test_name, test in self.active_tests.items():
            if test.is_active:
                variant = self.assign_variant(user_id, test_name)
                user_tests.append({
                    "test_name": test_name,
                    "variant": variant,
                    "description": test.description
                })
        
        return user_tests


# Pre-configured common tests
def setup_common_tests(manager: ABTestManager):
    """Set up common A/B tests for the platform."""
    
    # Test 1: Signup CTA text
    manager.create_test(
        name="signup_cta_text",
        description="Test different signup button text",
        variants={
            "control": 34,      # "Sign Up Free"
            "variant_a": 33,    # "Start Creating"
            "variant_b": 33     # "Try For Free"
        },
        goal_event="signup_completed"
    )
    
    # Test 2: Onboarding flow
    manager.create_test(
        name="onboarding_flow",
        description="Test simplified vs standard onboarding",
        variants={
            "control": 50,      # Standard flow (5 steps)
            "variant_a": 50     # Simplified flow (3 steps)
        },
        goal_event="first_video_created"
    )
    
    # Test 3: Pricing page layout
    manager.create_test(
        name="pricing_layout",
        description="Test pricing page layouts",
        variants={
            "control": 50,      # Current layout
            "variant_a": 50     # New layout with annual discount emphasized
        },
        goal_event="upgrade_to_pro"
    )
    
    logger.info("Set up common A/B tests")


# FastAPI integration example
"""
from fastapi import Request, Depends
from app.services.ab_testing import ABTestManager

ab_manager = ABTestManager()
setup_common_tests(ab_manager)

@app.get("/")
async def homepage(request: Request):
    user_id = request.cookies.get("user_id") or generate_temp_id()
    
    # Get variant for signup CTA
    cta_variant = ab_manager.assign_variant(user_id, "signup_cta_text")
    
    cta_text = {
        "control": "Sign Up Free",
        "variant_a": "Start Creating",
        "variant_b": "Try For Free"
    }.get(cta_variant, "Sign Up Free")
    
    return {"cta_text": cta_text}

@app.post("/signup")
async def signup(request: Request):
    user_id = request.cookies.get("user_id")
    
    # Track conversion
    ab_manager.track_event(user_id, "signup_cta_text", "signup_completed")
    
    # ... signup logic
"""


if __name__ == "__main__":
    # Example usage
    manager = ABTestManager()
    setup_common_tests(manager)
    
    # Simulate user assignment
    user1 = "user_123"
    user2 = "user_456"
    
    print(f"User 1 CTA variant: {manager.assign_variant(user1, 'signup_cta_text')}")
    print(f"User 2 CTA variant: {manager.assign_variant(user2, 'signup_cta_text')}")
    
    # Track events
    manager.track_event(user1, "signup_cta_text", "signup_completed")
    
    # Get results
    results = manager.get_results("signup_cta_text")
    print(f"\nTest Results: {results}")
