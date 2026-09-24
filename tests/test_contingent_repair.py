"""The contingent-repair instrument: what it separates, and where it honestly does not.

File summary
- Path: tests/test_contingent_repair.py
- Purpose: Pin the measurements the richer grammar produces, so a later change to
  the policies cannot silently move the claim. Each assertion states a measured
  fact, including the one that costs the proposed policy 1.52 expected loss.
- Core points:
  - The frozen flat grammar reproduces the recorded tie; that is the control.
  - A second supplier of the same premise and a binding budget break the tie.
  - Required lookahead depth grows with the length of the required repair chain.
  - The attribution discipline is not free, and the price is asserted, not hidden.
- Interfaces: pytest test functions
- Depends on: evaluation.contingent, evaluation.contingent_suite
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.adaptive_reference import (  # noqa: E402
    evaluate_policy,
    information_gain_policy,
    lookahead_policy,
    optimal_policy,
    reactive_prerequisite_policy,
    solve_optimal_policy,
)
from evaluation.contingent import (  # noqa: E402
    ambiguity_aware_repair_policy,
    ambiguity_report,
    evaluate_with_attribution,
    repair_catalogue_certificate,
    required_depth,
)
from evaluation.contingent_suite import (  # noqa: E402
    FAMILIES,
    REPAIR_SOURCE,
    attribution_is_expensive,
    false_isolation,
    flat_grammar,
    information_is_not_value,
    repair_cascade,
    supplier_choice_binding_budget,
)
from evaluation.real_contingent import measure_package  # noqa: E402

TOLERANCE = 1e-6
REAL_V3 = ROOT / "data" / "evaluation" / "cases" / "real_v3"

_FROZEN_PACKAGE: dict[str, object] = {}


def _frozen_package() -> dict:
    if not _FROZEN_PACKAGE:
        _FROZEN_PACKAGE.update(measure_package(REAL_V3))
    return _FROZEN_PACKAGE


def _optimal(problem) -> float:
    return solve_optimal_policy(problem).expected_loss


def test_the_flat_grammar_reproduces_the_recorded_tie():
    """The control: on the frozen grammar the incumbent control is already optimal."""

    problem = flat_grammar()
    optimum = _optimal(problem)
    assert evaluate_policy(reactive_prerequisite_policy, problem).expected_loss == pytest.approx(optimum)
    assert evaluate_policy(ambiguity_aware_repair_policy, problem).expected_loss == pytest.approx(optimum)


def test_a_second_supplier_of_one_premise_breaks_the_recorded_tie():
    """The grammar change, measured: the control that tied with directed repair no longer attains the optimum."""

    problem = supplier_choice_binding_budget()
    optimum = _optimal(problem)
    reactive = evaluate_policy(reactive_prerequisite_policy, problem).expected_loss
    gain = evaluate_policy(information_gain_policy, problem).expected_loss
    aware = evaluate_policy(ambiguity_aware_repair_policy, problem).expected_loss
    assert reactive > optimum + TOLERANCE
    assert gain > optimum + TOLERANCE
    assert aware == pytest.approx(optimum)
    # The failure branch is what the cheap supplier hides: it defers half the time.
    assert evaluate_policy(reactive_prerequisite_policy, problem).probability_defer == pytest.approx(0.5)


def test_information_per_unit_cost_is_not_decision_value():
    """A cheap readout that explains a nuisance is worth less than a dear one that moves the decision."""

    problem = information_is_not_value()
    optimum = _optimal(problem)
    assert evaluate_policy(information_gain_policy, problem).expected_loss > optimum + TOLERANCE
    assert evaluate_policy(ambiguity_aware_repair_policy, problem).expected_loss == pytest.approx(optimum)


def test_required_lookahead_depth_grows_with_the_repair_chain():
    """No fixed depth suffices: the depth that reaches the optimum tracks the chain length."""

    assert required_depth(repair_cascade(2), max_depth=5) == 3
    assert required_depth(repair_cascade(3), max_depth=5) == 4
    short = repair_cascade(3)
    assert required_depth(short, max_depth=2) is None, "no two-step policy attains the optimum here"
    assert evaluate_policy(lookahead_policy(2), short).expected_loss > _optimal(short) + TOLERANCE


def test_the_incumbent_controls_defer_entirely_on_a_chain_they_cannot_price():
    """Ordinary prerequisite handling is not enough once a supplier's failure has to be paid for."""

    problem = repair_cascade(3)
    for policy in (reactive_prerequisite_policy, information_gain_policy):
        evaluation = evaluate_policy(policy, problem)
        assert evaluation.probability_defer == pytest.approx(1.0)
        assert evaluation.expected_cost == pytest.approx(0.0)


def test_the_aware_policy_attains_the_exact_reference_on_every_family():
    """Where it is optimal it is exactly the reference, not merely close.

    `attribution_is_expensive` is excluded on purpose and asserted separately: on
    that family the reference itself returns an un-isolated attribution, so an
    exact match would mean the discipline had been abandoned.
    """

    for name, builder in FAMILIES.items():
        if name == "attribution_is_expensive":
            continue
        problem = builder()
        assert evaluate_policy(
            ambiguity_aware_repair_policy, problem
        ).expected_loss == pytest.approx(_optimal(problem), abs=TOLERANCE), name


def test_a_cascade_that_costs_more_than_a_deferral_is_not_bought():
    """A boundary control: the suite does not reward acquisition for its own sake."""

    problem = repair_cascade(4)
    assert _optimal(problem) == pytest.approx(4.0)
    assert evaluate_policy(ambiguity_aware_repair_policy, problem).probability_defer == pytest.approx(1.0)


def test_the_ambiguity_report_names_what_would_isolate_the_cause():
    flat = ambiguity_report(flat_grammar())
    assert flat.candidates == ("realised", "not_realised")
    assert set(flat.isolating_actions) == {"readout_one", "readout_two"}
    assert flat.complete
    chain = ambiguity_report(repair_cascade(2))
    assert chain.isolating_actions == ()
    assert chain.separating_bundles, "a bundle that isolates must still be recorded"


def test_a_truncated_bundle_search_is_reported_rather_than_assumed_complete():
    report = ambiguity_report(repair_cascade(2), bundle_limit=2)
    assert not report.complete


def test_the_attribution_discipline_has_a_price_and_the_suite_charges_it():
    """The uncomfortable measurement: the loss convention licenses an unsupported attribution.

    Isolating the two causes costs 3.5; acting on the prior is expected to lose 3.0.
    Every loss-minimising policy therefore decides without isolating, and the
    probability mass on which it does so is 0.68. The ambiguity-aware repair
    refuses that attribution and pays 1.52 more expected loss for the refusal.
    """

    problem = attribution_is_expensive()
    optimum = evaluate_with_attribution(ambiguity_aware_repair_policy, problem)
    reference = evaluate_with_attribution(optimal_policy(problem), problem)
    assert reference.unsupported_attribution == pytest.approx(0.68, abs=1e-9)
    assert optimum.unsupported_attribution == pytest.approx(0.0)
    assert optimum.evaluation.expected_loss > reference.evaluation.expected_loss + 1.0


def test_isolating_a_cause_costs_nothing_when_the_measurement_is_cheap():
    """The discipline is not conservatism for its own sake: on `false_isolation` it is free."""

    problem = false_isolation()
    reference = evaluate_with_attribution(optimal_policy(problem), problem)
    aware = evaluate_with_attribution(ambiguity_aware_repair_policy, problem)
    assert reference.unsupported_attribution == pytest.approx(0.0)
    assert aware.evaluation.expected_loss == pytest.approx(reference.evaluation.expected_loss)


def test_the_reactive_control_is_provably_optimal_on_the_original_menu():
    """The certificate, not a comparison between two heuristics.

    Every contingent policy restricted to the original menu -- reactive, entropy
    per cost, lookahead of any depth -- is bounded by the exact optimum of the
    menu-only problem. On this family the reactive control attains that bound, so
    its 3.5 is not a weakness of the control: it is the best any selection policy
    can do, and the repair catalogue is worth exactly 0.5 beyond it.
    """

    problem = supplier_choice_binding_budget()
    certificate = repair_catalogue_certificate(problem, catalogue_source=REPAIR_SOURCE)
    assert certificate["complete"] is True
    assert certificate["menu_only_optimum"] == pytest.approx(3.5)
    assert certificate["value_of_the_repair_catalogue"] == pytest.approx(0.5)
    assert evaluate_policy(reactive_prerequisite_policy, problem).expected_loss == pytest.approx(
        certificate["menu_only_optimum"]
    )
    assert solve_optimal_policy(problem).expected_loss == pytest.approx(certificate["closed_optimum"])


def test_a_certificate_is_zero_when_no_repair_catalogue_was_declared():
    """The negative control for the certificate itself."""

    certificate = repair_catalogue_certificate(flat_grammar(), catalogue_source=REPAIR_SOURCE)
    assert certificate["complete"] is True
    assert certificate["value_of_the_repair_catalogue"] == pytest.approx(0.0)


def test_the_frozen_package_cannot_certify_a_repair_value():
    """The real-package half of the diagnosis, as a bound rather than an interpretation.

    All 58 cases solve exactly in both worlds, so this is not a truncation artefact.
    The 27 reproduces the hand-run retyping count from 2026-09-13; the zero is the new
    information: the unrepaired menu already attains the optimum everywhere.
    """

    payload = _frozen_package()
    assert payload["cases"] == 58
    assert payload["certified"] == 58
    assert payload["cases_needing_a_typed_repair"] == 27
    assert payload["cases_where_the_declared_menu_already_decides_without_a_repair"] == 58
    assert payload["cases_where_the_repair_is_worth_something"] == 0
    assert payload["median_counterfactual_value"] == pytest.approx(0.0)


def test_the_frozen_menu_is_redundantly_decisive():
    """The mechanism behind the zero: a single registered action already separates the contrast."""

    retyped = [row for row in _frozen_package()["rows"] if row["repair"]]
    assert retyped
    assert all(row["individually_decisive_actions"] >= 1 for row in retyped)
    assert all(row["complete"] for row in retyped)
