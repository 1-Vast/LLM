"""Adapt declared typed modality records to the core pairing QC analysis."""
from typing import Any, Mapping

from maestro.tool_analysis import multimodal_alignment


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return pairing QC and review candidates without substituting quantities."""
    return multimodal_alignment(parameters)
