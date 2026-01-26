"""
Automatic Retry Logic with Exponential Backoff
Handles transient failures with intelligent retry strategies.
"""
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import random

from app.core.logging import get_logger

logger = get_logger(__name__)


class FailureType(str, Enum):
    """Classification of failure types"""
    NETWORK_TIMEOUT = "network_timeout"
    API_RATE_LIMIT = "api_rate_limit"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    INVALID_INPUT = "invalid_input"
    AUTHENTICATION_FAILURE = "authentication_failure"
    OUT_OF_MEMORY = "out_of_memory"
    UNKNOWN_ERROR = "unknown_error"


# Failure classification configuration
FAILURE_CONFIG = {
    FailureType.NETWORK_TIMEOUT: {
        "retryable": True,
        "max_retries": 5,
        "base_delay": 1.0,
        "max_delay": 60.0
    },
    FailureType.API_RATE_LIMIT: {
        "retryable": True,
        "max_retries": 5,
        "base_delay": 5.0,
        "max_delay": 300.0
    },
    FailureType.RESOURCE_UNAVAILABLE: {
        "retryable": True,
        "max_retries": 3,
        "base_delay": 2.0,
        "max_delay": 30.0
    },
    FailureType.INVALID_INPUT: {
        "retryable": False,
        "max_retries": 0,
        "base_delay": 0,
        "max_delay": 0
    },
    FailureType.AUTHENTICATION_FAILURE: {
        "retryable": False,
        "max_retries": 0,
        "base_delay": 0,
        "max_delay": 0
    },
    FailureType.OUT_OF_MEMORY: {
        "retryable": True,
        "max_retries": 1,
        "base_delay": 5.0,
        "max_delay": 10.0
    },
    FailureType.UNKNOWN_ERROR: {
        "retryable": True,
        "max_retries": 3,
        "base_delay": 2.0,
        "max_delay": 30.0
    }
}


@dataclass
class RetryAttempt:
    """Record of a single retry attempt"""
    attempt_number: int
    failure_type: FailureType
    error_message: str
    timestamp: datetime
    delay_seconds: float
    
    def to_dict(self):
        return {
            "attempt": self.attempt_number,
            "failure_type": self.failure_type.value,
            "error": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "delay_seconds": self.delay_seconds
        }


@dataclass
class RetryState:
    """Current retry state for a job/stage"""
    job_id: str
    stage_name: str
    attempts: list  # List of RetryAttempt
    max_retries_reached: bool = False
    next_retry_at: Optional[datetime] = None
    
    @property
    def attempt_count(self) -> int:
        return len(self.attempts)
    
    @property
    def last_failure_type(self) -> Optional[FailureType]:
        if self.attempts:
            return self.attempts[-1].failure_type
        return None
    
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "stage_name": self.stage_name,
            "attempt_count": self.attempt_count,
            "attempts": [a.to_dict() for a in self.attempts],
            "max_retries_reached": self.max_retries_reached,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None
        }


def classify_error(error: Exception) -> FailureType:
    """Classify an exception into a failure type"""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Network errors
    if any(kw in error_str for kw in ["timeout", "timed out", "connection"]):
        return FailureType.NETWORK_TIMEOUT
    
    # Rate limiting
    if any(kw in error_str for kw in ["rate limit", "too many requests", "429"]):
        return FailureType.API_RATE_LIMIT
    
    # Resource issues
    if any(kw in error_str for kw in ["unavailable", "not found", "503", "502"]):
        return FailureType.RESOURCE_UNAVAILABLE
    
    # Auth issues
    if any(kw in error_str for kw in ["unauthorized", "forbidden", "401", "403"]):
        return FailureType.AUTHENTICATION_FAILURE
    
    # Memory issues
    if any(kw in error_str for kw in ["memory", "oom", "heap"]):
        return FailureType.OUT_OF_MEMORY
    
    # Input validation
    if any(kw in error_type for kw in ["validation", "value", "type"]):
        return FailureType.INVALID_INPUT
    
    return FailureType.UNKNOWN_ERROR


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """Calculate exponential backoff delay with optional jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def is_retryable(failure_type: FailureType) -> bool:
    """Check if a failure type is retryable"""
    config = FAILURE_CONFIG.get(failure_type, FAILURE_CONFIG[FailureType.UNKNOWN_ERROR])
    return config["retryable"]


def get_max_retries(failure_type: FailureType) -> int:
    """Get maximum retry attempts for a failure type"""
    config = FAILURE_CONFIG.get(failure_type, FAILURE_CONFIG[FailureType.UNKNOWN_ERROR])
    return config["max_retries"]


class RetryStrategy:
    """Manages retry logic for a job or stage"""
    
    def __init__(self, job_id: str, stage_name: str):
        self.state = RetryState(
            job_id=job_id,
            stage_name=stage_name,
            attempts=[]
        )
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if we should retry after this error"""
        failure_type = classify_error(error)
        
        if not is_retryable(failure_type):
            logger.info(f"Error type {failure_type.value} is not retryable")
            return False
        
        max_retries = get_max_retries(failure_type)
        if self.state.attempt_count >= max_retries:
            self.state.max_retries_reached = True
            logger.info(f"Max retries ({max_retries}) reached for {failure_type.value}")
            return False
        
        return True
    
    def record_attempt(self, error: Exception) -> RetryAttempt:
        """Record a retry attempt and calculate next delay"""
        failure_type = classify_error(error)
        config = FAILURE_CONFIG.get(failure_type, FAILURE_CONFIG[FailureType.UNKNOWN_ERROR])
        
        delay = calculate_backoff(
            self.state.attempt_count,
            config["base_delay"],
            config["max_delay"]
        )
        
        attempt = RetryAttempt(
            attempt_number=self.state.attempt_count + 1,
            failure_type=failure_type,
            error_message=str(error),
            timestamp=datetime.now(),
            delay_seconds=delay
        )
        
        self.state.attempts.append(attempt)
        self.state.next_retry_at = datetime.now() + timedelta(seconds=delay)
        
        logger.info(
            f"Retry attempt {attempt.attempt_number} for {self.state.job_id}/{self.state.stage_name}: "
            f"{failure_type.value}, delay {delay:.1f}s"
        )
        
        return attempt
    
    async def wait_for_retry(self):
        """Wait for the calculated backoff period"""
        if self.state.attempts:
            delay = self.state.attempts[-1].delay_seconds
            logger.debug(f"Waiting {delay:.1f}s before retry")
            await asyncio.sleep(delay)


async def retry_with_backoff(
    func: Callable,
    job_id: str,
    stage_name: str,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with automatic retry and exponential backoff
    
    Args:
        func: Async function to execute
        job_id: Job identifier for logging
        stage_name: Stage identifier for logging
        *args, **kwargs: Arguments to pass to func
    
    Returns:
        Result of func if successful
    
    Raises:
        Exception: If all retries exhausted
    """
    strategy = RetryStrategy(job_id, stage_name)
    last_error = None
    
    while True:
        try:
            return await func(*args, **kwargs)
        
        except Exception as e:
            last_error = e
            
            if not strategy.should_retry(e):
                logger.error(f"Not retrying {job_id}/{stage_name}: {e}")
                raise
            
            strategy.record_attempt(e)
            await strategy.wait_for_retry()
    
    # Should not reach here, but just in case
    raise last_error
