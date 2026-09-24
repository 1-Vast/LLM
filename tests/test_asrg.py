import numpy as np
import pytest

from evaluation.asrg import action_gain, loss


def test_direction_matters_at_equal_candidate_norm():
    goal = [0.6, 0.0]
    assert action_gain(goal, [0, 0], [0.7, 0]) > 0
    assert action_gain(goal, [0, 0], [0, 0.7]) < 0


def test_overcorrection_and_equivalence_to_distance():
    goal = np.array([0.6, 0.0])
    current = np.array([0.0, 0.0])
    candidate = np.array([1.5, 0.0])
    gain = action_gain(goal, current, candidate)
    assert gain < 0
    assert np.isclose(gain, np.sum((current-goal)**2) - np.sum((candidate-goal)**2))


def test_invalid_geometry_rejected():
    with pytest.raises(ValueError, match="response_shape_mismatch"):
        action_gain([1, 2], [0, 0], [1])
    with pytest.raises(ValueError, match="invalid_response_or_weights"):
        action_gain([1], [0], [float("nan")])
    with pytest.raises(ValueError, match="invalid_response_or_weights"):
        action_gain([1], [0], [1], [-1])
