"""
Bulk Operations
Bulk schedule management.
"""
from typing import Dict, List
from dataclasses import dataclass, field
import uuid

from app.scheduling.models import ScheduledJob, ScheduleStatus


MAX_BULK_SIZE = 50


@dataclass
class BulkResult:
    """Result of bulk operation"""
    operation_id: str
    operation: str
    total: int
    success: int
    failed: int
    failures: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "operation_id": self.operation_id,
            "operation": self.operation,
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "failures": self.failures
        }


def bulk_pause(schedules: List[ScheduledJob]) -> BulkResult:
    """Pause multiple schedules"""
    if len(schedules) > MAX_BULK_SIZE:
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="pause",
            total=0, success=0, failed=1,
            failures=[{"error": f"Max {MAX_BULK_SIZE} schedules"}]
        )
    
    success = 0
    failures = []
    
    for s in schedules:
        if s.status == ScheduleStatus.ACTIVE:
            s.status = ScheduleStatus.PAUSED
            success += 1
        else:
            failures.append({"schedule_id": s.schedule_id, "error": f"Cannot pause: {s.status.value}"})
    
    return BulkResult(
        operation_id=str(uuid.uuid4()),
        operation="pause",
        total=len(schedules),
        success=success,
        failed=len(failures),
        failures=failures
    )


def bulk_resume(schedules: List[ScheduledJob]) -> BulkResult:
    """Resume multiple schedules"""
    if len(schedules) > MAX_BULK_SIZE:
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="resume",
            total=0, success=0, failed=1,
            failures=[{"error": f"Max {MAX_BULK_SIZE} schedules"}]
        )
    
    success = 0
    failures = []
    
    for s in schedules:
        if s.status == ScheduleStatus.PAUSED:
            s.status = ScheduleStatus.ACTIVE
            success += 1
        else:
            failures.append({"schedule_id": s.schedule_id, "error": f"Cannot resume: {s.status.value}"})
    
    return BulkResult(
        operation_id=str(uuid.uuid4()),
        operation="resume",
        total=len(schedules),
        success=success,
        failed=len(failures),
        failures=failures
    )


def bulk_cancel(schedules: List[ScheduledJob]) -> BulkResult:
    """Cancel multiple schedules"""
    if len(schedules) > MAX_BULK_SIZE:
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="cancel",
            total=0, success=0, failed=1,
            failures=[{"error": f"Max {MAX_BULK_SIZE} schedules"}]
        )
    
    success = 0
    failures = []
    
    for s in schedules:
        if s.status not in [ScheduleStatus.CANCELLED, ScheduleStatus.COMPLETED]:
            s.status = ScheduleStatus.CANCELLED
            s.next_run_at = None
            success += 1
        else:
            failures.append({"schedule_id": s.schedule_id, "error": f"Already: {s.status.value}"})
    
    return BulkResult(
        operation_id=str(uuid.uuid4()),
        operation="cancel",
        total=len(schedules),
        success=success,
        failed=len(failures),
        failures=failures
    )
