import asyncio
from typing import Any

from redis.asyncio import Redis

from app.cache.memory import MemoryCache
from app.cache.redis_cache import RedisCache
from app.config import get_settings
from app.models.pagination import PokemonListResponse
from app.models.pokemon import PokemonResponse, PokemonSprites
from app.services.pokeapi_client import PokeAPIClient


class PokemonService:
    def __init__(self, redis_client: Redis | None = None) -> None:
        self._settings = get_settings()
        self._client = PokeAPIClient()
        self._memory_cache = MemoryCache()
        self._redis_cache = RedisCache(redis_client) if redis_client else None

    @staticmethod
    def _pokemon_to_schema(data: dict[str, Any]) -> PokemonResponse:
        return PokemonResponse(
            name=data["name"],
            id=data["id"],
            height=data["height"],
            weight=data["weight"],
            types=[item["type"]["name"] for item in data.get("types", [])],
            sprites=PokemonSprites(
                front_default=data.get("sprites", {}).get("front_default"),
                back_default=data.get("sprites", {}).get("back_default"),
            ),
        )

    async def _get_cached(self, key: str) -> dict | list | None:
        cached = await self._memory_cache.get(key)
        if cached is not None:
            return cached
        if self._redis_cache:
            cached = await self._redis_cache.get(key)
            if cached is not None:
                await self._memory_cache.set(key, cached, self._settings.cache_ttl_seconds)
                return cached
        return None

    async def _set_cached(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        await self._memory_cache.set(key, value, ttl_seconds)
        if self._redis_cache:
            await self._redis_cache.set(key, value, ttl_seconds)

    async def get_pokemon(self, identifier: int | str) -> PokemonResponse:
        key = f"pokemon:{identifier}"
        cached = await self._get_cached(key)
        if cached is not None:
            return PokemonResponse.model_validate(cached)

        payload = await self._client.get_pokemon(identifier)
        pokemon = self._pokemon_to_schema(payload)
        await self._set_cached(key, pokemon.model_dump(), self._settings.pokemon_ttl_seconds)
        return pokemon

    async def list_pokemons(self, page: int, size: int) -> PokemonListResponse:
        key = f"pokemon:list:{page}:{size}"
        cached = await self._get_cached(key)
        if cached is not None:
            return PokemonListResponse.model_validate(cached)

        list_payload = await self._client.list_pokemons(page=page, size=size)
        urls = [item["url"] for item in list_payload.get("results", [])]

        async def fetch_by_url(url: str) -> dict:
            return await self._client._request(url.replace(self._settings.pokeapi_base_url, ""))

        detailed_payloads = await asyncio.gather(*[fetch_by_url(url) for url in urls])
        data = [self._pokemon_to_schema(item) for item in detailed_payloads]

        total = int(list_payload.get("count", 0))
        next_page = page + 1 if (page * size) < total else None
        prev_page = page - 1 if page > 1 else None

        response = PokemonListResponse(
            data=data,
            pagination={
                "total": total,
                "page": page,
                "size": size,
                "next": f"/pokemons?page={next_page}&size={size}" if next_page else None,
                "previous": f"/pokemons?page={prev_page}&size={size}" if prev_page else None,
            },
        )
        await self._set_cached(key, response.model_dump(), self._settings.list_ttl_seconds)
        return response

    async def get_by_name(self, name: str) -> PokemonResponse:
        return await self.get_pokemon(name)

    async def list_by_type(self, pokemon_type: str, page: int, size: int) -> PokemonListResponse:
        key = f"pokemon:type:{pokemon_type}:{page}:{size}"
        cached = await self._get_cached(key)
        if cached is not None:
            return PokemonListResponse.model_validate(cached)

        type_payload = await self._client.get_type(pokemon_type)
        pokemon_entries = [item["pokemon"] for item in type_payload.get("pokemon", [])]
        total = len(pokemon_entries)

        start = (page - 1) * size
        end = start + size
        selected_entries = pokemon_entries[start:end]

        detailed_payloads = await asyncio.gather(
            *[self._client.get_pokemon(item["name"]) for item in selected_entries]
        )
        data = [self._pokemon_to_schema(item) for item in detailed_payloads]

        next_page = page + 1 if end < total else None
        prev_page = page - 1 if page > 1 else None
        next_link = (
            f"/pokemons/type/{pokemon_type}?page={next_page}&size={size}" if next_page else None
        )
        previous_link = (
            f"/pokemons/type/{pokemon_type}?page={prev_page}&size={size}" if prev_page else None
        )

        response = PokemonListResponse(
            data=data,
            pagination={
                "total": total,
                "page": page,
                "size": size,
                "next": next_link,
                "previous": previous_link,
            },
        )

        await self._set_cached(key, response.model_dump(), self._settings.type_ttl_seconds)
        return response
