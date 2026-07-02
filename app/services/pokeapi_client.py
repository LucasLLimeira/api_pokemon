import asyncio

import httpx

from app.config import get_settings
from app.core.exceptions import PokeAPIError, PokemonNotFoundError


class PokeAPIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.pokeapi_base_url.rstrip("/")
        self._timeout = httpx.Timeout(10.0)

    async def _request(self, path: str) -> dict:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url)
                if response.status_code == 404:
                    raise PokemonNotFoundError()
                response.raise_for_status()
                return response.json()
            except PokemonNotFoundError:
                raise
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2**attempt)
        raise PokeAPIError(detail=f"PokeAPI request failed: {last_error}")

    async def get_pokemon(self, identifier: int | str) -> dict:
        return await self._request(f"/pokemon/{identifier}")

    async def list_pokemons(self, page: int, size: int) -> dict:
        offset = (page - 1) * size
        return await self._request(f"/pokemon?limit={size}&offset={offset}")

    async def get_type(self, pokemon_type: str) -> dict:
        return await self._request(f"/type/{pokemon_type}")
