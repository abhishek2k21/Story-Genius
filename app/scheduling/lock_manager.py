"""
Distributed Lock Manager
In-memory locking system to prevent concurrent execution of scheduled jobs.
"""
import threading
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class Lock:
    """Lock information"""
    key: str
    owner_id: str
    acquired_at: datetime
    ttl_seconds: float
    
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        elapsed = (datetime.utcnow() - self.acquired_at).total_seconds()
        return elapsed > self.ttl_seconds


class LockManager:
    """
    Distributed lock manager using in-memory storage.
    In production, this should use Redis or similar distributed store.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._locks: Dict[str, Lock] = {}
                    cls._instance._mutex = threading.RLock()
        return cls._instance
    
    def acquire_lock(
        self,
        key: str,
        owner_id: str,
        timeout: float = 10.0,
        ttl: float = 300.0  # 5 minutes default TTL
    ) -> bool:
        """
        Attempt to acquire a lock.
        
        Args:
            key: Lock identifier (e.g., "schedule:batch_123:lock")
            owner_id: Identifier of the process acquiring the lock
            timeout: How long to wait for lock acquisition (seconds)
            ttl: Lock time-to-live (seconds) - auto-release after this
            
        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            with self._mutex:
                # Clean up expired locks
                self._cleanup_expired_locks()
                
                # Check if lock is available
                if key not in self._locks:
                    # Acquire lock
                    self._locks[key] = Lock(
                        key=key,
                        owner_id=owner_id,
                        acquired_at=datetime.utcnow(),
                        ttl_seconds=ttl
                    )
                    return True
                
                # Check if we already own this lock
                existing_lock = self._locks[key]
                if existing_lock.owner_id == owner_id:
                    # Refresh lock
                    existing_lock.acquired_at = datetime.utcnow()
                    return True
            
            # Wait briefly before retrying
            time.sleep(0.1)
        
        return False
    
    def release_lock(self, key: str, owner_id: str) -> bool:
        """
        Release a lock.
        
        Args:
            key: Lock identifier
            owner_id: Identifier of the process releasing the lock
            
        Returns:
            True if lock released, False if lock not held by owner
        """
        with self._mutex:
            if key not in self._locks:
                return False
            
            lock = self._locks[key]
            if lock.owner_id != owner_id:
                # Can't release someone else's lock
                return False
            
            del self._locks[key]
            return True
    
    def is_locked(self, key: str) -> bool:
        """Check if a lock is currently held"""
        with self._mutex:
            self._cleanup_expired_locks()
            return key in self._locks
    
    def get_lock_owner(self, key: str) -> Optional[str]:
        """Get the owner of a lock"""
        with self._mutex:
            self._cleanup_expired_locks()
            if key in self._locks:
                return self._locks[key].owner_id
            return None
    
    def _cleanup_expired_locks(self):
        """Remove expired locks (internal, must be called with mutex held)"""
        expired_keys = [
            key for key, lock in self._locks.items()
            if lock.is_expired()
        ]
        for key in expired_keys:
            del self._locks[key]
    
    def force_release(self, key: str) -> bool:
        """Force release a lock (admin operation)"""
        with self._mutex:
            if key in self._locks:
                del self._locks[key]
                return True
            return False
    
    def get_all_locks(self) -> Dict[str, Dict]:
        """Get all active locks (for monitoring)"""
        with self._mutex:
            self._cleanup_expired_locks()
            return {
                key: {
                    "owner_id": lock.owner_id,
                    "acquired_at": lock.acquired_at.isoformat(),
                    "ttl_seconds": lock.ttl_seconds,
                    "expires_at": (lock.acquired_at + timedelta(seconds=lock.ttl_seconds)).isoformat()
                }
                for key, lock in self._locks.items()
            }


# Singleton instance
lock_manager = LockManager()
