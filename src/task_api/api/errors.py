"""Map framework and domain failures onto one error envelope."""

import logging
from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from task_api.api.schemas import error_body
from task_api.domain.exceptions import (
    ConflictError,
    DomainError,
    InvalidTaskError,
    TaskNotFoundError,
)

_STATUS_BY_TYPE: dict[type[DomainError], int] = {
    InvalidTaskError: 422,
    TaskNotFoundError: 404,
    ConflictError: 409,
}

logger = logging.getLogger(__name__)

_HTTP_CODES: dict[int, str] = {
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    503: "not_ready",
}


def validation_error_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for error in exc.errors():
        location = error.get("loc", ())
        message = str(error.get("msg", "Invalid value"))
        details.append({"field": _field_name(location), "message": message})
    return details


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected_error)


async def _domain_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        return _unexpected_payload()
    status_code = _STATUS_BY_TYPE.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content=error_body(exc.error_code, exc.message),
    )


async def _validation_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return _unexpected_payload()
    return JSONResponse(
        status_code=422,
        content=error_body(
            "validation_error",
            "Request validation failed",
            validation_error_details(exc),
        ),
    )


async def _http_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return _unexpected_payload()
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
    )


async def _unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        extra={"fields": {"path": request.url.path, "method": request.method}},
    )
    return _unexpected_payload()


def _unexpected_payload() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_body("internal_error", "An unexpected error occurred"),
    )


def _field_name(location: Sequence[object]) -> str:
    parts = [str(part) for part in location if part not in {"body", "query", "path"}]
    if not parts:
        return "request"
    return ".".join(parts)
