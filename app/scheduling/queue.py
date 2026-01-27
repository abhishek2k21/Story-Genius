"""
Priority Queue
Job queue with priority ordering.
"""
from typing import Dict, List, Optional
from datetime import datetime
import heapq
import threading

from app.scheduling.models import ScheduledJob, Priority


# Priority weights (lower = higher priority)
PRIORITY_WEIGHTS = {
    Priority.URGENT: 0,
    Priority.HIGH: 1,
    Priority.NORMAL: 2,
    Priority.LOW: 3
}


class PriorityQueue:
    """Priority-based job queue"""
    
    def __init__(self):
        self._queue: List[tuple] = []  # (priority, timestamp, schedule_id, schedule)
        self._lock = threading.Lock()
        self._counter = 0
    
    def push(self, schedule: ScheduledJob) -> None:
        """Add schedule to queue"""
        priority_weight = PRIORITY_WEIGHTS.get(schedule.priority, 2)
        
        with self._lock:
            heapq.heappush(
                self._queue,
                (priority_weight, self._counter, schedule.schedule_id, schedule)
            )
            self._counter += 1
    
    def pop(self) -> Optional[ScheduledJob]:
        """Get highest priority schedule"""
        with self._lock:
            if not self._queue:
                return None
            _, _, _, schedule = heapq.heappop(self._queue)
            return schedule
    
    def peek(self) -> Optional[ScheduledJob]:
        """View highest priority without removing"""
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0][3]
    
    def size(self) -> int:
        """Get queue size"""
        return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0
    
    def clear(self) -> None:
        """Clear the queue"""
        with self._lock:
            self._queue = []
    
    def remove(self, schedule_id: str) -> bool:
        """Remove schedule from queue"""
        with self._lock:
            for i, item in enumerate(self._queue):
                if item[2] == schedule_id:
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    return True
        return False
    
    def get_by_priority(self, priority: Priority) -> List[ScheduledJob]:
        """Get all schedules with specific priority"""
        weight = PRIORITY_WEIGHTS.get(priority, 2)
        return [item[3] for item in self._queue if item[0] == weight]


class QueueManager:
    """Manage multiple queues and concurrency"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._main_queue = PriorityQueue()
            cls._instance._running: Dict[str, ScheduledJob] = {}
            cls._instance._max_concurrent = 5
            cls._instance._user_limits: Dict[str, int] = {}  # user_id -> running count
            cls._instance._max_per_user = 3
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def enqueue(self, schedule: ScheduledJob) -> bool:
        """Add schedule to queue"""
        # Check user limit
        user_running = self._user_limits.get(schedule.user_id, 0)
        if user_running >= self._max_per_user:
            return False
        
        self._main_queue.push(schedule)
        return True
    
    def dequeue(self) -> Optional[ScheduledJob]:
        """Get next schedule to execute"""
        if len(self._running) >= self._max_concurrent:
            return None
        
        schedule = self._main_queue.pop()
        if schedule:
            with self._lock:
                self._running[schedule.schedule_id] = schedule
                user_count = self._user_limits.get(schedule.user_id, 0)
                self._user_limits[schedule.user_id] = user_count + 1
        
        return schedule
    
    def complete(self, schedule_id: str) -> None:
        """Mark schedule execution as complete"""
        with self._lock:
            if schedule_id in self._running:
                schedule = self._running.pop(schedule_id)
                user_count = self._user_limits.get(schedule.user_id, 1)
                self._user_limits[schedule.user_id] = max(0, user_count - 1)
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "queued": self._main_queue.size(),
            "running": len(self._running),
            "max_concurrent": self._max_concurrent,
            "by_priority": {
                "urgent": len(self._main_queue.get_by_priority(Priority.URGENT)),
                "high": len(self._main_queue.get_by_priority(Priority.HIGH)),
                "normal": len(self._main_queue.get_by_priority(Priority.NORMAL)),
                "low": len(self._main_queue.get_by_priority(Priority.LOW))
            }
        }


queue_manager = QueueManager()
