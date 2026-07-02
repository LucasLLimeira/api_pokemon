from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.config import get_settings
from app.services.pokemon_service import PokemonService


async def get_redis_client() -> AsyncGenerator[Redis | None, None]:
    settings = get_settings()
    redis_client: Redis | None = None
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        yield redis_client
    except Exception:
        yield None
    finally:
        if redis_client:
            await redis_client.aclose()


async def get_pokemon_service(redis_client: Redis | None = None) -> PokemonService:
    return PokemonService(redis_client=redis_client)
