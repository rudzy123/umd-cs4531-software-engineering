"""Environment-backed settings. Secrets stay in the environment, never in git."""

from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration loaded from the environment and an optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="TASK_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/tasks.db"
    app_name: str = "task-api"


def load_settings(**overrides: Any) -> Settings:
    """Load settings. Keyword arguments override environment variables.

    Tests pass ``_env_file=None`` so a developer's dotenv file cannot change results.
    """

    return Settings(**overrides)
