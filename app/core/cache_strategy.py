"""
Multi-Level Cache Strategy
Implements L1 (in-process) and L2 (Redis) caching with TTL management.
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl_seconds: int
    max_size: int = 1000  # Max items in L1 cache


# Cache configurations by type
CACHE_CONFIGS = {
    "llm_response": CacheConfig(ttl_seconds=86400),  # 24 hours
    "media": CacheConfig(ttl_seconds=604800),  # 7 days
    "metadata": CacheConfig(ttl_seconds=3600),  # 1 hour
    "user_session": CacheConfig(ttl_seconds=1800),  # 30 minutes
    "api_response": CacheConfig(ttl_seconds=300),  # 5 minutes
}


class L1Cache:
    """In-process memory cache (fast, limited size)"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get from L1 cache"""
        if key in self._cache:
            value, expires_at = self._cache[key]
            
            # Check if expired
            if datetime.utcnow() < expires_at:
                self._hits += 1
                logger.debug(f"L1 cache HIT: {key}")
                return value
            else:
                # Expired, remove
                del self._cache[key]
        
        self._misses += 1
        logger.debug(f"L1 cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set in L1 cache"""
        # Evict oldest if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expires_at)
        logger.debug(f"L1 cache SET: {key} (TTL={ttl_seconds}s)")
    
    def delete(self, key: str):
        """Delete from L1 cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all L1 cache"""
        self._cache.clear()
        logger.info("L1 cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "type": "L1",
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }


class L2Cache:
    """Redis cache (distributed, persistent) - Mock implementation"""
    
    def __init__(self):
        # Mock: In production, use Redis client
        self._redis_mock: Dict[str, tuple[str, datetime]] = {}
        self._hits = 0
        self._misses = 0
        logger.info("L2Cache initialized (mock mode)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get from Redis cache"""
        if key in self._redis_mock:
            value_json, expires_at = self._redis_mock[key]
            
            # Check if expired
            if datetime.utcnow() < expires_at:
                self._hits += 1
                logger.debug(f"L2 cache HIT: {key}")
                return json.loads(value_json)
            else:
                # Expired, remove
                del self._redis_mock[key]
        
        self._misses += 1
        logger.debug(f"L2 cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set in Redis cache"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        value_json = json.dumps(value)
        self._redis_mock[key] = (value_json, expires_at)
        logger.debug(f"L2 cache SET: {key} (TTL={ttl_seconds}s)")
    
    def delete(self, key: str):
        """Delete from Redis cache"""
        if key in self._redis_mock:
            del self._redis_mock[key]
    
    def clear(self):
        """Clear all Redis cache"""
        self._redis_mock.clear()
        logger.info("L2 cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "type": "L2",
            "size": len(self._redis_mock),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }


class CacheStrategy:
    """
    Multi-level cache (L1 + L2).
    
    Read: L1 → L2 → Source
    Write: L1 + L2
    """
    
    def __init__(self):
        self.l1 = L1Cache(max_size=1000)
        self.l2 = L2Cache()
        logger.info("CacheStrategy initialized (L1 + L2)")
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        Get from cache (L1 → L2).
        
        Args:
            cache_type: Type of cache (llm_response, media, etc.)
            key: Cache key
        
        Returns:
            Cached value or None
        """
        cache_key = self._make_key(cache_type, key)
        
        # Try L1 first
        value = self.l1.get(cache_key)
        if value is not None:
            return value
        
        # Try L2
        value = self.l2.get(cache_key)
        if value is not None:
            # Populate L1 for next time
            config = CACHE_CONFIGS.get(cache_type, CACHE_CONFIGS["api_response"])
            self.l1.set(cache_key, value, config.ttl_seconds)
            return value
        
        return None
    
    def set(self, cache_type: str, key: str, value: Any):
        """
        Set in cache (L1 + L2).
        
        Args:
            cache_type: Type of cache
            key: Cache key
            value: Value to cache
        """
        cache_key = self._make_key(cache_type, key)
        config = CACHE_CONFIGS.get(cache_type, CACHE_CONFIGS["api_response"])
        
        # Set in both L1 and L2
        self.l1.set(cache_key, value, config.ttl_seconds)
        self.l2.set(cache_key, value, config.ttl_seconds)
        
        logger.info(f"Cached: {cache_type}:{key} (TTL={config.ttl_seconds}s)")
    
    def delete(self, cache_type: str, key: str):
        """Delete from cache"""
        cache_key = self._make_key(cache_type, key)
        self.l1.delete(cache_key)
        self.l2.delete(cache_key)
    
    def clear(self, cache_type: Optional[str] = None):
        """Clear cache"""
        if cache_type is None:
            self.l1.clear()
            self.l2.clear()
        else:
            # Clear specific type (not implemented in mock)
            logger.warning(f"Clearing specific cache type '{cache_type}' not implemented")
    
    def get_stats(self) -> Dict:
        """Get combined cache statistics"""
        l1_stats = self.l1.get_stats()
        l2_stats = self.l2.get_stats()
        
        total_hits = l1_stats["hits"] + l2_stats["hits"]
        total_misses = l1_stats["misses"] + l2_stats["misses"]
        total = total_hits + total_misses
        
        overall_hit_rate = (total_hits / total * 100) if total > 0 else 0
        
        return {
            "overall_hit_rate": round(overall_hit_rate, 2),
            "total_requests": total,
            "l1": l1_stats,
            "l2": l2_stats
        }
    
    def _make_key(self, cache_type: str, key: str) -> str:
        """Generate cache key"""
        return f"{cache_type}:{key}"


# Decorator for caching function results
def cached(cache_type: str, key_fn=None):
    """
    Decorator to cache function results.
    
    Usage:
        @cached("llm_response", key_fn=lambda prompt: prompt)
        def generate_text(prompt: str):
            return llm.generate(prompt)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                # Default: hash args
                key = hashlib.md5(
                    json.dumps((args, kwargs), sort_keys=True).encode()
                ).hexdigest()
            
            # Try to get from cache
            cached_value = cache_strategy.get(cache_type, key)
            if cached_value is not None:
                logger.info(f"Cache HIT for {func.__name__}")
                return cached_value
            
            # Execute function
            logger.info(f"Cache MISS for {func.__name__}, executing")
            result = func(*args, **kwargs)
            
            # Cache result
            cache_strategy.set(cache_type, key, result)
            
            return result
        
        return wrapper
    return decorator


# Global instance
cache_strategy = CacheStrategy()
