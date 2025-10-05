"""Redis service for caching."""

import json
import logging
from typing import Any, List, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis caching operations."""

    def __init__(self) -> None:
        """Initialize Redis service."""
        self.client: Optional[redis.Redis] = None
        self.embedding_ttl = 86400  # 24 hours
        self.search_result_ttl = 3600  # 1 hour

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding for text.

        Args:
            text: Text to get embedding for

        Returns:
            Cached embedding or None
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            key = f"embedding:{hash(text)}"
            cached = await self.client.get(key)

            if cached:
                logger.debug(f"Cache hit for embedding: {text[:50]}...")
                return json.loads(cached)

            logger.debug(f"Cache miss for embedding: {text[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")
            return None

    async def set_embedding(self, text: str, embedding: List[float]) -> None:
        """
        Cache embedding for text.

        Args:
            text: Text the embedding is for
            embedding: Embedding vector to cache
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            key = f"embedding:{hash(text)}"
            await self.client.setex(
                key, self.embedding_ttl, json.dumps(embedding)
            )
            logger.debug(f"Cached embedding for: {text[:50]}...")

        except Exception as e:
            logger.error(f"Error caching embedding: {e}")

    async def get_search_result(self, query: str, filters: Optional[dict] = None) -> Optional[dict]:
        """
        Get cached search result.

        Args:
            query: Search query
            filters: Search filters

        Returns:
            Cached search result or None
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            # Create cache key from query and filters
            filter_str = json.dumps(filters, sort_keys=True) if filters else ""
            key = f"search:{hash(query + filter_str)}"

            cached = await self.client.get(key)

            if cached:
                logger.info(f"Cache hit for search: {query[:50]}...")
                return json.loads(cached)

            logger.debug(f"Cache miss for search: {query[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Error getting cached search result: {e}")
            return None

    async def set_search_result(
        self, query: str, result: dict, filters: Optional[dict] = None
    ) -> None:
        """
        Cache search result.

        Args:
            query: Search query
            result: Search result to cache
            filters: Search filters
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            # Create cache key from query and filters
            filter_str = json.dumps(filters, sort_keys=True) if filters else ""
            key = f"search:{hash(query + filter_str)}"

            await self.client.setex(
                key, self.search_result_ttl, json.dumps(result)
            )
            logger.info(f"Cached search result for: {query[:50]}...")

        except Exception as e:
            logger.error(f"Error caching search result: {e}")

    async def invalidate_search_cache(self, pattern: str = "search:*") -> None:
        """
        Invalidate search cache.

        Args:
            pattern: Redis key pattern to invalidate (can be exact key or pattern with *)
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            # If pattern contains *, use scan_iter
            if "*" in pattern:
                keys = []
                async for key in self.client.scan_iter(match=pattern):
                    keys.append(key)

                if keys:
                    await self.client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
            else:
                # Direct key deletion
                result = await self.client.delete(pattern)
                if result:
                    logger.info(f"Invalidated cache entry: {pattern}")

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis."""
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete key from Redis."""
        if not self.client:
            raise RuntimeError("Redis client not connected")

        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")

    async def health_check(self) -> dict:
        """Check Redis health."""
        if not self.client:
            return {"status": "down", "message": "Client not connected"}

        try:
            await self.client.ping()
            info = await self.client.info()

            return {
                "status": "up",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "down", "message": str(e)}


# Global Redis service instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Get global Redis service instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service

