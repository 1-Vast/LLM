"""Synthetic contract tests only; never biological validation evidence."""
from dataclasses import replace
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("native_replay", Path(__file__).with_name("replay.py"))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def row(identifier="one", drug="drug1", dose=1.0, outcome=2.0):
    return {"condition_id": identifier, "drug": drug, "dose_uM": dose, "cell": "cellA",
        "plate": "plate1", "time_hours": 24.0, "split": "development",
        "reference_prediction": 1.0, "state_prediction": 1.2, "observed_rms": outcome}


def test_condition_identity_and_unsupported_receipts(tmp_path):
    public = r.public_rows([(row(), row("high", dose=10))])
    backend = r.FrozenForecasts(public, "state", "fixture-v1")
    coordinator = r.PredictionCoordinator(backend, r.RunLogger(tmp_path), cache=r.PredictionCache())
    request = r.make_request(row(), "case", 1, "fixture-v1")
    _, answer = coordinator.predict(request, "test")
    assert answer.applicable
    for changed in (replace(request, intervention=replace(request.intervention, dose=3)),
                    replace(request, intervention=replace(request.intervention, time_hours=72)),
                    replace(request, context=replace(request.context, identifier="cellB")),
                    replace(request, readouts=("ATP_viability",)),
                    replace(request, observation_context={**request.observation_context, "model_provenance_sha256": "changed-checkpoint"}),
                    replace(request, observation_context={**request.observation_context, "assay": "ATP"})):
        assert not coordinator.predict(changed, "test")[1].applicable
        assert r.PredictionCache.key_for(changed, backend.name) != r.PredictionCache.key_for(request, backend.name)
    wrong = replace(answer, request_id="other")
    assert r.prediction_request_errors(wrong, request) == ("request_id_mismatch",)


def test_purchase_duplicate_condition_budget_restart(tmp_path):
    store = r.CaseStore(tmp_path / "case.sqlite")
    store.open_case("case", budget=2)
    _, receipt = r.purchase(store, "case", row())
    assert store.import_measurement("case", receipt["result"]).created is False
    assert store.snapshot("case").spent == 1
    with pytest.raises(ValueError, match="different content"):
        store.import_measurement("case", replace(receipt["result"], metrics={r.ENDPOINT: "9"}))
    restarted = r.CaseStore(tmp_path / "case.sqlite")
    assert restarted.snapshot("case").spent == 1
    r.purchase(restarted, "case", row("two"))
    with pytest.raises(ValueError, match="budget_or_plan_refused"):
        r.purchase(restarted, "case", row("three"))
    assert restarted.snapshot("case").spent == 2


def test_result_condition_mismatch(tmp_path):
    store = r.CaseStore(tmp_path / "case.sqlite")
    store.open_case("case", budget=2)
    a = r.action_for(row())
    plan = store.record_plan("case", [a], ready_to_measure=True, context_identifier="cellA")
    bad = r.MeasurementResult(a.identifier, "fixture", "fixture", "cellA", 24, None, True,
        conditions={**a.expected_conditions, "dose_uM": "3.0"}, evidence_kind=r.EvidenceKind.RETRIEVED_SOURCE,
        result_id="bad", plan_version=plan.plan_version)
    with pytest.raises(ValueError):
        store.import_measurement("case", bad)
    assert store.snapshot("case").spent == 0


def test_target_outcomes_absent_policy_and_same_information(tmp_path):
    pair = ((row("alo", "a", outcome=2), row("ahi", "a", 10, 6)),
            (row("blo", "b", outcome=1), row("bhi", "b", 10, 4)))
    transfer = {"slope": 1.0, "unacquired_rmse": 1.0, "acquired_rmse": .5}
    views = []
    def policy(view):
        views.append(view)
        assert all("observed_rms" not in item and "response" not in item for item in view)
        return "alo"
    first = r.replay_pair(pair, "state", transfer, tmp_path / "first", "first", policy)
    second = r.replay_pair(pair, "state", transfer, tmp_path / "second", "second", shared_acquisitions=["alo"])
    assert views
    assert first["final_choice"] == second["final_choice"]
    assert first["policy_view_after_acquisition"] == second["policy_view_after_acquisition"]
    assert first["budget"]["recorded_use"] == second["budget"]["recorded_use"] == 2
    altered = ((pair[0][0], {**pair[0][1], "observed_rms": -100}), pair[1])
    third = r.replay_pair(altered, "state", transfer, tmp_path / "third", "third", policy)
    assert third["final_choice"] == first["final_choice"]
    stopped = r.replay_pair(pair, "state", transfer, tmp_path / "stopped", "stopped",
                           policy=lambda view: (_ for _ in ()).throw(AssertionError("must not call")),
                           shared_acquisitions=[])
    assert stopped["budget"]["recorded_use"] == 1


def test_drug_split_and_train_only_transfer(tmp_path):
    rows = [row("a"), {**row("b"), "split": "evaluation"}]
    path = tmp_path / "records.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    with pytest.raises(ValueError, match="drug_split_leakage"):
        r.load_records(path)
    train = [(dict(row(f"{i}lo", str(i), outcome=2), split="train"),
              dict(row(f"{i}hi", str(i), 10, 3), split="train")) for i in range(3)]
    original = r.fit_transfer(train + [(row("lo"), row("hi", dose=10, outcome=999))], "state")
    changed = r.fit_transfer(train + [(row("lo", outcome=-99), row("hi", dose=10, outcome=-999))], "state")
    assert original == changed
