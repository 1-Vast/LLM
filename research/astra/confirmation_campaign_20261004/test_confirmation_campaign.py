"""Behaviour tests for the confirmation-campaign study's access contract.

File summary
- Path: research/astra/confirmation_campaign_20261004/test_confirmation_campaign.py
- Purpose: pin the rules every workstream relies on: no outcome reading before the campaign
  contract is frozen, a changed frozen file refuses access, every reading is logged with its owner
  and EXPLORATORY label, unknown owners are refused, and the design-only partition keeps
  evaluation lines out of the history set.
- Depends on: pytest; common.py; the frozen feedback-validation builder (synthetic release only).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.astra.confirmation_campaign_20261004.common import HERE, ROOT, exposed_ticket, partition
from research.astra.feedback_validation_20261003.jaaks import synthetic_release
from research.certified_discovery.screens import sha256
from tools.datasets.combination_screens import VaultRefusal

CONTRACT = HERE / "protocol/campaign_contract.json"


def _freeze(tmp_path: Path, digest: str | None = None) -> Path:
    name = CONTRACT.relative_to(ROOT).as_posix()
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps({"files": {name: digest or sha256(CONTRACT)}}), encoding="utf-8")
    return path


def test_reading_is_refused_before_the_contract_is_frozen(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    with pytest.raises(VaultRefusal):
        exposed_ticket("read", "design", source, log_path=tmp_path / "log.jsonl",
                       freeze_path=tmp_path / "missing.json")
    assert not (tmp_path / "log.jsonl").exists()


def test_each_reading_is_logged_with_owner_after_the_freeze(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    log = tmp_path / "log.jsonl"
    freeze = _freeze(tmp_path)
    exposed_ticket("first", "design", source, log_path=log, freeze_path=freeze)
    exposed_ticket("second", "resources", source, log_path=log, freeze_path=freeze)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [r["prior_openings"] for r in rows] == [0, 1]
    assert rows[0]["purpose"].startswith("[design] EXPLORATORY")
    assert rows[1]["purpose"].startswith("[resources] EXPLORATORY")


def test_changed_frozen_file_and_unknown_owner_are_refused(tmp_path: Path):
    source = synthetic_release(tmp_path / "release.csv", seed=1)
    with pytest.raises(VaultRefusal):
        exposed_ticket("read", "design", source, log_path=tmp_path / "log.jsonl",
                       freeze_path=_freeze(tmp_path, "0" * 64))
    with pytest.raises(ValueError, match="UNKNOWN_OWNER"):
        exposed_ticket("read", "someone", source, log_path=tmp_path / "log.jsonl", freeze_path=_freeze(tmp_path))


def test_partition_keeps_evaluation_lines_out_of_history():
    split = partition()
    assert sum(len(v["E"]) for v in split.values()) == 61
    assert sum(len(v["HD"]) for v in split.values()) == 64
    for v in split.values():
        assert not set(v["E"]) & set(v["HD"])
        assert set(v["repeat_lines_E"]) <= set(v["E"]) and set(v["repeat_lines_HD"]) <= set(v["HD"])
