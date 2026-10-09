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


def test_research_runner_targets_only_the_current_studies(monkeypatch):
    targets = []
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "argv", ["tools.research_validation", "--collect-only"])
    monkeypatch.setattr(pytest, "main", lambda args: targets.append(args) or 0)

    assert research_validation.main() == 0
    args = targets[0]
    expected = [str(ROOT / path) for path in research_validation.DEFAULT_TARGETS]
    assert args == [*expected, "--collect-only"]


def test_research_verification_preflight_reports_missing_assets(tmp_path):
    for study, _ in research_validation.STUDIES:
        path = tmp_path / study
        path.mkdir(parents=True)
        (path / "FREEZE.json").write_text('{"inputs": {}}', encoding="utf-8")

    blocked = research_validation.blocked_assets(tmp_path)
    assert blocked == sorted(result for _, result in research_validation.STUDIES)
