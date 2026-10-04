"""Behaviour tests for the reproducible-allocation study's shared access helper.

File summary
- Path: research/astra/reproducible_allocation_20261003/test_reproducible_allocation.py
- Purpose: pin the exposed-data access contract every workstream uses: each reading is logged
  with its owner and EXPLORATORY label, unknown owners are refused, a changed frozen file
  refuses access, and the returned ticket is accepted by the frozen panel builder only for the
  file it was issued for.
- Depends on: pytest; common.py; the frozen feedback-validation builder (synthetic release only).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.astra.feedback_validation_20261003.jaaks import build_panels, synthetic_release
from research.astra.reproducible_allocation_20261003.common import PRIOR_FREEZE, exposed_ticket
from tools.datasets.combination_screens import VaultRefusal


def test_each_reading_is_logged_with_owner_and_exploratory_label(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    log = tmp_path / "access.jsonl"
    first = exposed_ticket("first read", "allocation", source, log_path=log)
    second = exposed_ticket("second read", "repeats", source, log_path=log)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [r["prior_openings"] for r in rows] == [0, 1]
    assert rows[0]["purpose"].startswith("[allocation] EXPLORATORY")
    assert rows[1]["purpose"].startswith("[repeats] EXPLORATORY")
    assert first["data_sha256"] == second["data_sha256"]


def test_unknown_owner_is_refused_before_logging(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    log = tmp_path / "access.jsonl"
    with pytest.raises(ValueError, match="UNKNOWN_OWNER"):
        exposed_ticket("read", "someone", source, log_path=log)
    assert not log.exists()


def test_changed_frozen_file_refuses_access(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    freeze = json.loads(PRIOR_FREEZE.read_text(encoding="utf-8"))
    name = next(iter(freeze["files"]))
    freeze["files"][name] = "0" * 64
    tampered = tmp_path / "freeze.json"
    tampered.write_text(json.dumps(freeze), encoding="utf-8")
    with pytest.raises(VaultRefusal):
        exposed_ticket("read", "parent", source, log_path=tmp_path / "access.jsonl", freeze_path=tampered)


def test_ticket_opens_only_the_file_it_was_issued_for(tmp_path: Path):
    one = synthetic_release(tmp_path / "one.csv", seed=1)
    two = synthetic_release(tmp_path / "two.csv", seed=2)
    ticket = exposed_ticket("read", "parent", one, log_path=tmp_path / "access.jsonl")
    panels, report, _ = build_panels(ticket, one)
    assert panels and all(p["plate_overlap"] == 0 for p in report["panels"].values())
    with pytest.raises(PermissionError, match="VAULT_SEALED"):
        build_panels(ticket, two)
