"""
Idempotency Key System
Ensures exactly-once processing of batch operations.
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IdempotencyRecord:
    """Idempotency record"""
    key: str
    request_data: Dict[str, Any]
    response: Any
    created_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "request_data": self.request_data,
            "response": self.response,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }
    
    def is_expired(self) -> bool:
        """Check if record has expired"""
        return datetime.utcnow() > self.expires_at


class IdempotencyManager:
    """
    Manages idempotency keys for exactly-once processing.
    """
    
    # Default TTL: 24 hours
    DEFAULT_TTL_HOURS = 24
    
    def __init__(self, ttl_hours: int = DEFAULT_TTL_HOURS):
        self.ttl_hours = ttl_hours
        # In-memory storage (in production, use Redis/database)
        self._records: Dict[str, IdempotencyRecord] = {}
        logger.info(f"IdempotencyManager initialized (TTL={ttl_hours}h)")
    
    def generate_key(
        self,
        batch_id: str,
        item_id: str,
        operation: str,
        extra_data: Optional[Dict] = None
    ) -> str:
        """
        Generate idempotency key.
        
        Args:
            batch_id: Batch ID
            item_id: Item ID
            operation: Operation name
            extra_data: Optional extra data for uniqueness
        
        Returns:
            Idempotency key (SHA256 hash)
        """
        # Construct unique identifier
        data = {
            "batch_id": batch_id,
            "item_id": item_id,
            "operation": operation
        }
        
        if extra_data:
            data["extra"] = extra_data
        
        # Generate hash
        data_str = json.dumps(data, sort_keys=True)
        key = hashlib.sha256(data_str.encode()).hexdigest()
        
        logger.debug(f"Generated idempotency key: {key[:16]}... for {operation}")
        return key
    
    def check_duplicate(self, key: str) -> Optional[Any]:
        """
        Check if request is duplicate.
        
        Args:
            key: Idempotency key
        
        Returns:
            Cached response if duplicate, None otherwise
        """
        record = self._records.get(key)
        
        if not record:
            logger.debug(f"Key {key[:16]}... not found (first request)")
            return None
        
        # Check if expired
        if record.is_expired():
            logger.debug(f"Key {key[:16]}... expired, removing")
            del self._records[key]
            return None
        
        # Duplicate request!
        logger.info(
            f"Duplicate request detected: {key[:16]}... "
            f"(original: {record.created_at.isoformat()})"
        )
        return record.response
    
    def store_result(
        self,
        key: str,
        request_data: Dict[str, Any],
        response: Any
    ) -> IdempotencyRecord:
        """
        Store operation result.
        
        Args:
            key: Idempotency key
            request_data: Original request data
            response: Operation response
        
        Returns:
            Created record
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.ttl_hours)
        
        record = IdempotencyRecord(
            key=key,
            request_data=request_data,
            response=response,
            created_at=now,
            expires_at=expires_at
        )
        
        self._records[key] = record
        
        logger.debug(
            f"Stored result for key {key[:16]}... "
            f"(expires: {expires_at.isoformat()})"
        )
        
        return record
    
    def cleanup_expired(self) -> int:
        """
        Remove expired records.
        
        Returns:
            Number of records removed
        """
        expired_keys = [
            key for key, record in self._records.items()
            if record.is_expired()
        ]
        
        for key in expired_keys:
            del self._records[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired idempotency records")
        
        return len(expired_keys)
    
    def get_record(self, key: str) -> Optional[IdempotencyRecord]:
        """Get idempotency record by key"""
        return self._records.get(key)
    
    def delete_record(self, key: str) -> bool:
        """
        Delete idempotency record.
        
        Args:
            key: Idempotency key
        
        Returns:
            True if deleted, False if not found
        """
        if key in self._records:
            del self._records[key]
            logger.debug(f"Deleted idempotency record: {key[:16]}...")
            return True
        return False


# Decorator for idempotent operations
def idempotent_operation(
    idempotency_manager: IdempotencyManager,
    batch_id: str,
    item_id: str,
    operation: str
):
    """
    Decorator to make operations idempotent.
    
    Usage:
        @idempotent_operation(manager, "batch_123", "item_1", "process")
        def process_item(data):
            # Processing logic
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate idempotency key
            key = idempotency_manager.generate_key(
                batch_id=batch_id,
                item_id=item_id,
                operation=operation
            )
            
            # Check for duplicate
            cached_response = idempotency_manager.check_duplicate(key)
            if cached_response is not None:
                logger.info(f"Returning cached response for {operation}")
                return cached_response
            
            # Execute operation
            response = func(*args, **kwargs)
            
            # Store result
            request_data = {
                "args": args,
                "kwargs": kwargs
            }
            idempotency_manager.store_result(key, request_data, response)
            
            return response
        
        return wrapper
    return decorator


# Global instance
idempotency_manager = IdempotencyManager()
