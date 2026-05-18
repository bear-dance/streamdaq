import importlib
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from streamdaq.api.models.session import AddTasksRequest, SessionResponse
from streamdaq.api.models.task import TaskResponse
from streamdaq.sessions.base import Session
from streamdaq.tasks.base import Task


def _resolve_callable(path: Any, field_name: str) -> Any:
    """Resolve a callable from a fully qualified path string."""
    if path is None:
        return None
    if callable(path):
        return path
    if not isinstance(path, str):
        raise ValueError(f"{field_name} must be a callable or import path string")

    parts = path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid {field_name} import path: {path}")

    module_path, attr_name = parts
    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise ValueError(f"{field_name} not found in {module_path}: {attr_name}") from exc


def _instantiate_task(task_type: str, task_data: dict[str, Any]) -> Task:
    """Dynamically import a task class and instantiate it from JSON data."""
    # TODO: Test
    parts = task_type.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid task type format: {task_type}")

    module_path, class_name = parts
    module = importlib.import_module(module_path)
    try:
        task_class = getattr(module, class_name)
    except AttributeError as exc:
        raise ValueError(f"Task class {class_name} not found in module {module_path}") from exc

    if "input" in task_data:
        task_data["input"] = _resolve_callable(task_data["input"], "input")

    try:
        return task_class(**task_data)
    except TypeError as exc:
        raise ValueError(
            f"Failed to instantiate {class_name} with data {task_data}: {exc}"
        ) from exc


def _build_session_response(session: Session) -> SessionResponse:
    return SessionResponse(
        name=session.name,
        task_count=len(session.tasks),
        tasks=[
            TaskResponse(task_index=idx, name=task.name) for idx, task in enumerate(session.tasks)
        ],
    )


def create_router(session: Session) -> APIRouter:
    """Create a session router for a given session."""
    router = APIRouter(prefix="/session", tags=["session"])

    @router.post("/add-tasks", response_model=SessionResponse)
    async def add_tasks(request: AddTasksRequest = Body(...)) -> SessionResponse:
        """Add tasks to the session."""
        try:
            tasks = [_instantiate_task(task.task_type, task.task_data) for task in request.tasks]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        session.add_tasks(*tasks)
        return _build_session_response(session)

    @router.get("", response_model=SessionResponse)
    async def get_session() -> SessionResponse:
        """Get session details."""
        return _build_session_response(session)

    return router
