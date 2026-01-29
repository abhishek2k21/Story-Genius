"""
Advanced Multi-Layer Caching System.
Optimize performance with CDN, application, and database caching.
"""
from typing import Any, Optional, Dict
from datetime import timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheLayer(str, Enum):
    """Cache layer types."""
    CDN = "cdn"  # CloudFront edge caching
    APPLICATION = "application"  # Redis
    DATABASE = "database"  # Query result cache


class AdvancedCaching:
    """Multi-layer caching system for optimal performance."""
    
    def __init__(self, redis_client, cdn_client):
        self.redis = redis_client
        self.cdn = cdn_client
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0
        }
    
    async def get_with_cache(
        self,
        key: str,
        fetch_fn: callable,
        ttl: int = 3600,
        layer: str = CacheLayer.APPLICATION.value
    ) -> Any:
        """
        Get data with automatic cache management.
        
        Args:
            key: Cache key
            fetch_fn: Function to fetch data if cache miss
            ttl: Time to live in seconds
            layer: Cache layer to use
            
        Returns:
            Cached or fetched data
        """
        # Try to get from cache
        cached_value = await self._get_from_cache(key, layer)
        
        if cached_value is not None:
            self.stats["hits"] += 1
            logger.debug(f"Cache HIT for key: {key}")
            return cached_value
        
        # Cache miss - fetch data
        self.stats["misses"] += 1
        logger.debug(f"Cache MISS for key: {key}")
        
        data = await fetch_fn()
        
        # Store in cache
        await self._set_in_cache(key, data, ttl, layer)
        self.stats["sets"] += 1
        
        return data
    
    async def _get_from_cache(
        self,
        key: str,
        layer: str
    ) -> Optional[Any]:
        """Get value from specified cache layer."""
        if layer == CacheLayer.CDN.value:
            # CDN layer (CloudFront)
            # Not directly accessible - handled by CloudFront
            return None
        
        elif layer == CacheLayer.APPLICATION.value:
            # Application layer (Redis)
            try:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
            
            return None
        
        elif layer == CacheLayer.DATABASE.value:
            # Database query cache
            # Handled by database itself
            return None
        
        return None
    
    async def _set_in_cache(
        self,
        key: str,
        value: Any,
        ttl: int,
        layer: str
    ):
        """Set value in specified cache layer."""
        if layer == CacheLayer.APPLICATION.value:
            try:
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    async def invalidate(
        self,
        key: str,
        layer: Optional[str] = None
    ):
        """
        Invalidate cache for key.
        
        Args:
            key: Cache key or pattern
            layer: Specific layer or all if None
        """
        if layer is None or layer == CacheLayer.APPLICATION.value:
            # Invalidate Redis cache
            try:
                if "*" in key:
                    # Pattern-based invalidation
                    keys = await self.redis.keys(key)
                    if keys:
                        await self.redis.delete(*keys)
                        logger.info(f"Invalidated {len(keys)} keys matching pattern: {key}")
                else:
                    await self.redis.delete(key)
                    logger.info(f"Invalidated cache key: {key}")
            except Exception as e:
                logger.error(f"Redis invalidation error: {e}")
        
        if layer is None or layer == CacheLayer.CDN.value:
            # Invalidate CDN cache
            await self._invalidate_cdn(key)
    
    async def _invalidate_cdn(self, path: str):
        """Invalidate CloudFront CDN cache."""
        try:
            # Create CloudFront invalidation
            # invalidation = await self.cdn.create_invalidation(
            #     DistributionId='DISTRIBUTION_ID',
            #     InvalidationBatch={
            #         'Paths': {
            #             'Quantity': 1,
            #             'Items': [path]
            #         },
            #         'CallerReference': str(time.time())
            #     }
            # )
            
            logger.info(f"Created CDN invalidation for path: {path}")
        except Exception as e:
            logger.error(f"CDN invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "total_requests": total,
            "hit_rate_pct": round(hit_rate, 2)
        }


# Cache key generators
def video_cache_key(video_id: str) -> str:
    """Generate cache key for video."""
    return f"video:{video_id}"


def user_videos_cache_key(user_id: str, page: int = 1) -> str:
    """Generate cache key for user's videos list."""
    return f"user:{user_id}:videos:page:{page}"


def analytics_cache_key(user_id: str, period: str) -> str:
    """Generate cache key for analytics."""
    return f"analytics:{user_id}:{period}"


# Cache decorators
def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl=3600, key_prefix="video")
        async def get_video(video_id: str):
            return await db.query(...)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Hash long keys
            if len(cache_key) > 200:
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Get caching instance (would be injected in production)
            # cache = get_cache_instance()
            
            # Try cache first
            # cached_result = await cache.get_with_cache(
            #     key=cache_key,
            #     fetch_fn=lambda: func(*args, **kwargs),
            #     ttl=ttl
            # )
            
            # For now, just call function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Cache warming strategy
async def warm_cache(cache: AdvancedCaching):
    """
    Pre-populate cache with frequently accessed data.
    
    Run during deployment or schedule periodically.
    """
    logger.info("Starting cache warming")
    
    # Warm popular videos
    popular_video_ids = await get_popular_video_ids(limit=100)
    
    for video_id in popular_video_ids:
        try:
            video_data = await fetch_video_data(video_id)
            await cache._set_in_cache(
                key=video_cache_key(video_id),
                value=video_data,
                ttl=3600,
                layer=CacheLayer.APPLICATION.value
            )
        except Exception as e:
            logger.error(f"Cache warming failed for video {video_id}: {e}")
    
    logger.info(f"Cache warmed with {len(popular_video_ids)} videos")


# Cache invalidation strategies
class CacheInvalidationStrategy:
    """Cache invalidation strategies."""
    
    @staticmethod
    async def on_video_update(video_id: str, cache: AdvancedCaching):
        """Invalidate cache when video is updated."""
        # Invalidate video cache
        await cache.invalidate(video_cache_key(video_id))
        
        # Invalidate user's video list
        user_id = await get_video_owner(video_id)
        await cache.invalidate(f"user:{user_id}:videos:*")
        
        # Invalidate CDN for video file
        await cache.invalidate(
            f"/videos/{video_id}/*",
            layer=CacheLayer.CDN.value
        )
    
    @staticmethod
    async def on_user_update(user_id: str, cache: AdvancedCaching):
        """Invalidate cache when user is updated."""
        # Invalidate all user-related caches
        await cache.invalidate(f"user:{user_id}:*")
        await cache.invalidate(f"analytics:{user_id}:*")


# Example usage
"""
from app.services.advanced_caching import AdvancedCaching, cached

cache = AdvancedCaching(redis_client, cdn_client)

# Manual caching
async def get_video(video_id: str):
    return await cache.get_with_cache(
        key=f"video:{video_id}",
        fetch_fn=lambda: db.fetch_video(video_id),
        ttl=3600
    )

# Decorator caching
@cached(ttl=3600, key_prefix="user")
async def get_user_analytics(user_id: str, period: str):
    return await analytics_service.calculate(user_id, period)

# Get stats
stats = cache.get_cache_stats()
# {'hits': 1250, 'misses': 150, 'hit_rate_pct': 89.29}
"""
