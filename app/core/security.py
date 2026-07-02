from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.core.exceptions import AuthError

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def api_key_auth(x_api_key: str | None = Security(api_key_header)) -> None:
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise AuthError()
