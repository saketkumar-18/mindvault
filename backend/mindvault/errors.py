from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from mindvault.logging_setup import get_logger

logger = get_logger("mindvault.errors")


class AppError(Exception):
    """Base application error with a user-safe message and an optional suggestion.

    Raw stack traces are never shown to end users; only the structured payload.
    """

    status_code = 500
    code = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
                "status": self.status_code,
            }
        }
        if self.details is not None:
            payload["error"]["details"] = self.details
        if self.suggestion:
            payload["error"]["suggestion"] = self.suggestion
        return payload


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_error"


class PayloadTooLarge(AppError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedFileType(AppError):
    status_code = 415
    code = "unsupported_file_type"


class ServiceUnavailable(AppError):
    status_code = 503
    code = "service_unavailable"


class SecurityViolation(AppError):
    status_code = 400
    code = "security_error"


class NotReadyError(AppError):
    status_code = 409
    code = "not_ready"


class ProviderUnavailable(ServiceUnavailable):
    code = "provider_unavailable"


class IndexUnavailable(ServiceUnavailable):
    code = "index_unavailable"


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # exc.errors() can carry non-JSON-serializable ctx (e.g. bytes from a
        # malformed multipart body) — sanitize before rendering, or the error
        # handler itself 500s and masks the real 422.
        def _clean(obj: object) -> object:
            if isinstance(obj, bytes):
                return obj.decode("utf-8", "replace")[:200]
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_clean(v) for v in obj]
            return obj

        details = _clean(exc.errors())
        payload = {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "status": 422,
                "details": details,
            }
        }
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "http_error"
        if exc.status_code == 404:
            code = "not_found"
        elif exc.status_code == 405:
            code = "method_not_allowed"
        payload = {
            "error": {
                "code": code,
                "message": exc.detail or "HTTP error.",
                "status": exc.status_code,
            }
        }
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        payload = {
            "error": {
                "code": "internal_error",
                "message": "Something went wrong.",
                "status": 500,
                "suggestion": "View the technical logs for details.",
            }
        }
        return JSONResponse(status_code=500, content=payload)
