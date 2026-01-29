"""
Analytics Routers
Endpoints for usage stats and tracking.
"""
from typing import Optional

from fastapi import APIRouter, Query

from src.core.dependencies import OptionalApiKey
from src.domains.analytics.entities import (
    GenerationStats,
    StatsResponse,
    UsageEvent,
    UsageLogResponse,
)
from src.domains.analytics.services import AnalyticsService

router = APIRouter()


def get_user_id(api_key: Optional[str]) -> str:
    """Get user ID from API key (temp implementation)."""
    return api_key or "default_user"


@router.post("/events", response_model=UsageLogResponse)
async def log_event(
    event: UsageEvent,
    api_key: OptionalApiKey,
) -> UsageLogResponse:
    """Log a usage event."""
    service = AnalyticsService()
    return await service.log_event(event)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    api_key: OptionalApiKey,
    days: int = Query(7, ge=1, le=90),
) -> StatsResponse:
    """Get usage statistics."""
    service = AnalyticsService()
    user_id = get_user_id(api_key)
    return await service.get_stats(user_id, days)


@router.get("/stats/user", response_model=GenerationStats)
async def get_user_stats(
    api_key: OptionalApiKey,
    days: int = Query(30, ge=1, le=365),
) -> GenerationStats:
    """Get aggregated stats for current user."""
    service = AnalyticsService()
    user_id = get_user_id(api_key)
    return await service.get_user_stats(user_id, days)


@router.get("/events/recent", response_model=list[UsageLogResponse])
async def get_recent_events(
    api_key: OptionalApiKey,
    limit: int = Query(50, ge=1, le=500),
) -> list[UsageLogResponse]:
    """Get recent events for current user."""
    service = AnalyticsService()
    user_id = get_user_id(api_key)
    return await service.get_recent_events(user_id, limit)
