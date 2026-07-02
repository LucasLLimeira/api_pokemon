from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "API Pokemon"
    app_version: str = "1.0.0"
    debug: bool = False

    pokeapi_base_url: str = "https://pokeapi.co/api/v2"

    default_page_size: int = 20
    max_page_size: int = 100

    cache_ttl_seconds: int = 3600
    pokemon_ttl_seconds: int = 86400
    list_ttl_seconds: int = 3600
    type_ttl_seconds: int = 43200

    redis_url: str = "redis://redis:6379/0"
    api_key: str = "change-me"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
