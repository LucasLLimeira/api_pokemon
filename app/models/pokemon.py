from pydantic import BaseModel, Field


class PokemonSprites(BaseModel):
    front_default: str | None = None
    back_default: str | None = None


class PokemonResponse(BaseModel):
    name: str
    id: int
    height: int
    weight: int
    types: list[str] = Field(default_factory=list)
    sprites: PokemonSprites
