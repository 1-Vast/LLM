"""Adapt an approved declarative condition to the core table filter."""
from typing import Any, Mapping

from maestro.tool_analysis import table_filter


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return a bounded row sample without arbitrary expressions or writes."""
    return table_filter(parameters)
