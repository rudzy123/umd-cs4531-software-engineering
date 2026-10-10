"""Task routes. They translate HTTP into application calls and nothing more."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from task_api.api.dependencies import ServiceDep
from task_api.api.schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from task_api.domain.models import Priority, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreateRequest,
    response: Response,
    service: ServiceDep,
) -> TaskResponse:
    task = service.create_task(body.to_draft())
    response.headers["Location"] = f"/tasks/{task.id}"
    return TaskResponse.from_task(task)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    service: ServiceDep,
    priority: Priority | None = None,
    status: TaskStatus | None = None,
) -> list[TaskResponse]:
    tasks = service.list_tasks(priority=priority, status=status)
    return [TaskResponse.from_task(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, service: ServiceDep) -> TaskResponse:
    return TaskResponse.from_task(service.get_task(task_id))


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    service: ServiceDep,
) -> TaskResponse:
    return TaskResponse.from_task(service.update_task(task_id, body.to_patch()))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, service: ServiceDep) -> Response:
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
