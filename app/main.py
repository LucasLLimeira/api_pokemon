from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import AppError, app_error_handler, unhandled_error_handler
from app.core.logging import configure_logging
from app.db import create_db_and_tables, dispose_db, init_db
from app.middleware.request_context import RequestContextMiddleware
from app.services.pokemon_service import PokemonService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    init_db(settings.database_url)
    await create_db_and_tables()

    redis_client: Redis | None = None
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
    except Exception:
        redis_client = None

    app.state.redis_client = redis_client
    app.state.pokemon_service = PokemonService(redis_client=redis_client)

    yield

    if redis_client is not None:
        await redis_client.aclose()
    await dispose_db()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
