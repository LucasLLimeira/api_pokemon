import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: dict | list
    expires_at: float


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    async def get(self, key: str) -> dict | list | None:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    async def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl_seconds)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
