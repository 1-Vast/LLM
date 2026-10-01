"""Nonbiological contract fixtures; real forwards have separately saved receipts."""
import copy
import json
import subprocess
import sys

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from tools.datasets.state_prospective_input import (
    CONTROL, CONTEXT, KEY, PERT, build_requests, preprocess_new_rna, validate_requests,
)
from tools.datasets.state_panel_contract import validate


@pytest.fixture
def inputs():
    contract = {"axis": ["0:A", "1:B", "2:__UNRESOLVED__"], "feature_count": 3,
                "mapping": {CONTROL: 0, "drug_a": 1, "drug_b": 2},
                "unresolved_coordinates": [2], "new_rna_preprocessing_certified": False}
    baseline = ad.AnnData(obs=pd.DataFrame({PERT: [CONTROL] * 2, "cell_name": [CONTEXT] * 2,
                                           "plate": ["plate1"] * 2, "role": ["baseline_control"] * 2}, index=["c1", "c2"]))
    baseline.obsm[KEY] = np.array([[1, 2, 0], [3, 4, 0]], dtype=np.float32)
    baseline.uns["state_feature_axis"] = np.array(contract["axis"])
    return baseline, contract


def test_builder_preserves_controls_and_keeps_requests_out_of_observations(inputs):
    baseline, contract = inputs
    baseline.obs["future_endpoint"] = [999, -999]
    query = build_requests(baseline, ["drug_a", "drug_b"], 4, contract)
    assert "future_endpoint" not in query.obs
    assert query.obs["role"].value_counts().to_dict() == {"prediction_request": 8, "baseline_control": 2}
    np.testing.assert_array_equal(query.obsm[KEY][:2], baseline.obsm[KEY])
    assert not np.any(query.obsm[KEY][2:])


@pytest.mark.parametrize("mutation,match", [
    ("order", "feature order"), ("context", "context"), ("pool", "matched baseline"),
    ("unknown", "unknown perturbation"), ("controls", "missing baseline"),
    ("role", "observed outcomes"), ("count", "menu/count"),
])
def test_rejects_silent_inference_fallbacks(inputs, mutation, match):
    baseline, contract = inputs
    query = build_requests(baseline, ["drug_a", "drug_b"], 4, contract)
    if mutation == "order":
        query.uns["state_feature_axis"] = query.uns["state_feature_axis"][::-1]
    elif mutation == "context":
        query.obs.loc["prediction_request:0", "cell_name"] = "other"
    elif mutation == "pool":
        query.obs.loc["prediction_request:0", "plate"] = "other"
    elif mutation == "unknown":
        query.obs.loc["prediction_request:0", PERT] = "unknown"
    elif mutation == "controls":
        query = query[2:].copy()
    elif mutation == "role":
        query.obs.loc["prediction_request:0", "role"] = "response_observation"
    else:
        query = query[:-1].copy()
    with pytest.raises(ValueError, match=match):
        validate_requests(query, ["drug_a", "drug_b"], 4, contract)


def test_new_rna_cannot_fill_unnamed_coordinates(inputs):
    _, contract = inputs
    with pytest.raises(ValueError, match="uncertified"):
        preprocess_new_rna(np.ones((1, 3)), ["A", "B", "C"], contract)


def test_future_read_guard_rejects_an_actual_open(tmp_path):
    future = tmp_path / "future.txt"
    future.write_text("DO_NOT_READ", encoding="utf-8")
    code = "from tools.datasets.state_prospective_input import install_outcome_guard; import sys; install_outcome_guard(sys.argv[1], {'outcome_access_attempts': []}); open(sys.argv[1]).read()"
    done = subprocess.run([sys.executable, "-c", code, str(future)], capture_output=True, text=True)
    assert done.returncode != 0
    assert "future outcome access forbidden" in done.stderr
    assert "DO_NOT_READ" not in done.stdout


def panel():
    provenance = dict(source_record_id="fixture", source_file_sha256="f" * 64, source_row="1")
    times = [f"2026-01-01T{h:02d}:00:00+00:00" for h in range(10)]
    common = dict(question_id="q", parent_id="parent", physical_batch="culture")
    data = {k: [] for k in ("questions", "actions", "attempts", "state_samples", "response_samples")}
    data["questions"] = [dict(**common, context=CONTEXT, split="development", state_sample_id="s", decision_at=times[3],
                             expected_attempt_ids=json.dumps(["ctl", "a", "b"]), ledger_evidence="fixture roster")]
    data["state_samples"] = [dict(**common, **provenance, state_sample_id="s", aliquot_id="basal", role="baseline_observation",
                                 collected_at=times[0], processed_at=times[1], available_at=times[2], relation_evidence="fixture split log",
                                 qc_status="pass", cost_CNY="1", waiting_cost_CNY="1")]
    for action in ["ctl", "a", "b"]:
        data["actions"].append(dict(question_id="q", action_id=action, is_control=str(action == "ctl").lower(), control_action_id="ctl", **provenance))
        data["attempts"].append(dict(**common, **provenance, attempt_id=action, action_id=action, aliquot_id=action,
                                     shared_control_group="shared", control_attempt_id="ctl", status="executed", reason="", randomized_at=times[4],
                                     randomization_evidence="fixture RNG receipt", commanded_at=times[5], executed_at=times[6],
                                     execution_evidence="fixture actuator acknowledgement", qc_status="pass", qc_reason="", cost_CNY="1"))
        data["response_samples"].append(dict(**common, **provenance, response_sample_id="r" + action, attempt_id=action,
                                             aliquot_id=action, role="response_observation", collected_at=times[7], available_at=times[8],
                                             qc_status="pass", qc_reason="", observed_value="0", endpoint_id="fixture_endpoint",
                                             control_response_id="rctl", cost_CNY="1"))
    return data


def test_structural_pass_does_not_certify_efficacy():
    report = validate(panel())
    assert report["structural_contract_passed"], report
    assert report["attempts"] == 3
    assert not report["efficacy_ready"]


@pytest.mark.parametrize("table,index,key,value,error", [
    ("state_samples", 0, "available_at", "2026-01-01T04:00:00+00:00", "state_not_available"),
    ("state_samples", 0, "parent_id", "other", "state_parent_batch"),
    ("state_samples", 0, "role", "prediction_request", "prediction_request_in_observations"),
    ("questions", 0, "expected_attempt_ids", '["ctl", "a", "b", "cancelled_missing"]', "incomplete_attempt_denominator"),
    ("attempts", 1, "execution_evidence", "", "command_not_execution"),
    ("attempts", 1, "control_attempt_id", "b", "control_is_treatment"),
    ("attempts", 1, "aliquot_id", "basal", "destructive_RNA_not_same_aliquot"),
    ("attempts", 1, "randomization_evidence", "", "allocation_evidence_missing"),
    ("attempts", 1, "cost_CNY", "inf", "invalid_cost"),
    ("response_samples", 1, "aliquot_id", "other", "response_sample_join"),
    ("response_samples", 1, "collected_at", "2026-01-01T05:00:00+00:00", "response_time_order"),
    ("response_samples", 1, "observed_value", "nan", "nonfinite_observed_response"),
])
def test_panel_detects_identification_contract_breaks(table, index, key, value, error):
    data = panel()
    data[table][index][key] = value
    report = validate(data)
    assert not report["structural_contract_passed"]
    assert any(error in item for item in report["errors"]), report


def test_failed_attempt_kept_in_denominator_without_imputing_response():
    data = panel()
    data["attempts"][2].update(status="cancelled", reason="fixture instrument failure", qc_status="not_run", qc_reason="cancelled before assay")
    data["response_samples"].pop()
    report = validate(data)
    assert report["structural_contract_passed"], report
    assert report["attempts"] == 3
    assert report["missing_valid_response_attempts"] == ["b"]
    assert not report["efficacy_ready"]


def test_shared_control_and_culture_cannot_cross_split():
    data = panel()
    other = copy.deepcopy(data)
    for rows in other.values():
        for row in rows:
            row["question_id"] = "q2"
    for q in other["questions"]:
        q.update(split="test", state_sample_id="s2", expected_attempt_ids='["ctl2", "a2", "b2"]')
    other["state_samples"][0]["state_sample_id"] = "s2"
    for a in other["attempts"]:
        a["attempt_id"] += "2"
        a["control_attempt_id"] = "ctl2"
    for r in other["response_samples"]:
        r["response_sample_id"] += "2"
        r["attempt_id"] += "2"
        r["control_response_id"] = "rctl2"
    for key in data:
        data[key].extend(other[key])
    assert "shared_dependency_crosses_split" in validate(data)["errors"]
