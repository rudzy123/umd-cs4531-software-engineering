"""Persistence port. Application code depends on this, not on SQLAlchemy."""

from typing import Protocol
from uuid import UUID

from task_api.domain.models import Priority, Task, TaskStatus


class TaskRepository(Protocol):
    """Storage operations the application service is allowed to use."""

    def add(self, task: Task) -> None:
        """Persist a new task. Raises ConflictError if the id already exists."""
        ...

    def get(self, task_id: UUID) -> Task | None:
        """Return a detached copy, or None when the id is unknown."""
        ...

    def list_tasks(
        self,
        *,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """Return matching tasks ordered by creation time, then id."""
        ...

    def save(self, task: Task) -> None:
        """Replace the stored copy. Raises TaskNotFoundError if it disappeared."""
        ...

    def delete(self, task_id: UUID) -> bool:
        """Remove the task. Return False when it was already absent."""
        ...

    def ping(self) -> bool:
        """Report whether the backing store can answer a trivial query."""
        ...
