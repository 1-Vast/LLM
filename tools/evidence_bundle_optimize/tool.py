"""Adapt a declared evidence menu to the existing core selection and composition."""
from typing import Any, Mapping

from maestro.tool_analysis import evidence_bundle_optimize


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return exact fixed-menu selection and separately ranked conditional plans."""
    return evidence_bundle_optimize(parameters)
