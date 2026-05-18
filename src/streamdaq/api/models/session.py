from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from .task import TaskResponse


class TaskPayload(BaseModel):
    """Generic task payload for JSON deserialization."""

    task_type: str  # e.g., "streamdaq.tasks.base.Task"
    task_data: dict[str, Any]


class AddTasksRequest(BaseModel):
    tasks: list[TaskPayload]


class SessionResponse(BaseModel):
    """Session information used for API responses."""

    name: str | None
    task_count: int
    tasks: list["TaskResponse"]
