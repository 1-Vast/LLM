"""Unit-test the deterministic MAESTROAgent contrast and repair logic.

File summary
- Path: tests/test_maestro_agent.py
- Purpose: Unit-test the deterministic MAESTROAgent contrast and repair logic.
- Core points:
  - Asserts lowest-cost discriminating action selection and deferral handling.
  - Checks contrast construction and check outcomes without any LLM call.
- Interfaces: `test_*` functions
- Depends on: maestro, virtual_cell
"""
from maestro import EvidenceAction, MAESTROAgent, MechanismHypothesis
from maestro.models import DecisionStatus
from virtual_cell import StatePrediction


def test_agent_selects_the_lowest_cost_discriminating_action():
    hypotheses = (
        MechanismHypothesis("functional_gap", "Functional perturbation was incomplete."),
        MechanismHypothesis("mode_mismatch", "Intervention modes are not equivalent."),
    )
    actions = (
        EvidenceAction("expensive", "Broad assay", 100.0, ("functional_gap", "mode_mismatch")),
        EvidenceAction("focused", "Focused assay", 10.0, ("functional_gap", "mode_mismatch")),
    )

    decision = MAESTROAgent().decide(hypotheses, actions)

    assert decision.status is DecisionStatus.NEEDS_EVIDENCE
    assert decision.selected_action is not None
    assert decision.selected_action.identifier == "focused"


def test_agent_defers_when_no_action_can_discriminate():
    hypotheses = (
        MechanismHypothesis("a", "A"),
        MechanismHypothesis("b", "B"),
    )
    action = EvidenceAction("a_only", "A-only readout", 1.0, ("a",))

    decision = MAESTROAgent().decide(hypotheses, (action,))

    assert decision.status is DecisionStatus.DEFERRED
    assert decision.selected_action is None


def test_agent_preserves_the_world_model_applicability_boundary():
    hypotheses = (
        MechanismHypothesis("a", "A"),
        MechanismHypothesis("b", "B"),
    )
    action = EvidenceAction("assay", "Discriminating assay", 1.0, ("a", "b"))
    unavailable = StatePrediction(False, None, None, ("Outside applicability range.",))

    decision = MAESTROAgent().decide(hypotheses, (action,), unavailable)

    assert decision.status is DecisionStatus.NEEDS_EVIDENCE
    assert "outside its applicability range" in decision.rationale
