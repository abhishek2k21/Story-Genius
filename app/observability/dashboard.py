"""
Dashboard Data Aggregation
Aggregated statistics and trends for operational dashboards.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.observability.metrics import metrics
from app.observability.errors import error_tracker
from app.observability.health import health_monitor


@dataclass
class DashboardOverview:
    """System overview for dashboard"""
    health_status: str
    uptime_seconds: int
    version: str
    jobs_today: int
    errors_today: int
    avg_job_duration: float
    
    def to_dict(self) -> Dict:
        return {
            "health_status": self.health_status,
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "stats": {
                "jobs_today": self.jobs_today,
                "errors_today": self.errors_today,
                "avg_job_duration_sec": round(self.avg_job_duration, 2)
            }
        }


async def get_dashboard_overview() -> Dict:
    """Get system overview data"""
    # Get health
    health = await health_monitor.check_all()
    
    # Get metrics snapshot
    snapshot = metrics.get_snapshot()
    
    # Calculate jobs today (from counters)
    jobs_created = snapshot.get("counters", {}).get("jobs_created_total", 0)
    
    # Get errors
    error_summary = error_tracker.get_summary()
    
    # Get job duration average
    job_hist = snapshot.get("histograms", {}).get("job_duration_seconds", {})
    avg_duration = job_hist.get("avg", 0)
    
    return DashboardOverview(
        health_status=health.status.value,
        uptime_seconds=health.uptime_seconds,
        version=health.version,
        jobs_today=int(jobs_created),
        errors_today=error_summary.get("total_occurrences", 0),
        avg_job_duration=avg_duration
    ).to_dict()


def get_job_statistics(period: str = "day") -> Dict:
    """Get job statistics for period"""
    snapshot = metrics.get_snapshot()
    
    # Get counters
    counters = snapshot.get("counters", {})
    histograms = snapshot.get("histograms", {})
    
    return {
        "period": period,
        "jobs": {
            "created": counters.get("jobs_created_total", 0),
            "completed": counters.get("jobs_completed_total", 0),
            "in_progress": snapshot.get("gauges", {}).get("jobs_in_progress", 0)
        },
        "duration": histograms.get("job_duration_seconds", {}),
        "engines": {
            "executions": counters.get("engine_executions_total", 0),
            "duration": histograms.get("engine_duration_seconds", {})
        }
    }


def get_quality_trends() -> Dict:
    """Get content quality trends"""
    snapshot = metrics.get_snapshot()
    histograms = snapshot.get("histograms", {})
    
    return {
        "period": "recent",
        "quality_scores": {
            "content": histograms.get("content_quality_score", {}),
            "hook": histograms.get("hook_effectiveness_score", {}),
            "thumbnail_ctr": histograms.get("thumbnail_ctr_score", {}),
            "pacing": histograms.get("pacing_quality_score", {})
        }
    }


def get_api_statistics() -> Dict:
    """Get API usage statistics"""
    snapshot = metrics.get_snapshot()
    
    return {
        "requests": {
            "total": snapshot.get("counters", {}).get("api_requests_total", 0),
            "in_progress": snapshot.get("gauges", {}).get("api_requests_in_progress", 0)
        },
        "duration": snapshot.get("histograms", {}).get("api_request_duration_seconds", {})
    }


def get_error_dashboard() -> Dict:
    """Get error dashboard data"""
    summary = error_tracker.get_summary()
    errors = error_tracker.get_all_errors()
    
    return {
        "summary": summary,
        "top_errors": [e.to_dict() for e in errors[:10]]
    }
