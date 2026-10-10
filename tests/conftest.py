"""Shared fixtures. Each API test gets its own SQLite file."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from task_api.infrastructure.config import load_settings
from task_api.main import create_app


@pytest.fixture(autouse=True)
def clear_task_api_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("TASK_API_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def api_app(tmp_path: Path) -> Iterator[FastAPI]:
    database = tmp_path / "tasks.db"
    settings = load_settings(
        environment="test",
        log_level="WARNING",
        database_url=f"sqlite:///{database.as_posix()}",
        app_name="task-api-test",
        _env_file=None,
    )
    application = create_app(settings)
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(api_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(api_app) as test_client:
        yield test_client
