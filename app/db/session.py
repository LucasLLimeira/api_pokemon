from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    global _engine, _session_maker
    _engine = create_async_engine(database_url, echo=False)
    _session_maker = async_sessionmaker(_engine, expire_on_commit=False)


async def create_db_and_tables() -> None:
    if _engine is None:
        raise RuntimeError("Database engine has not been initialized")
    async with _engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    if _engine is not None:
        await _engine.dispose()


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    if _session_maker is None:
        raise RuntimeError("Database session maker has not been initialized")
    return _session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session