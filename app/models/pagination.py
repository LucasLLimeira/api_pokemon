from pydantic import BaseModel, Field

from app.models.pokemon import PokemonResponse


class PaginationResponse(BaseModel):
    total: int
    page: int
    size: int
    next: str | None = None
    previous: str | None = None


class PokemonListResponse(BaseModel):
    data: list[PokemonResponse] = Field(default_factory=list)
    pagination: PaginationResponse
