"""Pinned Cycloop replay; these are original-log diagnostics only."""
import json
from pathlib import Path
import numpy as np
import pytest
from research.astra.state_evidence_followup import control_action
from tools.datasets.state_evidence_followup import sha256

ROOT = Path(__file__).resolve().parents[2]


def test_controller_uses_predecision_reference():
    assert control_action([0.1], 0) == 0
    assert control_action([0.1], 0.2) == 1
    with pytest.raises(ValueError, match="nonfinite"):
        control_action([np.nan], 0)



def test_independent_saved_reconstruction():
    out = ROOT / "tools/datasets/audit_results/20261001_state_evidence_replay_v3"
    report = json.loads((out / "summary.json").read_text())
    totals = report["experiments"]
    assert sum(x["records"] for x in totals) == 2000
    assert sum(x["replayable"] for x in totals) == 1200
    assert sum(x["matches"] for x in totals) == 1200
    assert sum(x["same_row_mismatches"] for x in totals) == 103
    assert sum(x["label_references"] for x in totals) == 245657
    assert sum(x["missing_current_frame_fluorescence"] for x in totals) == 5864
    rows = [json.loads(line) for line in (out / "decisions.jsonl").read_text().splitlines()]
    assert len(rows) == 2000
    assert all(r["state_latest_frame"] < r["response_frame"] for r in rows)
    assert all(r["actuator_ack"] is None and r["qc"] is None for r in rows)
    assert report["state_efficacy_experiment"] is False
    for name, expected in json.loads((out / "outputs_sha256.json").read_text()).items():
        assert sha256(out / name) == expected
