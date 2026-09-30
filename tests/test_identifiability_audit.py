"""Contract tests for the 2026-09-30 task identifiability and dual-core influence audit.

File summary
- Path: tests/test_identifiability_audit.py
- Purpose: pin the invariants the audit's conclusions rest on, so a later change to a frozen
  artifact, a scorer or the STATE query path cannot silently move them.
- Core points:
  - The frozen e_data1 tables must carry every menu action for every episode; the audit's
    "no missing action" claim depends on it.
  - The unified must-act correct-rate gap must reproduce the registered headroom number, so the
    scorer unification is shown to be faithful rather than a new estimator.
  - The STATE sensitivity result is a byte-level claim about the predicted embedding, not about
    file names or summary numbers.
  - Every test skips when the artifact it reads is absent, so the audit can be re-run without them.
- Interfaces: `test_e_data1_tables_carry_the_whole_menu`, `test_unified_gap_reproduces_registered_headroom`,
  `test_state_shift_is_invariant_to_target_expression_and_batch`, `test_state_refuses_a_missing_target_row`
- Depends on: outputs/identifiability_audit_20260930, outputs/protocol_v2_1_20260927
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
AUDIT = ROOT / "outputs" / "identifiability_audit_20260930"
FROZEN = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1"


def _tables(prefix: str) -> list:
    paths = sorted((FROZEN / "tables").glob(f"{prefix}_*.jsonl.gz"))
    if not paths:
        pytest.skip(f"no frozen e_data1 tables for {prefix}")
    rows = []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)
    return rows


@pytest.mark.parametrize("prefix,menu", (("sciplex3_B", 12), ("l1000_LT", 8)))
def test_e_data1_tables_carry_the_whole_menu(prefix: str, menu: int):
    """No episode may silently drop a menu action; the coverage audit rests on this."""

    rows = _tables(prefix)
    assert rows, f"no episodes for {prefix}"
    sizes = {len(row["outcomes"]) for row in rows}
    assert sizes == {menu}, f"{prefix}: episode tables do not carry the whole menu: {sizes}"
    assert all(row["unplanned_tier_conditions"] == 0 for row in rows)


def test_unified_gap_reproduces_registered_headroom():
    """The unified must-act correct-rate gap must equal the registered protocol number."""

    path = AUDIT / "unified_score" / "unified_score.json"
    if not path.is_file():
        pytest.skip("unified score artifact absent")
    report = json.loads(path.read_text(encoding="utf-8"))
    for task in ("sciplex3:B", "l1000:LT"):
        registered = report["original_protocol_replay"][task]["oracle_minus_fixed_star_correct"]["difference"]
        recomputed = report["tasks"][task]["within_rule_action_gap_correct_rate"]["difference"]
        assert abs(recomputed - registered) < 5e-4, f"{task}: unified gap moved: {recomputed} vs {registered}"


def test_state_shift_is_invariant_to_target_expression_and_batch():
    """Target-row expression and batch labels must not enter the served shift."""

    path = AUDIT / "state_sensitivity" / "output_embedding_identity.json"
    if not path.is_file():
        pytest.skip("state sensitivity artifact absent")
    arms = {row["arm"]: row["embedding_sha256"] for row in json.loads(path.read_text(encoding="utf-8"))["arms"]}
    if "baseline" not in arms:
        pytest.skip("state baseline prediction absent")
    for name in ("target_expression_permuted", "target_expression_from_control",
                 "target_plate_single", "target_plate_unseen"):
        assert arms.get(name) == arms["baseline"], f"{name}: served embedding changed"


def test_state_refuses_a_missing_target_row():
    """Deleting the target rows is an interface refusal, not a prediction of no effect."""

    path = AUDIT / "state_sensitivity" / "state_sensitivity.json"
    if not path.is_file():
        pytest.skip("state sensitivity artifact absent")
    record = json.loads(path.read_text(encoding="utf-8"))["records"]["target_rows_deleted"]
    assert record["served"] is False
    assert record["refusal"] == "unsupported_query"
    assert record["refusal_class"] == "interface_refusal"


def test_task_summary_reports_a_verdict_for_every_task():
    path = AUDIT / "task_summary" / "task_summary.json"
    if not path.is_file():
        pytest.skip("task summary artifact absent")
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) >= 3, "task summary does not cover the three tasks"
    verdicts = {row["task"]: row["verdict"] for row in rows}
    assert set(verdicts.values()) <= {"comparable", "bounds_only", "replay_only"}
    assert all(row["verdict_reason"] for row in rows)
