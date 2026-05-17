from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskOutput:
    meta_stream: Callable[[Any], None]  # pw.io...write operation
    errors_only: Callable[[Any], None] | None = None
    valid_only: Callable[[Any], None] | None = None
