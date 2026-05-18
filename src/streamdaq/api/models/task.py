from typing import Any

from pydantic import BaseModel, Field


# Request/Response Models
class CheckInfo(BaseModel):
    """Information about a data quality check."""

    check_type: str
    name: str
    parameters: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True


class WindowInfo(BaseModel):
    """Information about a window."""

    window_type: str
    parameters: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True


class TaskResponse(BaseModel):
    """Complete Task information."""

    task_index: int
    name: str | None
    instant_checks: list[CheckInfo]
    window_checks: list[CheckInfo]
    window: WindowInfo | None
    input_kwargs: dict[str, Any] | None
    output_kwargs: dict[str, Any] | None

    class Config:
        arbitrary_types_allowed = True


class CheckPayload(BaseModel):
    """Generic check payload for JSON deserialization."""

    check_type: str  # e.g., "streamdaq.checks.instant.any_column.InSet"
    check_data: dict[
        str, Any
    ]  # e.g., {"name": "my_check", "column": "col1", "allowed_values": [1, 2, 3]}


class AddInstantChecksRequest(BaseModel):
    instant_checks: list[CheckPayload]


class AddWindowChecksRequest(BaseModel):
    window_checks: list[CheckPayload]
    window: dict[str, Any] = Field(description="Window configuration")


class AddChecksRequest(BaseModel):
    checks: list[CheckPayload]
    window: dict[str, Any] | None = None
