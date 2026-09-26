"""Adapt a recorded Typed Jev review to the advisory audit analysis."""
from typing import Any, Mapping

from maestro.tool_analysis import typed_decision_review


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a review artifact without calling a provider or changing a decision."""
    return typed_decision_review(parameters)
