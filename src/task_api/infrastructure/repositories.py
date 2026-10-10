"""SQLite adapter for the task repository port."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from task_api.domain.exceptions import ConflictError, TaskNotFoundError
from task_api.domain.models import Priority, Task, TaskStatus
from task_api.infrastructure.database import TaskRecord, database_reachable


class SqlAlchemyTaskRepository:
    """Maps domain tasks to rows. Callers own the transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> None:
        self._session.add(_to_record(task))
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise ConflictError(f"Task {task.id} already exists") from exc

    def get(self, task_id: UUID) -> Task | None:
        record = self._session.get(TaskRecord, str(task_id))
        if record is None:
            return None
        return _to_domain(record)

    def list_tasks(
        self,
        *,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        statement = select(TaskRecord).order_by(TaskRecord.created_at.asc(), TaskRecord.id.asc())
        if priority is not None:
            statement = statement.where(TaskRecord.priority == priority.value)
        if status is not None:
            statement = statement.where(TaskRecord.status == status.value)
        records = self._session.scalars(statement).all()
        return [_to_domain(record) for record in records]

    def save(self, task: Task) -> None:
        record = self._session.get(TaskRecord, str(task.id))
        if record is None:
            raise TaskNotFoundError(f"Task {task.id} was not found")
        record.title = task.title
        record.description = task.description
        record.priority = task.priority.value
        record.status = task.status.value
        record.created_at = task.created_at
        record.updated_at = task.updated_at
        self._session.flush()

    def delete(self, task_id: UUID) -> bool:
        record = self._session.get(TaskRecord, str(task_id))
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True

    def ping(self) -> bool:
        return database_reachable(self._session)


def _to_record(task: Task) -> TaskRecord:
    return TaskRecord(
        id=str(task.id),
        title=task.title,
        description=task.description,
        priority=task.priority.value,
        status=task.status.value,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _to_domain(record: TaskRecord) -> Task:
    return Task(
        id=UUID(record.id),
        title=record.title,
        description=record.description,
        priority=Priority(record.priority),
        status=TaskStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
