"""
Audience Insights & Segmentation
Track user behavior and segment audience.
"""
from typing import Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class UserSegment(Enum):
    """User segment types"""
    POWER_USER = "power_user"
    CASUAL_VIEWER = "casual_viewer"
    AT_RISK = "at_risk"
    NEW_USER = "new_user"


@dataclass
class UserBehavior:
    """User behavior metrics"""
    user_id: str
    videos_watched: int = 0
    total_watch_time: float = 0  # seconds
    avg_completion_rate: float = 0  # percentage
    last_visit: datetime = field(default_factory=datetime.utcnow)
    signup_date: datetime = field(default_factory=datetime.utcnow)
    device_type: str = "web"  # web, mobile, tablet
    location: str = "US"


@dataclass
class CohortData:
    """Cohort retention data"""
    cohort_month: str  # YYYY-MM
    total_users: int
    retention_30d: float
    retention_60d: float
    retention_90d: float


class AudienceInsights:
    """
    Audience tracking and segmentation system.
    
    Features:
    - User behavior tracking
    - Audience segmentation
    - Cohort analysis
    - Demographic insights
    """
    
    def __init__(self):
        self._users: Dict[str, UserBehavior] = {}
        self._watch_events: List[Dict] = []
        logger.info("AudienceInsights initialized")
    
    def track_user(
        self,
        user_id: str,
        device_type: str = "web",
        location: str = "US"
    ):
        """Add/update user in tracker"""
        if user_id not in self._users:
            self._users[user_id] = UserBehavior(
                user_id=user_id,
                device_type=device_type,
                location=location
            )
            logger.debug(f"Added user: {user_id}")
    
    def track_watch(
        self,
        user_id: str,
        video_id: str,
        watch_time: float,
        completion_rate: float
    ):
        """
        Track video watch event.
        
        Args:
            user_id: User ID
            video_id: Video ID
            watch_time: Time watched (seconds)
            completion_rate: Percentage of video watched
        """
        if user_id not in self._users:
            self.track_user(user_id)
        
        user = self._users[user_id]
        user.videos_watched += 1
        user.total_watch_time += watch_time
        user.last_visit = datetime.utcnow()
        
        # Update average completion rate
        current_total = user.avg_completion_rate * (user.videos_watched - 1)
        user.avg_completion_rate = (current_total + completion_rate) / user.videos_watched
        
        # Record event
        self._watch_events.append({
            "user_id": user_id,
            "video_id": video_id,
            "watch_time": watch_time,
            "completion_rate": completion_rate,
            "timestamp": datetime.utcnow()
        })
        
        logger.debug(
            f"Tracked watch: user={user_id}, video={video_id}, "
            f"completion={completion_rate:.1f}%"
        )
    
    def segment_user(self, user_id: str) -> UserSegment:
        """
        Classify user into a segment.
        
        Criteria:
        - Power User: >10 videos/week, >80% completion
        - Casual Viewer: <3 videos/week, <50% completion
        - At-Risk: Declining engagement (no visit in 30 days)
        - New User: Signed up within last 30 days
        
        Args:
            user_id: User ID
        
        Returns:
            User segment
        """
        if user_id not in self._users:
            return UserSegment.NEW_USER
        
        user = self._users[user_id]
        
        # Check if new user
        account_age = (datetime.utcnow() - user.signup_date).days
        if account_age <= 30:
            return UserSegment.NEW_USER
        
        # Check if at-risk (no visit in 30 days)
        days_since_visit = (datetime.utcnow() - user.last_visit).days
        if days_since_visit >= 30:
            return UserSegment.AT_RISK
        
        # Calculate videos per week
        weeks_active = max(account_age / 7, 1)
        videos_per_week = user.videos_watched / weeks_active
        
        # Classify based on activity
        if videos_per_week >= 10 and user.avg_completion_rate >= 80:
            return UserSegment.POWER_USER
        elif videos_per_week < 3 or user.avg_completion_rate < 50:
            return UserSegment.CASUAL_VIEWER
        else:
            return UserSegment.CASUAL_VIEWER
    
    def get_user_segments(self) -> Dict[UserSegment, List[str]]:
        """
        Get all users grouped by segment.
        
        Returns:
            Dict mapping segments to user IDs
        """
        segments = defaultdict(list)
        
        for user_id in self._users:
            segment = self.segment_user(user_id)
            segments[segment].append(user_id)
        
        logger.info(
            f"Segmented {len(self._users)} users: "
            f"Power={len(segments[UserSegment.POWER_USER])}, "
            f"Casual={len(segments[UserSegment.CASUAL_VIEWER])}, "
            f"AtRisk={len(segments[UserSegment.AT_RISK])}, "
            f"New={len(segments[UserSegment.NEW_USER])}"
        )
        
        return segments
    
    def cohort_analysis(self) -> List[CohortData]:
        """
        Perform cohort analysis based on signup month.
        
        Returns:
            List of cohort data
        """
        # Group users by signup month
        cohorts = defaultdict(list)
        
        for user in self._users.values():
            cohort_month = user.signup_date.strftime("%Y-%m")
            cohorts[cohort_month].append(user)
        
        # Calculate retention for each cohort
        cohort_data = []
        
        for cohort_month, users in sorted(cohorts.items()):
            total_users = len(users)
            
            # Count users still active at different intervals
            active_30d = sum(
                1 for u in users
                if (datetime.utcnow() - u.last_visit).days <= 30
            )
            active_60d = sum(
                1 for u in users
                if (datetime.utcnow() - u.last_visit).days <= 60
            )
            active_90d = sum(
                1 for u in users
                if (datetime.utcnow() - u.last_visit).days <= 90
            )
            
            cohort_data.append(CohortData(
                cohort_month=cohort_month,
                total_users=total_users,
                retention_30d=round((active_30d / total_users) * 100, 1),
                retention_60d=round((active_60d / total_users) * 100, 1),
                retention_90d=round((active_90d / total_users) * 100, 1)
            ))
        
        logger.info(f"Generated cohort analysis for {len(cohort_data)} cohorts")
        
        return cohort_data
    
    def get_demographics(self) -> Dict:
        """
        Get audience demographics.
        
        Returns:
            Demographics breakdown
        """
        device_breakdown = defaultdict(int)
        location_breakdown = defaultdict(int)
        
        for user in self._users.values():
            device_breakdown[user.device_type] += 1
            location_breakdown[user.location] += 1
        
        return {
            "total_users": len(self._users),
            "device_breakdown": dict(device_breakdown),
            "location_breakdown": dict(location_breakdown)
        }
    
    def get_user_report(self, user_id: str) -> Dict:
        """Get detailed report for a user"""
        if user_id not in self._users:
            return {}
        
        user = self._users[user_id]
        segment = self.segment_user(user_id)
        
        return {
            "user_id": user_id,
            "segment": segment.value,
            "videos_watched": user.videos_watched,
            "total_watch_time": round(user.total_watch_time / 60, 1),  # minutes
            "avg_completion_rate": round(user.avg_completion_rate, 1),
            "last_visit": user.last_visit.isoformat(),
            "signup_date": user.signup_date.isoformat(),
            "device_type": user.device_type,
            "location": user.location
        }


# Global instance
audience_insights = AudienceInsights()
