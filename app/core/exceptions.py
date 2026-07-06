from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, detail: str, status_code: int, error_code: str) -> None:
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(detail)


class PokemonNotFoundError(AppError):
    def __init__(self, detail: str = "Pokemon not found") -> None:
        super().__init__(detail=detail, status_code=404, error_code="POKEMON_NOT_FOUND")


class PokemonAlreadyExistsError(AppError):
    def __init__(self, detail: str = "Pokemon already exists") -> None:
        super().__init__(detail=detail, status_code=409, error_code="POKEMON_ALREADY_EXISTS")


class PokeAPIError(AppError):
    def __init__(self, detail: str = "Error while consuming PokeAPI") -> None:
        super().__init__(detail=detail, status_code=502, error_code="POKEAPI_ERROR")


class AuthError(AppError):
    def __init__(self, detail: str = "Invalid API key") -> None:
        super().__init__(detail=detail, status_code=401, error_code="INVALID_API_KEY")


def _error_payload(detail: str, error_code: str, request_id: str | None) -> dict[str, str | None]:
    return {
        "detail": detail,
        "error_code": error_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.detail, exc.error_code, request_id),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content=_error_payload("Internal server error", "INTERNAL_SERVER_ERROR", request_id),
    )
