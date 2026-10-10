"""Use cases for creating, querying, updating, and deleting tasks."""

import logging
from dataclasses import dataclass
from uuid import UUID

from task_api.domain.exceptions import InvalidTaskError, TaskNotFoundError
from task_api.domain.models import Clock, Priority, Task, TaskStatus, utc_now
from task_api.domain.repositories import TaskRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskDraft:
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM


@dataclass(frozen=True)
class TaskPatch:
    """Partial update. `provided` distinguishes an omitted field from a value."""

    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    status: TaskStatus | None = None
    provided: frozenset[str] = frozenset()


class TaskService:
    """Orchestrates domain behavior and the repository port."""

    def __init__(self, repository: TaskRepository, clock: Clock | None = None) -> None:
        self._repository = repository
        self._clock = clock or utc_now

    def create_task(self, draft: TaskDraft) -> Task:
        now = self._clock()
        task = Task(
            title=draft.title,
            description=draft.description,
            priority=draft.priority,
            created_at=now,
            updated_at=now,
            clock=self._clock,
        )
        self._repository.add(task)
        logger.info("task_created", extra={"fields": {"task_id": str(task.id)}})
        return task

    def get_task(self, task_id: UUID) -> Task:
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} was not found")
        return task

    def list_tasks(
        self,
        *,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        return self._repository.list_tasks(priority=priority, status=status)

    def update_task(self, task_id: UUID, patch: TaskPatch) -> Task:
        task = self.get_task(task_id)
        if "title" in patch.provided:
            if patch.title is None:
                raise InvalidTaskError("title cannot be null")
            task.rename(patch.title)
        if "description" in patch.provided:
            if patch.description is None:
                raise InvalidTaskError("description cannot be null")
            task.change_description(patch.description)
        if "priority" in patch.provided:
            if patch.priority is None:
                raise InvalidTaskError("priority cannot be null")
            task.assign_priority(patch.priority)
        if "status" in patch.provided:
            if patch.status is None:
                raise InvalidTaskError("status cannot be null")
            if patch.status is TaskStatus.COMPLETED:
                task.mark_completed()
            else:
                task.mark_open()
        self._repository.save(task)
        logger.info("task_updated", extra={"fields": {"task_id": str(task.id)}})
        return task

    def delete_task(self, task_id: UUID) -> None:
        if not self._repository.delete(task_id):
            raise TaskNotFoundError(f"Task {task_id} was not found")
        logger.info("task_deleted", extra={"fields": {"task_id": str(task_id)}})
