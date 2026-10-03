"""Process boundaries preserve facts and historical views, without biological claims."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from agent.case_store import CaseStore, MeasurementResult
from agent.memory import CaseStore as HistoricalCaseStore, RunLogger
from maestro.handoff import DecisionLayer, EvidenceLayer, ExecutionLayer, RoundRecord, WorldModelLayer
from maestro.models import EvidenceAction


def child(code, root):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    completed = subprocess.run([sys.executable, "-c", code, str(root)], env=environment,
                               capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def setup_case(root):
    store = CaseStore(root / "cases.sqlite")
    store.open_case("case", budget=3)
    actions = tuple(EvidenceAction(name, "Assay", 1, ("a", "b"), time_hours=24,
                                  expected_conditions={"dose": "1 uM"}) for name in ("a", "b"))
    store.record_plan("case", actions, ready_to_measure=True, context_identifier="cells")
    return store


def result(name, qc=True):
    return MeasurementResult(name, "Observed", "fixture:assay", "cells", 24, 2, qc,
                             conditions={"dose": "1 uM"}, result_id=f"result:{name}", plan_version=1)


def test_new_process_receives_original_pending_plan_without_replanning_or_double_charge(tmp_path):
    store = setup_case(tmp_path)
    assert HistoricalCaseStore is CaseStore
    store.start_action("case", 1, "a", attempt_id="attempt:a", source="fixture:receipt")
    code = '''
import json, sys
from pathlib import Path
from agent.case_store import MeasurementResult
from tests.fixtures.orchestration import _controller
root = Path(sys.argv[1])
controller = _controller(root, [])  # a planner/LLM call would exhaust the empty stub
store = controller._case_store
pending = store.pending_actions("case")
r = MeasurementResult("a", "Observed", "fixture:assay", "cells", 24, 2, False,
    conditions={"dose": "1 uM"}, result_id="result:a", plan_version=1)
first = controller.import_measurement("case", r)
retry = controller.import_measurement("case", r)
print(json.dumps({"pending": pending, "created": [first.created, retry.created],
    "remaining": store.pending_actions("case"), "budget": store.budget_status("case")}))
'''
    actual = child(code, tmp_path)
    assert actual["created"] == [True, False]
    assert actual["pending"][0]["attempt_id"] == "attempt:a"
    assert actual["pending"][0]["expected_conditions"] == {"dose": "1 uM"}
    assert [row["action_identifier"] for row in actual["remaining"]] == ["b"]
    assert actual["budget"]["recorded_use"] == 1
    assert actual["budget"]["reserved"] == 1
    valid_code = '''
import json, sys
from pathlib import Path
from agent.case_store import MeasurementResult
from tests.fixtures.orchestration import _controller
controller = _controller(Path(sys.argv[1]), [])
receipt = controller.import_measurement("case", MeasurementResult("b", "Observed", "fixture:assay",
    "cells", 24, 2, True, conditions={"dose": "1 uM"}, result_id="result:b", plan_version=1))
print(json.dumps({"created": receipt.created, "version": receipt.snapshot.plan_version}))
'''
    assert child(valid_code, tmp_path) == {"created": True, "version": 1}
    assert not store.pending_actions("case")
    assert store.snapshot("case").spent == 2
    assert store.snapshot("case").plan_version == 1
    assert store.snapshot("case").state.value == "result_qc_failed"


@pytest.mark.parametrize("revised_first", [True, False])
def test_review_rebuilds_all_saved_results_in_a_new_process(tmp_path, revised_first):
    store = setup_case(tmp_path)
    logger = RunLogger(tmp_path)
    plan = RoundRecord("session", 1, EvidenceLayer(missing_reason=("fixture_no_sources",)), WorldModelLayer.no_model(), DecisionLayer(), ExecutionLayer())
    logger.round(plan, stage="plan", case_id="case", plan_version=1)
    for name, revised in zip(("a", "b"), (revised_first, not revised_first)):
        store.import_measurement("case", result(name))
        view = replace(plan, execution=ExecutionLayer(result_id=f"result:{name}",
                       contradiction_flag=revised, belief_delta={"old-rule-hypothesis": -1} if revised else {}))
        logger.round(view, stage="result", case_id="case", plan_version=1)
        logger.round(view, stage="result", case_id="case", plan_version=1)  # exact receipt retry
    expected = logger.review_case("case", store)
    code = '''
import json, sys
from pathlib import Path
from agent.case_store import CaseStore
from agent.memory import RunLogger
root = Path(sys.argv[1])
print(json.dumps(RunLogger(root).review_case("case", CaseStore(root / "cases.sqlite"))))
'''
    actual = child(code, tmp_path)
    assert actual == json.loads(json.dumps(expected))
    assert actual["result_records"] == 2 and actual["rounds"] == 1
    assert actual["rounds_that_revised_a_judgement"] == 1
    assert actual["judgement_never_changed"] is False
    assert actual["budget"]["recorded_use"] == 2
    path = next((tmp_path / "rounds").glob("*.result.*.json"))
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="hash_mismatch"):
        logger.review_case("case", store)


def test_missing_result_view_is_not_reinterpreted_to_complete_history(tmp_path):
    store = setup_case(tmp_path)
    logger = RunLogger(tmp_path)
    plan = RoundRecord("session", 1, EvidenceLayer(missing_reason=("fixture_no_sources",)), WorldModelLayer.no_model(), DecisionLayer(), ExecutionLayer())
    logger.round(plan, stage="plan", case_id="case", plan_version=1)
    store.import_measurement("case", result("a"))
    with pytest.raises(ValueError, match="incomplete_results"):
        logger.review_case("case", store)


def test_legacy_unbound_view_cannot_claim_a_case_summary(tmp_path):
    store = setup_case(tmp_path)
    logger = RunLogger(tmp_path)
    logger.round(RoundRecord("session", 1, EvidenceLayer(missing_reason=("fixture_no_sources",)), WorldModelLayer.no_model(),
                            DecisionLayer(), ExecutionLayer()), stage="plan")
    with pytest.raises(ValueError, match="binding_missing"):
        logger.review_case("case", store)


@pytest.mark.parametrize("field,value,reason", [
    ("sha256", "wrong", "hash_mismatch"),
    ("plan_version", 2, "binding_conflict"),
    ("result_id", "different", "path_mismatch"),
])
def test_duplicate_audit_receipts_still_validate_every_binding(tmp_path, field, value, reason):
    store = setup_case(tmp_path)
    logger = RunLogger(tmp_path)
    plan = RoundRecord("session", 1, EvidenceLayer(missing_reason=("fixture_no_sources",)),
                       WorldModelLayer.no_model(), DecisionLayer(), ExecutionLayer())
    assert logger.round(plan, stage="plan", case_id="case", plan_version=1)
    store.import_measurement("case", result("a"))
    view = replace(plan, execution=ExecutionLayer(result_id="result:a"))
    assert logger.round(view, stage="result", case_id="case", plan_version=1)
    event = json.loads(logger.events_path.read_text().splitlines()[-1])
    event["payload"][field] = value
    with logger.events_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event) + "\n")
    with pytest.raises(ValueError, match=reason):
        logger.review_case("case", store)
