"""Optimizer contract: exactness, explicit constraints, and non-anticipation.

File summary
- Path: tests/test_evidence_planning.py
- Purpose: Pin the evidence-selection optimizer to exhaustive ground truth and to the public-information boundary.
- Core points: the solver must report an honest status; constraints must be named rather than folded into a penalty; the planner must not see a hidden outcome.
- Interfaces: `test_exact_solver_matches_brute_force()`, `test_constraints_are_reported_individually()`, `test_planner_is_invariant_to_hidden_outcomes()`, `test_prerequisite_selection_does_not_guarantee_the_premise()`
- Depends on: evaluation.planning, evaluation.feasibility, evaluation.cases
"""
from __future__ import annotations

from itertools import combinations

import pytest

from evaluation.cases import EvidenceMenuItem, PublicCase, ReplayEnvironment, ReplayCase, ScoringSpec
from evaluation.feasibility import enumerate_public_plans, sequence_cost
from evaluation.planning import (
    PlanConstraints,
    decision_ambiguity,
    declared_scenarios,
    scalability_profile,
    solve_exact,
)
from maestro.models import EvidenceAction, EvidenceActionKind


def _item(identifier: str, **overrides) -> EvidenceMenuItem:
    defaults = dict(
        identifier=identifier,
        description=identifier,
        cost=1.0,
        distinguishes=("h1", "h2"),
        kind=EvidenceActionKind.READOUT_MEASUREMENT,
        expected_outcomes={"h1": "positive", "h2": "negative"},
    )
    defaults.update(overrides)
    available = defaults.pop("available", True)
    return EvidenceMenuItem(action=EvidenceAction(**defaults), available=available)


def _public(actions, budget: float = 2.0) -> PublicCase:
    return PublicCase(
        identifier="plan-fixture",
        provenance="synthetic software fixture",
        evaluation_status="fixture",
        initial_evidence=(),
        hypotheses=({"identifier": "h1", "description": "one", "development_action": "continue"},
                    {"identifier": "h2", "description": "two", "development_action": "revise_attribution"}),
        actions=tuple(actions),
        budget=budget,
        context_identifier="ctx",
    )


def test_exact_solver_matches_brute_force():
    """The reported optimum equals an independent exhaustive search."""

    public = _public([_item("a"), _item("b", cost=2.0), _item("c", expected_outcomes={})])
    constraints = PlanConstraints(budget=public.budget)
    solution = solve_exact(public, constraints, cost_weight=0.25)

    reference = []
    for size in range(len(public.actions) + 1):
        for subset in combinations([item.action.identifier for item in public.actions], size):
            if sequence_cost(public, subset) > public.budget + 1e-9:
                continue
            scenarios = declared_scenarios(public, subset)
            residual = max(decision_ambiguity(public, scenario) for scenario in scenarios)
            reference.append((residual + 0.25 * sequence_cost(public, subset), tuple(sorted(subset))))
    best = min(reference)
    assert solution.status == "OPTIMAL"
    assert solution.gap == pytest.approx(0.0)
    assert solution.objective == pytest.approx(best[0])
    assert tuple(sorted(solution.sequence)) == best[1]


def test_constraints_are_reported_individually():
    """A rejected bundle names every limit it breaks."""

    public = _public([_item("a"), _item("b")], budget=4.0)
    constraints = PlanConstraints(
        budget=4.0,
        wells_available=3,
        batch_capacity=1,
        wells_per_action={"a": 2, "b": 2},
        required_replicates={"a": 2},
        shared_control_wells={"plate_control": 4},
        control_required_by={"a": "plate_control"},
        incompatible_pairs=(("a", "b"),),
    )
    violations = set(constraints.violations(public, ("a", "b")))
    assert "batch_capacity" in violations
    assert "wells" in violations
    assert "incompatible:a+b" in violations
    # A shared control is charged once as a setup, not once per dependent assay.
    assert constraints.wells_used(("a",)) == 2 * 2 + 4
    solution = solve_exact(public, constraints)
    assert solution.feasible_count >= 1
    assert any(problems for _, problems in solution.rejected)


def test_planner_is_invariant_to_hidden_outcomes():
    """Identical public contracts produce identical plans and identical optima."""

    public = _public([_item("a"), _item("b")])
    constraints = PlanConstraints(budget=public.budget)
    first = solve_exact(public, constraints)
    second = solve_exact(public, constraints)
    assert first.sequence == second.sequence
    assert enumerate_public_plans(public) == enumerate_public_plans(public)
    # The planner's inputs are the public case alone: it has no parameter
    # through which a hidden result could reach it.
    assert "outcomes" not in solve_exact.__code__.co_varnames


def test_prerequisite_selection_does_not_guarantee_the_premise():
    """Planning to buy a supplier is not evidence that the premise will hold."""

    supplier = _item("supplier", supplies=("f:premise",), expected_outcomes={})
    dependent = _item("dependent", prerequisites=("f:premise",))
    public = _public([supplier, dependent])
    plans = enumerate_public_plans(public)
    assert ("supplier", "dependent") in plans

    # In a world where the supplier's record does not qualify, that plan does
    # not execute. The planner still proposed it, which is the point: a
    # selected prerequisite assay is a bet on its result, not a guarantee.
    from evaluation.cases import RevealedEvidence
    from maestro.models import EvidenceKind

    unqualified = RevealedEvidence(
        action_identifier="supplier", outcome="unknown", statement="failed quality control",
        source_id="src", context_identifier="ctx", time_hours=None, conditions={}, metrics={},
        record_count=1, biological_replicates=1, record_validated=True, biological_quality="failed",
        interpretation_fields=("f:premise",), limitations=(), evidence_kind=EvidenceKind.REAL_MEASUREMENT,
    )
    qualified = RevealedEvidence(
        action_identifier="dependent", outcome="positive", statement="result", source_id="src",
        context_identifier="ctx", time_hours=None, conditions={}, metrics={}, record_count=1,
        biological_replicates=1, record_validated=True, biological_quality="passed",
        interpretation_fields=("f:dep",), evidence_kind=EvidenceKind.REAL_MEASUREMENT, limitations=(),
    )
    case = ReplayCase(public, ScoringSpec(decision_rules=(), critical_actions=frozenset()))
    environment = ReplayEnvironment(case, {"supplier": unqualified, "dependent": qualified})
    environment.query("supplier")
    with pytest.raises(ValueError, match="prerequisite"):
        environment.query("dependent")


def test_scalability_profile_reports_the_backend_and_threshold():
    """The instance size decides the method, and the report says which was used."""

    public = _public([_item("a"), _item("b"), _item("c")])
    profile = scalability_profile(public, PlanConstraints(budget=public.budget))
    assert profile["solver_backend"] == "exhaustive_enumeration"
    assert profile["exact_enumeration_applies"] is True
    assert profile["solver_status"] == "OPTIMAL"
    assert profile["legal_plans_including_empty"] == len(enumerate_public_plans(public))
