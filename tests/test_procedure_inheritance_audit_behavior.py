"""Supplemental behavioral audit: synthetic contracts, no scientific re-run."""
from __future__ import annotations

from collections import Counter
import copy
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/procedure_inheritance_20261020"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE))
import pi_model as M
import pi_fixtures as X
import pi_plan as PL

SPEC = importlib.util.spec_from_file_location("behavior_audit_tested", ROOT / "research/procedure_inheritance_20261020_audit1/audit_behavior.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_exit_metadata_tampering_is_detected_without_truth_or_refit(monkeypatch):
    lib = X.fixture_lib()
    plan = X.branching_plan(lib)
    reference = X.base_a()
    row = M.run_campaign(lib, M.Camp(reference, reference + X.profile(3), T=None), 4, plan, arm="plan")
    def forbidden(*args, **kwargs):
        raise AssertionError("The audit must not score a hidden outcome")
    monkeypatch.setattr(M.Camp, "utility", forbidden)
    monkeypatch.setattr(M.Camp, "oracle", forbidden)
    differences, _ = AUDIT.replay_row(M, lib, plan, reference, 4, row)
    assert differences == []
    altered = copy.deepcopy(row)
    altered.update(exit_unknown=True, unknown_step=1, post_unknown=.999, plan_applicable=False, plan_stop=True, direct_fallback=999)
    differences, _ = AUDIT.replay_row(M, lib, plan, reference, 4, altered)
    assert {d["field"] for d in differences} == {"exit_unknown", "unknown_step", "post_unknown", "plan_applicable", "plan_stop", "direct_fallback"}


@pytest.mark.parametrize("field", ["schema", "exits"])
def test_raw_serialized_content_is_checked_even_when_old_loader_ignores_it(field):
    document = X.branching_plan(X.fixture_lib()).to_json()
    assert AUDIT.raw_plan_errors(document) == []
    if field == "schema":
        document["content"][field] = "different_schema"
    else:
        document["content"][field]["unknown_posterior_u"] = .999
    assert PL.Plan.from_json(document).to_json() != document
    assert "raw content does not match exec_sha" in AUDIT.raw_plan_errors(document)


def test_coordinate_counter_rejects_missing_and_duplicate_backgrounds():
    rows = [{"arm": "f1_plan", "role": "task", "budget_arm": 3, "bg": b, "ckpt": 0, "batch": 1, "contract": "E"} for b in (8, 9)]
    expected = Counter(AUDIT.coordinates(row) for row in rows)
    assert AUDIT.coordinate_errors(rows, expected) == {"missing": [], "extra_or_duplicate": []}
    missing = AUDIT.coordinate_errors(rows[:1], expected)
    assert missing["missing"] and not missing["extra_or_duplicate"]
    replaced = AUDIT.coordinate_errors([rows[0], rows[0]], expected)
    assert replaced["missing"] and replaced["extra_or_duplicate"]


def test_unlogged_read_is_rejected_instead_of_supplied_from_a_world():
    lib = X.fixture_lib()
    plan = X.branching_plan(lib)
    reference = X.base_a()
    row = M.run_campaign(lib, M.Camp(reference, reference + X.profile(3), T=None), 4, plan, arm="plan")
    row["queries"] = row["queries"][1:]
    with pytest.raises(KeyError):
        AUDIT.replay_row(M, lib, plan, reference, 4, row)
