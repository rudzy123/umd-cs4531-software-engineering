"""SQLite adapter, including a second session so identity-map cheating cannot pass."""

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from task_api.domain.exceptions import ConflictError
from task_api.domain.models import Priority, Task, TaskStatus
from task_api.domain.repositories import TaskRepository
from task_api.infrastructure.database import (
    TaskRecord,
    create_db_engine,
    create_session_factory,
    init_database,
)
from task_api.infrastructure.repositories import SqlAlchemyTaskRepository


@pytest.fixture
def engine() -> Iterator[Engine]:
    database = create_db_engine("sqlite://")
    init_database(database)
    try:
        yield database
    finally:
        database.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return create_session_factory(engine)


def test_sqlalchemy_repository_satisfies_the_port(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        repository: TaskRepository = SqlAlchemyTaskRepository(session)
        assert repository.ping() is True


def test_task_survives_a_new_session(session_factory: sessionmaker[Session]) -> None:
    created_at = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    with session_factory() as session:
        repository = SqlAlchemyTaskRepository(session)
        task = Task(
            title="Persist me",
            description="across sessions",
            priority=Priority.HIGH,
            created_at=created_at,
            updated_at=created_at,
        )
        repository.add(task)
        task_id = task.id
        session.commit()

    with session_factory() as session:
        loaded = SqlAlchemyTaskRepository(session).get(task_id)

    assert loaded is not None
    assert loaded.title == "Persist me"
    assert loaded.description == "across sessions"
    assert loaded.priority is Priority.HIGH
    assert loaded.status is TaskStatus.OPEN
    assert loaded.created_at == created_at


def test_filters_and_updates_round_trip(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        repository = SqlAlchemyTaskRepository(session)
        first = Task(title="Keep", priority=Priority.LOW)
        second = Task(title="Change", priority=Priority.HIGH)
        repository.add(first)
        repository.add(second)
        second.assign_priority(Priority.LOW)
        second.mark_completed()
        repository.save(second)
        session.commit()
        second_id = second.id

    with session_factory() as session:
        repository = SqlAlchemyTaskRepository(session)
        low = repository.list_tasks(priority=Priority.LOW)
        completed = repository.list_tasks(status=TaskStatus.COMPLETED)
        loaded = repository.get(second_id)

    assert {task.title for task in low} == {"Keep", "Change"}
    assert [task.title for task in completed] == ["Change"]
    assert loaded is not None
    assert loaded.status is TaskStatus.COMPLETED


def test_delete_is_visible_to_the_next_session(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        repository = SqlAlchemyTaskRepository(session)
        task = Task(title="Gone")
        repository.add(task)
        assert repository.delete(task.id) is True
        assert repository.delete(task.id) is False
        session.commit()
        task_id = task.id

    with session_factory() as session:
        assert SqlAlchemyTaskRepository(session).get(task_id) is None


def test_duplicate_id_is_a_conflict(session_factory: sessionmaker[Session]) -> None:
    task = Task(title="Once")
    with session_factory() as session:
        repository = SqlAlchemyTaskRepository(session)
        repository.add(task)
        with pytest.raises(ConflictError):
            repository.add(task)
        session.rollback()


def test_check_constraint_rejects_an_empty_title(session_factory: sessionmaker[Session]) -> None:
    now = datetime(2026, 3, 1, tzinfo=UTC)
    with pytest.raises(IntegrityError), session_factory() as session:
        session.add(
            TaskRecord(
                id=str(uuid4()),
                title="",
                description="",
                priority="low",
                status="open",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
