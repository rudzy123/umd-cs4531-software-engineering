"""Application service behavior against the in-memory port."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from task_api.application.services import TaskDraft, TaskPatch, TaskService
from task_api.domain.exceptions import InvalidTaskError, TaskNotFoundError
from task_api.domain.models import Priority, TaskStatus
from task_api.domain.repositories import TaskRepository
from task_api.infrastructure.memory import InMemoryTaskRepository


class SequentialClock:
    def __init__(self) -> None:
        self._ticks = 0

    def __call__(self) -> datetime:
        self._ticks += 1
        return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=self._ticks)


def test_in_memory_repository_satisfies_the_port() -> None:
    repository: TaskRepository = InMemoryTaskRepository()
    assert repository.ping() is True


def test_create_then_get_returns_a_detached_copy() -> None:
    repository = InMemoryTaskRepository()
    service = TaskService(repository, clock=SequentialClock())

    created = service.create_task(TaskDraft(title="Write tests", priority=Priority.HIGH))
    loaded = service.get_task(created.id)

    assert loaded == created
    assert loaded is not created


def test_blank_title_is_rejected_before_persistence() -> None:
    repository = InMemoryTaskRepository()
    service = TaskService(repository)

    with pytest.raises(InvalidTaskError, match="title must not be empty"):
        service.create_task(TaskDraft(title="   "))

    assert repository.list_tasks() == []


def test_list_filters_by_priority_and_status() -> None:
    service = TaskService(InMemoryTaskRepository(), clock=SequentialClock())
    open_high = service.create_task(TaskDraft(title="Open high", priority=Priority.HIGH))
    service.create_task(TaskDraft(title="Open low", priority=Priority.LOW))
    completed = service.create_task(TaskDraft(title="Done high", priority=Priority.HIGH))
    service.update_task(
        completed.id,
        TaskPatch(status=TaskStatus.COMPLETED, provided=frozenset({"status"})),
    )

    high = service.list_tasks(priority=Priority.HIGH)
    open_tasks = service.list_tasks(status=TaskStatus.OPEN)
    both = service.list_tasks(priority=Priority.HIGH, status=TaskStatus.OPEN)

    assert [task.id for task in high] == [open_high.id, completed.id]
    assert {task.title for task in open_tasks} == {"Open high", "Open low"}
    assert [task.id for task in both] == [open_high.id]


def test_update_assigns_priority_and_completion() -> None:
    service = TaskService(InMemoryTaskRepository(), clock=SequentialClock())
    created = service.create_task(TaskDraft(title="Ship the API", priority=Priority.LOW))

    updated = service.update_task(
        created.id,
        TaskPatch(
            priority=Priority.HIGH,
            status=TaskStatus.COMPLETED,
            provided=frozenset({"priority", "status"}),
        ),
    )

    assert updated.priority is Priority.HIGH
    assert updated.status is TaskStatus.COMPLETED
    assert updated.updated_at > created.updated_at
    assert service.get_task(created.id).status is TaskStatus.COMPLETED


def test_empty_patch_does_not_change_the_task() -> None:
    service = TaskService(InMemoryTaskRepository(), clock=SequentialClock())
    created = service.create_task(TaskDraft(title="Leave me alone"))

    updated = service.update_task(created.id, TaskPatch())

    assert updated.title == created.title
    assert updated.updated_at == created.updated_at


def test_missing_task_cannot_be_read_updated_or_deleted() -> None:
    service = TaskService(InMemoryTaskRepository())
    missing = uuid4()

    with pytest.raises(TaskNotFoundError):
        service.get_task(missing)
    with pytest.raises(TaskNotFoundError):
        service.update_task(missing, TaskPatch(title="Nope", provided=frozenset({"title"})))
    with pytest.raises(TaskNotFoundError):
        service.delete_task(missing)


def test_delete_removes_the_task() -> None:
    service = TaskService(InMemoryTaskRepository())
    created = service.create_task(TaskDraft(title="Temporary"))

    service.delete_task(created.id)

    with pytest.raises(TaskNotFoundError):
        service.get_task(created.id)
