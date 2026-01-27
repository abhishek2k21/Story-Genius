"""
Schedule API Routes
Job scheduling, recurrence, and calendar.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.scheduling.models import (
    ScheduleType, ScheduleStatus, JobType, Priority, Frequency, RecurrenceRule
)
from app.scheduling.service import scheduling_service
from app.scheduling.timezone import list_timezones
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/schedules", tags=["scheduling"])


# ==================== Request Models ====================

class RecurrenceRuleRequest(BaseModel):
    frequency: str
    interval: int = 1
    days_of_week: Optional[List[int]] = None
    days_of_month: Optional[List[int]] = None
    time_of_day: str = "09:00"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    count: Optional[int] = None


class CreateScheduleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    job_type: str
    job_config: dict
    schedule_type: str
    scheduled_at: Optional[str] = None
    recurrence_rule: Optional[RecurrenceRuleRequest] = None
    timezone: str = "UTC"
    priority: str = "normal"
    max_runs: Optional[int] = None
    description: str = ""


class UpdateScheduleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    max_runs: Optional[int] = None


class CloneRequest(BaseModel):
    new_name: Optional[str] = None


class BulkIdsRequest(BaseModel):
    schedule_ids: List[str]


# ==================== Helper Functions ====================

def parse_recurrence(req: RecurrenceRuleRequest) -> RecurrenceRule:
    """Parse recurrence request to model"""
    return RecurrenceRule(
        frequency=Frequency(req.frequency),
        interval=req.interval,
        days_of_week=req.days_of_week or [],
        days_of_month=req.days_of_month or [],
        time_of_day=req.time_of_day,
        start_date=date.fromisoformat(req.start_date) if req.start_date else None,
        end_date=date.fromisoformat(req.end_date) if req.end_date else None,
        count=req.count
    )


# ==================== Schedule Endpoints ====================

@router.post("")
async def create_schedule(
    request: CreateScheduleRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create a new schedule"""
    try:
        job_type = JobType(request.job_type)
        schedule_type = ScheduleType(request.schedule_type)
        priority = Priority(request.priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    scheduled_at = None
    if request.scheduled_at:
        scheduled_at = datetime.fromisoformat(request.scheduled_at)
    
    recurrence_rule = None
    if request.recurrence_rule:
        recurrence_rule = parse_recurrence(request.recurrence_rule)
    
    schedule, msg = scheduling_service.create_schedule(
        user_id=auth.user.user_id,
        name=request.name,
        job_type=job_type,
        job_config=request.job_config,
        schedule_type=schedule_type,
        scheduled_at=scheduled_at,
        recurrence_rule=recurrence_rule,
        timezone=request.timezone,
        priority=priority,
        max_runs=request.max_runs,
        description=request.description
    )
    
    if not schedule:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "schedule": schedule.to_dict()}


@router.get("")
async def list_schedules(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """List user's schedules"""
    status_enum = ScheduleStatus(status) if status else None
    job_type_enum = JobType(job_type) if job_type else None
    
    schedules = scheduling_service.list_schedules(
        auth.user.user_id, status_enum, job_type_enum
    )
    
    return {
        "count": len(schedules),
        "schedules": [s.to_dict() for s in schedules]
    }


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get schedule details"""
    schedule = scheduling_service.get_schedule(schedule_id, auth.user.user_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule.to_dict()


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Update schedule"""
    updates = {}
    if request.name:
        updates["name"] = request.name
    if request.description is not None:
        updates["description"] = request.description
    if request.priority:
        updates["priority"] = Priority(request.priority)
    if request.max_runs:
        updates["max_runs"] = request.max_runs
    
    schedule, msg = scheduling_service.update_schedule(
        schedule_id, auth.user.user_id, **updates
    )
    
    if not schedule:
        raise HTTPException(status_code=404, detail=msg)
    
    return {"message": msg, "schedule": schedule.to_dict()}


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete schedule"""
    if scheduling_service.delete_schedule(schedule_id, auth.user.user_id):
        return {"message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


# ==================== Control Endpoints ====================

@router.post("/{schedule_id}/pause")
async def pause_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Pause schedule"""
    schedule, msg = scheduling_service.pause_schedule(schedule_id, auth.user.user_id)
    if not schedule:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "schedule": schedule.to_dict()}


@router.post("/{schedule_id}/resume")
async def resume_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Resume schedule"""
    schedule, msg = scheduling_service.resume_schedule(schedule_id, auth.user.user_id)
    if not schedule:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "schedule": schedule.to_dict()}


@router.post("/{schedule_id}/cancel")
async def cancel_schedule(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Cancel schedule"""
    schedule, msg = scheduling_service.cancel_schedule(schedule_id, auth.user.user_id)
    if not schedule:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "schedule": schedule.to_dict()}


@router.post("/{schedule_id}/run")
async def run_now(
    schedule_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Execute schedule immediately"""
    execution, msg = scheduling_service.run_now(schedule_id, auth.user.user_id)
    if not execution:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "execution": execution.to_dict()}


@router.post("/{schedule_id}/clone")
async def clone_schedule(
    schedule_id: str,
    request: CloneRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Clone schedule"""
    schedule, msg = scheduling_service.clone_schedule(
        schedule_id, auth.user.user_id, request.new_name
    )
    if not schedule:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "schedule": schedule.to_dict()}


# ==================== History Endpoints ====================

@router.get("/{schedule_id}/executions")
async def get_executions(
    schedule_id: str,
    limit: int = 20,
    auth: AuthContext = Depends(get_current_user)
):
    """Get execution history"""
    executions = scheduling_service.get_executions(schedule_id, auth.user.user_id, limit)
    return {
        "count": len(executions),
        "executions": [e.to_dict() for e in executions]
    }


@router.get("/{schedule_id}/next")
async def get_next_occurrences(
    schedule_id: str,
    n: int = 10,
    auth: AuthContext = Depends(get_current_user)
):
    """Get next N occurrences"""
    occurrences = scheduling_service.get_next_occurrences(schedule_id, auth.user.user_id, n)
    return {
        "count": len(occurrences),
        "occurrences": [o.isoformat() for o in occurrences]
    }


# ==================== Calendar Endpoints ====================

@router.get("/calendar/view")
async def get_calendar(
    start_date: str,
    end_date: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Get calendar view"""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    return scheduling_service.get_calendar(auth.user.user_id, start, end)


@router.get("/upcoming/list")
async def get_upcoming(
    limit: int = 10,
    hours: int = 24,
    auth: AuthContext = Depends(get_current_user)
):
    """Get upcoming executions"""
    upcoming = scheduling_service.get_upcoming(auth.user.user_id, limit, hours)
    return {"count": len(upcoming), "upcoming": upcoming}


# ==================== Utility Endpoints ====================

@router.get("/patterns/list")
async def get_patterns():
    """Get common schedule patterns"""
    patterns = scheduling_service.get_patterns()
    return {"count": len(patterns), "patterns": patterns}


@router.get("/timezones/list")
async def get_timezones():
    """Get supported timezones"""
    timezones = list_timezones()
    return {"count": len(timezones), "timezones": timezones}
