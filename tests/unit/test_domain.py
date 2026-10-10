"""Domain invariants."""

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from task_api.domain.exceptions import InvalidTaskError
from task_api.domain.models import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    Priority,
    Task,
    TaskStatus,
)


def test_strips_surrounding_whitespace() -> None:
    task = Task(title="  Plan the release  ", description="  notes  ")

    assert task.title == "Plan the release"
    assert task.description == "notes"
    assert task.priority is Priority.MEDIUM
    assert task.status is TaskStatus.OPEN


def test_rejects_a_blank_title() -> None:
    with pytest.raises(InvalidTaskError, match="title must not be empty"):
        Task(title="   ")


def test_rejects_a_title_that_is_too_long() -> None:
    with pytest.raises(InvalidTaskError, match="title must be at most"):
        Task(title="a" * (TITLE_MAX_LENGTH + 1))


def test_rejects_a_description_that_is_too_long() -> None:
    with pytest.raises(InvalidTaskError, match="description must be at most"):
        Task(title="Plan", description="a" * (DESCRIPTION_MAX_LENGTH + 1))


def test_rejects_a_priority_that_is_not_the_enum() -> None:
    with pytest.raises(InvalidTaskError, match="priority"):
        Task(title="Plan", priority=cast(Priority, "high"))


def test_completion_is_idempotent() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    later = start + timedelta(days=1)
    task = Task(title="Plan", created_at=start, updated_at=start, clock=lambda: later)

    task.mark_completed()
    assert task.status is TaskStatus.COMPLETED
    assert task.updated_at == later

    task.mark_completed()
    assert task.updated_at == later


def test_reopen_returns_a_completed_task_to_open() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    later = start + timedelta(days=1)
    task = Task(title="Plan", created_at=start, updated_at=start, clock=lambda: later)

    task.mark_completed()
    task.mark_open()

    assert task.status is TaskStatus.OPEN


def test_unchanged_priority_does_not_touch_the_clock() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)

    def fail_clock() -> datetime:
        raise AssertionError("clock should not run")

    task = Task(
        title="Plan",
        priority=Priority.LOW,
        created_at=start,
        updated_at=start,
        clock=fail_clock,
    )

    task.assign_priority(Priority.LOW)
    task.rename("Plan")
    task.change_description("")

    assert task.updated_at == start
