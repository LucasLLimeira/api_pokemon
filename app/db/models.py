from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


pokemon_types = Table(
    "pokemon_types",
    Base.metadata,
    Column("pokemon_id", ForeignKey("pokemons.id", ondelete="CASCADE"), primary_key=True),
    Column("type_id", ForeignKey("types.id", ondelete="CASCADE"), primary_key=True),
)


class TypeModel(Base):
    __tablename__ = "types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class PokemonModel(Base):
    __tablename__ = "pokemons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    height: Mapped[int] = mapped_column()
    weight: Mapped[int] = mapped_column()
    front_default: Mapped[str | None] = mapped_column(String(500), nullable=True)
    back_default: Mapped[str | None] = mapped_column(String(500), nullable=True)
    types: Mapped[list[TypeModel]] = relationship(
        secondary=pokemon_types,
        lazy="selectin",
    )