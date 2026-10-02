"""Scientific failure modes of the real-data adapter; constructed fixtures only."""
from dataclasses import replace
import json

import numpy as np
import pandas as pd
import pytest

from research.astra.gdsc_screen import (ACTION_IDS, MENU, assign_split, choose, contrast_mse,
                                      mean_interval, normalize_panel, predictor, save, sha, verify_manifest)
from research.astra.gdsc_replay import choose_from_forecasts, forecast_inputs, bound_state
from research.astra.decision_path import Candidate, DecisionPath
from maestro.models import EvidenceAction, FunctionalInterventionProfile
from agent.memory import CaseStore, MeasurementResult
from research.astra.interface import ExecutionBinding, ScientificQuery, raw_prediction_key


def assay():
    rows = []
    for i, tag in enumerate(["NC-1"]*3 + ["B"]*3):
        rows.append(dict(BARCODE="p1", SCAN_ID=17, POSITION=i, TAG=tag, DRUG_ID=np.nan, CONC=np.nan,
                         INTENSITY=110 if tag == "NC-1" else 10, source_row=i))
    for i, (drug, _, conc) in enumerate(MENU):
        rows.append(dict(BARCODE="p1", SCAN_ID=17, POSITION=i+6, TAG=f"L{i+1}-D1-S", DRUG_ID=drug,
                         CONC=conc, INTENSITY=[60, 120, 10][i], source_row=i+6))
    return pd.DataFrame(rows), pd.DataFrame({"BARCODE": ["p1"], "unit": ["patient1"]})


def test_normalization_keeps_shared_controls_and_untrimmed_negative_utility():
    raw, meta = assay()
    panel, observed, qc = normalize_panel(raw, meta)
    assert panel[ACTION_IDS].to_numpy()[0] == pytest.approx([.5, -.1, 1.])
    assert observed.control_id.nunique() == 1
    assert observed.source_row.tolist() == [6, 7, 8]
    assert qc[0]["eligible"]


@pytest.mark.parametrize("damage", ["missing", "wrong_dose", "duplicate", "fail", "nonfinite", "bad_controls"])
def test_broken_action_support_is_not_imputed(damage):
    raw, meta = assay()
    if damage == "missing": raw = raw.drop(index=7)
    if damage == "wrong_dose": raw.loc[7, "CONC"] = 9.0
    if damage == "duplicate": raw = pd.concat([raw, raw.loc[[7]]])
    if damage == "fail":
        bad = raw.loc[[7]].copy(); bad["TAG"] = "FAIL"; raw = pd.concat([raw, bad])
    if damage == "nonfinite": raw.loc[7, "INTENSITY"] = np.nan
    if damage == "bad_controls": raw.loc[raw.TAG == "B", "INTENSITY"] = 110
    with pytest.raises(ValueError, match="No qualified"):
        normalize_panel(raw, meta)


def test_future_patient_relative_is_excluded_with_date_boundary():
    m = pd.DataFrame({"DATE_CREATED": pd.date_range("2020-01-01", periods=10),
                      "unit": list("abcdefgaij"), "identity_qualified": [True]*10})
    split, _ = assign_split(m)
    assert split.loc[7, "split"] == "excluded_seen_patient_late"
    a = split.loc[split.split == "development"]
    b = split.loc[split.split == "confirmation"]
    assert set(a.unit).isdisjoint(b.unit)
    assert set(a.DATE_CREATED).isdisjoint(b.DATE_CREATED)


def test_prediction_cannot_read_identity_date_or_future_measurement():
    x = pd.DataFrame({"tissue": ["lung", "skin"]*8, "growth": ["Adherent"]*16,
                      "medium": ["RPMI"]*16, "log2_density": np.arange(16)/2})
    y = np.column_stack([np.arange(16)/16, np.ones(16), -np.arange(16)/16])
    model = predictor(("ridge", 1.), True).fit(x, y)
    a = model.predict(x)
    x["INTENSITY"] = np.arange(16)*99999
    x["patient_id"] = "test_identity"; x["BARCODE"] = "999"; x["date_cluster"] = "3000-01-01"
    assert np.array_equal(a, model.predict(x))


def test_common_response_main_effect_does_not_improve_contrast_metric():
    y = np.array([[0, .2, .4], [.5, .3, .1]])
    q = y + np.array([[300.], [-123.]])
    assert contrast_mse(y, q, [1, 1]) == pytest.approx(0, abs=1e-20)
    assert choose(q).tolist() == [2, 0]


def test_duplicated_records_do_not_fake_independent_precision():
    f = pd.DataFrame({"unit": ["a", "b", "c", "d"], "date_cluster": ["d1", "d1", "d2", "d2"]})
    v = np.array([1., -1., .3, -.2])
    one = mean_interval(f, v)
    two = mean_interval(pd.concat([f]*10, ignore_index=True), np.tile(v, 10))
    assert one["mean"] == pytest.approx(two["mean"])
    assert one["se"] == pytest.approx(two["se"])
    assert two["df"] == 1


def test_frozen_input_mutation_fails(tmp_path):
    save(tmp_path / "source.json", {"before": True})
    save(tmp_path / "manifest.json", {"source.json": sha(tmp_path / "source.json")})
    verify_manifest(tmp_path)
    save(tmp_path / "source.json", {"before": False})
    with pytest.raises(ValueError, match="changed"):
        verify_manifest(tmp_path)


def test_forecast_changes_selection_but_unsupported_input_uses_frozen_fallback():
    cs = tuple(Candidate(EvidenceAction(a, "fixture", 1, ())) for a in ACTION_IDS)
    q = {a: {"q": v, "supported": True} for a, v in zip(ACTION_IDS, [.1, .8, .3])}
    assert choose_from_forecasts(cs, q, 0)[0] == cs[1]
    q[ACTION_IDS[1]]["supported"] = False
    assert choose_from_forecasts(cs, q, 0)[0] == cs[0]


def test_replay_binds_actual_shuffled_inputs_and_distinguishes_model_members():
    meta = pd.DataFrame({"BARCODE": list("abcdefgh"), "split": ["confirmation"]*8,
                         "tissue": ["lung"]*4 + ["skin"]*4, "growth": ["Adherent"]*8,
                         "medium": ["RPMI"]*8, "log2_density": np.arange(8, dtype=float)})
    inputs = forecast_inputs(meta)
    assert "log2_density" not in inputs["C"]
    assert not inputs["shuffle"].equals(inputs["CS"])
    for tissue in ["lung", "skin"]:
        a = inputs["CS"].query("tissue == @tissue").log2_density
        b = inputs["shuffle"].query("tissue == @tissue").log2_density
        assert sorted(a) == sorted(b)
    keys = []
    # Even equal feature values must not alias distinct fitted model members.
    for member in ["C", "CS"]:
        state, transform = bound_state(inputs["C"].iloc[0].to_dict(), "p1", member)
        query = ScientificQuery(state, ACTION_IDS[0], "a"*64, "plate1", "panel", "ATP", 96., "continuous")
        binding = ExecutionBinding("b"*64, transform, "c"*64, 1, "fixture")
        keys.append(raw_prediction_key(query, binding))
    assert keys[0] != keys[1]


def test_reveal_checks_actual_conditions_and_never_double_charges(tmp_path):
    store = CaseStore(tmp_path / "cases.sqlite")
    action = EvidenceAction(ACTION_IDS[0], "constructed fixture", 1, (), time_hours=96,
                            expected_conditions={"conc": "2", "scan": "17"})
    core = DecisionPath(store, lambda *args: (Candidate(action),), lambda c, p: c[:1], lambda *args: None)
    planned = core.run("case", FunctionalInterventionProfile("offline", context_identifier="p1"), budget=1)
    store.record_prediction("case", planned.plan_version, action.identifier, "request", {"q": .5})
    fact = MeasurementResult(action.identifier, "constructed assay fixture", "fixture:row6", "p1", 96, None, True,
                             conditions={"conc": "9", "scan": "17"}, result_id="result")
    with pytest.raises(ValueError, match="condition"):
        store.import_measurement("case", fact)
    assert store.snapshot("case").spent == 0
    fact = replace(fact, conditions={"conc": "2", "scan": "17"})
    assert store.import_measurement("case", fact).created
    assert not store.import_measurement("case", fact).created
    assert store.prediction_for_result("case", "result")["request_id"] == "request"
    assert core.run("case", FunctionalInterventionProfile("offline", context_identifier="p1")).status == "stopped"
    assert store.snapshot("case").spent == 1
