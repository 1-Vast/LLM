"""The admissible objective: what it costs, what it buys, and where it cannot bind.

File summary
- Path: tests/test_admissible_repair.py
- Purpose: Pin the measurements of the admissible reference, so a later change to a
  policy, a family or a case declaration cannot silently move the claim. Every
  assertion is a measured fact, including the two nulls: nine of the ten recorded
  families pay nothing for the boundary, and the frozen package cannot test it at all.
- Core points:
  - The admissible reference never returns an un-isolated attribution, on any family.
  - The price of admissibility is 0.000 on nine of the ten recorded families and 0.680
    on `attribution_is_expensive`.
  - Re-pricing the recorded repair under the admissible objective makes it exact on all
    ten families; the recorded version stays 0.840 above the reference on one.
  - The repair catalogue is worth 0.000 under the shipped objective and strictly
    positive under the admissible one on the licensing-gap families, and each control
    removes the separation.
  - The frozen `real_v3` package never binds the constraint: its prior is uniform, its
    root decision is licensed, and its repair is worth nothing under either objective.
- Interfaces: pytest test functions
- Depends on: evaluation.admissible, evaluation.contingent, evaluation.contingent_suite,
  evaluation.licensing_gap, evaluation.real_admissible
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.admissible import (  # noqa: E402
    admissible_certificate,
    admissible_policy,
    admissible_repair_policy,
    admissible_row,
    price_of_admissibility,
    solve_admissible_policy,
)
from evaluation.adaptive_reference import evaluate_policy, solve_optimal_policy  # noqa: E402
from evaluation.contingent import (  # noqa: E402
    ambiguity_aware_repair_policy,
    unsupported_attribution,
)
from evaluation.contingent_suite import FAMILIES as RECORDED_FAMILIES  # noqa: E402
from evaluation.licensing_gap import (  # noqa: E402
    FAMILIES as LICENSING_GAP_FAMILIES,
    REPAIR_SOURCE,
    detection_power_sweep,
    gate_cost_sweep,
    licensing_gap,
    saving_sweep,
)
from evaluation.real_admissible import measure_package  # noqa: E402

TOLERANCE = 1e-6
REAL_V3 = ROOT / "data" / "evaluation" / "cases" / "real_v3"

_FROZEN_PACKAGE: dict[str, object] = {}


def _frozen_package() -> dict:
    if not _FROZEN_PACKAGE:
        _FROZEN_PACKAGE["payload"] = dict(measure_package(REAL_V3))
    return _FROZEN_PACKAGE["payload"]  # type: ignore[return-value]


def _every_family() -> dict[str, object]:
    families = {name: build() for name, build in RECORDED_FAMILIES.items()}
    families.update({name: build() for name, build in LICENSING_GAP_FAMILIES.items()})
    return families


def test_the_admissible_reference_never_returns_an_unlicensed_attribution() -> None:
    """The constraint is enforced by construction, not by a penalty that can be paid."""

    for name, problem in _every_family().items():
        row = admissible_row(admissible_policy(problem), problem, name).as_row()
        assert row["unsupported_attribution"] == pytest.approx(0.0, abs=TOLERANCE), name


def test_the_admissible_optimum_never_beats_the_unconstrained_one() -> None:
    """The record convention is a relaxation of the admissible class, so it must bound it."""

    for name, problem in _every_family().items():
        unconstrained = solve_optimal_policy(problem).expected_loss
        admissible = solve_admissible_policy(problem).expected_loss
        assert admissible >= unconstrained - TOLERANCE, name


def test_the_boundary_costs_nothing_on_nine_of_the_ten_recorded_families() -> None:
    """The recorded null is reproduced: the constraint is slack wherever attribution was licensed."""

    prices = {
        name: price_of_admissibility(build())["price_of_admissibility"]
        for name, build in RECORDED_FAMILIES.items()
    }
    assert prices["attribution_is_expensive"] == pytest.approx(0.68, abs=TOLERANCE)
    for name, price in prices.items():
        if name == "attribution_is_expensive":
            continue
        assert price == pytest.approx(0.0, abs=TOLERANCE), name


def test_the_recorded_repair_is_measurably_improved_by_re_pricing_it() -> None:
    """One operator changes: what the tail of a candidate bundle is priced against."""

    problem = RECORDED_FAMILIES["attribution_is_expensive"]()
    reference = solve_admissible_policy(problem).expected_loss
    recorded = evaluate_policy(ambiguity_aware_repair_policy, problem).expected_loss
    improved = evaluate_policy(admissible_repair_policy, problem).expected_loss
    assert reference == pytest.approx(3.5, abs=TOLERANCE)
    assert recorded == pytest.approx(4.34, abs=TOLERANCE)
    assert improved == pytest.approx(reference, abs=TOLERANCE)
    assert recorded - improved == pytest.approx(0.84, abs=TOLERANCE)


def test_the_re_priced_repair_attains_the_admissible_reference_on_every_family() -> None:
    """The improvement is not a trade: it is exact on the recorded suite as well."""

    for name, problem in _every_family().items():
        reference = solve_admissible_policy(problem).expected_loss
        improved = evaluate_policy(admissible_repair_policy, problem).expected_loss
        assert improved == pytest.approx(reference, abs=1e-6), name


def test_the_repair_catalogue_is_worth_nothing_until_the_boundary_is_enforced() -> None:
    """The recorded certificate and the admissible one disagree on the same instance."""

    for name in ("licensing_gap_replacement", "licensing_gap_composed"):
        certificate = admissible_certificate(LICENSING_GAP_FAMILIES[name](), catalogue_source=REPAIR_SOURCE)
        assert certificate["complete"] is True, name
        assert certificate["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.0, abs=TOLERANCE)
        assert certificate["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.25, abs=TOLERANCE)


def test_the_window_where_only_the_boundary_buys_the_repair_is_exactly_bounded() -> None:
    """A licensed route is worth buying iff it undercuts the deferral, and shipped-objective
    positive iff it undercuts the unlicensed attribution. The gap between the two is the
    interval in which the repair exists only because the framework enforces its own rule."""

    by_cost = {row["gate_cost"]: row for row in gate_cost_sweep((2.0, 2.5, 3.0, 3.25, 3.5))}
    # Route cost = gate + 0.5 readout; unlicensed attribution is worth 3.000, deferral 4.000.
    assert by_cost[2.0]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.5, abs=TOLERANCE)
    assert by_cost[2.5]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_cost[3.25]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_cost[3.25]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.25, abs=TOLERANCE)
    assert by_cost[3.0]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.5, abs=TOLERANCE)
    assert by_cost[3.5]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)


def test_a_shared_control_saving_is_what_makes_a_composed_repair_affordable() -> None:
    by_saving = {row["saving"]: row for row in saving_sweep((0.0, 0.5, 1.0, 1.5))}
    assert by_saving[0.0]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_saving[0.5]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.25, abs=TOLERANCE)
    assert by_saving[1.0]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.75, abs=TOLERANCE)
    # Only at a saving of 1.5 does the composed plan also beat the unlicensed attribution.
    assert by_saving[1.0]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_saving[1.5]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.25, abs=TOLERANCE)


def test_an_unreliable_gate_removes_the_value_of_the_repair() -> None:
    by_success = {row["gate_success"]: row for row in detection_power_sweep((1.0, 0.9, 0.5))}
    assert by_success[1.0]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.25, abs=TOLERANCE)
    assert by_success[0.9]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_success[0.5]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)


def test_each_control_removes_the_separation() -> None:
    """No saving, an already-isolating readout, and a wrong premise each return 0.000."""

    for name in (
        "licensing_gap_composed_no_saving",
        "licensing_gap_menu_already_isolating",
        "licensing_gap_wrong_premise",
    ):
        certificate = admissible_certificate(LICENSING_GAP_FAMILIES[name](), catalogue_source=REPAIR_SOURCE)
        assert certificate["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(0.0, abs=TOLERANCE), name
        assert certificate["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE), name
    unreliable = admissible_certificate(
        LICENSING_GAP_FAMILIES["licensing_gap_unreliable_gate"](), catalogue_source=REPAIR_SOURCE
    )
    assert unreliable["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)


def test_every_declared_family_has_a_unique_identifier() -> None:
    """Certificates and run records are keyed by identifier, so a collision loses one."""

    identifiers = [problem.identifier for problem in _every_family().values()]
    assert len(identifiers) == len(set(identifiers))


def test_the_recorded_repair_defers_where_the_re_priced_repair_buys() -> None:
    """The deferral is licensed, so refusing is safe -- but it costs the decision it could have bought."""

    problem = LICENSING_GAP_FAMILIES["licensing_gap_replacement"]()
    recorded = admissible_row(ambiguity_aware_repair_policy, problem, "recorded").as_row()
    improved = admissible_row(admissible_repair_policy, problem, "improved").as_row()
    assert recorded["probability_defer"] == pytest.approx(1.0, abs=TOLERANCE)
    assert recorded["expected_loss"] == pytest.approx(4.0, abs=TOLERANCE)
    assert improved["probability_defer"] == pytest.approx(0.0, abs=TOLERANCE)
    assert improved["expected_loss"] == pytest.approx(3.75, abs=TOLERANCE)
    assert improved["probability_wrong_decision"] == pytest.approx(0.0, abs=TOLERANCE)


def test_the_frozen_package_cannot_bind_the_constraint() -> None:
    """Not a failed measurement: a certified property of the package's declarations."""

    payload = _frozen_package()
    assert payload["cases"] == 58
    assert payload["certified"] == 58
    assert payload["cases_with_a_uniform_prior"] == 58
    assert payload["cases_whose_root_decision_is_licensed"] == 58
    assert payload["cases_where_the_boundary_binds"] == 0
    assert payload["cases_where_the_repair_is_worth_something"] == 0
    assert payload["cases_where_the_repair_is_worth_something_under_admissibility"] == 0
    assert payload["median_unsupported_attribution_of_the_unconstrained_reference"] == pytest.approx(0.0, abs=TOLERANCE)


def test_a_skewed_prior_is_what_makes_the_boundary_bind() -> None:
    """The one declaration that separates the licensing-gap family from the frozen package."""

    skewed = licensing_gap("skewed", readout_cost=0.5, gate_cost=3.25)
    uniform = licensing_gap(
        "uniform", prior={"realised": 0.5, "not_realised": 0.5}, readout_cost=0.5, gate_cost=3.25
    )
    assert price_of_admissibility(skewed)["price_of_admissibility"] == pytest.approx(0.75, abs=TOLERANCE)
    assert price_of_admissibility(uniform)["price_of_admissibility"] == pytest.approx(0.0, abs=TOLERANCE)
