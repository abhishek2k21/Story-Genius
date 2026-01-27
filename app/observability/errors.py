"""
Error Tracking and Aggregation
Capture, fingerprint, and aggregate errors for analysis.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import traceback
import threading


class ErrorCategory(str, Enum):
    TRANSIENT = "transient"       # Network, timeout, rate limit
    CONFIGURATION = "configuration"  # Invalid settings
    RESOURCE = "resource"         # Memory, disk, connections
    BUG = "bug"                   # Unexpected exception
    EXTERNAL = "external"         # Third-party API failure
    USER = "user"                 # Invalid input


class ErrorStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class ErrorRecord:
    """An aggregated error record"""
    error_id: str
    error_type: str
    error_message: str
    stack_trace: str
    fingerprint: str
    category: ErrorCategory
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int = 1
    affected_jobs: List[str] = field(default_factory=list)
    affected_batches: List[str] = field(default_factory=list)
    status: ErrorStatus = ErrorStatus.NEW
    resolution_notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "message": self.error_message,
            "fingerprint": self.fingerprint[:16],
            "category": self.category.value,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrences": self.occurrence_count,
            "affected_jobs": len(self.affected_jobs),
            "status": self.status.value
        }
    
    def to_detail_dict(self) -> Dict:
        d = self.to_dict()
        d["stack_trace"] = self.stack_trace
        d["affected_jobs"] = self.affected_jobs[:10]
        d["affected_batches"] = self.affected_batches[:10]
        d["resolution_notes"] = self.resolution_notes
        return d


def create_fingerprint(
    error_type: str,
    error_message: str,
    stack_frames: List[str]
) -> str:
    """Create fingerprint for error grouping"""
    # Normalize message by removing variable parts
    normalized_msg = _normalize_message(error_message)
    
    # Use top 3 frames
    top_frames = stack_frames[:3] if stack_frames else []
    
    content = f"{error_type}:{normalized_msg}:{':'.join(top_frames)}"
    return hashlib.md5(content.encode()).hexdigest()


def _normalize_message(message: str) -> str:
    """Remove variable parts from error message"""
    import re
    # Remove UUIDs
    message = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', message)
    # Remove numbers
    message = re.sub(r'\d+', '<N>', message)
    # Remove file paths
    message = re.sub(r'[A-Za-z]:\\[^\s]+', '<PATH>', message)
    message = re.sub(r'/[^\s]+', '<PATH>', message)
    return message


def categorize_error(error_type: str, error_message: str) -> ErrorCategory:
    """Categorize error based on type and message"""
    msg_lower = error_message.lower()
    
    # Transient errors
    transient_keywords = ["timeout", "connection", "network", "rate limit", "retry"]
    if any(k in msg_lower for k in transient_keywords):
        return ErrorCategory.TRANSIENT
    
    # Configuration errors
    config_keywords = ["config", "setting", "invalid parameter", "missing required"]
    if any(k in msg_lower for k in config_keywords):
        return ErrorCategory.CONFIGURATION
    
    # Resource errors
    resource_keywords = ["memory", "disk", "space", "connection pool", "exhausted"]
    if any(k in msg_lower for k in resource_keywords):
        return ErrorCategory.RESOURCE
    
    # External errors
    external_keywords = ["api", "external", "service unavailable", "502", "503"]
    if any(k in msg_lower for k in external_keywords):
        return ErrorCategory.EXTERNAL
    
    # User errors
    if "ValueError" in error_type or "validation" in msg_lower:
        return ErrorCategory.USER
    
    return ErrorCategory.BUG


class ErrorTracker:
    """Central error tracking and aggregation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._errors: Dict[str, ErrorRecord] = {}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def capture(
        self,
        exception: Exception,
        job_id: str = None,
        batch_id: str = None,
        context: Dict = None
    ) -> ErrorRecord:
        """Capture and aggregate an error"""
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        stack_frames = [line.strip() for line in stack_trace.split('\n') if 'File' in line]
        
        fingerprint = create_fingerprint(error_type, error_message, stack_frames)
        category = categorize_error(error_type, error_message)
        
        with self._lock:
            if fingerprint in self._errors:
                # Update existing
                record = self._errors[fingerprint]
                record.last_seen = datetime.utcnow()
                record.occurrence_count += 1
                if job_id and job_id not in record.affected_jobs:
                    record.affected_jobs.append(job_id)
                if batch_id and batch_id not in record.affected_batches:
                    record.affected_batches.append(batch_id)
            else:
                # Create new
                record = ErrorRecord(
                    error_id=fingerprint[:16],
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                    fingerprint=fingerprint,
                    category=category,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    affected_jobs=[job_id] if job_id else [],
                    affected_batches=[batch_id] if batch_id else []
                )
                self._errors[fingerprint] = record
            
            return record
    
    def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        """Get error by ID"""
        for record in self._errors.values():
            if record.error_id == error_id:
                return record
        return None
    
    def get_all_errors(self, status: ErrorStatus = None) -> List[ErrorRecord]:
        """Get all errors, optionally filtered by status"""
        errors = list(self._errors.values())
        if status:
            errors = [e for e in errors if e.status == status]
        return sorted(errors, key=lambda e: e.last_seen, reverse=True)
    
    def acknowledge(self, error_id: str) -> bool:
        """Acknowledge an error"""
        record = self.get_error(error_id)
        if record:
            record.status = ErrorStatus.ACKNOWLEDGED
            return True
        return False
    
    def resolve(self, error_id: str, notes: str = "") -> bool:
        """Mark error as resolved"""
        record = self.get_error(error_id)
        if record:
            record.status = ErrorStatus.RESOLVED
            record.resolution_notes = notes
            return True
        return False
    
    def get_summary(self) -> Dict:
        """Get error summary"""
        errors = list(self._errors.values())
        
        by_category = {}
        by_status = {}
        
        for e in errors:
            by_category[e.category.value] = by_category.get(e.category.value, 0) + 1
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        
        return {
            "total_unique": len(errors),
            "total_occurrences": sum(e.occurrence_count for e in errors),
            "by_category": by_category,
            "by_status": by_status,
            "recent": [e.to_dict() for e in errors[:5]]
        }


# Singleton instance
error_tracker = ErrorTracker()
