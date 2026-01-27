"""
Metrics Collection System
Counters, gauges, histograms, and timers for monitoring.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import time
import threading


@dataclass
class MetricValue:
    """A metric value with labels"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


class Counter:
    """Cumulative counter metric"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, value: float = 1, **labels):
        """Increment counter"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] += value
    
    def get(self, **labels) -> float:
        """Get counter value"""
        key = self._labels_key(labels)
        return self._values.get(key, 0)
    
    def _labels_key(self, labels: Dict) -> str:
        return str(sorted(labels.items()))
    
    def get_all(self) -> List[MetricValue]:
        """Get all counter values"""
        return [
            MetricValue(self.name, v, self._parse_key(k))
            for k, v in self._values.items()
        ]
    
    def _parse_key(self, key: str) -> Dict:
        if key == "[]":
            return {}
        try:
            return dict(eval(key))
        except:
            return {}


class Gauge:
    """Current value metric"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def set(self, value: float, **labels):
        """Set gauge value"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] = value
    
    def inc(self, value: float = 1, **labels):
        """Increment gauge"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] += value
    
    def dec(self, value: float = 1, **labels):
        """Decrement gauge"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] -= value
    
    def get(self, **labels) -> float:
        """Get gauge value"""
        key = self._labels_key(labels)
        return self._values.get(key, 0)
    
    def _labels_key(self, labels: Dict) -> str:
        return str(sorted(labels.items()))
    
    def get_all(self) -> List[MetricValue]:
        return [
            MetricValue(self.name, v, self._parse_key(k))
            for k, v in self._values.items()
        ]
    
    def _parse_key(self, key: str) -> Dict:
        if key == "[]":
            return {}
        try:
            return dict(eval(key))
        except:
            return {}


class Histogram:
    """Value distribution metric"""
    
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    
    def __init__(self, name: str, description: str = "", buckets: List[float] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._values: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def observe(self, value: float, **labels):
        """Record an observation"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key].append(value)
    
    def get_summary(self, **labels) -> Dict:
        """Get histogram summary"""
        key = self._labels_key(labels)
        values = self._values.get(key, [])
        
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_vals = sorted(values)
        count = len(sorted_vals)
        
        return {
            "count": count,
            "sum": sum(sorted_vals),
            "avg": sum(sorted_vals) / count,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "p50": self._percentile(sorted_vals, 50),
            "p95": self._percentile(sorted_vals, 95),
            "p99": self._percentile(sorted_vals, 99)
        }
    
    def _percentile(self, sorted_values: List[float], p: int) -> float:
        """Calculate percentile"""
        if not sorted_values:
            return 0
        idx = int(len(sorted_values) * p / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]
    
    def _labels_key(self, labels: Dict) -> str:
        return str(sorted(labels.items()))


class Timer:
    """Duration tracking with context manager"""
    
    def __init__(self, histogram: Histogram, **labels):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.observe(duration, **self.labels)
        return False


# Global metrics registry
class MetricsRegistry:
    """Central registry for all metrics"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._counters = {}
            cls._instance._gauges = {}
            cls._instance._histograms = {}
        return cls._instance
    
    def counter(self, name: str, description: str = "") -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(name, description)
        return self._counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, description)
        return self._gauges[name]
    
    def histogram(self, name: str, description: str = "", buckets: List[float] = None) -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description, buckets)
        return self._histograms[name]
    
    def get_all_metrics(self) -> Dict:
        """Get all metrics as dict"""
        return {
            "counters": {name: c.get_all() for name, c in self._counters.items()},
            "gauges": {name: g.get_all() for name, g in self._gauges.items()},
            "histograms": {name: h.get_summary() for name, h in self._histograms.items()}
        }
    
    def get_snapshot(self) -> Dict:
        """Get simplified snapshot"""
        counters = {}
        for name, c in self._counters.items():
            for mv in c.get_all():
                key = f"{name}"
                if mv.labels:
                    key += f"{mv.labels}"
                counters[key] = mv.value
        
        gauges = {}
        for name, g in self._gauges.items():
            for mv in g.get_all():
                key = f"{name}"
                if mv.labels:
                    key += f"{mv.labels}"
                gauges[key] = mv.value
        
        histograms = {}
        for name, h in self._histograms.items():
            histograms[name] = h.get_summary()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms
        }


# Singleton instance
metrics = MetricsRegistry()


# Pre-defined metrics
API_REQUESTS = metrics.counter("api_requests_total", "Total API requests")
API_DURATION = metrics.histogram("api_request_duration_seconds", "API request duration")
API_IN_PROGRESS = metrics.gauge("api_requests_in_progress", "In-progress requests")

JOBS_CREATED = metrics.counter("jobs_created_total", "Total jobs created")
JOBS_COMPLETED = metrics.counter("jobs_completed_total", "Total jobs completed")
JOBS_IN_PROGRESS = metrics.gauge("jobs_in_progress", "Jobs in progress")
JOB_DURATION = metrics.histogram("job_duration_seconds", "Job duration")

ENGINE_EXECUTIONS = metrics.counter("engine_executions_total", "Engine executions")
ENGINE_DURATION = metrics.histogram("engine_duration_seconds", "Engine duration")

ERRORS_TOTAL = metrics.counter("errors_total", "Total errors")
