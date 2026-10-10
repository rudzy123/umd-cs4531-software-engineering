"""Request and response models. These are the public HTTP contract."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from task_api.application.services import TaskDraft, TaskPatch
from task_api.domain.models import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    Priority,
    Task,
    TaskStatus,
)


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: list[ErrorDetail] | None = None


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


class TaskCreateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "Draft acceptance criteria",
                    "description": "Cover the happy path and the validation failures",
                    "priority": "high",
                }
            ]
        },
    )

    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    priority: Priority = Priority.MEDIUM

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    def to_draft(self) -> TaskDraft:
        return TaskDraft(
            title=self.title,
            description=self.description,
            priority=self.priority,
        )


class TaskUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    priority: Priority | None = None
    status: TaskStatus | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> Self:
        for name in ("title", "description", "priority", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self

    def to_patch(self) -> TaskPatch:
        return TaskPatch(
            title=self.title,
            description=self.description,
            priority=self.priority,
            status=self.status,
            provided=frozenset(self.model_fields_set),
        )


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_task(cls, task: Task) -> Self:
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


def error_body(
    error: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    parsed = None if details is None else [ErrorDetail.model_validate(item) for item in details]
    return ErrorResponse(error=error, message=message, details=parsed).model_dump()
