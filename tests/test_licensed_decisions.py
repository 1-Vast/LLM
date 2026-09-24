"""The licence that keeps the objective from contradicting the runtime.

File summary
- Path: tests/test_licensed_decisions.py
- Purpose: Pin the defect and the repair in the exact reference, before any number computed from it is quoted.
- Core points:
  - A finite penalty on a wrong terminal act does not enforce an evidence boundary: the expected-loss optimum attributes a cause it never isolated whenever isolation costs more than the penalty.
  - The repair is a constraint. An act that asserts a cause is admissible only when every surviving hypothesis would take that act, and the unlicensed rate is measured against that rule rather than against the objective.
  - The controls pin that the licence is neither a tax on measuring nor deferral by another name, and the composition separation survives it.
- Interfaces: evaluation.adaptive_reference (licence), evaluation.composition
- Depends on: src/
"""
import pytest

from evaluation.adaptive_reference import (
    AdaptiveAction,
    DecisionProblem,
    evaluate_policy,
    is_licensed,
    licensed_decisions,
    optimal_policy,
    solve_optimal_policy,
    surviving_hypotheses,
)
from evaluation.composition import composition_closure, menu_only
from maestro import CompositionRule

DEFER = "defer"
TWO = ("cause_a", "cause_b")


def _attribution_problem(*, prior_a: float, test_cost: float) -> DecisionProblem:
    return DecisionProblem(
        identifier="licence",
        hypotheses=TWO,
        prior={"cause_a": prior_a, "cause_b": 1.0 - prior_a},
        actions=(
            AdaptiveAction(
                identifier="isolation_test",
                cost=test_cost,
                outcome_model={"cause_a": {"a_seen": 1.0}, "cause_b": {"b_seen": 1.0}},
            ),
        ),
        budget=max(test_cost, 1.0),
        decisions=("attribute_a", "attribute_b", DEFER),
        loss={
            "attribute_a": {"cause_a": 0.0, "cause_b": 10.0},
            "attribute_b": {"cause_a": 10.0, "cause_b": 0.0},
            DEFER: {"cause_a": 4.0, "cause_b": 4.0},
        },
        attributions=("attribute_a", "attribute_b"),
    )


def test_a_finite_penalty_does_not_enforce_the_evidence_boundary():
    """The defect, stated as a measurement: the optimum always asserts a cause it never isolated."""

    problem = _attribution_problem(prior_a=0.95, test_cost=3.8)
    policy = optimal_policy(problem)
    evaluation = evaluate_policy(policy, problem)
    assert policy(problem, ()) == ("decide", "attribute_a")
    assert evaluation.unlicensed_attribution_rate == pytest.approx(1.0)
    assert evaluation.expected_cost == pytest.approx(0.0)


def test_the_licence_makes_the_same_optimum_buy_the_evidence_it_requires():
    """The repair: with the constraint in place the optimal policy measures before it attributes."""

    problem = _attribution_problem(prior_a=0.95, test_cost=3.8).licensed_variant()
    policy = optimal_policy(problem)
    evaluation = evaluate_policy(policy, problem)
    assert policy(problem, ()) == ("act", "isolation_test")
    assert evaluation.unlicensed_attribution_rate == pytest.approx(0.0)
    assert solve_optimal_policy(problem).expected_loss == pytest.approx(3.8)


def test_deferral_does_not_become_cheapest_under_the_licence():
    """The licence constrains attribution; it must not make giving up the best policy."""

    problem = _attribution_problem(prior_a=0.95, test_cost=3.8).licensed_variant()
    evaluation = evaluate_policy(optimal_policy(problem), problem)
    assert evaluation.probability_defer < 0.5
    assert solve_optimal_policy(problem).expected_loss < 4.0


def test_the_licence_costs_nothing_when_measuring_is_cheap():
    """Control: a test cheaper than the expected penalty is bought under both conventions."""

    problem = _attribution_problem(prior_a=0.95, test_cost=0.4)
    for variant in (problem, problem.licensed_variant()):
        evaluation = evaluate_policy(optimal_policy(variant), variant)
        assert evaluation.unlicensed_attribution_rate == pytest.approx(0.0)
        assert evaluation.expected_cost == pytest.approx(0.4)


def test_survivors_that_agree_on_an_action_are_licensed_to_act():
    """Control: the licence is agreement-based, not deferral-based."""

    problem = DecisionProblem(
        identifier="shared",
        hypotheses=TWO,
        prior={"cause_a": 0.5, "cause_b": 0.5},
        actions=(),
        budget=0.0,
        decisions=("continue", "attribute_a", "attribute_b", DEFER),
        loss={
            "continue": {"cause_a": 0.0, "cause_b": 0.0},
            "attribute_a": {"cause_a": 0.0, "cause_b": 10.0},
            "attribute_b": {"cause_a": 10.0, "cause_b": 0.0},
            DEFER: {"cause_a": 4.0, "cause_b": 4.0},
        },
        attributions=("attribute_a", "attribute_b"),
    )
    assert surviving_hypotheses(problem, ()) == TWO
    assert "continue" in licensed_decisions(problem, ())
    assert not is_licensed(problem, (), "attribute_a")
    assert evaluate_policy(optimal_policy(problem.licensed_variant()), problem.licensed_variant()).expected_loss == pytest.approx(0.0)


def test_attribution_becomes_licensed_once_the_test_isolates_the_cause():
    """The constraint is on the state of evidence, not on the act's name."""

    problem = _attribution_problem(prior_a=0.95, test_cost=3.8)
    history = (("isolation_test", "b_seen"),)
    assert surviving_hypotheses(problem, history) == ("cause_b",)
    assert is_licensed(problem, history, "attribute_b")
    assert not is_licensed(problem, history, "attribute_a")


def test_a_problem_whose_only_acts_are_attributions_is_refused():
    """With no admissible terminal act the search would have to invent one."""

    problem = DecisionProblem(
        identifier="no_exit",
        hypotheses=TWO,
        prior={"cause_a": 0.5, "cause_b": 0.5},
        actions=(),
        budget=0.0,
        decisions=("attribute_a", "attribute_b"),
        loss={
            "attribute_a": {"cause_a": 0.0, "cause_b": 10.0},
            "attribute_b": {"cause_a": 10.0, "cause_b": 0.0},
        },
        attributions=("attribute_a", "attribute_b"),
    )
    assert "no_non_attribution_decision" in problem.validate()


def test_the_licence_does_not_undo_the_composition_separation():
    """Robustness: the action-space result survives the corrected objective."""

    premise = "exposure:matched"
    gate = AdaptiveAction(
        identifier="exposure_match_panel",
        cost=1.0,
        outcome_model={h: {"matched": 0.9, "mismatched": 0.1} for h in ("realised", "not_realised")},
        supplies={"matched": (premise,), "mismatched": ()},
        role="premise_supplier",
    )
    readout = AdaptiveAction(
        identifier="phenotype_readout",
        cost=3.0,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        interpretation_gate=premise,
        uninterpretable_model={h: {"no_call": 1.0} for h in ("realised", "not_realised")},
    )
    base = DecisionProblem(
        identifier="composed",
        hypotheses=("realised", "not_realised"),
        prior={"realised": 0.5, "not_realised": 0.5},
        actions=(gate, readout),
        budget=3.5,
        decisions=("continue", "revise_intervention", DEFER),
        loss={
            "continue": {"realised": 0.0, "not_realised": 10.0},
            "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
            DEFER: {"realised": 4.0, "not_realised": 4.0},
        },
        attributions=("continue", "revise_intervention"),
    )
    values = []
    for variant in (base, base.licensed_variant()):
        closed, _refused = composition_closure(variant, CompositionRule("shared_plate", 1.0))
        menu = menu_only(closed)
        values.append(
            solve_optimal_policy(menu).expected_loss - solve_optimal_policy(closed).expected_loss
        )
    assert values[0] == pytest.approx(0.6)
    assert values[1] == pytest.approx(0.6)
