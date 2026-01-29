"""
Analytics Service
Usage tracking and statistics aggregation.
"""
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.domains.analytics.entities import (
    DailyStats,
    EventType,
    GenerationStats,
    ServiceType,
    StatsResponse,
    UsageEvent,
    UsageLogResponse,
)

logger = get_logger(__name__)

# In-memory storage (replace with DB in production)
_usage_logs: list[dict] = []


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def log_event(self, event: UsageEvent) -> UsageLogResponse:
        """Log a usage event."""
        log_entry = {
            "id": uuid.uuid4(),
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "project_id": event.project_id,
            "story_id": event.story_id,
            "service": event.service.value if event.service else None,
            "duration_ms": event.duration_ms,
            "tokens_used": event.tokens_used,
            "cost_usd": event.cost_usd,
            "metadata": event.metadata,
            "created_at": datetime.now(timezone.utc),
        }

        _usage_logs.append(log_entry)

        logger.info(
            f"Analytics: {event.event_type.value}",
            extra={"user_id": event.user_id, "service": event.service},
        )

        return UsageLogResponse(**log_entry)

    async def get_user_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> GenerationStats:
        """Get aggregated stats for a user."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        user_logs = [
            log for log in _usage_logs
            if log["user_id"] == user_id and log["created_at"] > cutoff
        ]

        return self._aggregate_stats(user_logs)

    async def get_stats(
        self,
        user_id: Optional[str] = None,
        days: int = 7,
    ) -> StatsResponse:
        """Get comprehensive stats with daily breakdown."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        logs = [log for log in _usage_logs if log["created_at"] > cutoff]
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]

        overall = self._aggregate_stats(logs)
        daily = self._get_daily_stats(logs, days)

        return StatsResponse(
            overall=overall,
            daily=daily,
            period=f"last_{days}_days",
        )

    async def get_recent_events(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[UsageLogResponse]:
        """Get recent events for a user."""
        user_logs = [
            log for log in _usage_logs
            if log["user_id"] == user_id
        ]

        # Sort by created_at descending
        user_logs.sort(key=lambda x: x["created_at"], reverse=True)

        return [UsageLogResponse(**log) for log in user_logs[:limit]]

    def _aggregate_stats(self, logs: list[dict]) -> GenerationStats:
        """Aggregate logs into stats."""
        stats = GenerationStats()

        for log in logs:
            event_type = log["event_type"]
            service = log.get("service")

            if event_type == EventType.PROJECT_CREATED.value:
                stats.total_projects += 1
            elif event_type == EventType.STORY_GENERATED.value:
                stats.total_stories += 1
            elif event_type == EventType.VIDEO_STARTED.value:
                stats.total_videos += 1
            elif event_type == EventType.VIDEO_COMPLETED.value:
                stats.videos_completed += 1
                if log.get("metadata", {}).get("duration_seconds"):
                    stats.total_duration_seconds += log["metadata"]["duration_seconds"]
            elif event_type == EventType.VIDEO_FAILED.value:
                stats.videos_failed += 1
            elif event_type == EventType.API_CALL.value:
                stats.total_api_calls += 1

            if service == ServiceType.GEMINI.value:
                stats.gemini_calls += 1
            elif service == ServiceType.VEO.value:
                stats.veo_calls += 1
            elif service in [ServiceType.ELEVENLABS.value, ServiceType.EDGE_TTS.value]:
                stats.tts_calls += 1

            if log.get("cost_usd"):
                stats.estimated_cost_usd += log["cost_usd"]

        return stats

    def _get_daily_stats(self, logs: list[dict], days: int) -> list[DailyStats]:
        """Get daily aggregated stats."""
        daily_data = defaultdict(lambda: {"events": 0, "videos": 0, "errors": 0, "durations": []})

        for log in logs:
            date_str = log["created_at"].strftime("%Y-%m-%d")
            daily_data[date_str]["events"] += 1

            if log["event_type"] == EventType.VIDEO_COMPLETED.value:
                daily_data[date_str]["videos"] += 1
                if log.get("duration_ms"):
                    daily_data[date_str]["durations"].append(log["duration_ms"])
            elif log["event_type"] == EventType.VIDEO_FAILED.value:
                daily_data[date_str]["errors"] += 1

        # Generate daily stats
        result = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            data = daily_data.get(date_str, {"events": 0, "videos": 0, "errors": 0, "durations": []})

            avg_time = None
            if data["durations"]:
                avg_time = sum(data["durations"]) / len(data["durations"])

            result.append(DailyStats(
                date=date_str,
                events_count=data["events"],
                videos_generated=data["videos"],
                errors_count=data["errors"],
                avg_generation_time_ms=avg_time,
            ))

        return result


# Singleton for easy access
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


async def log_event(event: UsageEvent) -> None:
    """Convenience function to log an event."""
    service = get_analytics_service()
    await service.log_event(event)
