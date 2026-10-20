"""Перевод ошибок use case'ов в HTTP. Единственное место, где прикладные ошибки узнают про статусы."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application import errors
from app.domain.errors import InvalidValue

_STATUS: dict[type[errors.AppError], int] = {
    errors.Unauthorized: 401,
    errors.InvalidCode: 400,
    errors.NotFound: 404,
    errors.Conflict: 409,
    errors.PayloadTooLarge: 413,
    errors.UnsupportedMedia: 415,
    errors.TooManyRequests: 429,
    errors.DeliveryFailed: 502,
    errors.ProviderUnavailable: 502,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(errors.AppError)
    async def handle_app_error(_: Request, error: errors.AppError) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(error, errors.Unauthorized):
            headers["WWW-Authenticate"] = "Bearer"
        if isinstance(error, errors.TooManyRequests) and error.retry_after:
            headers["Retry-After"] = str(error.retry_after)
        status = next((code for cls, code in _STATUS.items() if isinstance(error, cls)), 500)
        return JSONResponse({"detail": error.message}, status_code=status, headers=headers)

    @app.exception_handler(InvalidValue)
    async def handle_invalid_value(_: Request, error: InvalidValue) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=422)
