from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models.pagination import PokemonListResponse
from app.models.pokemon import PokemonResponse, PokemonSprites


class FakePokemonService:
    async def list_pokemons(self, page: int, size: int) -> PokemonListResponse:
        data = [
            PokemonResponse(
                name="pikachu",
                id=25,
                height=4,
                weight=60,
                types=["electric"],
                sprites=PokemonSprites(
                    front_default="https://img/pikachu-front.png",
                    back_default="https://img/pikachu-back.png",
                ),
            )
        ]
        return PokemonListResponse(
            data=data,
            pagination={
                "total": 1,
                "page": page,
                "size": size,
                "next": None,
                "previous": None,
            },
        )

    async def get_pokemon(self, identifier: int | str) -> PokemonResponse:
        if str(identifier) == "9999":
            from app.core.exceptions import PokemonNotFoundError

            raise PokemonNotFoundError()
        return PokemonResponse(
            name="pikachu",
            id=25,
            height=4,
            weight=60,
            types=["electric"],
            sprites=PokemonSprites(
                front_default="https://img/pikachu-front.png",
                back_default="https://img/pikachu-back.png",
            ),
        )

    async def get_by_name(self, name: str) -> PokemonResponse:
        return await self.get_pokemon(name)

    async def list_by_type(self, pokemon_type: str, page: int, size: int) -> PokemonListResponse:
        return await self.list_pokemons(page=page, size=size)


@pytest.fixture()
def client() -> Any:
    with TestClient(app) as test_client:
        test_client.app.state.pokemon_service = FakePokemonService()
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    settings = get_settings()
    return {"x-api-key": settings.api_key}
