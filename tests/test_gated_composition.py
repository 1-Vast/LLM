"""Interpretation gates and shared-control composition, pinned before the claim they support.

File summary
- Path: tests/test_gated_composition.py
- Purpose: Pin the semantics of an uninterpretable success and of a composed plan, and pin the two separations the reference reports.
- Core points:
  - A gated readout is legal without its premise and returns a qualified outcome that moves no belief; the grammar could not express that before.
  - The exact optimal policy over the menu is strictly worse than the exact optimal policy over the closure, and a zero-saving control attributes the difference to the declared saving.
  - The controller returns a plan rather than an action for this failure, and the plan's readout is the one the contrast already wanted.
- Interfaces: evaluation.adaptive_reference, evaluation.composition, maestro.composition, maestro.contrast
- Depends on: src/
"""
import pytest

from evaluation.adaptive_reference import (
    AdaptiveAction,
    DecisionProblem,
    legal,
    posterior,
    solve_optimal_policy,
)
from evaluation.composition import composition_closure, menu_only
from maestro import (
    CompositionRule,
    ContrastCheck,
    DevelopmentAction,
    EvidenceAction,
    EvidenceScope,
    GatedEvidencePlan,
    MAESTROAgent,
    MechanismHypothesis,
    NonDiscriminabilityReason,
    PlanAuthorization,
    PlanComposer,
    RepairKind,
    RepairProposal,
    composition_is_legal,
    rank_plans,
)

TWO = ("realised", "not_realised")
PREMISE = "functional:target_activity"
HYPOTHESES = (
    MechanismHypothesis("h_gap", "Insufficient perturbation.", DevelopmentAction.REVISE_INTERVENTION),
    MechanismHypothesis("h_mode", "Mode non-equivalence.", DevelopmentAction.CHANGE_INTERVENTION_MODE),
)


def _problem(actions, budget, *, prior=None, identifier="gated") -> DecisionProblem:
    return DecisionProblem(
        identifier=identifier,
        hypotheses=TWO,
        prior=prior or {"realised": 0.5, "not_realised": 0.5},
        actions=tuple(actions),
        budget=budget,
        decisions=("continue", "revise_intervention", "defer"),
        loss={
            "continue": {"realised": 0.0, "not_realised": 10.0},
            "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
            "defer": {"realised": 4.0, "not_realised": 4.0},
        },
    )


def _premise_action(*, fails=False, cost=1.0) -> AdaptiveAction:
    model = (
        {h: {"matched": 0.9, "mismatched": 0.1} for h in TWO}
        if fails
        else {h: {"matched": 1.0} for h in TWO}
    )
    return AdaptiveAction(
        identifier="exposure_panel",
        cost=cost,
        outcome_model=model,
        supplies={"matched": (PREMISE,), "mismatched": ()},
        role="premise_supplier",
    )


def _gated_readout(*, cost=3.0, gate=PREMISE) -> AdaptiveAction:
    return AdaptiveAction(
        identifier="phenotype_readout",
        cost=cost,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        prerequisites=(),
        supplies={"high": ("phenotype:discordant",), "low": ("phenotype:concordant",)},
        interpretation_gate=gate,
        uninterpretable_model={h: {"no_call": 1.0} for h in TWO} if gate else None,
    )


def test_a_gated_readout_is_legal_without_its_premise_and_moves_no_belief():
    """The uninterpretable success: it runs, it returns a qualified value, it decides nothing."""

    problem = _problem([_premise_action(), _gated_readout()], 3.5)
    assert problem.action("phenotype_readout") in legal(problem, ())
    assert posterior(problem, (("phenotype_readout", "no_call"),)) == pytest.approx(
        {"realised": 0.5, "not_realised": 0.5}
    )


def test_buying_the_premise_first_makes_the_same_readout_informative():
    """The same action and outcome label, a different declared model."""

    problem = _problem([_premise_action(), _gated_readout()], 3.5)
    history = (("exposure_panel", "matched"), ("phenotype_readout", "high"))
    assert posterior(problem, history)["realised"] > 0.99


def test_the_menu_cannot_reach_the_composed_plan_and_the_closure_can():
    """The action-space separation, on the instance the report script publishes."""

    problem = _problem([_premise_action(fails=True), _gated_readout()], 3.5)
    closed, refused = composition_closure(problem, CompositionRule("shared_plate", 1.0))
    assert not refused
    menu_loss = solve_optimal_policy(menu_only(closed)).expected_loss
    closed_loss = solve_optimal_policy(closed).expected_loss
    assert menu_loss == pytest.approx(4.0)
    assert closed_loss == pytest.approx(3.4)
    assert menu_loss - closed_loss == pytest.approx(0.6)


def test_a_zero_shared_control_saving_removes_the_separation():
    """Negative control: without the declared saving the composed plan is unaffordable."""

    problem = _problem([_premise_action(fails=True), _gated_readout()], 3.5)
    closed, _ = composition_closure(problem, CompositionRule("shared_plate", 0.0))
    assert solve_optimal_policy(menu_only(closed)).expected_loss == pytest.approx(
        solve_optimal_policy(closed).expected_loss
    )


def test_a_readout_that_needs_no_gate_removes_the_separation():
    """Negative control: gating, not bundling, is the load-bearing ingredient."""

    problem = _problem([_premise_action(fails=True), _gated_readout(gate=None)], 3.5)
    closed, _ = composition_closure(problem, CompositionRule("shared_plate", 1.0))
    assert solve_optimal_policy(menu_only(closed)).expected_loss == pytest.approx(
        solve_optimal_policy(closed).expected_loss
    )


def test_a_gate_that_supplies_an_unneeded_field_is_refused_rather_than_composed():
    """A composition is admissible only when the gate is what makes the readout interpretable."""

    unrelated = AdaptiveAction(
        identifier="unrelated_panel",
        cost=1.0,
        outcome_model={h: {"ok": 1.0} for h in TWO},
        supplies={"ok": ("functional:unrelated",)},
        role="premise_supplier",
    )
    problem = _problem([unrelated, _gated_readout()], 3.5)
    closed, refused = composition_closure(problem, CompositionRule("shared_plate", 1.0))
    assert not any(action.is_composed for action in closed.actions)
    assert refused == ()
    assert solve_optimal_policy(closed).expected_loss == pytest.approx(4.0)


GATED_READOUT = EvidenceAction(
    identifier="phenotype_readout",
    description="The phenotype the contrast wants, interpretable only through the premise.",
    cost=2.0,
    distinguishes=("h_gap", "h_mode"),
    expected_outcomes={"h_gap": "discordant", "h_mode": "concordant"},
    interpretation_gate=PREMISE,
)


def _premise_evidence(identifier: str, cost: float, *, detection_power=None) -> EvidenceAction:
    """A registered assay that declares the premise it discharges and how often it qualifies."""

    return EvidenceAction(
        identifier=identifier,
        description="A measurement of the interpretation premise.",
        cost=cost,
        distinguishes=("h_gap", "h_mode"),
        supplies=(PREMISE,),
        expected_outcomes={"h_gap": "matched", "h_mode": "matched"},
        detection_power=detection_power,
    )


PRECISE_GATE = _premise_evidence("precise_panel", 2.0, detection_power=1.0)
CHEAP_GATE = _premise_evidence("cheap_panel", 1.0, detection_power=0.5)


def _contrast():
    agent = MAESTROAgent()
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (GATED_READOUT,))
    assert contrast is not None
    return agent, contrast


def _missing_premise_check() -> ContrastCheck:
    return ContrastCheck(
        executable=True,
        prerequisites_satisfied=False,
        discriminable=True,
        decision_separating=True,
        reasons=(NonDiscriminabilityReason.MISSING_PREREQUISITE,),
        missing_prerequisites=(PREMISE,),
        outcome_separated=True,
    )


def test_two_gates_that_answer_the_same_question_are_ordered_by_declared_detection_power():
    """Price cannot be the only declared difference between two assays that answer one question."""

    _agent, contrast = _contrast()
    ranked = rank_plans(
        PlanComposer(CompositionRule("shared_plate", 0.5)).compose(
            contrast,
            (GATED_READOUT, CHEAP_GATE, PRECISE_GATE),
            {GATED_READOUT.identifier: (PREMISE,)},
        ),
        contrast,
    )
    assert [item.plan.gate.identifier for item in ranked][0] == "precise_panel"


def test_without_a_declared_detection_power_price_breaks_the_tie():
    """The fallback is price, stated rather than hidden."""

    _agent, contrast = _contrast()
    undeclared_cheap = _premise_evidence("cheap_panel", 1.0)
    undeclared_dear = _premise_evidence("dear_panel", 2.0)
    ranked = rank_plans(
        PlanComposer(CompositionRule("shared_plate", 0.5)).compose(
            contrast,
            (GATED_READOUT, undeclared_cheap, undeclared_dear),
            {GATED_READOUT.identifier: (PREMISE,)},
        ),
        contrast,
    )
    assert ranked[0].plan.gate.cost == pytest.approx(1.0)


def test_a_declared_detection_power_outranks_an_undeclared_cheaper_assay():
    """Declaring how often an assay qualifies is itself information the ordering uses."""

    _agent, contrast = _contrast()
    undeclared = _premise_evidence("unstated_panel", 1.0)
    ranked = rank_plans(
        PlanComposer(CompositionRule("shared_plate", 0.5)).compose(
            contrast,
            (GATED_READOUT, undeclared, PRECISE_GATE),
            {GATED_READOUT.identifier: (PREMISE,)},
        ),
        contrast,
    )
    assert ranked[0].plan.gate.identifier == "precise_panel"


def test_the_controller_returns_a_plan_rather_than_a_replacement_action():
    """The repair keeps the contrast's own readout and buys the premise that makes it interpretable."""

    agent = MAESTROAgent(composition_rule=CompositionRule("shared_plate", 0.5))
    contrast = agent.construct_contrast("c", HYPOTHESES, (), (GATED_READOUT,))
    assert contrast is not None
    proposal = agent.repair_contrast(
        contrast, _missing_premise_check(), (GATED_READOUT, PRECISE_GATE)
    )
    assert proposal.composed_plan is not None
    assert proposal.replacement_action is None
    assert proposal.composed_plan.readout.identifier == "phenotype_readout"
    assert proposal.promised_fields == (PREMISE,)
    assert PREMISE in proposal.interpretation_boundary


def test_a_controller_without_a_composition_rule_keeps_the_menu_behaviour():
    """Composition is a switch, so the ablation is one operator and not two code paths."""

    agent, contrast = _contrast()
    proposal = agent.repair_contrast(contrast, _missing_premise_check(), (GATED_READOUT, PRECISE_GATE))
    assert proposal.composed_plan is None
    assert proposal.replacement_action is PRECISE_GATE


def test_a_proposal_cannot_carry_both_a_plan_and_a_replacement_action():
    plan = GatedEvidencePlan(
        identifier="plan[precise_panel|phenotype_readout]",
        gate=PRECISE_GATE,
        readout=GATED_READOUT,
        rule=CompositionRule("shared_plate", 0.5),
    )
    with pytest.raises(ValueError):
        RepairProposal(
            kind=RepairKind.ADD_PREREQUISITE_MEASUREMENT,
            replacement_action=PRECISE_GATE,
            modified_fields=(),
            triggered_by=(),
            interpretation_boundary="",
            composed_plan=plan,
        )


def test_the_composed_execution_view_keeps_the_readouts_expected_outcomes():
    """The gate contributes premises, not an interpretation of the phenotype."""

    plan = GatedEvidencePlan(
        identifier="plan[precise_panel|phenotype_readout]",
        gate=PRECISE_GATE,
        readout=GATED_READOUT,
        rule=CompositionRule("shared_plate", 0.5),
    )
    action = plan.to_evidence_action()
    assert action.expected_outcomes == GATED_READOUT.expected_outcomes
    assert action.cost == pytest.approx(3.5)
    assert action.prerequisites == ()
    assert plan.supplies() == (PREMISE,)
    assert action.detection_power == GATED_READOUT.detection_power


def test_a_detection_power_outside_the_unit_interval_is_refused():
    """An assay that cannot return a qualified result is not a registered measurement."""

    with pytest.raises(ValueError):
        _premise_evidence("impossible_panel", 1.0, detection_power=0.0)


def test_a_composition_is_authorized_by_the_premise_it_repairs_not_by_a_field_intersection():
    """A named grant with a scope and an expiry, rather than two lists that happen to overlap."""

    plan = GatedEvidencePlan(
        identifier="plan[precise_panel|phenotype_readout]",
        gate=PRECISE_GATE,
        readout=GATED_READOUT,
        rule=CompositionRule("shared_plate", 0.5),
    )
    authorization = plan.authorization()
    assert isinstance(authorization, PlanAuthorization)
    assert authorization.premise == PREMISE
    assert authorization.granted_by == "precise_panel"
    assert authorization.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION
    assert "qualified real result" in authorization.provisional_until
    assert composition_is_legal(plan) == ()


def test_a_plan_whose_gate_cannot_grant_the_premise_is_refused():
    """The authorization is checked, so a coincidence cannot stand in for a grant."""

    unrelated = EvidenceAction(
        identifier="unrelated_panel",
        description="A measurement of a different premise.",
        cost=1.0,
        distinguishes=("h_gap", "h_mode"),
        supplies=("functional:unrelated",),
    )
    plan = GatedEvidencePlan(
        identifier="plan[unrelated_panel|phenotype_readout]",
        gate=unrelated,
        readout=GATED_READOUT,
        rule=CompositionRule("shared_plate", 0.5),
    )
    assert composition_is_legal(plan) == ("gate_does_not_grant_the_authorized_premise",)
