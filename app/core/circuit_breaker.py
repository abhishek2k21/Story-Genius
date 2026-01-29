"""
Circuit breaker pattern implementation for resilient service calls.
"""
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    Prevents cascading failures by failing fast when a service is down.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    
    Transitions:
    - CLOSED → OPEN: After failure_threshold consecutive failures
    - OPEN → HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN → CLOSED: After success_threshold consecutive successes
    - HALF_OPEN → OPEN: If any request fails
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again (OPEN → HALF_OPEN)
            success_threshold: Number of successes needed to close circuit
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        
        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s"
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        # Check if we should attempt recovery
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"CircuitBreaker '{self.name}': OPEN → HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self.recovery_timeout}s."
                )
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Success - update state
            self._on_success()
            
            return result
        
        except Exception as e:
            # Failure - update state
            self._on_failure()
            raise
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.success_threshold:
                # Recovered - close circuit
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info(f"CircuitBreaker '{self.name}': HALF_OPEN → CLOSED (recovered)")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery - reopen circuit
            self.state = CircuitState.OPEN
            self.failure_count = 0
            logger.warning(f"CircuitBreaker '{self.name}': HALF_OPEN → OPEN (recovery failed)")
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                # Too many failures - open circuit
                self.state = CircuitState.OPEN
                logger.error(
                    f"CircuitBreaker '{self.name}': CLOSED → OPEN "
                    f"({self.failure_count} failures)"
                )
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"CircuitBreaker '{self.name}' manually reset to CLOSED")
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 2,
    name: Optional[str] = None
):
    """
    Decorator for circuit breaker pattern.
    
    Usage:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def call_external_api():
            # Your code here
            pass
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying again
        success_threshold: Number of successes needed to close circuit
        name: Name for logging (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            name=breaker_name
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Expose breaker for testing/monitoring
        wrapper.circuit_breaker = breaker
        
        return wrapper
    
    return decorator


# Example usage:
if __name__ == "__main__":
    @circuit_breaker(failure_threshold=3, recovery_timeout=5)
    def flaky_service():
        """Simulated flaky external service."""
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service unavailable")
        return "Success"
    
    # Test circuit breaker
    for i in range(10):
        try:
            result = flaky_service()
            print(f"Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"Call {i+1}: Circuit breaker OPEN - {e}")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
        
        time.sleep(1)
