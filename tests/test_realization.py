"""The biological anchor: monotone realisation coordinates and their identifiability.

File summary
- Path: tests/test_realization.py
- Purpose: pin the section-31/42/43 contract — the residual coordinate is monotone by
  construction, its absolute scale needs an anchor, the monotone-reparameterisation family is
  demonstrated rather than asserted, and the four ablations are declared as unrun.
- Core points: assertions here are contract tests, not biological results.
- Interfaces: `test_residual_is_monotone_and_bounded()`, `test_absolute_scale_needs_an_anchor()`,
  `test_monotone_reparameterisation_is_not_identified()`,
  `test_self_combination_rule_gap_depends_on_shape()`,
  `test_alignment_disagreement_names_the_inverted_pairs()`,
  `test_ablation_arms_are_declared_and_not_claimed_as_run()`
- Depends on: virtual_cell.realization
"""
import math

import pytest

from virtual_cell.realization import (
    ABLATION_ARMS,
    AlignmentEntry,
    MonotoneRealization,
    ScaleAnchor,
    ablation_plan,
    alignment_disagreement,
    monotone_reparameterisation_demo,
    self_combination_residual,
)


def _realization(hill: float = 1.0, compound: str = "compound-a") -> MonotoneRealization:
    return MonotoneRealization(
        compound=compound,
        context_identifier="NCI-H596",
        mode="drug",
        exposure_hours=24.0,
        log_ec50=math.log(1.0),
        hill=hill,
        dose_window=(0.0, 100.0),
        measured_points=6,
        source="declared test fit",
    )


def test_residual_is_monotone_and_bounded():
    realization = _realization()
    doses = [0.0, 0.01, 0.1, 1.0, 10.0, 100.0]
    residuals = [realization.residual(dose) for dose in doses]
    assert residuals[0] == 1.0
    assert all(0.0 < value <= 1.0 for value in residuals)
    assert all(later < earlier for earlier, later in zip(residuals, residuals[1:]))
    assert realization.residual(1.0) == pytest.approx(0.5)
    assert realization.dose_for_residual(0.5) == pytest.approx(1.0)
    assert realization.dose_for_residual(0.999) == 0.0 or realization.dose_for_residual(0.999) > 0
    assert realization.dose_for_residual(0.001) is None
    with pytest.raises(ValueError):
        realization.dose_for_residual(0.0)


def test_absolute_scale_needs_an_anchor():
    realization = _realization()
    ordinal = realization.identifiability([ScaleAnchor.NONE])
    assert ordinal.level == "ordinal_only"
    assert ordinal.absolute_scale_licensed is False
    assert any("percent inhibition" in item for item in ordinal.limitations)
    with pytest.raises(ValueError, match="ordinal-only"):
        realization.require_absolute_scale([ScaleAnchor.NONE])

    scaled = realization.require_absolute_scale([ScaleAnchor.MEASURED_FUNCTIONAL_STRENGTH])
    assert scaled.absolute_scale_licensed is True
    assert scaled.level == "scaled"
    # Fail closed: the self-combination identity is not exact, and it may pin the scale
    # only inside a dose window that was validated. An anchor offered without one is
    # refused by name, not granted. The previous behaviour granted it unconditionally.
    unvalidated = realization.identifiability([ScaleAnchor.SELF_COMBINATION])
    assert unvalidated.level == "ordinal_only"
    assert unvalidated.absolute_scale_licensed is False
    assert "self_combination_anchor_without_validated_dose_window" in unvalidated.limitations
    with pytest.raises(ValueError, match="ordinal-only"):
        realization.require_absolute_scale([ScaleAnchor.SELF_COMBINATION])

    validated = MonotoneRealization(
        compound="compound-a",
        context_identifier="NCI-H596",
        mode="drug",
        exposure_hours=24.0,
        log_ec50=math.log(1.0),
        hill=1.0,
        dose_window=(0.0, 100.0),
        measured_points=6,
        source="declared test fit",
        dose_window_validated=True,
    )
    self_combined = validated.identifiability([ScaleAnchor.SELF_COMBINATION])
    assert self_combined.absolute_scale_licensed is False
    assert "structural assumptions" in self_combined.statement


def test_monotone_reparameterisation_is_not_identified():
    # r' = r^2 as the second coordinate, with V'(r') = k sqrt(r') the paired response.
    realization = _realization()
    doses = [0.1, 0.5, 1.0, 2.0, 5.0]
    demonstration = monotone_reparameterisation_demo(realization, doses=doses, response_slope=2.0)
    assert demonstration["identifications_agree_on_the_grid"] is True
    assert all(
        row["responses_agree"] and row["residual_under_identification_1"] != row["residual_under_identification_2"]
        for row in demonstration["rows"]
    )


def test_self_combination_rule_gap_depends_on_shape():
    hyperbolic = self_combination_residual(_realization(hill=1.0), [(1.0, 2.0)])
    assert hyperbolic["rows"][0]["rule_gap"] == pytest.approx(0.25 - 0.5 * (1 / 3), abs=1e-12)
    assert hyperbolic["gap_sign"] == "dose_addition_leaves_more_function"
    cooperative = self_combination_residual(_realization(hill=3.0), [(1.0, 2.0)])
    assert cooperative["rows"][0]["rule_gap"] < 0.0
    assert cooperative["gap_sign"] == "independent_action_leaves_more_function"
    outside = self_combination_residual(_realization(), [(80.0, 80.0)])
    assert outside["rows"][0]["reason"] == "outside_declared_window"


def test_alignment_disagreement_names_the_inverted_pairs():
    entries = (
        AlignmentEntry("compound-a", dose=1.0, residual=0.10),
        AlignmentEntry("compound-b", dose=2.0, residual=0.80),
    )
    report = alignment_disagreement(entries)
    assert report["orders_agree"] is False
    assert report["inversions"][0]["pair"] == ["compound-a", "compound-b"]
    assert report["order_by_nominal_dose"] == ["compound-a", "compound-b"]
    assert report["order_by_realized_residual"] == ["compound-b", "compound-a"]

    agreed = alignment_disagreement(
        (
            AlignmentEntry("compound-a", dose=1.0, residual=0.10),
            AlignmentEntry("compound-b", dose=2.0, residual=0.05),
        )
    )
    assert agreed["orders_agree"] is True
    assert agreed["inversions"] == []


def test_ablation_arms_are_declared_and_not_claimed_as_run():
    plan = ablation_plan()
    assert {item["arm"] for item in plan["arms"]} == set(ABLATION_ARMS)
    assert plan["executed"] is False
    assert all(item["executed"] is False for item in plan["arms"])
    assert "not run" in plan["reading"]
