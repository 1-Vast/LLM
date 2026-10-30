"""Contract tests for basal-similarity phenotype transfer (src/virtual_cell/context_transfer.py)."""
from __future__ import annotations

import numpy as np
import pytest

from virtual_cell.context_transfer import VALIDATED_SCOPE, transfer_prior


def test_the_most_similar_reference_dominates_at_low_temperature():
    basal = np.eye(3)
    outcomes = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, -1.0]])
    prior = transfer_prior(np.array([0.9, 0.1, 0.0]), basal, outcomes, tau=0.01)
    assert prior.refusal is None and prior.scope == VALIDATED_SCOPE
    assert prior.values == pytest.approx([1.0, 0.0], abs=1e-3)
    assert prior.weights.sum() == pytest.approx(1.0)


def test_missing_reference_outcomes_are_skipped_not_read_as_zero():
    prior = transfer_prior(np.array([1.0, 0.0]), np.array([[1.0, 0.0], [0.9, 0.1]]), np.array([[np.nan], [2.0]]), tau=1.0)
    assert prior.values[0] == pytest.approx(2.0)


def test_a_condition_no_reference_measured_has_no_prior():
    prior = transfer_prior(np.array([1.0, 0.0]), np.array([[1.0, 0.0], [0.0, 1.0]]), np.array([[np.nan], [np.nan]]))
    assert np.isnan(prior.values[0])


def test_top_m_restricts_transfer_to_the_nearest_references():
    basal = np.array([[1.0, 0.0, 0.0], [0.8, 0.2, 0.0], [0.0, 0.0, 1.0]])
    outcomes = np.array([[1.0], [1.0], [-50.0]])
    prior = transfer_prior(np.array([1.0, 0.1, 0.0]), basal, outcomes, tau=10.0, top_m=2)
    assert prior.values[0] == pytest.approx(1.0) and prior.weights[2] == 0.0


def test_unusable_inputs_are_refused_by_name():
    assert transfer_prior(np.ones(2), np.empty((0, 2)), np.empty((0, 1))).refusal == "NO_REFERENCE_CONTEXTS"
    assert transfer_prior(np.ones(3), np.ones((2, 2)), np.ones((2, 1))).refusal == "BASAL_AXIS_MISMATCH"
    assert transfer_prior(np.array([np.nan, 1.0]), np.ones((2, 2)), np.ones((2, 1))).refusal == "NONFINITE_BASAL"
    with pytest.raises(ValueError):
        transfer_prior(np.ones(2), np.eye(2), np.ones((2, 1)), tau=0.0)
