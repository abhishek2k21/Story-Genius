"""
Observability API Routes
Health, metrics, errors, and dashboard endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.observability.health import health_monitor, HealthStatus
from app.observability.metrics import metrics
from app.observability.errors import error_tracker, ErrorStatus
from app.observability.dashboard import (
    get_dashboard_overview, get_job_statistics, 
    get_quality_trends, get_api_statistics, get_error_dashboard
)

router = APIRouter(prefix="/v1", tags=["observability"])


# ==================== Health Endpoints ====================

@router.get("/health")
async def get_health():
    """Overall health status"""
    health = await health_monitor.check_all()
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
    return health.to_dict()


@router.get("/health/live")
async def liveness_probe():
    """Liveness probe for container orchestration"""
    return health_monitor.liveness()


@router.get("/health/ready")
async def readiness_probe():
    """Readiness probe for container orchestration"""
    return health_monitor.readiness()


@router.get("/health/components")
async def get_component_health():
    """All component health statuses"""
    health = await health_monitor.check_all()
    return {
        "overall": health.status.value,
        "components": [c.to_dict() for c in health.components]
    }


# ==================== Metrics Endpoints ====================

@router.get("/metrics")
async def get_all_metrics():
    """Current metrics snapshot"""
    return metrics.get_snapshot()


@router.get("/metrics/jobs")
async def get_job_metrics():
    """Job-related metrics"""
    snapshot = metrics.get_snapshot()
    return {
        "counters": {k: v for k, v in snapshot.get("counters", {}).items() if "job" in k.lower()},
        "gauges": {k: v for k, v in snapshot.get("gauges", {}).items() if "job" in k.lower()},
        "histograms": {k: v for k, v in snapshot.get("histograms", {}).items() if "job" in k.lower()}
    }


@router.get("/metrics/engines")
async def get_engine_metrics():
    """Engine-related metrics"""
    snapshot = metrics.get_snapshot()
    return {
        "counters": {k: v for k, v in snapshot.get("counters", {}).items() if "engine" in k.lower()},
        "histograms": {k: v for k, v in snapshot.get("histograms", {}).items() if "engine" in k.lower()}
    }


@router.get("/metrics/api")
async def get_api_metrics():
    """API-related metrics"""
    snapshot = metrics.get_snapshot()
    return {
        "counters": {k: v for k, v in snapshot.get("counters", {}).items() if "api" in k.lower()},
        "gauges": {k: v for k, v in snapshot.get("gauges", {}).items() if "api" in k.lower()},
        "histograms": {k: v for k, v in snapshot.get("histograms", {}).items() if "api" in k.lower()}
    }


# ==================== Error Endpoints ====================

@router.get("/errors")
async def get_errors(status: Optional[str] = None):
    """List all errors with optional status filter"""
    status_enum = None
    if status:
        try:
            status_enum = ErrorStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    errors = error_tracker.get_all_errors(status_enum)
    return {
        "count": len(errors),
        "errors": [e.to_dict() for e in errors]
    }


@router.get("/errors/summary")
async def get_error_summary():
    """Error summary statistics"""
    return error_tracker.get_summary()


@router.get("/errors/{error_id}")
async def get_error_details(error_id: str):
    """Get specific error details"""
    error = error_tracker.get_error(error_id)
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    return error.to_detail_dict()


@router.post("/errors/{error_id}/acknowledge")
async def acknowledge_error(error_id: str):
    """Acknowledge an error"""
    if error_tracker.acknowledge(error_id):
        return {"status": "acknowledged", "error_id": error_id}
    raise HTTPException(status_code=404, detail="Error not found")


class ResolveRequest(BaseModel):
    notes: str = Field(default="")


@router.post("/errors/{error_id}/resolve")
async def resolve_error(error_id: str, request: ResolveRequest):
    """Mark error as resolved"""
    if error_tracker.resolve(error_id, request.notes):
        return {"status": "resolved", "error_id": error_id}
    raise HTTPException(status_code=404, detail="Error not found")


# ==================== Dashboard Endpoints ====================

@router.get("/dashboard/overview")
async def dashboard_overview():
    """System overview dashboard data"""
    return await get_dashboard_overview()


@router.get("/dashboard/jobs")
async def dashboard_jobs(period: str = "day"):
    """Job statistics dashboard"""
    return get_job_statistics(period)


@router.get("/dashboard/quality")
async def dashboard_quality():
    """Quality trends dashboard"""
    return get_quality_trends()


@router.get("/dashboard/api")
async def dashboard_api():
    """API statistics dashboard"""
    return get_api_statistics()


@router.get("/dashboard/errors")
async def dashboard_errors():
    """Error dashboard data"""
    return get_error_dashboard()
