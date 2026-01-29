"""
Analytics Dashboard.
User and admin analytics visualization and business intelligence.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """Generate analytics dashboards for users and admins."""
    
    def __init__(self, db_session, analytics_service):
        self.db = db_session
        self.analytics = analytics_service
    
    def get_user_dashboard(self, user_id: str) -> Dict:
        """
        Get user-facing analytics dashboard.
        
        Shows video performance, engagement, growth metrics.
        
        Args:
            user_id: User ID
            
        Returns:
            User analytics dashboard
        """
        # Get user's videos
        videos = self._get_user_videos(user_id)
        
        if not videos:
            return {
                "message": "No videos yet. Create your first video to see analytics!",
                "videos_created": 0
            }
        
        # Calculate overview metrics
        total_videos = len(videos)
        total_views = sum(v.get("views", 0) for v in videos)
        total_likes = sum(v.get("likes", 0) for v in videos)
        total_shares = sum(v.get("shares", 0) for v in videos)
        avg_watch_time = self._calculate_avg_watch_time(videos)
        
        # Calculate engagement rate
        engagement_rate = (
            (total_likes + total_shares) / total_views * 100
            if total_views > 0 else 0
        )
        
        # Growth metrics (month over month)
        videos_this_month = len([
            v for v in videos
            if self._is_recent(v["created_at"], days=30)
        ])
        
        videos_last_month = len([
            v for v in videos
            if self._is_recent(v["created_at"], days=60, offset_days=30)
        ])
        
        growth_rate = (
            ((videos_this_month - videos_last_month) / videos_last_month * 100)
            if videos_last_month > 0 else 100
        )
        
        # Top performing videos
        top_videos = sorted(videos, key=lambda x: x.get("views", 0), reverse=True)[:5]
        
        # Platform breakdown
        platform_stats = self._get_platform_breakdown(videos)
        
        # Weekly activity
        weekly_activity = self._get_weekly_activity(videos)
        
        return {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            
            "overview": {
                "total_videos": total_videos,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_shares": total_shares,
                "avg_watch_time_seconds": round(avg_watch_time, 1),
                "engagement_rate_pct": round(engagement_rate, 2)
            },
            
            "growth": {
                "videos_this_month": videos_this_month,
                "videos_last_month": videos_last_month,
                "growth_rate_pct": round(growth_rate, 1),
                "trend": "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable"
            },
            
            "top_videos": [
                {
                    "id": v["id"],
                    "title": v["title"],
                    "views": v.get("views", 0),
                    "likes": v.get("likes", 0),
                    "engagement_rate": self._calculate_engagement(v),
                    "created_at": v["created_at"]
                }
                for v in top_videos
            ],
            
            "platform_breakdown": platform_stats,
            "weekly_activity": weekly_activity
        }
    
    def get_admin_dashboard(self) -> Dict:
        """
        Get admin-facing business intelligence dashboard.
        
        Platform-wide metrics, revenue, user behavior, growth.
        
        Returns:
            Admin BI dashboard
        """
        return {
            "generated_at": datetime.utcnow().isoformat(),
            
            "platform_health": self._get_platform_health(),
            "revenue_metrics": self._get_revenue_metrics(),
            "user_metrics": self._get_user_metrics(),
            "content_metrics": self._get_content_metrics(),
            "growth_trends": self._get_growth_trends(),
            "cohort_analysis": self._get_cohort_analysis()
        }
    
    def _get_platform_health(self) -> Dict:
        """Get platform health metrics."""
        return {
            "uptime_pct": 99.98,
            "avg_response_time_ms": 180,
            "error_rate_pct": 0.015,
            "active_users_24h": 450,
            "videos_created_24h": 120,
            "status": "Healthy"
        }
    
    def _get_revenue_metrics(self) -> Dict:
        """Get revenue and financial metrics."""
        current_mrr = 15000
        last_month_mrr = 12700
        
        return {
            "mrr": current_mrr,
            "mrr_growth_pct": round(((current_mrr - last_month_mrr) / last_month_mrr * 100), 1),
            "arr": current_mrr * 12,
            "total_customers": 500,
            "paying_customers": 125,
            "conversion_rate_pct": 25.0,
            "arpu": round(current_mrr / 125, 2),
            "churn_rate_pct": 2.8,
            "ltv": 1200,
            "cac": 180,
            "ltv_cac_ratio": round(1200 / 180, 2)
        }
    
    def _get_user_metrics(self) -> Dict:
        """Get user behavior metrics."""
        return {
            "total_users": 1250,
            "active_users_7d": 550,
            "active_users_30d": 820,
            "new_signups_7d": 120,
            "activation_rate_pct": 45.0,
            "avg_videos_per_user": 8.5,
            "avg_session_duration_min": 12.3
        }
    
    def _get_content_metrics(self) -> Dict:
        """Get content creation metrics."""
        return {
            "total_videos": 10625,
            "videos_created_7d": 840,
            "videos_published_7d": 680,
            "avg_video_length_sec": 45,
            "most_popular_templates": [
                {"name": "Instagram Reel", "usage": 2500},
                {"name": "TikTok Tutorial", "usage": 1800},
                {"name": "YouTube Short", "usage": 1500}
            ],
            "platform_distribution": {
                "youtube": 35,
                "instagram": 30,
                "tiktok": 25,
                "facebook": 7,
                "twitter": 3
            }
        }
    
    def _get_growth_trends(self) -> Dict:
        """Get growth trend data."""
        # Last 6 months data
        months = []
        for i in range(6):
            months.append({
                "month": (datetime.utcnow() - timedelta(days=30*i)).strftime("%b %Y"),
                "signups": 90 + i * 10,
                "mrr": 9000 + i * 1000,
                "active_users": 350 + i * 75
            })
        
        return {
            "monthly_trends": list(reversed(months)),
            "signup_velocity": "+18% MoM",
            "revenue_velocity": "+15% MoM"
        }
    
    def _get_cohort_analysis(self) -> Dict:
        """Get cohort retention analysis."""
        return {
            "month_0_retention": 100,
            "month_1_retention": 65,
            "month_2_retention": 52,
            "month_3_retention": 45,
            "month_6_retention": 38,
            "month_12_retention": 32
        }
    
    # Helper methods
    
    def _get_user_videos(self, user_id: str) -> List[Dict]:
        """Get all videos for user."""
        # Query database
        # Placeholder data
        return [
            {
                "id": "v1",
                "title": "Product Demo",
                "views": 1200,
                "likes": 85,
                "shares": 12,
                "watch_time": 35,
                "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "platform": "youtube"
            },
            {
                "id": "v2",
                "title": "Tutorial Video",
                "views": 850,
                "likes": 62,
                "shares": 8,
                "watch_time": 42,
                "created_at": (datetime.utcnow() - timedelta(days=12)).isoformat(),
                "platform": "instagram"
            }
        ]
    
    def _calculate_avg_watch_time(self, videos: List[Dict]) -> float:
        """Calculate average watch time across videos."""
        if not videos:
            return 0
        
        total_watch_time = sum(v.get("watch_time", 0) for v in videos)
        return total_watch_time / len(videos)
    
    def _calculate_engagement(self, video: Dict) -> float:
        """Calculate engagement rate for video."""
        views = video.get("views", 0)
        if views == 0:
            return 0
        
        likes = video.get("likes", 0)
        shares = video.get("shares", 0)
        
        return round((likes + shares) / views * 100, 2)
    
    def _is_recent(
        self,
        date_str: str,
        days: int,
        offset_days: int = 0
    ) -> bool:
        """Check if date is within specified days range."""
        date = datetime.fromisoformat(date_str)
        now = datetime.utcnow()
        
        start = now - timedelta(days=days + offset_days)
        end = now - timedelta(days=offset_days)
        
        return start <= date <= end
    
    def _get_platform_breakdown(self, videos: List[Dict]) -> Dict:
        """Get breakdown by platform."""
        platforms = {}
        
        for video in videos:
            platform = video.get("platform", "unknown")
            if platform not in platforms:
                platforms[platform] = {
                    "count": 0,
                    "total_views": 0
                }
            
            platforms[platform]["count"] += 1
            platforms[platform]["total_views"] += video.get("views", 0)
        
        return platforms
    
    def _get_weekly_activity(self, videos: List[Dict]) -> List[Dict]:
        """Get weekly activity chart data."""
        activity = []
        
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=i)
            day_videos = [
                v for v in videos
                if datetime.fromisoformat(v["created_at"]).date() == day.date()
            ]
            
            activity.append({
                "date": day.strftime("%Y-%m-%d"),
                "day_name": day.strftime("%A"),
                "videos_created": len(day_videos)
            })
        
        return list(reversed(activity))


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends
from app.services.analytics_dashboard import AnalyticsDashboard

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_user_dashboard(current_user: User = Depends(get_current_user)):
    '''Get user analytics dashboard.'''
    dashboard = AnalyticsDashboard(db_session, analytics_service)
    return dashboard.get_user_dashboard(current_user.id)

@router.get("/admin/dashboard")
async def get_admin_dashboard(current_user: User = Depends(require_admin)):
    '''Get admin BI dashboard.'''
    dashboard = AnalyticsDashboard(db_session, analytics_service)
    return dashboard.get_admin_dashboard()
"""
