"""HTTP access log. The message is an event name; details live under fields."""

import logging
import time
import uuid
from collections.abc import Sequence
from typing import cast

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

_REQUEST_ID_LIMIT = 128


class RequestLoggingMiddleware:
    """Record method, path, status, and duration for every HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = _request_id(scope)
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                MutableHeaders(scope=message).append("x-request-id", request_id)
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "request_completed",
                extra={
                    "fields": {
                        "request_id": request_id,
                        "method": str(scope.get("method", "")),
                        "path": str(scope.get("path", "")),
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    }
                },
            )


def _request_id(scope: Scope) -> str:
    headers = cast(Sequence[tuple[bytes, bytes]], scope.get("headers", []))
    for name, value in headers:
        if name.lower() == b"x-request-id":
            text = value.decode(errors="replace").strip()
            if text:
                return text[:_REQUEST_ID_LIMIT]
    return str(uuid.uuid4())
