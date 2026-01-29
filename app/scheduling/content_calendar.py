"""
Content Calendar and Scheduling
Schedule content publishing and manage calendar.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ScheduleStatus(Enum):
    """Schedule status"""
    PENDING = "pending"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ScheduledVideo:
    """Scheduled video data"""
    schedule_id: str
    video_id: str
    creator_id: str
    publish_date: datetime
    status: ScheduleStatus = ScheduleStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    series_id: Optional[str] = None
    platforms: List[str] = field(default_factory=lambda: ["platform"])


@dataclass
class ContentSeries:
    """Recurring content series"""
    series_id: str
    creator_id: str
    name: str
    frequency: str  # daily, weekly, monthly
    videos: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class ContentCalendar:
    """
    Content calendar and scheduling system.
    
    Features:
    - Schedule video publishing
    - Recurring content series
    - Calendar views (monthly, weekly, daily)
    - Auto-publish on schedule
    """
    
    def __init__(self):
        self._schedules: Dict[str, ScheduledVideo] = {}
        self._series: Dict[str, ContentSeries] = {}
        self._creator_schedules: Dict[str, List[str]] = {}  # creator_id -> schedule_ids
        logger.info("ContentCalendar initialized")
    
    def schedule_video(
        self,
        schedule_id: str,
        video_id: str,
        creator_id: str,
        publish_date: datetime,
        platforms: Optional[List[str]] = None
    ) -> ScheduledVideo:
        """
        Schedule a video for publishing.
        
        Args:
            schedule_id: Unique schedule ID
            video_id: Video ID
            creator_id: Creator user ID
            publish_date: When to publish
            platforms: Platforms to publish to
        
        Returns:
            Scheduled video
        """
        schedule = ScheduledVideo(
            schedule_id=schedule_id,
            video_id=video_id,
            creator_id=creator_id,
            publish_date=publish_date,
            platforms=platforms or ["platform"]
        )
        
        self._schedules[schedule_id] = schedule
        
        # Index by creator
        if creator_id not in self._creator_schedules:
            self._creator_schedules[creator_id] = []
        self._creator_schedules[creator_id].append(schedule_id)
        
        logger.info(
            f"Scheduled video {video_id} for {publish_date.isoformat()} "
            f"(platforms: {platforms})"
        )
        
        return schedule
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledVideo]:
        """Get schedule by ID"""
        return self._schedules.get(schedule_id)
    
    def update_schedule(
        self,
        schedule_id: str,
        new_publish_date: datetime
    ):
        """
        Update schedule publish date.
        
        Args:
            schedule_id: Schedule ID
            new_publish_date: New publish date
        """
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        schedule = self._schedules[schedule_id]
        old_date = schedule.publish_date
        schedule.publish_date = new_publish_date
        
        logger.info(
            f"Updated schedule {schedule_id}: "
            f"{old_date.isoformat()} → {new_publish_date.isoformat()}"
        )
    
    def cancel_schedule(self, schedule_id: str):
        """
        Cancel a scheduled video.
        
        Args:
            schedule_id: Schedule ID
        """
        if schedule_id not in self._schedules:
            return
        
        schedule = self._schedules[schedule_id]
        schedule.status = ScheduleStatus.CANCELLED
        
        logger.info(f"Cancelled schedule {schedule_id}")
    
    def get_calendar(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[ScheduledVideo]:
        """
        Get calendar view for date range.
        
        Args:
            creator_id: Creator user ID
            start_date: Start date
            end_date: End date
        
        Returns:
            List of scheduled videos in range
        """
        schedule_ids = self._creator_schedules.get(creator_id, [])
        schedules = [
            self._schedules[sid] for sid in schedule_ids
            if sid in self._schedules
        ]
        
        # Filter by date range
        schedules = [
            s for s in schedules
            if start_date <= s.publish_date <= end_date
            and s.status == ScheduleStatus.PENDING
        ]
        
        # Sort by publish date
        schedules.sort(key=lambda s: s.publish_date)
        
        return schedules
    
    def get_monthly_calendar(
        self,
        creator_id: str,
        year: int,
        month: int
    ) -> List[ScheduledVideo]:
        """
        Get calendar for a specific month.
        
        Args:
            creator_id: Creator user ID
            year: Year
            month: Month (1-12)
        
        Returns:
            Scheduled videos for month
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return self.get_calendar(creator_id, start_date, end_date)
    
    def create_series(
        self,
        series_id: str,
        creator_id: str,
        name: str,
        frequency: str,
        videos: List[str]
    ) -> ContentSeries:
        """
        Create a recurring content series.
        
        Args:
            series_id: Unique series ID
            creator_id: Creator user ID
            name: Series name
            frequency: Frequency (daily, weekly, monthly)
            videos: Video IDs in series
        
        Returns:
            Created series
        """
        series = ContentSeries(
            series_id=series_id,
            creator_id=creator_id,
            name=name,
            frequency=frequency,
            videos=videos
        )
        
        self._series[series_id] = series
        
        logger.info(
            f"Created series {series_id}: {name} "
            f"({frequency}, {len(videos)} videos)"
        )
        
        return series
    
    def schedule_series(
        self,
        series_id: str,
        start_date: datetime
    ) -> List[ScheduledVideo]:
        """
        Schedule all videos in a series.
        
        Args:
            series_id: Series ID
            start_date: First publish date
        
        Returns:
            List of created schedules
        """
        if series_id not in self._series:
            raise ValueError(f"Series not found: {series_id}")
        
        series = self._series[series_id]
        schedules = []
        
        # Calculate frequency delta
        if series.frequency == "daily":
            delta = timedelta(days=1)
        elif series.frequency == "weekly":
            delta = timedelta(weeks=1)
        elif series.frequency == "monthly":
            delta = timedelta(days=30)  # Approximate
        else:
            delta = timedelta(days=1)
        
        # Schedule each video
        current_date = start_date
        for i, video_id in enumerate(series.videos):
            schedule_id = f"{series_id}_schedule_{i}"
            
            schedule = self.schedule_video(
                schedule_id=schedule_id,
                video_id=video_id,
                creator_id=series.creator_id,
                publish_date=current_date
            )
            schedule.series_id = series_id
            
            schedules.append(schedule)
            current_date += delta
        
        logger.info(
            f"Scheduled series {series_id}: {len(schedules)} videos "
            f"starting {start_date.isoformat()}"
        )
        
        return schedules
    
    def get_pending_publications(
        self,
        before: Optional[datetime] = None
    ) -> List[ScheduledVideo]:
        """
        Get videos pending publication.
        
        Args:
            before: Optional cutoff date (default: now)
        
        Returns:
            Pending scheduled videos
        """
        cutoff = before or datetime.utcnow()
        
        pending = [
            schedule for schedule in self._schedules.values()
            if schedule.status == ScheduleStatus.PENDING
            and schedule.publish_date <= cutoff
        ]
        
        # Sort by publish date
        pending.sort(key=lambda s: s.publish_date)
        
        return pending
    
    def mark_published(self, schedule_id: str):
        """Mark schedule as published"""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].status = ScheduleStatus.PUBLISHED
            logger.info(f"Marked schedule {schedule_id} as published")
    
    def mark_failed(self, schedule_id: str):
        """Mark schedule as failed"""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].status = ScheduleStatus.FAILED
            logger.info(f"Marked schedule {schedule_id} as failed")


# Global instance
content_calendar = ContentCalendar()
