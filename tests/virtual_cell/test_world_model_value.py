"""Contract tests for decision-level world-model admission (src/maestro/world_model_value.py)."""
from __future__ import annotations

import math

import pytest

from maestro.world_model_value import (
    IncrementEstimate,
    PhenotypeBridge,
    ValueCeiling,
    admit_world_model,
    plan_measure_or_predict,
    realised_fraction,
)

SAME_WELL = PhenotypeBridge("survival_selectivity_5uM", "STATE X_hvg mean deviation", "spheroid", True, True, True, "tahoe")


def ceiling(oracle=0.30, cheap=None, units=40, mub=0.05, endpoint="survival_selectivity_5uM"):
    return ValueCeiling(endpoint, "within-context pearson r", oracle, cheap if cheap is not None else {"basal_kernel": 0.20, "organ": 0.08}, units, mub)


def test_a_same_unit_bridge_with_headroom_is_admitted_and_names_the_best_cheap_prior():
    verdict = admit_world_model(SAME_WELL, ceiling())
    assert verdict.admitted and verdict.reasons == ()
    assert verdict.best_cheap_prior == "basal_kernel"
    assert verdict.margin == pytest.approx(0.10)


def test_a_perfect_forecast_that_cannot_beat_the_cheap_prior_is_refused_by_name():
    verdict = admit_world_model(SAME_WELL, ceiling(oracle=0.22))
    assert not verdict.admitted and verdict.reasons == ("WM_CEILING_BELOW_MUB",)
    assert verdict.margin == pytest.approx(0.02)


def test_cross_assay_or_cross_dose_pairing_is_not_an_authenticated_bridge():
    cross = PhenotypeBridge("survival_selectivity_5uM", "L1000 signature", "different assay", False, False, True, "lincs+ctrp")
    assert "BRIDGE_NOT_SAME_UNIT" in admit_world_model(cross, ceiling()).reasons


def test_a_bridge_for_another_endpoint_cannot_license_this_one():
    assert "BRIDGE_ENDPOINT_MISMATCH" in admit_world_model(SAME_WELL, ceiling(endpoint="g1_selectivity_5uM")).reasons


def test_too_few_reference_contexts_and_unestimated_scores_refuse():
    assert "INSUFFICIENT_REFERENCE_UNITS" in admit_world_model(SAME_WELL, ceiling(units=4)).reasons
    verdict = admit_world_model(SAME_WELL, ceiling(oracle=math.nan))
    assert not verdict.admitted and "CEILING_UNESTIMATED" in verdict.reasons and verdict.margin is None
    assert "CEILING_UNESTIMATED" in admit_world_model(SAME_WELL, ceiling(cheap={})).reasons


def test_minimum_useful_benefit_must_be_declared_positive():
    with pytest.raises(ValueError):
        ceiling(mub=0.0)


def test_realised_fraction_reports_recovered_headroom_and_refuses_without_headroom():
    assert realised_fraction(0.30, 0.25, 0.20) == pytest.approx(0.5)
    assert realised_fraction(0.30, 0.10, 0.20) == pytest.approx(-1.0)
    assert realised_fraction(0.20, 0.25, 0.20) is None


def est(point, lower, upper, units=48, domain="mixseq_10x_24h_to_prism_5d"):
    return IncrementEstimate(point, lower, upper, units, domain)


def test_a_forecast_whose_lower_bound_clears_the_mub_is_admitted():
    plan = plan_measure_or_predict(est(0.1, -0.2, 0.3), est(0.12, 0.07, 0.2), minimum_useful_benefit=0.05)
    assert plan.action == "ADMIT_WORLD_MODEL" and plan.reasons == ()


def test_measure_early_needs_the_measurement_lower_bound_and_names_the_failed_transport():
    plan = plan_measure_or_predict(est(0.2, 0.08, 0.3), est(-0.09, -0.18, -0.005), minimum_useful_benefit=0.05)
    assert plan.action == "MEASURE_EARLY" and plan.reasons == ("WM_TRANSPORT_UNQUALIFIED",)


def test_the_block_k_development_point_estimate_would_now_abstain():
    # development: ceiling +0.139 [-0.049, +0.298]; forecast -0.150 [-0.326, +0.064]
    plan = plan_measure_or_predict(est(0.139, -0.049, 0.298, units=24), est(-0.150, -0.326, 0.064, units=24), minimum_useful_benefit=0.05)
    assert plan.action == "ABSTAIN"
    assert set(plan.reasons) == {"FORECAST_INCONCLUSIVE", "MEASUREMENT_INCONCLUSIVE"}


def test_use_prior_only_when_every_interval_is_wholly_below_the_mub():
    plan = plan_measure_or_predict(est(-0.107, -0.155, -0.059, units=16), None, minimum_useful_benefit=0.05)
    assert plan.action == "USE_PRIOR"
    assert plan.reasons == ("WM_FORECAST_NOT_EVALUATED", "WM_CEILING_BELOW_MUB")
    assert plan_measure_or_predict(None, None, minimum_useful_benefit=0.05).action == "USE_PRIOR"


def test_too_few_reference_units_abstains_and_bad_estimates_are_rejected():
    plan = plan_measure_or_predict(est(0.3, 0.2, 0.4, units=6), None, minimum_useful_benefit=0.05)
    assert plan.action == "ABSTAIN" and plan.reasons == ("INSUFFICIENT_REFERENCE_UNITS_MEASUREMENT",)
    with pytest.raises(ValueError):
        est(0.1, 0.2, 0.3)
    with pytest.raises(ValueError):
        est(math.nan, 0.0, 0.1)
    with pytest.raises(ValueError):
        plan_measure_or_predict(None, None, minimum_useful_benefit=0.0)
