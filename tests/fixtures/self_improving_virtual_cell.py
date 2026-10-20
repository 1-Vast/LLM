"""Loader for the self-improving virtual-cell prototype (synthetic software tests only; no biological meaning)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "self_improving_virtual_cell_20261020"


def load():
    entry = str(STUDY)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return {n: importlib.import_module(n) for n in ("svc_world", "svc_programs", "svc_evolution", "svc_study", "svc_summarize", "svc_llm")}
