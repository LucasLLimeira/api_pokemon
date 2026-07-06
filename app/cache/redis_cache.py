import json
import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def get(self, key: str) -> dict | list | None:
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.exception("redis_get_failed")
            return None

    async def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        try:
            await self._redis.set(key, json.dumps(value), ex=ttl_seconds)
        except Exception:
            logger.exception("redis_set_failed")

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception:
            logger.exception("redis_delete_failed")
