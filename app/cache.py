"""
 ============================================================================
 Redis Cache Management
 ============================================================================
 Description: Redis integration for caching GIS query results
 Key structure: gis_cache:lat:lng with 48-hour TTL
 Optimized for sub-50ms response times on cached queries
 ============================================================================
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Async Redis cache manager for GIS query results.
    Implements caching with TTL and key-based retrieval.
    """
    
    client: Optional[redis.Redis] = None
    
    @classmethod
    async def connect(cls) -> redis.Redis:
        """
        Initialize Redis connection.
        
        Returns:
            redis.Redis: Redis client instance
        """
        if cls.client is None:
            try:
                cls.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,  # Reduced timeout to fail faster
                    protocol=2  # Use RESP2 protocol for compatibility with Redis 3.2.100
                )
                # Test connection with timeout
                import asyncio
                try:
                    await asyncio.wait_for(cls.client.ping(), timeout=2.0)
                    logger.info("Redis connection established successfully")
                except asyncio.TimeoutError:
                    logger.warning("Redis connection timeout - cache will be disabled")
                    cls.client = None
                except Exception as ping_error:
                    logger.warning(f"Redis ping failed: {ping_error} - cache will be disabled")
                    cls.client = None
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e} - cache will be disabled")
                # Cache is optional, log warning but don't fail
                cls.client = None
        return cls.client
    
    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls.client:
            await cls.client.close()
            cls.client = None
            logger.info("Redis connection closed")
    
    @classmethod
    def _make_key(cls, lat: float, lng: float, endpoint: str = "") -> str:
        """
        Generate cache key from coordinates and endpoint.
        
        Args:
            lat: Latitude
            lng: Longitude
            endpoint: Optional endpoint identifier for namespacing
            
        Returns:
            Cache key string
        """
        # Round coordinates to 6 decimal places (~11cm precision)
        lat_rounded = round(lat, 6)
        lng_rounded = round(lng, 6)
        
        if endpoint:
            return f"gis_cache:{endpoint}:{lat_rounded}:{lng_rounded}"
        return f"gis_cache:{lat_rounded}:{lng_rounded}"
    
    @classmethod
    async def get(cls, lat: float, lng: float, endpoint: str = "") -> Optional[dict]:
        """
        Retrieve cached result for given coordinates.
        
        Args:
            lat: Latitude
            lng: Longitude
            endpoint: Optional endpoint identifier
            
        Returns:
            Cached data as dict, or None if not found
        """
        if cls.client is None:
            return None
        
        try:
            key = cls._make_key(lat, lng, endpoint)
            cached_data = await cls.client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    async def get_key(cls, key: str) -> Optional[dict]:
        """
        Retrieve cached result for a given key string.
        
        Args:
            key: Cache key string
            
        Returns:
            Cached data as dict, or None if not found
        """
        if cls.client is None:
            return None
        
        try:
            cached_data = await cls.client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    async def set(cls, lat: float, lng: float, data: dict, endpoint: str = "") -> bool:
        """
        Cache result for given coordinates with TTL.
        
        Args:
            lat: Latitude
            lng: Longitude
            data: Data to cache (must be JSON serializable)
            endpoint: Optional endpoint identifier
            
        Returns:
            True if successful, False otherwise
        """
        if cls.client is None:
            return False
        
        try:
            key = cls._make_key(lat, lng, endpoint)
            serialized_data = json.dumps(data)
            
            await cls.client.setex(
                key,
                settings.CACHE_TTL_SECONDS,
                serialized_data
            )
            
            logger.debug(f"Cached data for key: {key} (TTL: {settings.CACHE_TTL_SECONDS}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    async def set_key(cls, key: str, data: dict, ttl: int = None) -> bool:
        """
        Cache result for a given key string with TTL.
        
        Args:
            key: Cache key string
            data: Data to cache (must be JSON serializable)
            ttl: Time to live in seconds (defaults to CACHE_TTL_SECONDS)
            
        Returns:
            True if successful, False otherwise
        """
        if cls.client is None:
            return False
        
        try:
            serialized_data = json.dumps(data)
            cache_ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
            
            await cls.client.setex(
                key,
                cache_ttl,
                serialized_data
            )
            
            logger.debug(f"Cached data for key: {key} (TTL: {cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    async def delete(cls, lat: float, lng: float, endpoint: str = "") -> bool:
        """
        Delete cached result for given coordinates.
        
        Args:
            lat: Latitude
            lng: Longitude
            endpoint: Optional endpoint identifier
            
        Returns:
            True if successful, False otherwise
        """
        if cls.client is None:
            return False
        
        try:
            key = cls._make_key(lat, lng, endpoint)
            await cls.client.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "gis_cache:*")
            
        Returns:
            Number of keys deleted
        """
        if cls.client is None:
            return 0
        
        try:
            keys = []
            async for key in cls.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await cls.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache keys matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0


# Dependency for FastAPI routes
async def get_cache():
    """
    Dependency injection for cache access.
    Ensures Redis connection is initialized.
    """
    await CacheManager.connect()
    return CacheManager
