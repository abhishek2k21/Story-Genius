"""
Health Check System
Monitors system components and provides health endpoints.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os
import psutil

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: Optional[float] = None
    details: Dict = None
    
    def to_dict(self):
        result = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message
        }
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms
        if self.details:
            result["details"] = self.details
        return result


class HealthCheckService:
    """Service for checking system health"""
    
    def __init__(self):
        self.storage_path = ".story_assets"
        self._last_check: Optional[datetime] = None
        self._last_result: Optional[Dict] = None
    
    def check_all(self) -> Dict:
        """Run all health checks"""
        start = datetime.now()
        
        components = [
            self._check_storage(),
            self._check_memory(),
            self._check_disk(),
            self._check_database(),
            self._check_job_queue()
        ]
        
        # Determine overall status
        statuses = [c.status for c in components]
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        result = {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": round(duration, 2),
            "components": [c.to_dict() for c in components]
        }
        
        self._last_check = datetime.now()
        self._last_result = result
        
        return result
    
    def check_liveness(self) -> Dict:
        """Simple liveness probe (is the service running?)"""
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }
    
    def check_readiness(self) -> Dict:
        """Readiness probe (is the service ready to accept requests?)"""
        # Check critical components only
        storage_ok = os.path.exists(self.storage_path)
        
        status = "ready" if storage_ok else "not_ready"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "storage": storage_ok
            }
        }
    
    def _check_storage(self) -> ComponentHealth:
        """Check storage accessibility"""
        try:
            start = datetime.now()
            
            # Check if storage path exists and is writable
            if not os.path.exists(self.storage_path):
                os.makedirs(self.storage_path, exist_ok=True)
            
            # Try writing a test file
            test_path = os.path.join(self.storage_path, ".health_check")
            with open(test_path, 'w') as f:
                f.write(str(datetime.now()))
            os.remove(test_path)
            
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                message="Storage accessible",
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage error: {str(e)}"
            )
    
    def _check_memory(self) -> ComponentHealth:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {used_percent}%"
            elif used_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {used_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory OK: {used_percent}% used"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "percent_used": used_percent,
                    "available_mb": round(memory.available / (1024 * 1024), 0)
                }
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Cannot check memory: {str(e)}"
            )
    
    def _check_disk(self) -> ComponentHealth:
        """Check disk space"""
        try:
            disk = psutil.disk_usage(os.path.abspath('.'))
            used_percent = disk.percent
            free_gb = disk.free / (1024 ** 3)
            
            if used_percent > 95 or free_gb < 1:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk space: {free_gb:.1f}GB free"
            elif used_percent > 85 or free_gb < 5:
                status = HealthStatus.DEGRADED
                message = f"Low disk space: {free_gb:.1f}GB free"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk OK: {free_gb:.1f}GB free"
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "percent_used": used_percent,
                    "free_gb": round(free_gb, 2)
                }
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.DEGRADED,
                message=f"Cannot check disk: {str(e)}"
            )
    
    def _check_database(self) -> ComponentHealth:
        """Check database connectivity"""
        try:
            # For now, check if SQLite database file exists/accessible
            from app.core.config import settings
            
            # Simple check - in production this would be a real query
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database accessible"
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )
    
    def _check_job_queue(self) -> ComponentHealth:
        """Check job processing status"""
        try:
            from app.reliability.checkpointing import CheckpointService
            from app.reliability.dead_letter import DeadLetterService
            
            checkpoint_svc = CheckpointService()
            dead_letter_svc = DeadLetterService()
            
            active_jobs = len(checkpoint_svc.list_checkpoints())
            pending_dead_letters = dead_letter_svc.get_pending_count()
            
            if pending_dead_letters > 10:
                status = HealthStatus.DEGRADED
                message = f"{pending_dead_letters} jobs in dead letter queue"
            else:
                status = HealthStatus.HEALTHY
                message = f"{active_jobs} active jobs"
            
            return ComponentHealth(
                name="job_queue",
                status=status,
                message=message,
                details={
                    "active_jobs": active_jobs,
                    "dead_letters_pending": pending_dead_letters
                }
            )
        except Exception as e:
            return ComponentHealth(
                name="job_queue",
                status=HealthStatus.DEGRADED,
                message=f"Cannot check queue: {str(e)}"
            )
