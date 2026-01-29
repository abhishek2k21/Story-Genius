"""
Tests for Distributed Locking in Scheduler
"""
import pytest
import threading
import time
from datetime import datetime, timedelta

from app.scheduling.lock_manager import lock_manager
from app.scheduling.models import (
    ScheduledJob, JobType, ScheduleType, ScheduleStatus, Priority,
    RecurrenceRule, Frequency
)
from app.scheduling.executor import schedule_executor

def test_lock_manager_basic():
    """Test basic lock acquisition and release"""
    key = "test:lock:1"
    owner = "test_owner"
    
    # Acquire lock
    assert lock_manager.acquire_lock(key, owner, timeout=1.0)
    
    # Should be locked
    assert lock_manager.is_locked(key)
    assert lock_manager.get_lock_owner(key) == owner
    
    # Release lock
    assert lock_manager.release_lock(key, owner)
    
    # Should be unlocked
    assert not lock_manager.is_locked(key)

def test_lock_manager_concurrent():
    """Test concurrent lock acquisition"""
    key = "test:lock:2"
    owner1 = "owner_1"
    owner2 = "owner_2"
    
    # Owner 1 acquires lock
    assert lock_manager.acquire_lock(key, owner1, timeout=0.5)
    
    # Owner 2 should fail to acquire (timeout quickly)
    assert not lock_manager.acquire_lock(key, owner2, timeout=0.1)
    
    # Owner 1 releases
    lock_manager.release_lock(key, owner1)
    
    # Owner 2 should now succeed
    assert lock_manager.acquire_lock(key, owner2, timeout=0.5)
    lock_manager.release_lock(key, owner2)

def test_lock_expiry():
    """Test lock auto-expiry"""
    key = "test:lock:3"
    owner = "test_owner"
    
    # Acquire with 1 second TTL
    assert lock_manager.acquire_lock(key, owner, timeout=0.5, ttl=1.0)
    assert lock_manager.is_locked(key)
    
    # Wait for expiry
    time.sleep(1.5)
    
    # Should be expired and cleaned up
    assert not lock_manager.is_locked(key)

def test_concurrent_schedule_execution():
    """Test that concurrent execution is prevented"""
    schedule = ScheduledJob(
        schedule_id="test_schedule_1",
        user_id="test_user",
        name="Test Schedule",
        job_type=JobType.VIDEO_GENERATION,
        job_config={"test": "data"},
        schedule_type=ScheduleType.RECURRING,
        recurrence_rule=RecurrenceRule(frequency=Frequency.DAILY),
        next_run_at=datetime.utcnow()
    )
    
    schedule_executor.register_schedule(schedule)
    
    results = []
    
    def execute():
        execution = schedule_executor.execute_schedule(schedule)
        results.append(execution.status.value)
    
    threads = []
    for i in range(3):
        thread = threading.Thread(target=execute)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # At least one should complete, others skipped
    assert "completed" in results
    assert "skipped" in results
    
    print(f"Execution results: {results}")
