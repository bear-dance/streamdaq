from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar

import pathway as pw

from streamdaq.checks.base import DataQualityCheck
from streamdaq.measures.base import DataQualityMeasure
from streamdaq.translators.string_to_callable import string_to_callable
from streamdaq.utils.data_type_applicability import DataTypeApplicability


@dataclass
class WindowDataQualityCheck(DataQualityCheck):
    measure: DataQualityMeasure
    must_be: Callable[[Any], bool] | str
    _applicability: ClassVar[DataTypeApplicability] = DataTypeApplicability.ANY_COLUMN

    def __post_init__(self):
        if isinstance(self.must_be, Callable):
            return

        self.must_be = string_to_callable(str(self.must_be))

    def get_reducer(self) -> pw.ColumnExpression:
        # TODO THINK THROUGH THIS REDUCER A BIT MORE HOW TO GET THE MEASURE COLUMN NAME
        # probably something like pw.apply_with_type(must_be, bool, pw.this["measure_name"])
        # for now the only blocker is to get the measure name in a structured way
        return pw.apply_with_type(
            lambda value: self.must_be(len(str(value))), bool, pw.this[self.column]
        )
