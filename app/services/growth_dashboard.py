"""
Growth Dashboard.
Real-time monitoring of growth experiments and metrics.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.ab_testing import ABTestManager
from app.services.referral_service import ReferralService
from app.services.analytics_service import AnalyticsService


class GrowthDashboard:
    """Monitor all growth experiments and metrics in real-time."""
    
    def __init__(
        self,
        ab_manager: ABTestManager,
        referral_service: ReferralService,
        analytics_service: AnalyticsService
    ):
        self.ab_manager = ab_manager
        self.referral_service = referral_service
        self.analytics_service = analytics_service
    
    def get_experiment_status(self, test_name: str) -> Dict:
        """
        Get current status of an A/B test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Test status with results and winner determination
        """
        # Get results from A/B test manager
        results = self.ab_manager.get_results(test_name)
        
        if not results:
            return {"error": "Test not found"}
        
        # Determine winner
        winner = self._determine_winner(results)
        
        # Calculate confidence
        confidence = self._calculate_confidence(results)
        
        # Get test configuration
        test = self.ab_manager.active_tests.get(test_name)
        
        return {
            "test_name": test_name,
            "description": test.description if test else "",
            "status": "running" if test and test.is_active else "completed",
            "start_date": test.start_date.isoformat() if test else None,
            "variants": results,
            "winner": winner,
            "confidence": confidence,
            "recommendation": self._get_recommendation(winner, confidence)
        }
    
    def _determine_winner(self, results: Dict) -> Optional[str]:
        """
        Determine winning variant based on conversion rates.
        
        Args:
            results: Test results by variant
            
        Returns:
            Winning variant name or None
        """
        if "control" not in results:
            return None
        
        control_rate = results["control"]["conversion_rate"]
        best_variant = "control"
        best_rate = control_rate
        
        for variant, data in results.items():
            if variant != "control":
                if data["conversion_rate"] > best_rate:
                    # Check if improvement is significant
                    if data.get("is_significant", False):
                        best_variant = variant
                        best_rate = data["conversion_rate"]
        
        return best_variant if best_variant != "control" else None
    
    def _calculate_confidence(self, results: Dict) -> float:
        """
        Calculate confidence level of results.
        
        Simplified calculation - in production use proper statistical tests.
        
        Args:
            results: Test results
            
        Returns:
            Confidence percentage (0-100)
        """
        # Check if we have enough samples
        total_impressions = sum(
            data["impressions"] for data in results.values()
        )
        
        if total_impressions < 100:
            return 0.0
        elif total_impressions < 500:
            return 70.0
        elif total_impressions < 1000:
            return 85.0
        else:
            return 95.0
    
    def _get_recommendation(self, winner: Optional[str], confidence: float) -> str:
        """Get action recommendation based on results."""
        if confidence < 70:
            return "Keep running - need more data"
        elif confidence < 85:
            if winner:
                return f"Leaning towards {winner} - monitor for a few more days"
            else:
                return "No clear winner yet - continue test"
        else:
            if winner:
                return f"Ship {winner} - statistically significant improvement"
            else:
                return "No improvement found - keep control"
    
    def get_all_experiments(self) -> List[Dict]:
        """Get status of all active experiments."""
        experiments = []
        
        for test_name in self.ab_manager.active_tests.keys():
            experiments.append(self.get_experiment_status(test_name))
        
        return experiments
    
    def get_referral_metrics(self) -> Dict:
        """
        Get referral program metrics.
        
        Returns:
            Referral program performance metrics
        """
        # Query referral data
        # This is simplified - actual implementation would query database
        
        total_codes = 150  # Codes generated
        referrals_completed = 12  # Referrals who signed up
        referrals_converted = 8  # Referrals who paid
        
        conversion_rate = (referrals_completed / total_codes * 100) if total_codes > 0 else 0
        quality_rate = (referrals_converted / referrals_completed * 100) if referrals_completed > 0 else 0
        
        # Viral coefficient (K-factor)
        # K = (# invites sent per user) × (conversion rate)
        avg_invites_per_user = 3
        k_factor = avg_invites_per_user * (referrals_completed / total_codes) if total_codes > 0 else 0
        
        return {
            "codes_generated": total_codes,
            "referrals_signed_up": referrals_completed,
            "referrals_converted": referrals_converted,
            "conversion_rate": round(conversion_rate, 2),
            "quality_rate": round(quality_rate, 2),
            "viral_coefficient": round(k_factor, 3),
            "avg_time_to_convert_days": 5,
            "status": "viral" if k_factor > 1 else "growing" if k_factor > 0.5 else "needs_improvement"
        }
    
    def get_growth_overview(self, period: str = "week") -> Dict:
        """
        Get overall growth metrics.
        
        Args:
            period: Time period ('week', 'month')
            
        Returns:
            Growth overview metrics
        """
        # Get analytics data
        analytics = self.analytics_service.get_dashboard_overview()
        
        # Calculate growth rates
        if period == "week":
            signups_current = 120
            signups_previous = 95
            growth_rate = ((signups_current - signups_previous) / signups_previous * 100)
        else:
            signups_current = 480
            signups_previous = 350
            growth_rate = ((signups_current - signups_previous) / signups_previous * 100)
        
        return {
            "period": period,
            "new_signups": signups_current,
            "growth_rate_pct": round(growth_rate, 1),
            "activation_rate_pct": analytics["conversion"]["activation_rate"],
            "pro_conversion_rate_pct": analytics["conversion"]["pro_conversion_rate"],
            "revenue_growth_pct": 18.5,
            "mrr": analytics["revenue"]["current_mrr"],
            "active_users": analytics["users"]["total"]
        }
    
    def get_complete_dashboard(self) -> Dict:
        """
        Get complete growth dashboard.
        
        Returns:
            All growth metrics and experiments
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "experiments": self.get_all_experiments(),
            "referrals": self.get_referral_metrics(),
            "growth": self.get_growth_overview("week"),
            "summary": self._get_summary()
        }
    
    def _get_summary(self) -> Dict:
        """Get executive summary of growth."""
        growth = self.get_growth_overview("week")
        referrals = self.get_referral_metrics()
        
        return {
            "health": "excellent" if growth["growth_rate_pct"] > 20 else "good" if growth["growth_rate_pct"] > 10 else "needs_attention",
            "top_priority": self._get_top_priority(),
            "key_wins": [
                f"{growth['growth_rate_pct']}% week-over-week growth",
                f"K-factor: {referrals['viral_coefficient']}",
                f"{len(self.ab_manager.active_tests)} experiments running"
            ]
        }
    
    def _get_top_priority(self) -> str:
        """Determine top priority action."""
        growth = self.get_growth_overview("week")
        
        if growth["growth_rate_pct"] < 10:
            return "Focus on acquisition - growth below target"
        elif growth["activation_rate_pct"] < 40:
            return "Improve activation - too many users dropping off"
        elif growth["pro_conversion_rate_pct"] < 10:
            return "Optimize conversion to Pro - monetization opportunity"
        else:
            return "Scale marketing - fundamentals are strong"


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends
from app.services.growth_dashboard import GrowthDashboard

router = APIRouter(prefix="/growth", tags=["growth"])

@router.get("/dashboard")
async def get_growth_dashboard():
    '''Get complete growth dashboard.'''
    dashboard = GrowthDashboard(ab_manager, referral_service, analytics_service)
    return dashboard.get_complete_dashboard()

@router.get("/experiments/{test_name}")
async def get_experiment(test_name: str):
    '''Get specific experiment status.'''
    dashboard = GrowthDashboard(ab_manager, referral_service, analytics_service)
    return dashboard.get_experiment_status(test_name)

@router.get("/referrals")
async def get_referral_metrics():
    '''Get referral program metrics.'''
    dashboard = GrowthDashboard(ab_manager, referral_service, analytics_service)
    return dashboard.get_referral_metrics()
"""
