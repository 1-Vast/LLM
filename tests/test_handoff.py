"""The four-layer round: structured handoffs, mandatory fields, run-level review.

File summary
- Path: tests/test_handoff.py
- Purpose: pin the section-30 contract — layers exchange structured records, three fields
  are mandatory, an incomplete round is refused rather than written, and a run that never
  sets the contradiction flag reports that as a finding.
- Core points: assertions here are contract tests, not biological results.
- Interfaces: `test_in_distribution_is_mandatory()`, `test_abstention_must_name_a_reason()`,
  `test_rejected_candidates_carry_reasons_and_are_never_chosen()`,
  `test_contradiction_requires_a_belief_delta()`, `test_write_round_refuses_an_incomplete_record()`,
  `test_review_run_reports_a_run_that_never_revised()`,
  `test_selection_reasons_are_named_for_every_candidate()`,
  `test_orchestrator_writes_a_plan_round_with_the_mandatory_fields()`
- Depends on: maestro.handoff, agent
"""
import json
import hashlib
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path

import pytest

from agent.memory import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.llm import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.handoff import (
    ComparabilityStatus,
    DecisionLayer,
    EvidenceLayer,
    ExecutionLayer,
    RejectedCandidate,
    RoundRecord,
    WorldModelLayer,
    rejected_from_selection,
    review_run,
    write_round,
)

from tests.fixtures.stub_client import StubClient  # noqa: E402
def _round(
    *,
    world_model: WorldModelLayer | None = None,
    decision: DecisionLayer | None = None,
    execution: ExecutionLayer | None = None,
) -> RoundRecord:
    return RoundRecord(
        session_id="session-1",
        round_index=1,
        evidence=EvidenceLayer(
            records=("evidence-1",),
            conflicts=("a", "b"),
            comparability_status=ComparabilityStatus.COMPARABLE,
        ),
        world_model=world_model or WorldModelLayer(in_distribution=False, abstain_reason="no_model"),
        decision=decision or DecisionLayer(chosen=("act-1",), rationale="ready_for_mechanism_update"),
        execution=execution or ExecutionLayer(stop_decision="planned_pending_result"),
    )


def test_in_distribution_is_mandatory():
    with pytest.raises(ValueError, match="l2_in_distribution_missing"):
        _round(world_model=WorldModelLayer(in_distribution=None)).validate()


def test_abstention_must_name_a_reason():
    record = _round(world_model=WorldModelLayer(in_distribution=False))
    assert "l2_abstention_without_reason" in record.problems()
    with pytest.raises(ValueError):
        record.validate()
    world_model = WorldModelLayer(in_distribution=False, abstain_reason="out_of_domain")
    assert world_model.problems() == ()
    assert "l2_in_distribution_without_mean" in WorldModelLayer(
        in_distribution=True, interval=None
    ).problems()


def test_rejected_candidates_carry_reasons_and_are_never_chosen():
    decision = DecisionLayer(
        chosen=("act-1",),
        rejected=(RejectedCandidate("act-1", "waiting_for_prerequisite"), RejectedCandidate("act-2", "  ")),
        rationale="ready",
    )
    problems = decision.problems()
    assert "l3_rejected_and_chosen:act-1" in problems
    assert "l3_rejected_without_reason:act-2" in problems
    assert "l3_defer_with_execution" in DecisionLayer(chosen=("act-1",), defer_flag=True).problems()


def test_contradiction_requires_a_belief_delta():
    assert "l4_contradiction_without_belief_delta" in ExecutionLayer(contradiction_flag=True).problems()
    assert "l4_observation_without_result_id" in ExecutionLayer(observed={"x": 1.0}).problems()


def test_write_round_refuses_an_incomplete_record(tmp_path: Path):
    path = tmp_path / "rounds" / "session-1.plan.json"
    with pytest.raises(ValueError):
        write_round(path, _round(world_model=WorldModelLayer(in_distribution=None)))
    assert not path.exists()

    digest = write_round(path, _round())
    assert len(digest) == 64
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "maestro.round.v1"
    layers = payload["layers"]
    assert layers["L2_world_model"]["in_distribution"] is False
    assert layers["L2_world_model"]["abstain_reason"] == "no_model"
    assert layers["L3_decision"]["rejected"] == []
    assert layers["L4_execution"]["contradiction_flag"] is False


@pytest.mark.parametrize("stage,kind", [("plan", "round_record_written"), ("result", "round_result_recorded")])
def test_run_logger_preserves_round_bytes_and_event_identity(tmp_path, stage, kind):
    record = _round(execution=ExecutionLayer(observed={"readout": 1.0}, result_id="r1",
                                          stop_decision="result_imported:act-1"))
    expected = tmp_path / "expected.json"
    digest = write_round(expected, record)
    logger = RunLogger(tmp_path / "log")
    assert logger.round(record, stage=stage)
    path, = (logger.root / "rounds").glob(f"session-1.{stage}*.json")
    assert path.read_bytes() == expected.read_bytes()
    event, = map(json.loads, logger.events_path.read_text().splitlines())
    assert event["kind"] == kind and event["session_id"] == "session-1"
    assert event["payload"]["sha256"] == digest
    if stage == "result":
        assert event["payload"]["result_id"] == "r1"
    else:
        assert event["payload"]["layers"] == 4


def test_run_logger_refuses_incomplete_round_without_creating_a_file(tmp_path):
    logger = RunLogger(tmp_path)
    assert not logger.round(_round(world_model=WorldModelLayer(in_distribution=None)), stage="plan")
    assert not (tmp_path / "rounds/session-1.plan.json").exists()
    event, = map(json.loads, logger.events_path.read_text().splitlines())
    assert event["kind"] == "round_record_rejected"
    assert "l2_in_distribution_missing" in event["payload"]["reason"]


@pytest.mark.parametrize("revised_first", [True, False])
def test_multiple_results_keep_receipt_hashes_and_all_revisions(tmp_path, revised_first):
    controller = object.__new__(MAESTROOrchestrator)
    controller._logger = RunLogger(tmp_path)
    controller._round_records = {"session-1": _round()}
    controller._round_results = {}
    turn = SimpleNamespace(session_id="session-1")
    records = []
    for index, revised in enumerate((revised_first, not revised_first)):
        result_id = f"result:{index}"
        admission = SimpleNamespace(result_id=result_id, admitted_fields=(), admissible=True)
        state = SimpleNamespace(updates=[SimpleNamespace(result_id=result_id,
                                                         eliminated=("a",) if revised else ())])
        records.append(controller._write_result_round(turn, SimpleNamespace(identifier=f"act-{index}"),
            SimpleNamespace(metrics={"shared_readout": float(index)}), admission, state, result_id=result_id))
    events = [json.loads(line) for line in controller._logger.events_path.read_text().splitlines()]
    assert len({event["payload"]["path"] for event in events}) == 2
    for event in events:
        path = Path(event["payload"]["path"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == event["payload"]["sha256"]
    cached = tuple(controller._round_results["session-1"].values())
    assert cached == tuple(records)
    assert [record.execution.observed["shared_readout"] for record in cached] == [0.0, 1.0]
    review = review_run(cached)
    assert review["rounds"] == 1 and review["rounds_with_a_result"] == 1
    assert review["result_records"] == 2
    assert review["rounds_that_revised_a_judgement"] == 1
    assert review["judgement_never_changed"] is False


def test_result_receipt_retry_is_identical_and_conflict_cannot_overwrite(tmp_path):
    logger = RunLogger(tmp_path)
    record = _round(execution=ExecutionLayer(result_id="r:/1", observed={"readout": 1.0}))
    assert logger.round(record, stage="result")
    event = json.loads(logger.events_path.read_text().splitlines()[0])
    path = Path(event["payload"]["path"])
    original = path.read_bytes()
    assert logger.round(record, stage="result")
    assert not logger.round(replace(record, execution=replace(record.execution, observed={"readout": 2.0})),
                            stage="result")
    assert path.read_bytes() == original


def test_review_run_reports_a_run_that_never_revised():
    planned = _round()
    executed = _round(
        execution=ExecutionLayer(observed={"readout": 1.0}, result_id="result-1", stop_decision="result_imported")
    )
    review = review_run((planned, executed))
    assert review["rounds"] == 1
    assert review["rounds_with_a_result"] == 1
    assert review["judgement_never_changed"] is True

    revised = _round(
        execution=ExecutionLayer(
            observed={"readout": 1.0},
            belief_delta={"a": -1.0},
            contradiction_flag=True,
            result_id="result-1",
        )
    )
    assert review_run((planned, revised))["judgement_never_changed"] is False
    assert review_run(())["judgement_never_changed"] is False


def test_selection_reasons_are_named_for_every_candidate():
    rejected = rejected_from_selection(
        ("act-1", "act-2", "act-3", "act-4"),
        ("act-1",),
        waiting=("act-2: functional:target_activity",),
        budget_exceeded=("act-3",),
    )
    reasons = {item.action_identifier: item.reason for item in rejected}
    assert reasons == {
        "act-2": "waiting_for_prerequisite:functional:target_activity",
        "act-3": "exceeds_budget",
        "act-4": "not_selected_by_selector",
    }


def test_orchestrator_writes_a_plan_round_with_the_mandatory_fields(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis",
                "research_question": "Resolve discrepancy.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell line",
                "phenotype_endpoint": "viability",
                "supplied_evidence": [],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "identifier": "contrast",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["readout"],
                "action_identifier": "act-1",
                "outcome_categories": ["a", "b"],
                "interpretation_boundaries": ["A declaration is not a result."],
            },
        ]
    )
    root = tmp_path / "log" / "20260914"
    memory = MemoryStore(root / "memory.sqlite")
    orchestrator = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        virtual_cell=None,
    )
    turn = orchestrator.run(
        "Resolve discrepancy.",
        available_actions=(
            EvidenceAction("act-1", "Assay one.", 1.0, ("a", "b")),
            EvidenceAction("act-2", "Assay two.", 1.0, ("a", "b"), prerequisites=("functional:target_activity",)),
        ),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
    )

    path = root / "rounds" / f"{turn.session_id}.plan.json"
    assert path.is_file()
    layers = json.loads(path.read_text(encoding="utf-8"))["layers"]
    assert layers["L2_world_model"]["in_distribution"] is False
    assert layers["L2_world_model"]["abstain_reason"] == "no_world_model_registered"
    rejected = {item["action"]: item["reason"] for item in layers["L3_decision"]["rejected"]}
    assert rejected.get("act-2", "").startswith("waiting_for_prerequisite")
    assert layers["L4_execution"]["contradiction_flag"] is False
