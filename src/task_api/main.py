"""Process entry point and application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

from task_api import __version__
from task_api.api.errors import register_exception_handlers
from task_api.api.middleware import RequestLoggingMiddleware
from task_api.api.routers import health_router, tasks_router
from task_api.infrastructure.config import Settings
from task_api.infrastructure.database import (
    create_db_engine,
    create_session_factory,
    init_database,
    prepare_sqlite_path,
)
from task_api.infrastructure.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an app. Tests pass settings; the server process uses the environment."""

    resolved = settings if settings is not None else Settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        active = cast(Settings, application.state.settings)
        prepare_sqlite_path(active.database_url)
        engine = create_db_engine(active.database_url)
        application.state.engine = engine
        application.state.session_factory = create_session_factory(engine)
        init_database(engine)
        logger.info(
            "application_started",
            extra={"fields": {"environment": active.environment}},
        )
        try:
            yield
        finally:
            engine.dispose()
            logger.info("application_stopped")

    application = FastAPI(
        title="Task API",
        version=__version__,
        summary="Task-management service for the CS 4531 software-engineering reference.",
        lifespan=lifespan,
    )
    application.state.settings = resolved
    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(tasks_router)
    return application


app = create_app()
