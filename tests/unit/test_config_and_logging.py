"""Structured logging and environment configuration."""

import json
import logging

import pytest

from task_api.infrastructure.config import load_settings
from task_api.infrastructure.logging import HANDLER_NAME, JsonFormatter, configure_logging


def test_json_formatter_emits_one_object_with_fields() -> None:
    record = logging.LogRecord(
        name="task_api.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="task_created",
        args=(),
        exc_info=None,
    )
    record.fields = {"task_id": "abc", "note": "line\nbreak"}

    rendered = JsonFormatter().format(record)
    payload = json.loads(rendered)

    assert "\n" not in rendered
    assert payload["message"] == "task_created"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "task_api.test"
    assert payload["fields"] == {"task_id": "abc", "note": "line\nbreak"}


def test_configure_logging_installs_one_handler() -> None:
    configure_logging("INFO")
    configure_logging("not-a-level")

    names = [handler.name for handler in logging.getLogger().handlers]
    assert names.count(HANDLER_NAME) == 1


def test_settings_read_the_task_api_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASK_API_ENVIRONMENT", "ci")
    monkeypatch.setenv("TASK_API_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TASK_API_DATABASE_URL", "sqlite://")

    settings = load_settings(_env_file=None)

    assert settings.environment == "ci"
    assert settings.log_level == "DEBUG"
    assert settings.database_url == "sqlite://"
    assert settings.app_name == "task-api"


def test_unknown_settings_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASK_API_NOT_A_REAL_SETTING", "surprise")

    settings = load_settings(_env_file=None)

    assert not hasattr(settings, "not_a_real_setting")
