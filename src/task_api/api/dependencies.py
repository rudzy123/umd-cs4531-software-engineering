"""Composition root. This is the only API module that imports infrastructure."""

from collections.abc import Iterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from task_api.application.services import TaskService
from task_api.domain.repositories import TaskRepository
from task_api.infrastructure.database import session_scope
from task_api.infrastructure.repositories import SqlAlchemyTaskRepository


def get_session(request: Request) -> Iterator[Session]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    yield from session_scope(factory)


def get_task_repository(
    session: Annotated[Session, Depends(get_session)],
) -> TaskRepository:
    return SqlAlchemyTaskRepository(session)


def get_task_service(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository)


SessionDep = Annotated[Session, Depends(get_session)]
RepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]
ServiceDep = Annotated[TaskService, Depends(get_task_service)]
