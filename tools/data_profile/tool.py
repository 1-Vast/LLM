"""Adapt approved dataset parameters to the core structure profiler."""
from typing import Any, Mapping

from maestro.tool_analysis import data_profile


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return a versioned structured result without writing dataset files."""
    return data_profile(parameters)
