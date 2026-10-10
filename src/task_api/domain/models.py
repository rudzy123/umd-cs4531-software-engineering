"""Task aggregate and the invariants that protect it."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from task_api.domain.exceptions import InvalidTaskError

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"


def validate_title(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        raise InvalidTaskError("title must not be empty")
    if len(stripped) > TITLE_MAX_LENGTH:
        raise InvalidTaskError(f"title must be at most {TITLE_MAX_LENGTH} characters")
    return stripped


def validate_description(description: str) -> str:
    stripped = description.strip()
    if len(stripped) > DESCRIPTION_MAX_LENGTH:
        message = f"description must be at most {DESCRIPTION_MAX_LENGTH} characters"
        raise InvalidTaskError(message)
    return stripped


@dataclass
class Task:
    """A unit of work owned by the domain, not by the database or the HTTP layer."""

    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    clock: Clock = field(default=utc_now, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.title = validate_title(self.title)
        self.description = validate_description(self.description)
        if not isinstance(self.priority, Priority):
            raise InvalidTaskError("priority must be one of: low, medium, high")
        if not isinstance(self.status, TaskStatus):
            raise InvalidTaskError("status must be one of: open, completed")

    def rename(self, title: str) -> None:
        validated = validate_title(title)
        if validated == self.title:
            return
        self.title = validated
        self._touch()

    def change_description(self, description: str) -> None:
        validated = validate_description(description)
        if validated == self.description:
            return
        self.description = validated
        self._touch()

    def assign_priority(self, priority: Priority) -> None:
        if priority is self.priority:
            return
        self.priority = priority
        self._touch()

    def mark_completed(self) -> None:
        self._change_status(TaskStatus.COMPLETED)

    def mark_open(self) -> None:
        self._change_status(TaskStatus.OPEN)

    def _change_status(self, status: TaskStatus) -> None:
        if status is self.status:
            return
        self.status = status
        self._touch()

    def _touch(self) -> None:
        self.updated_at = self.clock()
