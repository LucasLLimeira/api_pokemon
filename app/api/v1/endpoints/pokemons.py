from fastapi import APIRouter, Depends, Path, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import api_key_auth
from app.db import get_db_session
from app.models.pagination import PokemonListResponse
from app.models.pokemon import PokemonCreate, PokemonResponse, PokemonUpdate
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


@router.get("/local", response_model=PokemonListResponse)
async def list_local_pokemons(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    service: PokemonService = Depends(get_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> PokemonListResponse:
    settings = get_settings()
    size = min(size, settings.max_page_size)
    return await service.list_local_pokemons(page=page, size=size, db_session=db_session)


@router.get("/name/{name}", response_model=PokemonResponse)
async def get_pokemon_by_name(
    name: str = Path(min_length=1),
    service: PokemonService = Depends(get_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> PokemonResponse:
    return await service.get_pokemon(name, db_session=db_session)


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
    db_session: AsyncSession = Depends(get_db_session),
) -> PokemonResponse:
    return await service.get_pokemon(pokemon_id, db_session=db_session)


@router.post("", response_model=PokemonResponse, status_code=status.HTTP_201_CREATED)
async def create_pokemon(
    payload: PokemonCreate,
    service: PokemonService = Depends(get_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> PokemonResponse:
    return await service.create_pokemon(payload, db_session=db_session)


@router.put("/{pokemon_id}", response_model=PokemonResponse)
async def update_pokemon(
    payload: PokemonUpdate,
    pokemon_id: int = Path(ge=1),
    service: PokemonService = Depends(get_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> PokemonResponse:
    return await service.update_pokemon(pokemon_id, payload, db_session=db_session)


@router.delete("/{pokemon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pokemon(
    pokemon_id: int = Path(ge=1),
    service: PokemonService = Depends(get_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    await service.delete_pokemon(pokemon_id, db_session=db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
