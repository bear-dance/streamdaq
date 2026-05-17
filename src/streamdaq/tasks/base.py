from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Self

import pathway as pw

from streamdaq.checks.base import DataQualityCheck
from streamdaq.checks.instant.base import InstantDataQualityCheck
from streamdaq.checks.window.base import WindowDataQualityCheck
from streamdaq.tasks.task_output import TaskOutput
from streamdaq.windows.base import Window


@dataclass
class Task:
    input: Callable[[Any], pw.Table]
    output: Callable[[Any], None] | TaskOutput
    name: str | None = None
    instant_checks: list[InstantDataQualityCheck] = field(default_factory=lambda: [])
    window_checks: list[WindowDataQualityCheck] = field(default_factory=lambda: [])
    window: Window | None = None
    name: str | None = None
    input_kwargs: dict[str, Any] | None = None
    output_kwargs: dict[str, Any] | None = None

    def __post_init__(self):
        self.instant_table: pw.Table | None = None
        self.window_table: pw.Table | None = None

    def add_instant_checks(self, *instant_checks: InstantDataQualityCheck) -> Self:
        for instant_check in instant_checks:
            self.instant_checks.append(instant_check)
        return self

    def add_window_checks(self, *window_checks: WindowDataQualityCheck, window: Window) -> Self:
        self.window = window
        for window_check in window_checks:
            self.window_checks.append(window_check)
        return self

    def add_checks(self, *checks: DataQualityCheck, window: Window | None = None) -> Self:
        instant_checks = [check for check in checks if isinstance(check, InstantDataQualityCheck)]
        window_checks = [check for check in checks if isinstance(check, WindowDataQualityCheck)]
        if len(window_checks) > 0 and window is None:
            raise ValueError("TODO CANNOT INSTANTIATE WINDOW CHECKS WITHOUT WINDOW")

        self.add_instant_checks(*instant_checks)
        self.add_window_checks(*window_checks)

        return self

    def _construct_pw_dag(self) -> pw.Table:
        # TODO ADD AN IF AND DO NOT CALL FUNCTION IF THERE ARE NOT INSTANT OR WINDOW DAGS
        self.instant_table = self.__construct_pw_dag_for_instant_checks()
        self.window_table = self.__construct_pw_dag_for_window_checks()
        return self.instant_table, self.window_table

    def __construct_pw_dag_for_instant_checks(self) -> pw.Table: ...

    def __construct_pw_dag_for_window_checks(self) -> pw.Table: ...
