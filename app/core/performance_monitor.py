"""
Performance Monitoring
Tracks performance metrics including response times, cache hits, and query duration.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime


class PerformanceMonitor:
    """
    Monitors application performance metrics.
    """
    
    def __init__(self):
        # Response times (ms)
        self._response_times: List[float] = []
        
        # Query durations (ms)
        self._query_durations: List[float] = []
        
        # Cache metrics
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Error counts
        self._errors = defaultdict(int)
        
        logger.info("PerformanceMonitor initialized")
    
    def record_response_time(self, duration_ms: float):
        """Record API response time"""
        self._response_times.append(duration_ms)
        
        # Keep last 1000
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]
    
    def record_query_duration(self, duration_ms: float):
        """Record database query duration"""
        self._query_durations.append(duration_ms)
        
        if len(self._query_durations) > 1000:
            self._query_durations = self._query_durations[-1000:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self._cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self._cache_misses += 1
    
    def record_error(self, error_type: str):
        """Record error"""
        self._errors[error_type] += 1
    
    def get_metrics(self) -> Dict:
        """Get all performance metrics"""
        return {
            "response_times": self._get_percentiles(self._response_times),
            "query_durations": self._get_percentiles(self._query_durations),
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": self._calculate_hit_rate()
            },
            "errors": dict(self._errors),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_percentiles(self, values: List[float]) -> Dict:
        """Calculate percentiles"""
        if not values:
            return {
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "avg": 0,
                "count": 0
            }
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "p50": round(sorted_values[int(count * 0.50)], 2),
            "p95": round(sorted_values[int(count * 0.95)], 2),
            "p99": round(sorted_values[int(count * 0.99)], 2),
            "avg": round(sum(values) / count, 2),
            "count": count
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        
        return round((self._cache_hits / total) * 100, 2)


# Context manager for timing
class Timer:
    """Timer context manager for measuring execution time"""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000
        logger.debug(f"{self.name} took {self.duration_ms:.2f}ms")


# Global instance
performance_monitor = PerformanceMonitor()
