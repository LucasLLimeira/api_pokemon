import asyncio

import pytest

from app.cache.memory import MemoryCache


@pytest.mark.asyncio
async def test_memory_cache_set_get() -> None:
    cache = MemoryCache()
    value = {"id": 25}

    await cache.set("pokemon:25", value, ttl_seconds=60)
    cached = await cache.get("pokemon:25")

    assert cached == value


@pytest.mark.asyncio
async def test_memory_cache_ttl_expiration() -> None:
    cache = MemoryCache()
    await cache.set("pokemon:25", {"id": 25}, ttl_seconds=0)

    await asyncio.sleep(0.01)
    cached = await cache.get("pokemon:25")

    assert cached is None
