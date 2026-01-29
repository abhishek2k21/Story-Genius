"""
LLM Cache System
Caches LLM responses to reduce API calls and costs.
"""
import hashlib
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: str
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry


class LLMCache:
    """
    In-memory LLM response cache.
    In production, use Redis for distributed caching.
    """
    
    DEFAULT_TTL = 86400  # 24 hours
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
    
    def generate_key(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            model: Model name
            prompt: Prompt text
            temperature: Temperature setting
            top_p: Top-p setting
            **kwargs: Additional parameters
            
        Returns:
            Cache key (hash)
        """
        # Create deterministic key
        key_data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs
        }
        
        # Sort for consistency
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Hash to fixed-length key
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[str]:
        """
        Get cached response.
        
        Args:
            key: Cache key
            
        Returns:
            Cached response or None
        """
        entry = self._cache.get(key)
        
        if not entry:
            self._misses += 1
            logger.debug(f"Cache MISS: {key[:16]}...")
            return None
        
        # Check expiration
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache EXPIRED: {key[:16]}...")
            return None
        
        # Update hit count
        entry.hit_count += 1
        self._hits += 1
        
        logger.debug(
            f"Cache HIT: {key[:16]}... (hit_count: {entry.hit_count})",
            extra={"cache_key": key, "hit_count": entry.hit_count}
        )
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ):
        """
        Cache a response.
        
        Args:
            key: Cache key
            value: Response to cache
            ttl: Time-to-live in seconds (default: 24 hours)
        """
        ttl = ttl or self.DEFAULT_TTL
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl
        )
        
        self._cache[key] = entry
        
        logger.debug(
            f"Cache SET: {key[:16]}... (ttl: {ttl}s)",
            extra={"cache_key": key, "ttl": ttl}
        )
    
    def delete(self, key: str):
        """Delete cache entry"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache DELETE: {key[:16]}...")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"Cache cleared ({count} entries)")
    
    def cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }


# Global cache instance
llm_cache = LLMCache()
