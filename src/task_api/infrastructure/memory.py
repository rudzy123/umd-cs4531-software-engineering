"""In-memory adapter. Tests use it to exercise the service without a database."""

from uuid import UUID

from task_api.domain.exceptions import ConflictError, TaskNotFoundError
from task_api.domain.models import Priority, Task, TaskStatus


class InMemoryTaskRepository:
    """Stores detached copies so a caller must save changes to persist them."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        self.available = True

    def add(self, task: Task) -> None:
        if task.id in self._tasks:
            raise ConflictError(f"Task {task.id} already exists")
        self._tasks[task.id] = _copy(task)

    def get(self, task_id: UUID) -> Task | None:
        stored = self._tasks.get(task_id)
        if stored is None:
            return None
        return _copy(stored)

    def list_tasks(
        self,
        *,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        tasks = [_copy(task) for task in self._tasks.values()]
        if priority is not None:
            tasks = [task for task in tasks if task.priority is priority]
        if status is not None:
            tasks = [task for task in tasks if task.status is status]
        return sorted(tasks, key=lambda task: (task.created_at, str(task.id)))

    def save(self, task: Task) -> None:
        if task.id not in self._tasks:
            raise TaskNotFoundError(f"Task {task.id} was not found")
        self._tasks[task.id] = _copy(task)

    def delete(self, task_id: UUID) -> bool:
        try:
            del self._tasks[task_id]
        except KeyError:
            return False
        return True

    def ping(self) -> bool:
        return self.available


def _copy(task: Task) -> Task:
    return Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        id=task.id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        clock=task.clock,
    )
