"""Counterexamples for offline coordinate and actual-n sampling diagnostics."""
import json

import numpy as np
import pytest

from tools.analysis.observation_audit import main, numerical_axis_matches, projection_variance


def test_alias_needs_an_informative_contrast_and_consistency_is_not_independent():
    raw = np.array([[1, 1], [2, 2], [0, 3]], dtype=float)
    aliased = numerical_axis_matches(['TNF', 'SDK2'], raw[:2], raw[:2, :1], ['TNF'])
    assert not aliased['all_coordinates_matched']
    assert aliased['records'][0]['matching_source_indices'] == [0, 1]
    unique = numerical_axis_matches(['TNF', 'SDK2'], raw, raw[:, :1], ['TNF'],
                                    consistency=(raw[:1], raw[:1, :1]))
    assert unique['all_coordinates_matched']
    assert not unique['independent_validation']
    assert not unique['model_output_axis_authenticated']


@pytest.mark.parametrize('raw,target', [([[0, 1], [0, 2]], [[0], [0]]),
                                      ([[1e-7, 1], [2e-7, 2]], [[1e-7], [2e-7]])])
def test_zero_or_tiny_support_cannot_authenticate(raw, target):
    result = numerical_axis_matches(['A', 'B'], raw, target, ['A'])
    assert not result['all_coordinates_matched']


def test_wrong_coordinate_or_inconsistent_exposed_rows_fails():
    raw = np.array([[1, 2], [3, 4]], dtype=float)
    assert not numerical_axis_matches(['A', 'B'], raw, raw[:, 1:], ['A'])['all_coordinates_matched']
    result = numerical_axis_matches(['A', 'B'], raw, raw[:, :1], ['A'],
                                    consistency=(raw, raw[:, :1] + 0.1))
    assert not result['all_coordinates_matched']


@pytest.mark.parametrize('targets', [
    [[0, -2], [0, -2], [0, 2]],  # zero support and tied absolute responses
    [[-2, -2], [-2, -2], [2, 2]],  # negative expressions and duplicate trajectories
    [[1, 0], [1, 0], [1, 0]],  # deliberately declared against the wrong columns
])
def test_row_filter_matches_independent_full_broadcast_oracle(targets):
    raw = np.array([[0, -2, -2, 1], [0, -2, -2, 1], [0, 2, 3, 1]], dtype=float)
    targets = np.array(targets, dtype=float)
    result = numerical_axis_matches(['A', 'B', 'C', 'D'], raw, targets, ['A', 'B'])
    for column, record in enumerate(result['records']):
        oracle = np.flatnonzero(np.all(np.abs(raw - targets[:, column, None]) <= 1e-5, axis=0)).tolist()
        assert record['matching_source_indices'] == oracle
        assert record['expected_max_error'] == float(np.max(np.abs(raw[:, column] - targets[:, column])))
        assert record['nonzero_rows'] == int(np.count_nonzero(np.abs(targets[:, column]) > 1e-5))
        assert record['passed'] == (oracle == [column] and record['nonzero_rows'] >= 2)


@pytest.mark.parametrize('names,raw,target,symbols', [
    (['A', 'A'], [[1, 2]], [[1]], ['A']),
    (['A'], [[float('nan')]], [[1]], ['A']),
    (['A'], [[1], [2]], [[1]], ['A']),
    (['A'], [[1]], [[1]], ['B']),
    (['A'], [[1]], [[1, 1]], ['A', 'A']),
])
def test_invalid_coordinate_inputs_are_rejected(names, raw, target, symbols):
    with pytest.raises(ValueError):
        numerical_axis_matches(names, raw, target, symbols)


def test_actual_n_and_covariance_match_direct_computation():
    values = np.array([[1, 2], [2, 4], [4, 8]], dtype=float)
    weights = np.array([0.5, 0.5])
    result = projection_variance(values, weights)
    expected = float(weights @ np.cov(values, rowvar=False, ddof=1) @ weights / len(values))
    assert result['cells'] == 3
    assert result['scalar_sample_mean_variance'] == pytest.approx(expected)
    assert result['scalar_sample_mean_variance'] != pytest.approx(expected * 3 / 32)
    assert result['full_to_diagonal_ratio'] > 1
    assert result['independent_biological_units'] is None


def test_general_weights_and_exact_cancellation():
    values = np.array([[1, 2], [3, 6], [4, 8]], dtype=float)
    result = projection_variance(values, [2, -1])
    assert result['scalar_sample_variance'] == 0
    assert result['scalar_sample_mean_variance'] == 0
    assert result['diagonal_only_sample_mean_variance'] > 0
    assert result['covariance_sample_mean_variance'] < 0
    constant = projection_variance(np.ones((3, 2)), [1, 1])
    assert constant['full_to_diagonal_ratio'] is None
    assert constant['scalar_mean'] == 2  # no implicit weight normalization


@pytest.mark.parametrize('values,weights', [([[1]], [1]), ([[1], [2]], [0]),
                                          ([[1], [2]], [np.inf]),
                                          ([[1, 2], [3, 4]], [1]),
                                          ([[1], [np.nan]], [1])])
def test_invalid_variance_inputs_fail(values, weights):
    with pytest.raises(ValueError):
        projection_variance(values, weights)


def test_local_npz_cli_consumes_explicit_arrays(tmp_path, capsys):
    path = tmp_path / 'input.npz'
    np.savez(path, names=np.array(['A', 'B']), raw=[[1, 2], [3, 4]],
             targets=[[1], [3]], symbols=np.array(['A']), values=[[1], [3]], weights=[1])
    main(['axis', str(path)])
    result = json.loads(capsys.readouterr().out)
    assert result['all_coordinates_matched']
    assert not result['source_identity_authenticated']
    main(['variance', str(path)])
    assert json.loads(capsys.readouterr().out)['scalar_sample_mean_variance'] == 1
