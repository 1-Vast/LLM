"""The opt-in research test runner is scoped to this checkout."""
from __future__ import annotations

import sys
import os
import subprocess
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
    args = targets[0]
    assert args[0] == str(ROOT / "research/astra") and args[-1] == "--collect-only"
    assert f"--ignore={ROOT / 'research/data'}" in args
    assert all(f"--ignore-glob={pattern}" in args for pattern in research_validation.ARCHIVE_GLOBS)


def test_research_runner_can_explicitly_include_archives(monkeypatch):
    targets = []
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "argv", ["tools.research_validation", "--include-archives", "--collect-only"])
    monkeypatch.setattr(pytest, "main", lambda args: targets.append(args) or 0)
    assert research_validation.main() == 0
    assert targets == [[str(ROOT / "research"), "--collect-only"]]


def test_default_collection_excludes_archived_test_copies(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts = ''\n")
    tree = tmp_path / "research"
    for directory in ("astra", "astra/results/frozen", "astra/baseline_20261002", "paused", "data", "experiments"):
        folder = tree / directory
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "test_probe.py").write_text("def test_probe():\n    pass\n")
    script = ("from pathlib import Path; from tools import research_validation as runner; "
              "runner.ROOT=Path.cwd(); raise SystemExit(runner.main())")
    config = tmp_path / "pyproject.toml"
    result = subprocess.run([sys.executable, "-c", script, "-c", str(config), "--collect-only", "-q"], cwd=tmp_path,
                            env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    collected = [line for line in result.stdout.splitlines() if "::" in line]
    assert collected == ["research/astra/test_probe.py::test_probe"]
    assert "results/frozen" not in result.stdout and "baseline_20261002" not in result.stdout
