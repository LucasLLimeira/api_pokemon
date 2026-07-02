from fastapi import APIRouter, Depends, Path, Query, Request

from app.config import get_settings
from app.core.security import api_key_auth
from app.models.pagination import PokemonListResponse
from app.models.pokemon import PokemonResponse
from app.services.pokemon_service import PokemonService

router = APIRouter(prefix="/pokemons", dependencies=[Depends(api_key_auth)])


def get_service(request: Request) -> PokemonService:
    return request.app.state.pokemon_service


@router.get("", response_model=PokemonListResponse)
async def list_pokemons(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    service: PokemonService = Depends(get_service),
) -> PokemonListResponse:
    settings = get_settings()
    size = min(size, settings.max_page_size)
    return await service.list_pokemons(page=page, size=size)


@router.get("/name/{name}", response_model=PokemonResponse)
async def get_pokemon_by_name(
    name: str = Path(min_length=1),
    service: PokemonService = Depends(get_service),
) -> PokemonResponse:
    return await service.get_by_name(name)


@router.get("/type/{pokemon_type}", response_model=PokemonListResponse)
async def get_pokemons_by_type(
    pokemon_type: str = Path(min_length=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    service: PokemonService = Depends(get_service),
) -> PokemonListResponse:
    settings = get_settings()
    size = min(size, settings.max_page_size)
    return await service.list_by_type(pokemon_type=pokemon_type, page=page, size=size)


@router.get("/{pokemon_id}", response_model=PokemonResponse)
async def get_pokemon_by_id(
    pokemon_id: int = Path(ge=1),
    service: PokemonService = Depends(get_service),
) -> PokemonResponse:
    return await service.get_pokemon(pokemon_id)
