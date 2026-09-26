"""Adapt a declared measured signature to the reference-library retrieval analysis."""
from typing import Any, Mapping

from virtual_cell.signature_retrieval import signature_retrieval


def run(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Rank the reference classes a measured signature resembles; never a mechanism verdict."""
    return signature_retrieval(parameters)
