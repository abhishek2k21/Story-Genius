"""
Advanced Analytics Service.
Business intelligence and data-driven decision making.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Comprehensive analytics for business intelligence."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    # MRR (Monthly Recurring Revenue) Metrics
    
    def get_mrr_metrics(self) -> Dict:
        """
        Calculate Monthly Recurring Revenue metrics.
        
        Returns:
            MRR breakdown and growth metrics
        """
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # Current MRR
        current_mrr = self._calculate_mrr(current_month)
        last_mrr = self._calculate_mrr(last_month)
        
        # Growth
        mrr_growth = ((current_mrr - last_mrr) / last_mrr * 100) if last_mrr > 0 else 0
        
        # Breakdown
        new_mrr = self._calculate_new_mrr(current_month)
        expansion_mrr = self._calculate_expansion_mrr(current_month)
        churned_mrr = self._calculate_churned_mrr(current_month)
        
        # ARPU (Average Revenue Per User)
        active_users = self._count_active_subscribers()
        arpu = (current_mrr / active_users) if active_users > 0 else 0
        
        return {
            "current_mrr": round(current_mrr, 2),
            "last_month_mrr": round(last_mrr, 2),
            "mrr_growth_pct": round(mrr_growth, 2),
            "new_mrr": round(new_mrr, 2),
            "expansion_mrr": round(expansion_mrr, 2),
            "churned_mrr": round(churned_mrr, 2),
            "arpu": round(arpu, 2),
            "active_subscribers": active_users
        }
    
    def _calculate_mrr(self, month: datetime) -> float:
        """Calculate MRR for a specific month."""
        # Sum of all active subscriptions normalized to monthly
        # This is simplified - actual implementation would query subscriptions
        return 15000.00  # Placeholder
    
    def _calculate_new_mrr(self, month: datetime) -> float:
        """Calculate new MRR from new customers."""
        return 3000.00  # Placeholder
    
    def _calculate_expansion_mrr(self, month: datetime) -> float:
        """Calculate expansion MRR from upgrades."""
        return 1500.00  # Placeholder
    
    def _calculate_churned_mrr(self, month: datetime) -> float:
        """Calculate churned MRR from cancellations."""
        return 500.00  # Placeholder
    
    def _count_active_subscribers(self) -> int:
        """Count active paying subscribers."""
        return 500  # Placeholder
    
    # Retention Cohort Analysis
    
    def get_retention_cohorts(self, months: int = 12) -> Dict:
        """
        Calculate retention cohorts.
        
        Args:
            months: Number of months to analyze
            
        Returns:
            Cohort retention data
        """
        cohorts = []
        
        end_month = datetime.now().replace(day=1)
        
        for i in range(months):
            cohort_month = end_month - timedelta(days=30 * i)
            
            # Users who signed up in this cohort
            cohort_users = self._get_cohort_users(cohort_month)
            cohort_size = len(cohort_users)
            
            if cohort_size == 0:
                continue
            
            # Calculate retention for each subsequent month
            retention = {}
            for month_offset in range(min(i + 1, 12)):
                check_month = cohort_month + timedelta(days=30 * month_offset)
                active_users = self._count_active_users_in_month(cohort_users, check_month)
                retention[f"month_{month_offset}"] = round(active_users / cohort_size * 100, 1)
            
            cohorts.append({
                "cohort_month": cohort_month.strftime("%Y-%m"),
                "cohort_size": cohort_size,
                "retention": retention
            })
        
        return {"cohorts": cohorts}
    
    def _get_cohort_users(self, month: datetime) -> List[str]:
        """Get users who signed up in a specific month."""
        # Query users by signup month
        # Placeholder
        return []
    
    def _count_active_users_in_month(
        self,
        cohort_users: List[str],
        month: datetime
    ) -> int:
        """Count how many cohort users were active in a specific month."""
        # Check activity (login, video creation, etc.)
        # Placeholder
        return 0
    
    # Feature Adoption
    
    def get_feature_adoption(self) -> Dict:
        """
        Calculate feature adoption rates.
        
        Returns:
            Adoption rates for key features
        """
        total_users = self._count_total_users()
        
        features = [
            {
                "name": "Templates",
                "description": "Used video template",
                "users_who_tried": self._count_feature_users("template_used"),
                "adoption_rate_pct": 0
            },
            {
                "name": "Custom Branding",
                "description": "Added custom logo/watermark",
                "users_who_tried": self._count_feature_users("branding_used"),
                "adoption_rate_pct": 0
            },
            {
                "name": "Integrations",
                "description": "Connected external service",
                "users_who_tried": self._count_feature_users("integration_connected"),
                "adoption_rate_pct": 0
            },
            {
                "name": "Collaboration",
                "description": "Invited team member",
                "users_who_tried": self._count_feature_users("team_invited"),
                "adoption_rate_pct": 0
            },
            {
                "name": "Scheduling",
                "description": "Scheduled video publish",
                "users_who_tried": self._count_feature_users("video_scheduled"),
                "adoption_rate_pct": 0
            }
        ]
        
        # Calculate adoption rates
        for feature in features:
            if total_users > 0:
                feature["adoption_rate_pct"] = round(
                    feature["users_who_tried"] / total_users * 100,
                    1
                )
        
        return {
            "total_users": total_users,
            "features": sorted(features, key=lambda x: x["adoption_rate_pct"], reverse=True)
        }
    
    def _count_total_users(self) -> int:
        """Count total users."""
        # Placeholder
        return 500
    
    def _count_feature_users(self, feature_event: str) -> int:
        """Count users who used a specific feature."""
        # Query analytics events
        # Placeholder
        return 0
    
    # Conversion Funnel
    
    def get_conversion_funnel(self) -> Dict:
        """
        Calculate conversion funnel from visitor to paid customer.
        
        Returns:
            Funnel stages with conversion rates
        """
        # Define funnel stages
        stages = [
            {"name": "Visited Site", "users": self._count_site_visitors()},
            {"name": "Started Signup", "users": self._count_signup_starts()},
            {"name": "Completed Signup", "users": self._count_signups()},
            {"name": "Email Verified", "users": self._count_verified_users()},
            {"name": "Created First Video", "users": self._count_activated_users()},
            {"name": "Upgraded to Pro", "users": self._count_pro_subscriptions()}
        ]
        
        # Calculate conversion rates
        for i, stage in enumerate(stages):
            if i == 0:
                stage["conversion_pct"] = 100.0
            else:
                prev_users = stages[i-1]["users"]
                stage["conversion_pct"] = round(
                    (stage["users"] / prev_users * 100) if prev_users > 0 else 0,
                    1
                )
            
            # Overall conversion from beginning
            first_stage_users = stages[0]["users"]
            stage["overall_conversion_pct"] = round(
                (stage["users"] / first_stage_users * 100) if first_stage_users > 0 else 0,
                1
            )
        
        return {"stages": stages}
    
    def _count_site_visitors(self) -> int:
        """Count site visitors (last 30 days)."""
        return 10000  # Placeholder
    
    def _count_signup_starts(self) -> int:
        """Count signup starts."""
        return 2000  # Placeholder
    
    def _count_signups(self) -> int:
        """Count completed signups."""
        return 1500  # Placeholder
    
    def _count_verified_users(self) -> int:
        """Count email verified users."""
        return 1200  # Placeholder
    
    def _count_activated_users(self) -> int:
        """Count users who created first video."""
        return 600  # Placeholder
    
    def _count_pro_subscriptions(self) -> int:
        """Count Pro subscriptions."""
        return 150  # Placeholder
    
    # LTV (Lifetime Value) Metrics
    
    def get_ltv_metrics(self) -> Dict:
        """
        Calculate Customer Lifetime Value metrics.
        
        Returns:
            LTV, CAC, and related metrics
        """
        # Average subscription length (months)
        avg_lifetime_months = self._calculate_avg_lifetime()
        
        # Average monthly revenue per customer
        arpu = self.get_mrr_metrics()["arpu"]
        
        # LTV = ARPU × Average Lifetime
        ltv = arpu * avg_lifetime_months
        
        # Customer Acquisition Cost
        cac = self._calculate_cac()
        
        # LTV:CAC ratio (should be > 3)
        ltv_cac_ratio = (ltv / cac) if cac > 0 else 0
        
        # Payback period (months to recover CAC)
        payback_period = (cac / arpu) if arpu > 0 else 0
        
        return {
            "avg_ltv": round(ltv, 2),
            "avg_cac": round(cac, 2),
            "ltv_cac_ratio": round(ltv_cac_ratio, 2),
            "payback_period_months": round(payback_period, 1),
            "avg_lifetime_months": round(avg_lifetime_months, 1),
            "monthly_arpu": round(arpu, 2)
        }
    
    def _calculate_avg_lifetime(self) -> float:
        """Calculate average customer lifetime in months."""
        # 1 / churn_rate
        monthly_churn_rate = 0.05  # 5% monthly churn
        return 1 / monthly_churn_rate if monthly_churn_rate > 0 else 0
    
    def _calculate_cac(self) -> float:
        """Calculate Customer Acquisition Cost."""
        # (Sales + Marketing Spend) / New Customers
        return 120.00  # Placeholder
    
    # Overview Dashboard
    
    def get_dashboard_overview(self) -> Dict:
        """
        Get complete dashboard overview.
        
        Returns:
            All key metrics for dashboard
        """
        return {
            "users": {
                "total": self._count_total_users(),
                "active_today": self._count_active_today(),
                "new_this_week": self._count_new_this_week(),
                "growth_this_week_pct": self._calculate_user_growth()
            },
            "revenue": self.get_mrr_metrics(),
            "engagement": {
                "videos_created_today": self._count_videos_today(),
                "avg_videos_per_user": self._calculate_avg_videos_per_user(),
                "dau_mau_ratio": self._calculate_dau_mau_ratio()
            },
            "conversion": {
                "signup_conversion_rate": self._calculate_signup_conversion(),
                "activation_rate": self._calculate_activation_rate(),
                "pro_conversion_rate": self._calculate_pro_conversion()
            }
        }
    
    def _count_active_today(self) -> int:
        """Count active users today."""
        return 120  # Placeholder
    
    def _count_new_this_week(self) -> int:
        """Count new users this week."""
        return 45  # Placeholder
    
    def _calculate_user_growth(self) -> float:
        """Calculate week-over-week user growth."""
        return 15.5  # Placeholder
    
    def _count_videos_today(self) -> int:
        """Count videos created today."""
        return 230  # Placeholder
    
    def _calculate_avg_videos_per_user(self) -> float:
        """Average videos per user."""
        return 4.2  # Placeholder
    
    def _calculate_dau_mau_ratio(self) -> float:
        """DAU/MAU ratio (stickiness)."""
        return 0.35  # 35%
    
    def _calculate_signup_conversion(self) -> float:
        """Signup conversion rate."""
        return 15.0  # 15%
    
    def _calculate_activation_rate(self) -> float:
        """Activation rate (first video)."""
        return 40.0  # 40%
    
    def _calculate_pro_conversion(self) -> float:
        """Free to Pro conversion rate."""
        return 10.0  # 10%
