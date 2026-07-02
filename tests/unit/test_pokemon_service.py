import pytest

from app.core.exceptions import PokemonNotFoundError
from app.services.pokemon_service import PokemonService


class StubClient:
    def __init__(self) -> None:
        self.calls = 0

    async def get_pokemon(self, identifier):
        self.calls += 1
        if str(identifier) == "9999":
            raise PokemonNotFoundError()
        return {
            "name": "pikachu",
            "id": 25,
            "height": 4,
            "weight": 60,
            "types": [{"type": {"name": "electric"}}],
            "sprites": {
                "front_default": "https://img/pikachu-front.png",
                "back_default": "https://img/pikachu-back.png",
            },
        }


async def test_get_pokemon_uses_cache():
    service = PokemonService(redis_client=None)
    stub = StubClient()
    service._client = stub

    first = await service.get_pokemon(25)
    second = await service.get_pokemon(25)

    assert first.id == 25
    assert second.id == 25
    assert stub.calls == 1


async def test_get_pokemon_not_found_propagates():
    service = PokemonService(redis_client=None)
    stub = StubClient()
    service._client = stub

    with pytest.raises(PokemonNotFoundError):
        await service.get_pokemon(9999)
