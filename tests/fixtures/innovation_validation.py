"""Loader and tiny synthetic streams for the innovation-validation tests (synthetic only; no real outcome file is ever opened here)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "routes" / "observation_acquisition" / "innovation_validation_20261020"
NAMES = ("iv_core", "iv_gates", "iv_search", "iv_conv", "iv_worlds", "iv_stats", "iv_replay", "iv_example", "iv_run", "iv_verify", "iv_post")


def load():
    entry = str(STUDY)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return {n: importlib.import_module(n) for n in NAMES}


def tiny_stream(kind="alias", seed=3, n_drugs=12):
    return load()["iv_worlds"].make_stream(kind, seed, n_drugs=n_drugs)
