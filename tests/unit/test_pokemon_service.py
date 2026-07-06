import pytest

from app.core.exceptions import PokemonNotFoundError
from app.db import create_db_and_tables, dispose_db, get_session_maker, init_db
from app.models.pokemon import PokemonCreate, PokemonSprites, PokemonUpdate
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


@pytest.fixture()
async def db_session(tmp_path):
    init_db(f"sqlite+aiosqlite:///{tmp_path / 'pokemon.db'}")
    await create_db_and_tables()
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session
    await dispose_db()


async def test_pokemon_crud_flow_with_db(db_session):
    service = PokemonService(redis_client=None)

    created = await service.create_pokemon(
        PokemonCreate(
            name="bulbasaur",
            height=7,
            weight=69,
            types=["grass", "poison"],
            sprites=PokemonSprites(
                front_default="https://img/bulbasaur-front.png",
                back_default="https://img/bulbasaur-back.png",
            ),
        ),
        db_session=db_session,
    )

    assert created.id == 1
    assert created.types == ["grass", "poison"]

    updated = await service.update_pokemon(
        created.id,
        PokemonUpdate(
            name="testmon-updated",
            weight=130,
        ),
        db_session=db_session,
    )

    assert updated.name == "testmon-updated"
    assert updated.weight == 130

    await service.delete_pokemon(updated.id, db_session=db_session)

    with pytest.raises(PokemonNotFoundError):
        await service.get_pokemon(updated.name, db_session=db_session)

    remaining = await service.list_local_pokemons(page=1, size=20, db_session=db_session)
    assert remaining.pagination.total == 0


async def test_list_local_pokemons_returns_records(db_session):
    service = PokemonService(redis_client=None)

    await service.create_pokemon(
        PokemonCreate(
            name="charmander",
            height=6,
            weight=85,
            types=["fire"],
            sprites=PokemonSprites(),
        ),
        db_session=db_session,
    )

    response = await service.list_local_pokemons(page=1, size=20, db_session=db_session)

    assert response.pagination.total == 1
    assert response.data[0].name == "charmander"
