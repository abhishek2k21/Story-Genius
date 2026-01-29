"""
Cache Manager with Redis Sentinel support for High Availability.
"""
import logging
from typing import Optional, Any
from redis.sentinel import Sentinel
from redis.exceptions import RedisError
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager with Sentinel for automatic failover.
    
    Features:
    - Automatic master discovery via Sentinel
    - Failover handling
    - Read from replicas for performance
    - Connection pooling
    """
    
    def __init__(
        self,
        sentinels: list = None,
        master_name: str = "mymaster",
        socket_timeout: float = 0.1,
        password: Optional[str] = None
    ):
        """
        Initialize cache manager with Sentinel.
        
        Args:
            sentinels: List of (host, port) tuples for Sentinel nodes
            master_name: Name of the master in Sentinel config
            socket_timeout: Socket timeout in seconds
            password: Redis password
        """
        if sentinels is None:
            # Default Sentinel endpoints in Kubernetes
            sentinels = [
                ('redis-ha-0.redis-ha', 26379),
                ('redis-ha-1.redis-ha', 26379),
                ('redis-ha-2.redis-ha', 26379)
            ]
        
        self.master_name = master_name
        self.password = password
        
        # Create Sentinel instance
        self.sentinel = Sentinel(
            sentinels,
            socket_timeout=socket_timeout,
            password=password
        )
        
        logger.info(f"CacheManager initialized with Sentinel: {sentinels}")
    
    def get_master(self):
        """Get Redis master connection for writes."""
        try:
            return self.sentinel.master_for(
                self.master_name,
                socket_timeout=0.1,
                password=self.password,
                decode_responses=True
            )
        except RedisError as e:
            logger.error(f"Failed to get Redis master: {e}")
            raise
    
    def get_slave(self):
        """Get Redis slave connection for reads (load distribution)."""
        try:
            return self.sentinel.slave_for(
                self.master_name,
                socket_timeout=0.1,
                password=self.password,
                decode_responses=True
            )
        except RedisError as e:
            logger.error(f"Failed to get Redis slave: {e}")
            # Fallback to master if slave unavailable
            return self.get_master()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (reads from slave).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            slave = self.get_slave()
            value = slave.get(key)
            
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            
            return None
        
        except RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Set value in cache (writes to master).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            master = self.get_master()
            
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            result = master.setex(key, ttl, value)
            return bool(result)
        
        except RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            master = self.get_master()
            result = master.delete(key)
            return bool(result)
        
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            master = self.get_master()
            keys = master.keys(pattern)
            
            if keys:
                return master.delete(*keys)
            
            return 0
        
        except RedisError as e:
            logger.error(f"Cache invalidate error for pattern {pattern}: {e}")
            return 0
    
    def publish(self, channel: str, message: str) -> int:
        """
        Publish message to Pub/Sub channel for distributed cache invalidation.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of subscribers that received the message
        """
        try:
            master = self.get_master()
            return master.publish(channel, message)
        
        except RedisError as e:
            logger.error(f"Cache publish error: {e}")
            return 0
    
    def health_check(self) -> bool:
        """
        Check if cache is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            master = self.get_master()
            return master.ping()
        except:
            return False


# Global cache manager instance
cache_manager = CacheManager()
