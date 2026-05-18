import importlib
import json
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from streamdaq.api.models.task import (
    AddChecksRequest,
    AddInstantChecksRequest,
    AddWindowChecksRequest,
    CheckInfo,
    TaskResponse,
    WindowInfo,
)
from streamdaq.checks.base import DataQualityCheck
from streamdaq.sessions.base import Session
from streamdaq.tasks.base import Task
from streamdaq.windows.base import Window


def _import_and_instantiate_check(check_type: str, check_data: dict[str, Any]) -> DataQualityCheck:
    """
    Dynamically import a check class and instantiate it from JSON data.

    Args:
        check_type: Fully qualified class name (e.g., "streamdaq.checks.instant.any_column.InSet")
        check_data: Dictionary of initialization parameters

    Returns:
        Instantiated check object
    """
    try:
        # Split module path and class name
        parts = check_type.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid check type format: {check_type}")

        module_path, class_name = parts

        # Import the module
        module = importlib.import_module(module_path)

        # Get the class
        check_class = getattr(module, class_name)

        # Instantiate with provided data
        return check_class(**check_data)
    except ImportError as e:
        raise ValueError(f"Failed to import check module {module_path}: {e}")
    except AttributeError as e:
        raise ValueError(f"Check class {class_name} not found in module: {e}")
    except TypeError as e:
        raise ValueError(f"Failed to instantiate {class_name} with data {check_data}: {e}")


def _extract_check_info(check: DataQualityCheck) -> CheckInfo:
    """Extract serializable information from a check object."""
    check_class = check.__class__
    module_name = check_class.__module__
    class_name = check_class.__name__
    check_type = f"{module_name}.{class_name}"

    # Extract check parameters as a dict
    parameters = {}
    if hasattr(check, "__dict__"):
        for key, value in check.__dict__.items():
            if not key.startswith("_"):
                try:
                    json.dumps(value, default=str)
                    parameters[key] = value
                except (TypeError, ValueError):
                    parameters[key] = str(value)

    return CheckInfo(
        check_type=check_type,
        name=check.name,
        parameters=parameters,
    )


def _extract_window_info(window: Window | None) -> WindowInfo | None:
    """Extract serializable information from a window object."""
    if window is None:
        return None

    window_class = window.__class__
    module_name = window_class.__module__
    class_name = window_class.__name__
    window_type = f"{module_name}.{class_name}"

    # Extract window parameters as a dict
    parameters = {}
    if hasattr(window, "__dict__"):
        for key, value in window.__dict__.items():
            if not key.startswith("_"):
                try:
                    json.dumps(value, default=str)
                    parameters[key] = value
                except (TypeError, ValueError):
                    parameters[key] = str(value)

    return WindowInfo(
        window_type=window_type,
        parameters=parameters,
    )


def _build_task_response(task: Task, task_index: int) -> TaskResponse:
    """Build a complete TaskResponse from a Task object."""
    return TaskResponse(
        task_index=task_index,
        name=task.name,
        instant_checks=[_extract_check_info(check) for check in task.instant_checks],
        window_checks=[_extract_check_info(check) for check in task.window_checks],
        window=_extract_window_info(task.window),
        input_kwargs=task.input_kwargs,
        output_kwargs=task.output_kwargs,
    )


def create_router(session: Session) -> APIRouter:
    """Create a tasks router for a given session."""
    router = APIRouter(prefix="/tasks", tags=["tasks"])

    def _get_task(task_index: int) -> tuple[Task, int]:
        """Helper to get task by index from session."""
        if task_index < 0 or task_index >= len(session.tasks):
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Task at index {task_index} not found. Session has {len(session.tasks)} tasks."
                ),
            )
        return session.tasks[task_index], task_index

    @router.post("/{task_index}/add-instant-checks", response_model=TaskResponse)
    async def add_instant_checks(
        task_index: int,
        request: AddInstantChecksRequest = Body(...),
    ) -> TaskResponse:
        """Add instant checks to a task.

        Example payload:
        {
            "instant_checks": [
                {
                    "check_type": "streamdaq.checks.instant.any_column.InSet",
                    "check_data": {
                        "name": "allowed_values_check",
                        "column": "my_column",
                        "allowed_values": [1, 2, 3]
                    }
                }
            ]
        }
        """
        task, idx = _get_task(task_index)

        try:
            instant_checks = [
                _import_and_instantiate_check(check.check_type, check.check_data)
                for check in request.instant_checks
            ]
            task.add_instant_checks(*instant_checks)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return _build_task_response(task, idx)

    @router.post("/{task_index}/add-window-checks", response_model=TaskResponse)
    async def add_window_checks(
        task_index: int,
        request: AddWindowChecksRequest = Body(...),
    ) -> TaskResponse:
        """Add window checks to a task.

        Example payload:
        {
            "window_checks": [
                {
                    "check_type": "streamdaq.checks.window.SomeWindowCheck",
                    "check_data": {
                        "name": "window_check",
                        "column": "my_column"
                    }
                }
            ],
            "window": {
                "window_type": "streamdaq.windows.SomeWindow",
                "window_data": {...}
            }
        }
        """
        task, idx = _get_task(task_index)

        try:
            # TODO: Implement window instantiation from request.window
            # For now, window needs to be passed separately
            raise HTTPException(
                status_code=501,
                detail="Window instantiation from JSON not yet implemented",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return _build_task_response(task, idx)

    @router.post("/{task_index}/add-checks", response_model=TaskResponse)
    async def add_checks(
        task_index: int,
        request: AddChecksRequest = Body(...),
    ) -> TaskResponse:
        """Add checks (instant or window) to a task.

        Example payload:
        {
            "checks": [
                {
                    "check_type": "streamdaq.checks.instant.any_column.InSet",
                    "check_data": {
                        "name": "allowed_values_check",
                        "column": "my_column",
                        "allowed_values": [1, 2, 3]
                    }
                }
            ],
            "window": null
        }
        """
        task, idx = _get_task(task_index)

        try:
            checks = [
                _import_and_instantiate_check(check.check_type, check.check_data)
                for check in request.checks
            ]
            # TODO: Implement window instantiation if needed
            task.add_checks(*checks, window=None)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return _build_task_response(task, idx)

    @router.get("/{task_index}", response_model=TaskResponse)
    async def get_task(task_index: int) -> TaskResponse:
        """Get task details."""
        task, idx = _get_task(task_index)
        return _build_task_response(task, idx)

    return router
