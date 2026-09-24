"""The exclusion budget a rule-out requires, and what the budget still cannot buy.

File summary
- Path: tests/test_exclusion_licensing.py
- Purpose: pin three things about the tolerance-parameterised licensing rule, so none of
  them can move silently: that it reproduces the recorded admissible class exactly at the
  recorded tolerance; that the budget at which a rule-out starts licensing is exactly the
  rule-out's own declared error rate; and that granting the budget cannot rescue a weak
  rule-out, because the licensed act still carries the residual loss.
- Core points:
  - Equivalence at 1e-9 is asserted on every recorded family, so this module extends the
    recorded objective rather than competing with it.
  - Two thresholds are separate and both exact. Licensing needs `tau >= alpha`. Value
    needs `alpha < (deferral - cost) / wrong`, because the licensed act is still scored
    against the full posterior and therefore costs `alpha * wrong`.
  - Raising the budget must not loosen tie-breaking; the tie tolerance is held fixed and
    that separation is asserted against the source.
- Interfaces: pytest test functions
- Depends on: evaluation.exclusion_licensing, evaluation.admissible,
  evaluation.exclusion_discontinuity, evaluation.contingent_suite, evaluation.licensing_gap
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.admissible import (  # noqa: E402
    admissible_certificate,
    admissible_terminal,
    price_of_admissibility,
    solve_admissible_policy,
)
from evaluation.contingent_suite import FAMILIES as RECORDED_FAMILIES  # noqa: E402
from evaluation.exclusion_discontinuity import (  # noqa: E402
    CATALOGUE_SOURCE,
    DEFERRAL,
    WRONG,
    exclusion_family,
)
from evaluation.exclusion_licensing import (  # noqa: E402
    RECORDED_EXCLUSION_TOLERANCE,
    TIE_TOLERANCE,
    admissible_certificate_at,
    admissible_terminal_at,
    exclusion_tolerance_sweep,
    price_of_admissibility_at,
    solve_admissible_policy_at,
)
from evaluation.licensing_gap import (  # noqa: E402
    FAMILIES as LICENSING_GAP_FAMILIES,
    REPAIR_SOURCE,
)

TOLERANCE = 1e-6
CONTROL = "orthogonal_context_control"
EXCLUDING_OUTCOME = "control_context_resistant"
CONTROL_COST = 1.0


def _every_recorded_family() -> dict[str, object]:
    families = {name: build() for name, build in RECORDED_FAMILIES.items()}
    families.update({name: build() for name, build in LICENSING_GAP_FAMILIES.items()})
    return families


def _expected_value(power: float, cost: float = CONTROL_COST) -> float:
    """What the rule-out can be worth once its budget is granted.

    The licensed act is still scored against the full posterior, so it costs
    `alpha * wrong`. Buying the rule-out is therefore worth `deferral - cost -
    alpha * wrong`, and worth nothing at all when that is not positive.
    """

    alpha = 1.0 - power
    return max(0.0, DEFERRAL - cost - alpha * WRONG)


def test_at_the_recorded_tolerance_the_two_implementations_agree() -> None:
    """The extension must reduce to the recorded objective, family by family."""

    for name, problem in _every_recorded_family().items():
        recorded = solve_admissible_policy(problem).expected_loss
        extended = solve_admissible_policy_at(
            problem, exclusion_tolerance=RECORDED_EXCLUSION_TOLERANCE
        ).expected_loss
        assert extended == pytest.approx(recorded, abs=TOLERANCE), name
        # The terminal rule returns (decision, loss); compare the two separately, because
        # a mixed string/float sequence is not something approx can be asked to compare.
        recorded_decision, recorded_loss = admissible_terminal(problem, ())
        extended_decision, extended_loss = admissible_terminal_at(
            problem, (), exclusion_tolerance=RECORDED_EXCLUSION_TOLERANCE
        )
        assert extended_decision == recorded_decision, name
        assert extended_loss == pytest.approx(recorded_loss, abs=TOLERANCE), name


def test_the_recorded_price_and_certificate_are_reproduced() -> None:
    """Both reported quantities, not only the optimum, agree at the recorded tolerance."""

    for name in ("licensing_gap_replacement", "licensing_gap_composed"):
        problem = LICENSING_GAP_FAMILIES[name]()
        recorded_price = price_of_admissibility(problem)["price_of_admissibility"]
        extended_price = price_of_admissibility_at(
            problem, exclusion_tolerance=RECORDED_EXCLUSION_TOLERANCE
        )["price_of_admissibility"]
        assert extended_price == pytest.approx(recorded_price, abs=TOLERANCE), name
        recorded_value = admissible_certificate(problem, catalogue_source=REPAIR_SOURCE)[
            "value_of_the_repair_catalogue_admissible"
        ]
        extended_value = admissible_certificate_at(
            problem,
            exclusion_tolerance=RECORDED_EXCLUSION_TOLERANCE,
            catalogue_source=REPAIR_SOURCE,
        )["value_of_the_repair_catalogue_admissible"]
        assert extended_value == pytest.approx(recorded_value, abs=TOLERANCE), name


@pytest.mark.parametrize("power", [0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
def test_the_licensing_threshold_is_exactly_the_declared_error_rate(power: float) -> None:
    """After the excluding outcome, the attribution is licensed at `alpha` and not below.

    This is what makes the tolerance an identified quantity rather than a knob: the budget
    a rule-out needs is the posterior mass it leaves on the hypothesis it ruled out, which
    is its own declared false-exclusion rate.
    """

    problem = exclusion_family(power, CONTROL_COST)
    alpha = 1.0 - power
    history = ((CONTROL, EXCLUDING_OUTCOME),)
    below, _ = admissible_terminal_at(
        problem, history, exclusion_tolerance=alpha * (1.0 - 1e-6)
    )
    at, _ = admissible_terminal_at(problem, history, exclusion_tolerance=alpha * (1.0 + 1e-6))
    assert below == "defer", power
    assert at == "continue", power


@pytest.mark.parametrize("power", [0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
def test_a_granted_budget_cannot_launder_a_weak_rule_out(power: float) -> None:
    """Licensing is necessary and not sufficient: the residual loss is still paid.

    At `alpha` the act becomes licensed, but it is scored against the full posterior and
    costs `alpha * wrong`. So the rule-out is worth something only while
    `alpha < (deferral - cost) / wrong`, which is 0.3 under the recorded convention. At
    detection powers 0.6 and 0.7 the value stays exactly 0.000 even with the budget
    granted, which is the property that stops the budget being a way to buy a decision
    with a bad test.
    """

    problem = exclusion_family(power, CONTROL_COST)
    alpha = 1.0 - power
    certificate = admissible_certificate_at(
        problem, exclusion_tolerance=alpha * (1.0 + 1e-6), catalogue_source=CATALOGUE_SOURCE
    )
    assert certificate["complete"] is True, power
    assert certificate["value_of_the_repair_catalogue_admissible"] == pytest.approx(
        _expected_value(power), abs=TOLERANCE
    ), power
    if alpha >= (DEFERRAL - CONTROL_COST) / WRONG:
        assert certificate["value_of_the_repair_catalogue_admissible"] == pytest.approx(
            0.0, abs=TOLERANCE
        ), power


def test_the_price_of_the_boundary_falls_once_the_rule_out_licenses() -> None:
    """The boundary stops being expensive exactly where the evidence starts licensing."""

    problem = exclusion_family(0.9, CONTROL_COST)
    alpha = 1.0 - 0.9
    dear = price_of_admissibility_at(problem, exclusion_tolerance=alpha * (1.0 - 1e-6))
    cheap = price_of_admissibility_at(problem, exclusion_tolerance=alpha * (1.0 + 1e-6))
    assert dear["price_of_admissibility"] == pytest.approx(2.0, abs=TOLERANCE)
    assert cheap["price_of_admissibility"] == pytest.approx(0.0, abs=TOLERANCE)
    assert dear["admissible_probability_defer"] == pytest.approx(1.0, abs=TOLERANCE)
    assert cheap["admissible_probability_defer"] == pytest.approx(0.0, abs=TOLERANCE)


def test_licensing_at_a_budget_is_still_counted_as_unsupported_at_the_strict_rule() -> None:
    """Raising the budget buys a decision, and the cost of the budget stays visible.

    The attribution metric is computed at the recorded 1e-9 rule, so an act licensed only
    by a granted budget is still counted as unsupported there. That is the honest
    accounting: a reader who refuses the budget can read the mass it bought.
    """

    problem = exclusion_family(0.9, CONTROL_COST)
    strict = price_of_admissibility_at(problem, exclusion_tolerance=1e-9)
    relaxed = price_of_admissibility_at(problem, exclusion_tolerance=0.1 * (1.0 + 1e-6))
    assert strict["admissible_unsupported_attribution"] == pytest.approx(0.0, abs=TOLERANCE)
    assert relaxed["admissible_unsupported_attribution"] > TOLERANCE


def test_the_sweep_reports_every_budget_it_required() -> None:
    """The sweep is the reporting form: one row per budget, with completeness."""

    rows = exclusion_tolerance_sweep(
        exclusion_family(0.9, CONTROL_COST),
        (1e-9, 0.01, 0.05, 0.1000001, 0.2),
        catalogue_source=CATALOGUE_SOURCE,
    )
    assert len(rows) == 5
    assert all(row["complete"] for row in rows)
    values = [row["value_of_the_repair_catalogue_admissible"] for row in rows]
    assert values[:3] == [pytest.approx(0.0, abs=TOLERANCE)] * 3
    assert values[3] == pytest.approx(_expected_value(0.9), abs=TOLERANCE)
    assert values[4] == pytest.approx(_expected_value(0.9), abs=TOLERANCE)


def test_a_budget_outside_the_unit_interval_is_refused() -> None:
    """A tolerance is a probability mass; 1.0 would exclude every hypothesis at once."""

    problem = exclusion_family(0.9, CONTROL_COST)
    with pytest.raises(ValueError):
        admissible_terminal_at(problem, (), exclusion_tolerance=1.0)
    with pytest.raises(ValueError):
        admissible_terminal_at(problem, (), exclusion_tolerance=-0.1)


def test_the_tie_tolerance_is_held_fixed_and_separate() -> None:
    """Raising the exclusion budget must not silently loosen tie-breaking."""

    assert TIE_TOLERANCE == RECORDED_EXCLUSION_TOLERANCE
    source = (ROOT / "src" / "evaluation" / "exclusion_licensing.py").read_text(encoding="utf-8")
    # The tie comparison must reference the fixed constant, not the declared budget.
    assert "abs(loss - best) <= TIE_TOLERANCE" in source
