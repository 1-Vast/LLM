"""Adapt approved column parameters to the core descriptive analysis."""
from typing import Any, Mapping

from maestro.tool_analysis import column_summary


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return a versioned summary, not an independent-sample claim."""
    return column_summary(parameters)
