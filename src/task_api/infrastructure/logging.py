"""JSON logs. One object per line so a collector can index fields."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

HANDLER_NAME = "task_api_json"


class JsonFormatter(logging.Formatter):
    """Render a log record as a single JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload["fields"] = fields
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Attach one JSON handler to the root logger without removing test handlers."""

    root = logging.getLogger()
    root.setLevel(_coerce_level(level))
    if any(handler.name == HANDLER_NAME for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.name = HANDLER_NAME
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def _coerce_level(level: str) -> int:
    value = logging.getLevelName(level.upper())
    if isinstance(value, int):
        return value
    return logging.INFO
