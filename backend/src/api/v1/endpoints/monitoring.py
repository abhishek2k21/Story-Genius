"""
Monitoring Endpoints
Usage stats, cost tracking, and health metrics.
"""
from fastapi import APIRouter

from src.core.usage_logging import get_usage_tracker
from src.core.observability import get_metrics

router = APIRouter()


@router.get("/usage")
async def get_usage_summary(hours: int = 24) -> dict:
    """
    Get API usage summary.

    Returns cost estimates and request counts by service.
    """
    tracker = get_usage_tracker()
    return tracker.get_summary(hours)


@router.get("/metrics")
async def get_metrics_summary() -> dict:
    """
    Get application metrics.

    Returns counters and timing statistics.
    """
    metrics = get_metrics()
    return metrics.get_all()


@router.get("/costs")
async def get_cost_breakdown(days: int = 7) -> dict:
    """
    Get detailed cost breakdown by service.
    """
    tracker = get_usage_tracker()
    summary = tracker.get_summary(hours=days * 24)

    return {
        "period_days": days,
        "total_cost_usd": summary["total_cost_usd"],
        "by_service": {
            service: {
                "requests": data["requests"],
                "cost_usd": round(data["cost_usd"], 4),
                "error_rate": data["errors"] / max(data["requests"], 1),
            }
            for service, data in summary.get("by_service", {}).items()
        },
        "estimates": {
            "daily_avg": round(summary["total_cost_usd"] / max(days, 1), 4),
            "monthly_projection": round(summary["total_cost_usd"] / max(days, 1) * 30, 2),
        },
    }
