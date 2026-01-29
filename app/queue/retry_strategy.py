"""
Retry Strategy and Dead-Letter Queue
Implements exponential backoff retry and DLQ for failed tasks.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 5
    backoff_delays: list = None  # [60, 300, 1800, 7200] seconds
    backoff_max: int = 7200  # 2 hours
    jitter: bool = True
    
    def __post_init__(self):
        if self.backoff_delays is None:
            self.backoff_delays = [60, 300, 1800, 7200]  # 1m, 5m, 30m, 2h


class RetryStrategy:
    """
    Exponential backoff retry strategy.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        logger.info(f"RetryStrategy initialized with {self.config.max_retries} max retries")
    
    def calculate_delay(self, retry_count: int) -> int:
        """
        Calculate retry delay based on retry count.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
        
        Returns:
            Delay in seconds
        """
        if retry_count >= len(self.config.backoff_delays):
            # Use max delay for retries beyond configured delays
            delay = self.config.backoff_max
        else:
            delay = self.config.backoff_delays[retry_count]
        
        # Add jitter to avoid thundering herd
        if self.config.jitter:
            import random
            jitter = random.uniform(0, delay * 0.1)  # 0-10% jitter
            delay += jitter
        
        logger.debug(f"Retry {retry_count + 1}: delay={delay:.1f}s")
        return int(delay)
    
    def should_retry(self, retry_count: int, error: Exception) -> bool:
        """
        Determine if task should be retried.
        
        Args:
            retry_count: Current retry count
            error: Exception that occurred
        
        Returns:
            True if should retry, False otherwise
        """
        # Check max retries
        if retry_count >= self.config.max_retries:
            logger.warning(f"Max retries ({self.config.max_retries}) reached")
            return False
        
        # Check if error is retryable (all exceptions for now)
        # In production, filter out permanent errors (4xx client errors)
        return True


@dataclass
class DLQEntry:
    """Dead-letter queue entry"""
    task_id: str
    task_name: str
    args: tuple
    kwargs: dict
    error_message: str
    error_type: str
    retry_count: int
    failed_at: datetime
    original_eta: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "args": self.args,
            "kwargs": self.kwargs,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "retry_count": self.retry_count,
            "failed_at": self.failed_at.isoformat(),
            "original_eta": self.original_eta.isoformat() if self.original_eta else None
        }


class DeadLetterQueue:
    """
    Dead-letter queue for permanently failed tasks.
    Stores tasks that exceeded max retries.
    """
    
    def __init__(self):
        self._entries: Dict[str, DLQEntry] = {}
        logger.info("DeadLetterQueue initialized")
    
    def add(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: dict,
        error: Exception,
        retry_count: int,
        original_eta: Optional[datetime] = None
    ) -> DLQEntry:
        """
        Add failed task to DLQ.
        
        Args:
            task_id: Task ID
            task_name: Task name
            args: Task args
            kwargs: Task kwargs
            error: Exception that caused failure
            retry_count: Number of retries attempted
            original_eta: Original ETA if scheduled
        
        Returns:
            DLQ entry
        """
        entry = DLQEntry(
            task_id=task_id,
            task_name=task_name,
            args=args,
            kwargs=kwargs,
            error_message=str(error),
            error_type=type(error).__name__,
            retry_count=retry_count,
            failed_at=datetime.utcnow(),
            original_eta=original_eta
        )
        
        self._entries[task_id] = entry
        
        logger.error(
            f"Task {task_id} ({task_name}) added to DLQ after {retry_count} retries: {error}",
            extra={"dlq_entry": entry.to_dict()}
        )
        
        # In production: trigger alert
        self._trigger_alert(entry)
        
        return entry
    
    def get(self, task_id: str) -> Optional[DLQEntry]:
        """Get DLQ entry by task ID"""
        return self._entries.get(task_id)
    
    def list_all(self) -> list[DLQEntry]:
        """List all DLQ entries"""
        return list(self._entries.values())
    
    def remove(self, task_id: str) -> bool:
        """
        Remove entry from DLQ (after manual resolution).
        
        Args:
            task_id: Task ID
        
        Returns:
            True if removed, False if not found
        """
        if task_id in self._entries:
            del self._entries[task_id]
            logger.info(f"Removed task {task_id} from DLQ")
            return True
        return False
    
    def retry_task(self, task_id: str) -> Optional[DLQEntry]:
        """
        Manually retry a DLQ task.
        
        Args:
            task_id: Task ID
        
        Returns:
            DLQ entry if exists
        """
        entry = self.get(task_id)
        if not entry:
            return None
        
        logger.info(f"Manually retrying DLQ task {task_id}")
        
        # In production: re-enqueue task
        # from app.queue.celery_app import celery_app
        # celery_app.send_task(
        #     entry.task_name,
        #     args=entry.args,
        #     kwargs=entry.kwargs
        # )
        
        # Remove from DLQ
        self.remove(task_id)
        
        return entry
    
    def _trigger_alert(self, entry: DLQEntry):
        """Trigger alert for DLQ entry"""
        # In production: send to monitoring system
        # For now, just log
        logger.critical(
            f"DLQ ALERT: Task {entry.task_name} permanently failed",
            extra={
                "task_id": entry.task_id,
                "error": entry.error_message,
                "retry_count": entry.retry_count
            }
        )


# Global instances
retry_strategy = RetryStrategy()
dlq = DeadLetterQueue()


# Circuit breaker for repeated failures
class CircuitBreaker:
    """
    Circuit breaker to stop retrying when repeated failures occur.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 300,  # 5 minutes
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        
        logger.info(f"CircuitBreaker initialized (threshold={failure_threshold})")
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function args
            **kwargs: Function kwargs
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            # Check if timeout has elapsed
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half-open"
                logger.info("Circuit breaker half-open, allowing one attempt")
            else:
                raise Exception("Circuit breaker is OPEN, blocking calls")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            logger.info("Circuit breaker closed after successful call")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(
                f"Circuit breaker OPENED after {self.failure_count} failures",
                extra={"last_failure": self.last_failure_time.isoformat()}
            )
