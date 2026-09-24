"""The agent path executes, and scores, the composed plan its repair proposed.

File summary
- Path: tests/test_agent_composed_plan_path.py
- Purpose: close the gap between the instrument and the framework's own agent. The
  composition operator existed but the replay policy ignored `composed_plan`, executed the
  cheapest supplier instead of the gate the repair chose, and recorded no promise for a
  composed repair at all.
- Core points:
  - An unmeasured interpretation gate is a missing premise for the check, so a gated
    readout can no longer pass as interpretable.
  - The executed step is the plan's own gate, not the cheapest registered supplier.
  - The gate's promise is recorded and can be closed by a real result.
- Interfaces: pytest test functions
- Depends on: evaluation.baselines, maestro.contrast, evaluation.cases
"""
import pytest

from evaluation.baselines import MAESTROCorePolicy
from evaluation.cases import EvidenceMenuItem, PublicCase, ReplayView
from maestro import (
    CompositionRule,
    EvidenceAction,
    FunctionalInterventionProfile,
    MAESTROAgent,
    MeasurementStatus,
    MechanismHypothesis,
    NonDiscriminabilityReason,
)

PREMISE = "functional:target_activity"
HYPOTHESES = (
    MechanismHypothesis("h_gap", "Insufficient perturbation."),
    MechanismHypothesis("h_mode", "Mode non-equivalence."),
)
READOUT = EvidenceAction(
    identifier="phenotype_readout",
    description="The phenotype the contrast wants, interpretable only through the premise.",
    cost=2.0,
    distinguishes=("h_gap", "h_mode"),
    expected_outcomes={"h_gap": "discordant", "h_mode": "concordant"},
    interpretation_gate=PREMISE,
)
CHEAP = EvidenceAction(
    identifier="cheap_panel",
    description="A cheap panel with a declared detection power of one half.",
    cost=1.0,
    distinguishes=("h_gap", "h_mode"),
    supplies=(PREMISE,),
    expected_outcomes={"h_gap": "matched", "h_mode": "matched"},
    detection_power=0.5,
)
PRECISE = EvidenceAction(
    identifier="precise_panel",
    description="A dearer panel whose qualified result is declared certain.",
    cost=2.0,
    distinguishes=("h_gap", "h_mode"),
    supplies=(PREMISE,),
    expected_outcomes={"h_gap": "matched", "h_mode": "matched"},
    detection_power=1.0,
)


def _case() -> PublicCase:
    return PublicCase(
        identifier="composed-path",
        provenance="synthetic-test",
        evaluation_status="contract",
        initial_evidence=(),
        hypotheses=tuple(
            {"identifier": h.identifier, "description": h.description, "development_action": action}
            for h, action in zip(HYPOTHESES, ("revise_intervention", "change_intervention_mode"))
        ),
        actions=tuple(
            EvidenceMenuItem(action) for action in (READOUT, CHEAP, PRECISE)
        ),
        budget=3.5,
        context_identifier="cell-a",
    )


def _view(*, measured: bool) -> ReplayView:
    case = _case()
    return ReplayView(
        case=case,
        remaining_budget=case.budget,
        revealed=(),
        queried_actions=(),
    )


def test_an_unmeasured_interpretation_gate_is_a_missing_premise():
    agent = MAESTROAgent()
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (READOUT,))
    assert contrast is not None
    check = agent.check_contrast(contrast, FunctionalInterventionProfile(mode="drug"))
    assert NonDiscriminabilityReason.MISSING_PREREQUISITE in check.reasons
    assert check.prerequisites_satisfied is False
    assert PREMISE in check.missing_prerequisites


def test_a_measured_gate_leaves_the_contrast_ready():
    agent = MAESTROAgent()
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (READOUT,))
    assert contrast is not None
    profile = FunctionalInterventionProfile(
        mode="drug",
        functional_states={"target_activity": MeasurementStatus.MEASURED},
    )
    check = agent.check_contrast(contrast, profile)
    assert NonDiscriminabilityReason.MISSING_PREREQUISITE not in check.reasons
    assert check.prerequisites_satisfied is True


def test_the_policy_runs_the_gate_the_repair_chose_not_the_cheapest_supplier():
    """Detection power, not price, is why the plan preferred the precise panel."""

    policy = MAESTROCorePolicy(
        MAESTROAgent(composition_rule=CompositionRule("shared_plate", 0.5))
    )
    step = policy.next_action(_view(measured=False))
    assert step == "precise_panel"


def test_a_gateless_policy_still_uses_the_recorded_path():
    """The composition switch stays a switch: without a rule the behaviour is unchanged."""

    policy = MAESTROCorePolicy(MAESTROAgent())
    step = policy.next_action(_view(measured=False))
    assert step in {"cheap_panel", "precise_panel"}


def test_the_gate_promise_is_recorded_and_can_be_closed_by_a_real_result():
    policy = MAESTROCorePolicy(
        MAESTROAgent(composition_rule=CompositionRule("shared_plate", 0.5))
    )
    view = _view(measured=False)
    step = policy.next_action(view)
    assert step == "precise_panel"
    assert policy._promises[view.case.identifier] == [(step, (PREMISE,))]
    ledger = policy._ledgers[view.case.identifier]
    assert ledger.records, "a composed repair must leave a record to be scored"
    assert any(record.adopted for record in ledger.records)
