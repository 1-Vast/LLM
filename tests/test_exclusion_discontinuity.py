"""The admissible objective credits exclusion, not information, and the jump is pinned here.

File summary
- Path: tests/test_exclusion_discontinuity.py
- Purpose: pin the property of the licensing rule that decides whether a repair can be
  worth anything, so a later change to `admissible_terminal` or to `contingent.licensed`
  cannot move it silently.
- Core points:
  - The admissible repair value is exactly 0.000 at every declared detection power below
    1.0, at every declared control cost, and equals `deferral - cost` at 1.0.
  - The price of admissibility moves the other way: it rises with detection power and
    collapses to 0.000 once the observation excludes, so the boundary is most expensive
    exactly where the evidence is most informative and still unlicensed.
  - The discontinuity is a property of this family, not a theorem about the objective:
    the recorded `licensing_gap` families have a strictly positive price *and* a strictly
    positive admissible repair value at the same time, and that contrast is asserted here
    so the narrower claim cannot be over-read.
- Interfaces: pytest test functions
- Depends on: evaluation.exclusion_discontinuity, evaluation.admissible,
  evaluation.licensing_gap
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.admissible import admissible_certificate, price_of_admissibility  # noqa: E402
from evaluation.exclusion_discontinuity import (  # noqa: E402
    CATALOGUE_SOURCE,
    DEFAULT_COSTS,
    DEFAULT_POWERS,
    DEFERRAL,
    detection_power_cost_grid,
    exclusion_family,
)
from evaluation.licensing_gap import (  # noqa: E402
    FAMILIES as LICENSING_GAP_FAMILIES,
    REPAIR_SOURCE,
)

TOLERANCE = 1e-6


def _grid() -> tuple[dict, ...]:
    return tuple(dict(row) for row in detection_power_cost_grid())


def test_every_declared_cell_of_the_grid_is_certified() -> None:
    """A truncated search certifies nothing, so completeness is asserted before the values."""

    rows = _grid()
    assert len(rows) == len(DEFAULT_POWERS) * len(DEFAULT_COSTS)
    for row in rows:
        assert row["complete"] is True, row


def test_information_alone_is_worth_nothing_under_the_admissible_objective() -> None:
    """Below full exclusion the repair value is exactly zero, at every declared cost."""

    for row in _grid():
        if row["excludes_a_hypothesis"]:
            continue
        assert row["value_of_the_repair_catalogue_admissible"] == pytest.approx(
            0.0, abs=TOLERANCE
        ), row


def test_exclusion_is_worth_the_deferral_minus_the_control_cost() -> None:
    """Once an outcome excludes a hypothesis the licensed act becomes reachable."""

    for row in _grid():
        if not row["excludes_a_hypothesis"]:
            continue
        assert row["value_of_the_repair_catalogue_admissible"] == pytest.approx(
            DEFERRAL - row["control_cost"], abs=TOLERANCE
        ), row


def test_the_boundary_is_dearest_where_the_evidence_is_best_and_still_unlicensed() -> None:
    """The price rises with detection power below 1.0, then collapses to zero at 1.0."""

    by_power = {
        row["detection_power"]: row
        for row in _grid()
        if row["control_cost"] == pytest.approx(1.0)
    }
    assert by_power[0.6]["price_of_admissibility"] == pytest.approx(0.0, abs=TOLERANCE)
    assert by_power[0.8]["price_of_admissibility"] == pytest.approx(1.0, abs=TOLERANCE)
    assert by_power[0.9]["price_of_admissibility"] == pytest.approx(2.0, abs=TOLERANCE)
    assert by_power[0.99]["price_of_admissibility"] == pytest.approx(2.9, abs=TOLERANCE)
    assert by_power[1.0]["price_of_admissibility"] == pytest.approx(0.0, abs=TOLERANCE)
    below = [row for row in _grid() if not row["excludes_a_hypothesis"] and row["control_cost"] == 1.0]
    prices = [row["price_of_admissibility"] for row in sorted(below, key=lambda item: item["detection_power"])]
    assert prices == sorted(prices)


def test_the_unconstrained_objective_does_pay_for_information() -> None:
    """The contrast that makes the null a statement about the objective, not the action.

    The same declared control is worth something under the shipped objective well before it
    excludes anything, which is why the zero above cannot be read as the control being
    uninformative.
    """

    rows = {
        row["detection_power"]: row
        for row in _grid()
        if row["control_cost"] == pytest.approx(1.0)
    }
    assert rows[0.9]["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(2.0, abs=TOLERANCE)
    assert rows[0.9]["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)


def test_a_cheap_control_does_not_rescue_a_non_excluding_one() -> None:
    """Directly separates exclusion from the recorded cost-window explanation.

    At a cost of 0.25 the licensed route undercuts the deferral of 4.000 by a wide margin,
    so a cost window would credit it. The admissible value is still exactly 0.000.
    """

    certificate = admissible_certificate(
        exclusion_family(0.9, 0.25), catalogue_source=CATALOGUE_SOURCE
    )
    assert certificate["complete"] is True
    assert certificate["value_of_the_repair_catalogue_admissible"] == pytest.approx(0.0, abs=TOLERANCE)
    assert certificate["value_of_the_repair_catalogue_unconstrained"] == pytest.approx(2.75, abs=TOLERANCE)


def test_the_discontinuity_is_a_family_property_and_not_a_theorem() -> None:
    """The recorded licensing-gap families have both quantities strictly positive at once.

    There the catalogue supplies a *premise* that unlocks a separate excluding readout,
    rather than being the only informative action itself, so the price of the boundary and
    the value of the repair coexist. Asserting it here keeps the claim above narrow.
    """

    for name in ("licensing_gap_replacement", "licensing_gap_composed"):
        problem = LICENSING_GAP_FAMILIES[name]()
        price = price_of_admissibility(problem)["price_of_admissibility"]
        value = admissible_certificate(problem, catalogue_source=REPAIR_SOURCE)[
            "value_of_the_repair_catalogue_admissible"
        ]
        assert price == pytest.approx(0.75, abs=TOLERANCE), name
        assert value == pytest.approx(0.25, abs=TOLERANCE), name
        assert price > TOLERANCE and value > TOLERANCE, name


def test_the_declared_family_rejects_an_undeclarable_detection_power() -> None:
    """A power below one half would make the control's own labelling meaningless."""

    with pytest.raises(ValueError):
        exclusion_family(0.4)
    with pytest.raises(ValueError):
        exclusion_family(0.9, 0.0)
