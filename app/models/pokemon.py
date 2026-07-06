from pydantic import BaseModel, Field


class PokemonSprites(BaseModel):
    front_default: str | None = None
    back_default: str | None = None


class PokemonBase(BaseModel):
    name: str
    height: int
    weight: int
    types: list[str] = Field(default_factory=list)
    sprites: PokemonSprites


class PokemonCreate(PokemonBase):
    pass


class PokemonUpdate(BaseModel):
    name: str | None = None
    height: int | None = None
    weight: int | None = None
    types: list[str] | None = None
    sprites: PokemonSprites | None = None


class PokemonResponse(PokemonBase):
    id: int
