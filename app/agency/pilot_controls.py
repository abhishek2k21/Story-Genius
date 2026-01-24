"""
Pilot Controls and Safety
Implements rate limits, kill switches, and human-in-the-loop controls.
"""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import threading

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class JobState(str, Enum):
    """Job state for kill switch tracking."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    KILLED = "killed"
    FAILED = "failed"


@dataclass
class RateLimiter:
    """Rate limiter for API/generation requests."""
    max_requests_per_minute: int = 20
    max_requests_per_hour: int = 200
    
    _minute_requests: List[datetime] = field(default_factory=list)
    _hour_requests: List[datetime] = field(default_factory=list)
    
    def can_proceed(self) -> tuple:
        """Check if request can proceed."""
        now = datetime.utcnow()
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        self._minute_requests = [r for r in self._minute_requests if r > minute_ago]
        self._hour_requests = [r for r in self._hour_requests if r > hour_ago]
        
        # Check limits
        if len(self._minute_requests) >= self.max_requests_per_minute:
            return False, f"Rate limit: {self.max_requests_per_minute}/min exceeded"
        
        if len(self._hour_requests) >= self.max_requests_per_hour:
            return False, f"Rate limit: {self.max_requests_per_hour}/hour exceeded"
        
        return True, "OK"
    
    def record_request(self):
        """Record a request."""
        now = datetime.utcnow()
        self._minute_requests.append(now)
        self._hour_requests.append(now)


@dataclass
class HumanInTheLoopConfig:
    """Configuration for human-in-the-loop controls."""
    # Approval requirements
    require_hook_approval: bool = False
    require_batch_approval: bool = False
    
    # Locks
    lock_persona: bool = False
    locked_persona_id: str = ""
    lock_visual_style: bool = False
    locked_visual_style_id: str = ""
    
    # Limits
    max_retries: int = 2
    max_batch_size: int = 50
    max_duration: int = 35
    
    # Safety
    auto_pause_on_failures: int = 5  # Pause after N consecutive failures
    
    def validate_job_config(self, config: dict) -> tuple:
        """Validate job config against controls."""
        issues = []
        
        if config.get("duration", 30) > self.max_duration:
            issues.append(f"Duration exceeds max ({self.max_duration}s)")
        
        if self.lock_persona and config.get("persona") != self.locked_persona_id:
            issues.append("Persona is locked")
        
        return len(issues) == 0, issues


class HookApprovalQueue:
    """Queue for hook approvals (human-in-the-loop)."""
    
    def __init__(self):
        self._pending: Dict[str, Dict] = {}
        self._approved: Dict[str, bool] = {}
    
    def submit_for_approval(self, job_id: str, hooks: List[Dict]) -> str:
        """Submit hooks for approval."""
        approval_id = f"approval_{uuid.uuid4().hex[:8]}"
        
        self._pending[approval_id] = {
            "job_id": job_id,
            "hooks": hooks,
            "submitted_at": datetime.utcnow(),
            "status": "pending"
        }
        
        logger.info(f"Hooks submitted for approval: {approval_id}")
        return approval_id
    
    def approve(self, approval_id: str, selected_hook_index: int = 0) -> bool:
        """Approve a hook selection."""
        if approval_id not in self._pending:
            return False
        
        self._pending[approval_id]["status"] = "approved"
        self._pending[approval_id]["selected_index"] = selected_hook_index
        self._approved[approval_id] = True
        
        logger.info(f"Approved: {approval_id}, selected hook {selected_hook_index}")
        return True
    
    def reject(self, approval_id: str, reason: str = "") -> bool:
        """Reject hooks and request regeneration."""
        if approval_id not in self._pending:
            return False
        
        self._pending[approval_id]["status"] = "rejected"
        self._pending[approval_id]["reason"] = reason
        self._approved[approval_id] = False
        
        logger.info(f"Rejected: {approval_id} - {reason}")
        return True
    
    def is_approved(self, approval_id: str) -> Optional[bool]:
        """Check if approval exists and its status."""
        return self._approved.get(approval_id)
    
    def get_pending(self) -> List[Dict]:
        """Get all pending approvals."""
        return [
            {**v, "approval_id": k}
            for k, v in self._pending.items()
            if v["status"] == "pending"
        ]


class KillSwitch:
    """Kill switch for runaway jobs."""
    
    def __init__(self):
        self._killed_jobs: set = set()
        self._running_jobs: Dict[str, datetime] = {}
        self._global_kill: bool = False
        self._consecutive_failures: int = 0
        self._auto_pause_threshold: int = 5
    
    def register_job(self, job_id: str):
        """Register a running job."""
        self._running_jobs[job_id] = datetime.utcnow()
    
    def unregister_job(self, job_id: str, success: bool):
        """Unregister a completed job."""
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]
        
        if success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._auto_pause_threshold:
                logger.warning(f"Auto-pause triggered after {self._consecutive_failures} failures")
                self._global_kill = True
    
    def kill_job(self, job_id: str) -> bool:
        """Kill a specific job."""
        if job_id in self._running_jobs:
            self._killed_jobs.add(job_id)
            logger.warning(f"Kill switch activated for job: {job_id}")
            return True
        return False
    
    def kill_all(self):
        """Kill all running jobs."""
        self._global_kill = True
        for job_id in list(self._running_jobs.keys()):
            self._killed_jobs.add(job_id)
        logger.warning(f"GLOBAL KILL: Stopped {len(self._killed_jobs)} jobs")
    
    def resume(self):
        """Resume after global kill."""
        self._global_kill = False
        self._consecutive_failures = 0
        logger.info("System resumed from kill state")
    
    def should_stop(self, job_id: str) -> bool:
        """Check if a job should stop."""
        return self._global_kill or job_id in self._killed_jobs
    
    def get_status(self) -> Dict:
        """Get kill switch status."""
        return {
            "global_kill": self._global_kill,
            "running_jobs": len(self._running_jobs),
            "killed_jobs": len(self._killed_jobs),
            "consecutive_failures": self._consecutive_failures
        }


class PilotControlService:
    """
    Central service for pilot controls and safety.
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.kill_switch = KillSwitch()
        self.approval_queue = HookApprovalQueue()
        self._client_configs: Dict[str, HumanInTheLoopConfig] = {}
    
    def set_client_config(self, client_id: str, config: HumanInTheLoopConfig):
        """Set human-in-the-loop config for a client."""
        self._client_configs[client_id] = config
        logger.info(f"Set HITL config for client {client_id}")
    
    def get_client_config(self, client_id: str) -> HumanInTheLoopConfig:
        """Get config for a client (or default)."""
        return self._client_configs.get(client_id, HumanInTheLoopConfig())
    
    def can_start_job(self, client_id: str = None) -> tuple:
        """Check if a new job can start."""
        # Check rate limits
        can, msg = self.rate_limiter.can_proceed()
        if not can:
            return False, msg
        
        # Check global kill
        if self.kill_switch._global_kill:
            return False, "System is paused. Contact admin."
        
        return True, "OK"
    
    def start_job(self, job_id: str):
        """Record job start."""
        self.rate_limiter.record_request()
        self.kill_switch.register_job(job_id)
    
    def end_job(self, job_id: str, success: bool):
        """Record job end."""
        self.kill_switch.unregister_job(job_id, success)
    
    def get_system_status(self) -> Dict:
        """Get overall system status."""
        return {
            "rate_limiter": {
                "requests_last_minute": len(self.rate_limiter._minute_requests),
                "requests_last_hour": len(self.rate_limiter._hour_requests)
            },
            "kill_switch": self.kill_switch.get_status(),
            "pending_approvals": len(self.approval_queue.get_pending())
        }


# Global instance
_pilot_controls = None

def get_pilot_controls() -> PilotControlService:
    """Get global pilot control service."""
    global _pilot_controls
    if _pilot_controls is None:
        _pilot_controls = PilotControlService()
    return _pilot_controls
