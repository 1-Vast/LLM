"""Expected-coverage selection: declared detection power changes the chosen bundle.

File summary
- Path: tests/test_acquisition.py
- Purpose: pin the stochastic set-cover objective — a noisy wide assay can lose to a certain
  narrow one, a missing detection power is treated as certain *and named*, blocked actions are
  reported as blocked, and an exhausted pool returns `too_large` instead of a heuristic answer.
- Core points: assertions here are contract tests, not biological results.
- Interfaces: `test_a_certain_narrow_bundle_beats_a_noisy_wide_one()`,
  `test_absent_detection_power_is_assumed_certain_and_named()`,
  `test_blocked_and_unaffordable_actions_are_named()`,
  `test_coverage_threshold_separates_named_from_probable_coverage()`,
  `test_a_pool_above_the_cap_is_refused_rather_than_approximated()`,
  `test_orchestrator_can_select_by_expected_coverage()`
- Depends on: maestro.acquisition
"""
import json
from pathlib import Path

import pytest

from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MeasurementStatus
from maestro import MAESTROAgent
from maestro.acquisition import MAXIMUM_CANDIDATES, select_expected_coverage


def _action(
    identifier: str,
    *,
    distinguishes: tuple[str, ...],
    cost: float,
    power: float | None = None,
    prerequisites: tuple[str, ...] = (),
) -> EvidenceAction:
    return EvidenceAction(
        identifier=identifier,
        description=f"{identifier} assay",
        cost=cost,
        distinguishes=distinguishes,
        prerequisites=prerequisites,
        detection_power=power,
    )


def test_a_certain_narrow_bundle_beats_a_noisy_wide_one():
    profile = FunctionalInterventionProfile(mode="inhibition")
    noisy = _action("noisy-wide", distinguishes=("a", "b"), cost=1.0, power=0.4)
    certain = _action("certain-narrow", distinguishes=("a",), cost=1.0, power=1.0)
    plan = select_expected_coverage(
        frozenset({"a", "b"}), (noisy, certain), profile, budget=1.0
    )
    # Expected coverage: noisy-wide = 0.4 + 0.4 = 0.8; certain-narrow = 1.0 + 0.0 = 1.0.
    assert plan.expected_coverage == pytest.approx(1.0)
    assert plan.plan.actions[0].identifier == "certain-narrow"
    assert plan.probability_of("b") == 0.0
    assert {item.action_identifier for item in plan.rejected} == {"noisy-wide"}

    with_two = select_expected_coverage(frozenset({"a", "b"}), (noisy, certain), profile, budget=2.0)
    assert {action.identifier for action in with_two.plan.actions} == {"noisy-wide", "certain-narrow"}
    assert with_two.expected_coverage == pytest.approx(1.4)
    assert with_two.probability_of("b") == pytest.approx(0.4)


def test_absent_detection_power_is_assumed_certain_and_named():
    profile = FunctionalInterventionProfile(mode="inhibition")
    undeclared = _action("undeclared", distinguishes=("a",), cost=1.0)
    plan = select_expected_coverage(frozenset({"a"}), (undeclared,), profile, budget=1.0)
    assert plan.coverage_probability["a"] == 1.0
    assert plan.assumptions == ("assumed_certain_execution:undeclared",)


def test_blocked_and_unaffordable_actions_are_named():
    profile = FunctionalInterventionProfile(mode="inhibition")
    chosen = _action("certain", distinguishes=("a",), cost=1.0, power=1.0)
    blocked = _action(
        "blocked",
        distinguishes=("b",),
        cost=1.0,
        power=1.0,
        prerequisites=("functional:target_activity",),
    )
    costly = _action("costly", distinguishes=("b",), cost=5.0, power=1.0)
    plan = select_expected_coverage(
        frozenset({"a", "b"}), (chosen, blocked, costly), profile, budget=2.0
    )
    reasons = {item.action_identifier: item.reason for item in plan.rejected}
    assert reasons["blocked"] == "waiting_for_prerequisite:functional:target_activity"
    assert reasons["costly"] == "exceeds_budget"
    assert plan.plan.waiting_for_prerequisites == ("blocked: functional:target_activity",)

    measured = FunctionalInterventionProfile(
        mode="inhibition", functional_states={"target_activity": MeasurementStatus.MEASURED}
    )
    unblocked = select_expected_coverage(
        frozenset({"a", "b"}), (chosen, blocked, costly), measured, budget=5.0
    )
    assert {action.identifier for action in unblocked.plan.actions} == {"certain", "blocked"}


def test_coverage_threshold_separates_named_from_probable_coverage():
    profile = FunctionalInterventionProfile(mode="inhibition")
    weak = _action("weak", distinguishes=("a", "b"), cost=1.0, power=0.05)
    plan = select_expected_coverage(
        frozenset({"a", "b"}), (weak,), profile, budget=1.0, coverage_threshold=0.5
    )
    assert plan.plan.covered == frozenset()
    assert plan.plan.uncovered == frozenset({"a", "b"})
    assert plan.probability_of("a") == pytest.approx(0.05)
    assert plan.expected_coverage == pytest.approx(0.10)


def test_a_pool_above_the_cap_is_refused_rather_than_approximated():
    profile = FunctionalInterventionProfile(mode="inhibition")
    actions = tuple(
        _action(f"act-{index:02d}", distinguishes=("a",), cost=1.0, power=1.0)
        for index in range(MAXIMUM_CANDIDATES + 1)
    )
    plan = select_expected_coverage(frozenset({"a"}), actions, profile, budget=1.0)
    assert plan.status == "too_large"
    assert plan.plan.actions == ()
    assert set(plan.plan.rejection_reasons.values()) == {"exact_candidate_limit_exceeded"}
    assert "exact enumeration stops at 16" in (plan.reason or "")

    with pytest.raises(ValueError):
        select_expected_coverage(frozenset({"a"}), actions, profile, budget=-1.0)


class _StubClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def complete_json(self, messages, **kwargs):
        return self.responses.pop(0), object()


def test_orchestrator_can_select_by_expected_coverage(tmp_path: Path):
    client = _StubClient(
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
                "action_identifier": "noisy-wide",
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
        power_aware_selection=True,
    )
    orchestrator.run(
        "Resolve discrepancy.",
        available_actions=(
            EvidenceAction("noisy-wide", "Noisy wide assay.", 1.0, ("a", "b"), detection_power=0.4),
            EvidenceAction("certain-narrow", "Certain narrow assay.", 1.0, ("a",), detection_power=1.0),
        ),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        budget=1.0,
    )

    events = [
        json.loads(line)
        for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selection = next(
        event for event in events if event["kind"] == "expected_coverage_selection_completed"
    )
    assert selection["payload"]["selected_action_ids"] == ["certain-narrow"]
    assert selection["payload"]["expected_coverage"] == pytest.approx(1.0)
    assert selection["payload"]["coverage_probability"]["b"] == 0.0
    reasons = {item["action"]: item["reason"] for item in selection["payload"]["rejected"]}
    assert reasons["noisy-wide"] == "exceeds_budget"


def test_orchestrator_handoff_preserves_the_exact_candidate_limit(tmp_path: Path):
    client = _StubClient(
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
                "action_identifier": "act-00",
                "outcome_categories": ["a", "b"],
                "interpretation_boundaries": ["A declaration is not a result."],
            },
        ]
    )
    root = tmp_path / "log" / "20260915"
    memory = MemoryStore(root / "memory.sqlite")
    orchestrator = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        power_aware_selection=True,
    )
    actions = tuple(
        EvidenceAction(f"act-{index:02d}", "Assay.", 1.0, ("a", "b"), detection_power=1.0)
        for index in range(MAXIMUM_CANDIDATES + 1)
    )

    turn = orchestrator.run(
        "Resolve discrepancy.", available_actions=actions,
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"), budget=1.0,
    )

    payload = json.loads(next((root / "rounds").glob("*.plan.json")).read_text(encoding="utf-8"))
    rejected = payload["layers"]["L3_decision"]["rejected"]
    assert turn.selected_actions == ()
    assert len(rejected) == MAXIMUM_CANDIDATES + 1
    assert {item["reason"] for item in rejected} == {"exact_candidate_limit_exceeded"}
