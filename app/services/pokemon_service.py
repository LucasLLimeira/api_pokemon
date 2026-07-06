import asyncio
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cache.memory import MemoryCache
from app.cache.redis_cache import RedisCache
from app.config import get_settings
from app.core.exceptions import PokemonAlreadyExistsError, PokemonNotFoundError
from app.db.models import PokemonModel, TypeModel
from app.models.pagination import PokemonListResponse
from app.models.pokemon import (
    PokemonCreate,
    PokemonResponse,
    PokemonSprites,
    PokemonUpdate,
)
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

    @staticmethod
    def _pokemon_model_to_schema(model: PokemonModel) -> PokemonResponse:
        return PokemonResponse(
            name=model.name,
            id=model.id,
            height=model.height,
            weight=model.weight,
            types=[item.name for item in model.types],
            sprites=PokemonSprites(
                front_default=model.front_default,
                back_default=model.back_default,
            ),
        )

    @staticmethod
    def _normalize_type_names(type_names: list[str]) -> list[str]:
        return sorted({item.strip().lower() for item in type_names if item.strip()})

    async def _cache_pokemon(self, pokemon: PokemonResponse) -> None:
        payload = pokemon.model_dump()
        ttl = self._settings.pokemon_ttl_seconds
        await self._set_cached(f"pokemon:{pokemon.id}", payload, ttl)
        await self._set_cached(f"pokemon:{pokemon.name}", payload, ttl)

    async def _invalidate_pokemon_cache(self, pokemon_id: int, *names: str | None) -> None:
        keys = {f"pokemon:{pokemon_id}"}
        keys.update(f"pokemon:{name}" for name in names if name)
        for key in keys:
            await self._memory_cache.delete(key)
            if self._redis_cache:
                await self._redis_cache.delete(key)

    async def _get_local_pokemon(
        self, db_session: AsyncSession, identifier: int | str
    ) -> PokemonModel | None:
        stmt = select(PokemonModel).options(selectinload(PokemonModel.types))
        if isinstance(identifier, int) or str(identifier).isdigit():
            stmt = stmt.where(PokemonModel.id == int(identifier))
        else:
            stmt = stmt.where(PokemonModel.name == str(identifier).strip().lower())

        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _resolve_types(
        self, db_session: AsyncSession, type_names: list[str]
    ) -> list[TypeModel]:
        normalized_names = self._normalize_type_names(type_names)
        if not normalized_names:
            return []

        result = await db_session.execute(
            select(TypeModel).where(TypeModel.name.in_(normalized_names))
        )
        existing_types = {item.name: item for item in result.scalars().all()}
        resolved_types: list[TypeModel] = []

        for type_name in normalized_names:
            type_model = existing_types.get(type_name)
            if type_model is None:
                type_model = TypeModel(name=type_name)
                db_session.add(type_model)
            resolved_types.append(type_model)

        await db_session.flush()
        return resolved_types

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

    async def get_pokemon(
        self, identifier: int | str, db_session: AsyncSession | None = None
    ) -> PokemonResponse:
        key = f"pokemon:{identifier}"
        cached = await self._get_cached(key)
        if cached is not None:
            return PokemonResponse.model_validate(cached)

        if db_session is not None:
            local_pokemon = await self._get_local_pokemon(db_session, identifier)
            if local_pokemon is not None:
                pokemon = self._pokemon_model_to_schema(local_pokemon)
                await self._cache_pokemon(pokemon)
                return pokemon

        payload = await self._client.get_pokemon(identifier)
        pokemon = self._pokemon_to_schema(payload)
        await self._cache_pokemon(pokemon)
        return pokemon

    async def get_by_name(
        self, name: str, db_session: AsyncSession | None = None
    ) -> PokemonResponse:
        return await self.get_pokemon(name, db_session=db_session)

    async def create_pokemon(
        self, payload: PokemonCreate, db_session: AsyncSession
    ) -> PokemonResponse:
        normalized_name = payload.name.strip().lower()
        existing = await db_session.execute(
            select(PokemonModel).where(PokemonModel.name == normalized_name)
        )
        if existing.scalar_one_or_none() is not None:
            raise PokemonAlreadyExistsError()

        pokemon = PokemonModel(
            name=normalized_name,
            height=payload.height,
            weight=payload.weight,
            front_default=payload.sprites.front_default,
            back_default=payload.sprites.back_default,
        )
        pokemon.types = await self._resolve_types(db_session, payload.types)
        db_session.add(pokemon)

        try:
            await db_session.commit()
        except IntegrityError as exc:
            await db_session.rollback()
            raise PokemonAlreadyExistsError() from exc

        stored_pokemon = await self._get_local_pokemon(db_session, pokemon.id)
        if stored_pokemon is None:
            raise PokemonNotFoundError()

        response = self._pokemon_model_to_schema(stored_pokemon)
        await self._cache_pokemon(response)
        return response

    async def update_pokemon(
        self, pokemon_id: int, payload: PokemonUpdate, db_session: AsyncSession
    ) -> PokemonResponse:
        pokemon = await self._get_local_pokemon(db_session, pokemon_id)
        if pokemon is None:
            raise PokemonNotFoundError()

        previous_name = pokemon.name
        if payload.name is not None:
            pokemon.name = payload.name.strip().lower()
        if payload.height is not None:
            pokemon.height = payload.height
        if payload.weight is not None:
            pokemon.weight = payload.weight
        if payload.sprites is not None:
            pokemon.front_default = payload.sprites.front_default
            pokemon.back_default = payload.sprites.back_default
        if payload.types is not None:
            pokemon.types = await self._resolve_types(db_session, payload.types)

        try:
            await db_session.commit()
        except IntegrityError as exc:
            await db_session.rollback()
            raise PokemonAlreadyExistsError() from exc

        updated_pokemon = await self._get_local_pokemon(db_session, pokemon.id)
        if updated_pokemon is None:
            raise PokemonNotFoundError()

        response = self._pokemon_model_to_schema(updated_pokemon)
        await self._invalidate_pokemon_cache(response.id, previous_name, response.name)
        await self._cache_pokemon(response)
        return response

    async def delete_pokemon(self, pokemon_id: int, db_session: AsyncSession) -> None:
        pokemon = await self._get_local_pokemon(db_session, pokemon_id)
        if pokemon is None:
            raise PokemonNotFoundError()

        pokemon_name = pokemon.name
        await db_session.delete(pokemon)
        await db_session.commit()
        await self._invalidate_pokemon_cache(pokemon_id, pokemon_name)

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

    async def list_local_pokemons(
        self, page: int, size: int, db_session: AsyncSession
    ) -> PokemonListResponse:
        total = int((await db_session.scalar(select(func.count()).select_from(PokemonModel))) or 0)
        stmt = (
            select(PokemonModel)
            .options(selectinload(PokemonModel.types))
            .order_by(PokemonModel.id)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db_session.execute(stmt)
        data = [self._pokemon_model_to_schema(item) for item in result.scalars().all()]

        next_page = page + 1 if (page * size) < total else None
        prev_page = page - 1 if page > 1 else None
        return PokemonListResponse(
            data=data,
            pagination={
                "total": total,
                "page": page,
                "size": size,
                "next": f"/pokemons/local?page={next_page}&size={size}" if next_page else None,
                "previous": f"/pokemons/local?page={prev_page}&size={size}" if prev_page else None,
            },
        )
