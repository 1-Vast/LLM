"""The exact adaptive reference, its controls, and the semantics they share with execution.

File summary
- Path: tests/test_adaptive_reference.py
- Purpose: pin the properties the reference must have before any comparison is read as evidence: exactness, non-anticipativity, honest completeness, and agreement with the shared legality rule.
- Core points:
  - The dynamic programme is checked against an independent recursion written here, and the policy evaluator is checked against the programme's own value.
  - Where the action grammar makes a reactive control optimal, the test asserts the equivalence rather than hiding it.
  - Competent controls keep ordinary prerequisite handling, so a separation has to come from contingency, not from a disabled baseline.
- Interfaces: pytest test functions
- Depends on: evaluation.adaptive_reference, evaluation.feasibility, evaluation.cases
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.adaptive_reference import (
    DEFER,
    AdaptiveAction,
    DecisionProblem,
    clairvoyant_loss,
    evaluate_policy,
    fixed_order_policy,
    information_gain_policy,
    legal,
    lookahead_policy,
    optimal_policy,
    policy_tree,
    posterior,
    reactive_prerequisite_policy,
    solve_optimal_policy,
    terminal,
    to_evidence_action,
)
from evaluation.cases import EvidenceMenuItem, PublicCase
from evaluation.feasibility import legal_actions

HYPOTHESES = ("realised", "not_realised")
LOSS = {
    "continue": {"realised": 0.0, "not_realised": 10.0},
    "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
    DEFER: {"realised": 4.0, "not_realised": 4.0},
}


def _separating(identifier: str, cost: float, **kwargs) -> AdaptiveAction:
    return AdaptiveAction(
        identifier=identifier,
        cost=cost,
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        **kwargs,
    )


def _flat_problem() -> DecisionProblem:
    return DecisionProblem(
        identifier="flat",
        hypotheses=HYPOTHESES,
        prior={"realised": 0.5, "not_realised": 0.5},
        actions=(_separating("readout_one", 1.0), _separating("readout_two", 1.0)),
        budget=2.0,
        decisions=("continue", "revise_intervention", DEFER),
        loss=LOSS,
        family="flat_grammar",
    )


def _supplier_problem() -> DecisionProblem:
    unreliable = AdaptiveAction(
        identifier="cheap_supplier", cost=1.0, role="premise_supplier",
        outcome_model={h: {"ok": 0.5, "failed": 0.5} for h in HYPOTHESES},
        supplies={"ok": ("premise",)},
    )
    reliable = AdaptiveAction(
        identifier="reliable_supplier", cost=2.0, role="premise_supplier",
        outcome_model={h: {"ok": 1.0} for h in HYPOTHESES},
        supplies={"ok": ("premise",)},
    )
    return DecisionProblem(
        identifier="supplier_failure",
        hypotheses=HYPOTHESES,
        prior={"realised": 0.5, "not_realised": 0.5},
        actions=(unreliable, reliable, _separating("gated_readout", 1.0, prerequisites=("premise",))),
        budget=3.0,
        decisions=("continue", "revise_intervention", DEFER),
        loss=LOSS,
        family="supplier_failure_with_binding_budget",
    )


def _independent_value(problem: DecisionProblem, history=()) -> float:
    """A plain recursion with no memoisation, written independently of the module's."""

    best = terminal(problem, history)[1]
    for action in legal(problem, history):
        expected = action.cost
        for outcome in action.outcomes():
            probability = sum(
                posterior(problem, history)[h] * action.outcome_model[h].get(outcome, 0.0) for h in problem.hypotheses
            )
            if probability > 0:
                expected += probability * _independent_value(problem, history + ((action.identifier, outcome),))
        best = min(best, expected)
    return best


@pytest.mark.parametrize("problem", [_flat_problem(), _supplier_problem()])
def test_the_dynamic_programme_matches_an_independent_recursion(problem):
    solution = solve_optimal_policy(problem)
    assert solution.complete
    assert solution.expected_loss == pytest.approx(_independent_value(problem), abs=1e-12)


@pytest.mark.parametrize("problem", [_flat_problem(), _supplier_problem()])
def test_evaluating_the_optimal_policy_reproduces_its_value(problem):
    solution = solve_optimal_policy(problem)
    evaluation = evaluate_policy(optimal_policy(problem), problem)
    assert evaluation.expected_loss == pytest.approx(solution.expected_loss, abs=1e-12)


def test_a_policy_sees_only_public_declarations_and_history():
    """Changing only the hidden truth changes the loss, never the policy's choices.

    The reactive control buys the cheap supplier first, so a truth in which that
    supplier fails more often must cost it more, while its decision tree, which
    is built from the public declarations and the history alone, stays the same.
    """

    planning = _supplier_problem()
    harsher = AdaptiveAction(
        identifier="cheap_supplier", cost=1.0, role="premise_supplier",
        outcome_model={h: {"ok": 0.1, "failed": 0.9} for h in HYPOTHESES},
        supplies={"ok": ("premise",)},
    )
    truth = DecisionProblem(
        identifier="harsher_truth", hypotheses=planning.hypotheses, prior=planning.prior,
        actions=(harsher, *planning.actions[1:]), budget=planning.budget,
        decisions=planning.decisions, loss=planning.loss,
    )
    policy = reactive_prerequisite_policy
    assert [step for _, step in policy_tree(policy, planning)] == [
        step for _, step in policy_tree(policy, planning)
    ]
    under_declared = evaluate_policy(policy, planning).expected_loss
    under_truth = evaluate_policy(policy, planning, truth).expected_loss
    assert under_truth > under_declared + 1e-9
    # The optimal policy never buys the unreliable supplier, so its loss is the
    # same under both truths: that is the property that makes it the reference.
    optimal = optimal_policy(planning)
    assert evaluate_policy(optimal, planning, truth).expected_loss == pytest.approx(
        evaluate_policy(optimal, planning).expected_loss
    )


def test_the_flat_grammar_makes_the_reactive_control_optimal():
    problem = _flat_problem()
    optimal = solve_optimal_policy(problem).expected_loss
    reactive = evaluate_policy(reactive_prerequisite_policy, problem).expected_loss
    assert reactive == pytest.approx(optimal, abs=1e-12), "equivalence is the result, not a failure"


def test_a_failing_supplier_under_a_binding_budget_separates_reactive_from_optimal():
    problem = _supplier_problem()
    optimal = solve_optimal_policy(problem).expected_loss
    reactive = evaluate_policy(reactive_prerequisite_policy, problem).expected_loss
    lookahead = evaluate_policy(lookahead_policy(2), problem).expected_loss
    assert optimal < reactive - 1e-9
    assert lookahead == pytest.approx(optimal, abs=1e-9), "two-step lookahead is enough for this instance"


def test_the_controls_keep_their_prerequisite_handling():
    """The reactive control must buy a blocked readout's supplier, or the comparison is rigged."""

    problem = _supplier_problem()
    step = reactive_prerequisite_policy(problem, ())
    assert step[0] == "act" and step[1].endswith("supplier")
    gain = information_gain_policy(problem, ())
    assert gain[0] == "act"


def test_a_capped_search_reports_bounds_rather_than_a_certificate():
    solution = solve_optimal_policy(_supplier_problem(), state_cap=3)
    assert not solution.complete
    assert solution.stopping_reason == "state_cap_reached"
    assert solution.lower_bound == pytest.approx(clairvoyant_loss(_supplier_problem()))


def test_the_evaluator_refuses_an_illegal_step():
    problem = _flat_problem()

    def rogue(_problem, history):
        return ("act", "readout_one") if len(history) < 2 else ("decide", DEFER)

    with pytest.raises(ValueError):
        evaluate_policy(rogue, problem)


def test_a_fixed_order_control_stops_when_nothing_is_legal():
    problem = _flat_problem()
    evaluation = evaluate_policy(fixed_order_policy(("readout_one", "readout_two")), problem)
    assert evaluation.expected_cost == pytest.approx(2.0)
    assert evaluation.probability_wrong_decision == pytest.approx(0.0)


def test_legality_agrees_with_the_shared_execution_rule():
    problem = _supplier_problem()
    actions = tuple(EvidenceMenuItem(to_evidence_action(action, problem.hypotheses)) for action in problem.actions)
    public = PublicCase(
        identifier="bridge", provenance="synthetic", evaluation_status="fixture", initial_evidence=(),
        hypotheses=tuple({"identifier": name} for name in problem.hypotheses), actions=actions,
        budget=problem.budget, context_identifier="ctx",
    )
    for history in ((), (("cheap_supplier", "ok"),), (("cheap_supplier", "failed"),)):
        supplied = frozenset(field for action, outcome in history for field in problem.action(action).supplies.get(outcome, ()))
        queried = tuple(action for action, _ in history)
        spent = sum(problem.action(action).cost for action, _ in history)
        shared = {item.action.identifier for item in legal_actions(public, queried, spent, supplied)}
        assert shared == {action.identifier for action in legal(problem, history)}
