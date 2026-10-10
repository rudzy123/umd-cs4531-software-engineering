"""Route modules."""

from task_api.api.routers.health import router as health_router
from task_api.api.routers.tasks import router as tasks_router

__all__ = ["health_router", "tasks_router"]
