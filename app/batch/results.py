"""
Batch Result Models
Aggregation and reporting for batch operations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class RetryStrategy(str, Enum):
    """Retry strategy for failed items"""
    NONE = "none"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    IMMEDIATE = "immediate"


@dataclass
class ItemError:
    """Individual item error"""
    item_id: str
    order: int
    error_code: str
    error_message: str
    timestamp: datetime
    retry_count: int = 0


@dataclass
class BatchResult:
    """
    Batch processing result with aggregation.
    Provides comprehensive summary of batch execution.
    """
    batch_id: str
    total_items: int
    succeeded: int
    failed: int
    pending: int
    skipped: int = 0
    
    errors: List[ItemError] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> int:
        """Calculate duration in milliseconds"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.succeeded / self.total_items) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if batch is fully complete"""
        return self.pending == 0 and self.failed == 0
    
    @property
    def is_partial(self) -> bool:
        """Check if batch has partial success"""
        return self.succeeded > 0 and self.failed > 0
    
    def add_error(self, error: ItemError):
        """Add an error to the result"""
        self.errors.append(error)
        self.failed += 1
    
    def mark_success(self):
        """Mark an item as successful"""
        self.succeeded += 1
        if self.pending > 0:
            self.pending -= 1
    
    def finalize(self):
        """Mark batch as complete"""
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "batch_id": self.batch_id,
            "total_items": self.total_items,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "pending": self.pending,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate, 2),
            "duration_ms": self.duration_ms,
            "is_complete": self.is_complete,
            "is_partial": self.is_partial,
            "errors": [
                {
                    "item_id": e.item_id,
                    "order": e.order,
                    "error_code": e.error_code,
                    "error_message": e.error_message,
                    "retry_count": e.retry_count
                }
                for e in self.errors[:10]  # Limit to first 10 errors
            ],
            "error_count": len(self.errors),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


def calculate_backoff_delay(retry_count: int, base_delay: float = 1.0, max_delay: float = 32.0) -> float:
    """
    Calculate exponential backoff delay.
    
    Retry 1: 1s
    Retry 2: 2s
    Retry 3: 4s
    Retry 4: 8s
    Retry 5: 16s
    Retry 6+: 32s (capped)
    """
    delay = base_delay * (2 ** (retry_count - 1))
    return min(delay, max_delay)
