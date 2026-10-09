"""Utility, covariance-only protection, and integration-bound checks."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

spec = importlib.util.spec_from_file_location("decision_utility", Path(__file__).with_name("utility.py"))
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)


def useful_measurement():
    mean = np.r_[[6., 5., 4., 3., 2., 1.9], np.zeros(6)]
    direction = np.array([100., 100., 100., 100., 100., 103.])
    covariance = np.zeros((12, 12)); covariance[:6, :6] = np.outer(direction, direction)
    covariance[:6, 6] = direction; covariance[6, :6] = direction; covariance[6, 6] = 1.
    return mean, covariance


def test_known_useful_measurement_uses_same_conditioned_incumbent():
    mean, covariance = useful_measurement()
    gains, caps = decision.expected_gains(mean, covariance, range(5), np.arange(-2., 3.))
    np.testing.assert_allclose(gains[0], [0., 0., 0., 2.9, 5.9], atol=1e-12)
    np.testing.assert_allclose(caps[0], 9.)
    np.testing.assert_array_equal(gains[1:], 0.)


def test_gate_rejects_uncertain_mean_improvement_and_accepts_precise_improvement():
    mean = np.array([6., 5., 4., 3., 2., 2.1]); before = mean.copy()
    covariance = np.eye(6); covariance_before = covariance.copy()
    rejected = decision.protected_selection(mean, covariance, range(5))
    assert not rejected["accepted"] and rejected["selected"] == list(range(5))
    assert rejected["incoming"] == [5] and rejected["outgoing"] == [4]
    assert rejected["pair_probabilities"][0]["probability"] < 1-(1-.95)/(25*8)
    accepted = decision.protected_selection(mean, covariance*1e-8, range(5))
    assert accepted["accepted"] and accepted["selected"] == [0, 1, 2, 3, 5]
    np.testing.assert_array_equal(mean, before); np.testing.assert_array_equal(covariance, covariance_before)


def test_vectorized_gate_matches_single_posterior_gate():
    mean, covariance = useful_measurement(); normals = np.array([-2., 0., 1., 4.])
    gains, _ = decision.expected_gains(mean, covariance, range(5), normals, gated=True)
    direction = covariance[:6, 6]
    conditional = covariance[:6, :6]-np.outer(direction, direction)
    for i, z in enumerate(normals):
        posterior = mean[:6]+direction*z
        protected = decision.protected_selection(posterior, conditional, range(5))
        expected = posterior[protected["selected"]].sum()-posterior[:5].sum()
        np.testing.assert_allclose(gains[0, i], expected, atol=1e-12)


def test_multicomparison_integration_bound_and_tail_clipping_are_explicit():
    mean, covariance = useful_measurement(); normals = np.r_[np.zeros(511), 100.]
    result = decision.estimate(mean, covariance, range(5), normals)
    assert result["gross_model_EVSI_sample"][0] > result["truncated_EVSI_sample"][0]
    expected = result["truncated_EVSI_sample"]-result["cap"]*np.sqrt(np.log(146*8/.05)/(2*512))
    np.testing.assert_allclose(result["mc_lower"], expected)
    assert result["mc_integration_only"]
    assert norm.ppf(1-(1-.95)/(25*8)) > norm.ppf(1-(1-.95)/25)


def test_default_permissions_block_screening_and_functional_endpoint_is_forbidden():
    assert len(decision.permission_blocks()) == 3
    assert not decision.permission_blocks(independent_model_risk_certificate=True,
                                         cost_utility_registered=True, failure_latency_registered=True)
    assert decision.permission_blocks(endpoint="viability", independent_model_risk_certificate=True,
                                     cost_utility_registered=True, failure_latency_registered=True)
    with pytest.raises(ValueError, match="scientific_permission"):
        decision.utility([1., 2.], endpoint="viability")
    assert decision.utility([1., -.5]) == .5


def test_zero_variance_is_finite_and_deterministic_ties_are_not_safe_improvement():
    mean = np.zeros(292); covariance = np.zeros((292, 292)); incumbent = list(range(5))
    result = decision.estimate(mean, covariance, incumbent, np.zeros(512), gated=True)
    for key in ("gross_model_EVSI_sample", "truncated_EVSI_sample", "mc_lower", "cap"):
        np.testing.assert_array_equal(result[key], np.zeros(146))
    rejected = decision.protected_selection(mean[:146], covariance[:146, :146], [1, 2, 3, 4, 5])
    assert not rejected["accepted"] and rejected["pair_probabilities"][0]["probability"] == .5


def test_uncertified_policy_never_reads_A_and_charges_only_five_B():
    from research.decision_value import validation
    prior = np.arange(146.)
    fitted = {"joint": np.eye(292), "offset": np.zeros(146)}
    result = validation.run_policy(prior, fitted, lambda i: pytest.fail("uncertified purchase"), "certified_evsi")
    assert result["purchased_A"] == [] and result["cost"] == 5
    assert len(result["permission_blocks"]) == 3 and result["selected"] == list(range(145, 140, -1))


def test_rejected_selection_preserves_paid_observation_in_posterior(monkeypatch):
    from research.decision_value import validation
    calls = []
    def scores(*args, **kwargs):
        lower = np.full(146, -1.)
        if not calls:
            lower[0] = 1.
        return {"mc_lower": lower, "cap": np.ones(146)}
    monkeypatch.setattr(validation, "estimate", scores)
    prior = np.arange(146.)
    covariance = validation.posterior.common_joint(np.eye(146), np.ones(146))
    def buy(index):
        calls.append(index)
        return 284.
    result = validation.shadow(prior, np.zeros(146), covariance, buy, gated=True)
    assert calls == [0] and result["cost"] == 6
    assert result["posterior_mean_B"][0] == 142.
    assert result["selected"] == list(range(145, 140, -1))
    assert not result["history"][0]["update_gate"]["accepted"]
