from fastapi import APIRouter

from app.api.v1.endpoints.pokemons import router as pokemon_router

api_router = APIRouter()
api_router.include_router(pokemon_router, tags=["pokemons"])
