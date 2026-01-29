"""
Schedule Executor
Executes scheduled jobs with lock-based concurrency control.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid

from app.scheduling.models import (
    ScheduledJob, ScheduleExecution, ExecutionStatus,
    ScheduleStatus, JobType, create_execution_id
)
from app.scheduling.queue import PriorityQueue
from app.scheduling.lock_manager import lock_manager


class ScheduleExecutor:
    """Execute scheduled jobs with distributed locking"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._schedules: Dict[str, ScheduledJob] = {}
            cls._instance._executions: Dict[str, List[ScheduleExecution]] = {}  # schedule_id -> executions
            cls._instance._queue = PriorityQueue()
            cls._instance._lock = threading.Lock()
            cls._instance._running = False
            cls._instance._thread = None
        return cls._instance
    
    def register_schedule(self, schedule: ScheduledJob) -> None:
        """Register a schedule for execution"""
        with self._lock:
            self._schedules[schedule.schedule_id] = schedule
            self._executions[schedule.schedule_id] = []
    
    def get_due_schedules(self, as_of: datetime = None) -> List[ScheduledJob]:
        """Get all schedules due for execution"""
        if as_of is None:
            as_of = datetime.utcnow()
        
        due = []
        for schedule in self._schedules.values():
            if schedule.status != ScheduleStatus.ACTIVE:
                continue
            if schedule.next_run_at and schedule.next_run_at <= as_of:
                due.append(schedule)
        
        # Sort by priority and time
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        due.sort(key=lambda s: (priority_order.get(s.priority.value, 2), s.next_run_at))
        
        return due
    
    def execute_schedule(self, schedule: ScheduledJob) -> ScheduleExecution:
        """Execute a single schedule with distributed locking"""
        
        # Generate lock key
        lock_key = f"schedule:{schedule.schedule_id}:lock"
        owner_id = f"executor:{threading.current_thread().ident}"
        
        # Try to acquire lock
        if not lock_manager.acquire_lock(lock_key, owner_id, timeout=2.0, ttl=300.0):
            # Lock acquisition failed - another process is executing this
            execution = ScheduleExecution(
                execution_id=create_execution_id(),
                schedule_id=schedule.schedule_id,
                scheduled_for=schedule.next_run_at or datetime.utcnow(),
                started_at=datetime.utcnow(),
                status=ExecutionStatus.SKIPPED,
                error_message="Skipped: Already executing in another process"
            )
            if schedule.schedule_id not in self._executions:
                self._executions[schedule.schedule_id] = []
            self._executions[schedule.schedule_id].append(execution)
            return execution
        
        try:
            execution = ScheduleExecution(
                execution_id=create_execution_id(),
                schedule_id=schedule.schedule_id,
                scheduled_for=schedule.next_run_at or datetime.utcnow(),
                started_at=datetime.utcnow(),
                status=ExecutionStatus.RUNNING
            )
            
            # Add to executions
            if schedule.schedule_id not in self._executions:
                self._executions[schedule.schedule_id] = []
            self._executions[schedule.schedule_id].append(execution)
            
            try:
                # Simulate job creation
                execution.job_id = str(uuid.uuid4())
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.result_summary = {"status": "success"}
            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
            
            # Update schedule
            schedule.last_run_at = datetime.utcnow()
            schedule.run_count += 1
            
            # Check max runs
            if schedule.max_runs and schedule.run_count >= schedule.max_runs:
                schedule.status = ScheduleStatus.COMPLETED
                schedule.next_run_at = None
            elif schedule.recurrence_rule:
                from app.scheduling.recurrence import calculate_next_occurrence
                schedule.next_run_at = calculate_next_occurrence(
                    schedule.recurrence_rule,
                    datetime.utcnow()
                )
            else:
                # One-time schedule
                schedule.status = ScheduleStatus.COMPLETED
                schedule.next_run_at = None
            
            schedule.updated_at = datetime.utcnow()
            
            return execution
        finally:
            # Always release the lock
            lock_manager.release_lock(lock_key, owner_id)
    
    def run_now(self, schedule: ScheduledJob, count_run: bool = False) -> ScheduleExecution:
        """Execute schedule immediately"""
        execution = ScheduleExecution(
            execution_id=create_execution_id(),
            schedule_id=schedule.schedule_id,
            scheduled_for=datetime.utcnow(),
            started_at=datetime.utcnow(),
            status=ExecutionStatus.RUNNING,
            is_manual=True
        )
        
        if schedule.schedule_id not in self._executions:
            self._executions[schedule.schedule_id] = []
        self._executions[schedule.schedule_id].append(execution)
        
        try:
            execution.job_id = str(uuid.uuid4())
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
        
        if count_run:
            schedule.run_count += 1
            if schedule.max_runs and schedule.run_count >= schedule.max_runs:
                schedule.status = ScheduleStatus.COMPLETED
        
        return execution
    
    def handle_missed(self, schedule: ScheduledJob) -> List[ScheduleExecution]:
        """Handle missed executions based on policy"""
        executions = []
        now = datetime.utcnow()
        
        if schedule.missed_policy == MissedPolicy.SKIP:
            # Just update next run
            if schedule.recurrence_rule:
                schedule.next_run_at = calculate_next_occurrence(
                    schedule.recurrence_rule, now
                )
            return executions
        
        elif schedule.missed_policy == MissedPolicy.RUN_LATEST:
            # Execute once for the most recent miss
            execution = self.execute_schedule(schedule)
            executions.append(execution)
        
        elif schedule.missed_policy == MissedPolicy.RUN_ALL:
            # Execute all missed (limited to prevent overload)
            max_catchup = 5
            count = 0
            while schedule.next_run_at and schedule.next_run_at < now and count < max_catchup:
                execution = self.execute_schedule(schedule)
                executions.append(execution)
                count += 1
        
        return executions
    
    def get_executions(self, schedule_id: str, limit: int = 20) -> List[ScheduleExecution]:
        """Get execution history for schedule"""
        executions = self._executions.get(schedule_id, [])
        return sorted(executions, key=lambda e: e.scheduled_for, reverse=True)[:limit]
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledJob]:
        """Get schedule by ID"""
        return self._schedules.get(schedule_id)
    
    def unregister_schedule(self, schedule_id: str) -> None:
        """Remove schedule from executor"""
        with self._lock:
            self._schedules.pop(schedule_id, None)


schedule_executor = ScheduleExecutor()
