"""The opt-in research test runner is scoped to this checkout."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools import research_validation


ROOT = Path(__file__).resolve().parents[1]


def test_research_runner_requires_the_repository_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="checkout-local"):
        research_validation.main()


def test_research_runner_targets_the_checkout_research_tree(monkeypatch):
    targets = []
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "argv", ["tools.research_validation", "--collect-only"])
    monkeypatch.setattr(pytest, "main", lambda args: targets.append(args) or 0)

    assert research_validation.main() == 0
    assert targets == [[str(ROOT / "research"), "--collect-only"]]
