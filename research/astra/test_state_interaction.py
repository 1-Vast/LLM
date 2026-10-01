"""Contracts for diagnostic scope, residual identities and decision semantics."""
import numpy as np
import pytest

from research.astra.state_interaction import (
    action_center, choices, compare_choices, development_shrinkage,
    double_center, matched_permutation_diagnostic, residual_diagnostics,
    split_reliability,
)


def test_common_state_shift_has_no_interaction():
    utility = np.array([[1., 3., 6.], [11., 13., 16.]])
    assert np.allclose(double_center(utility), 0)
    assert np.allclose(action_center(utility)[0], action_center(utility)[1])


def test_centering_removes_both_main_effects_but_preserves_interaction():
    utility = np.array([[0., 2.], [4., 1.]])
    centered = double_center(utility)
    assert np.allclose(centered.mean(axis=0), 0)
    assert np.allclose(centered.mean(axis=1), 0)
    assert not np.allclose(centered, 0)


def test_lower_rank_swap_is_not_best_action_change():
    utility = np.array([[5., 2., 1.], [5., 1., 2.]])
    selected = choices(utility, 0)
    assert compare_choices(*selected, *utility, 0) == "subordinate_relation_change"


def test_ties_abstentions_and_real_switches_are_distinct():
    utility = np.array([[0., 0., -1.], [2., 1., 0.], [0., 1., 2.]])
    selected = choices(utility, 1e-6)
    assert selected[0]["selected"] is None
    assert selected[0]["exact_top_tie"]
    assert compare_choices(selected[0], selected[1], utility[0], utility[1], 1e-6) == "abstention_change"
    assert compare_choices(selected[1], selected[2], utility[1], utility[2], 1e-6) == "best_action_change"


def test_residual_risk_identity_and_shrinkage():
    baseline = np.ones((3, 2))
    truth = baseline + np.arange(6).reshape(3, 2)
    prediction = baseline + 4 * (truth - baseline)
    diagnostic = residual_diagnostics(truth, baseline, prediction)
    assert diagnostic["risk_difference"] == pytest.approx(diagnostic["identity_difference"])
    assert development_shrinkage(truth, baseline, prediction, split="development") == pytest.approx(.25)


def test_test_outcomes_cannot_select_shrinkage():
    with pytest.raises(ValueError, match="never test"):
        development_shrinkage([[1]], [[0]], [[2]], split="test")


def test_zero_residual_prediction_is_allowed():
    assert development_shrinkage([[2]], [[1]], [[1]], split="development") == 0


def test_matched_permutation_is_reproducible_and_cannot_use_unmatched_rows():
    truth = np.arange(8).reshape(4, 2)
    first = matched_permutation_diagnostic(truth, truth, repeats=30)
    assert first == matched_permutation_diagnostic(truth, truth, repeats=30)
    assert first["observed_MSE"] == 0
    assert first["permutation_MSE_mean"] > 0
    with pytest.raises(ValueError, match="Matched shapes"):
        matched_permutation_diagnostic(truth, np.arange(10).reshape(5, 2))


@pytest.mark.parametrize("utility", [[[np.nan, 1]], [[]], []])
def test_invalid_utility_is_rejected(utility):
    with pytest.raises(ValueError):
        choices(utility, 0)


def test_negative_tolerance_rejected():
    with pytest.raises(ValueError):
        choices([[1, 2]], -1)


def test_shared_control_noise_cancels_in_action_difference():
    first = {"a": [[5., 7.]], "b": [[2., 3.]]}
    second = {"a": [[5., 7.]], "b": [[2., 3.]]}
    result = split_reliability(first, second, [[0., 0.]], [[10., 20.]])
    assert result["action_contrasts"][0]["split_RMS"] == 0
    for diagnostic in result["absolute_response"].values():
        assert diagnostic["shared_control_split_RMS"] == 0
        assert diagnostic["independent_control_split_RMS"] > 0


def test_reliability_rejects_unmatched_actions():
    with pytest.raises(ValueError, match="action sets"):
        split_reliability({"a": [[1]]}, {"b": [[1]]}, [[0]], [[0]])
