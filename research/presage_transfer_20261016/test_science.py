"""Scientific falsification checks, separate from default software tests."""
import numpy as np
import evaluate as e


def test_withheld_outcomes_cannot_change_prediction():
    rng = np.random.default_rng(4)
    x, y = rng.normal(size=(20, 3)), rng.normal(size=(20, 5))
    train, test = np.arange(15), np.arange(15, 20)
    p = e.ridge_predict(x, y, train, test, 10)
    changed = y.copy()
    changed[test] = rng.normal(size=(5, 5)) * 10000
    np.testing.assert_array_equal(p, e.ridge_predict(x, changed, train, test, 10))


def test_test_feature_distribution_does_not_fit_normaliser():
    rng = np.random.default_rng(5)
    x, y = rng.normal(size=(20, 3)), rng.normal(size=(20, 5))
    train = np.arange(15)
    before = e.ridge_predict(x, y, train, np.array([15]), 10)
    x[16:] = 100000
    np.testing.assert_array_equal(before, e.ridge_predict(x, y, train, np.array([15]), 10))


def test_permutation_breaks_feature_correspondence_and_preserves_strata():
    embedding = np.eye(20)
    strata = np.repeat(np.arange(2), 10)[:, None]
    shuffled, perm = e.permute_rows(embedding, strata, 7)
    assert np.mean(perm != np.arange(20)) > .5
    np.testing.assert_array_equal(strata, strata[perm])
    np.testing.assert_array_equal(shuffled, embedding[perm])
    assert not np.array_equal(shuffled, embedding)


def test_missing_nominated_well_consumes_slot_without_oracle_replacement():
    prediction = np.array([[-5., -4., 0.]])
    outcome = np.array([[np.nan, -2., -2.]])
    result = e.ranking(prediction, outcome, 1)
    assert result["slots"] == 1 and result["hits"] == 0
    assert result["missing_selected"] == 1
    assert e.ranking(prediction, outcome, 2)["hits"] == 1


def test_cell_rows_are_not_bootstrap_units():
    difference = np.array([1., 1., -1.])
    low, high = e.interval(difference, np.array(["same", "same", "other"]))
    assert low == -1 and high == 1
