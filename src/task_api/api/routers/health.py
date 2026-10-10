"""Liveness and readiness. Liveness ignores dependencies; readiness checks the database."""

from fastapi import APIRouter, HTTPException

from task_api.api.dependencies import RepositoryDep
from task_api.api.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["operations"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"description": "A required dependency is unavailable"}},
)
def ready(repository: RepositoryDep) -> ReadinessResponse:
    if not repository.ping():
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return ReadinessResponse(status="ready", database="ok")
