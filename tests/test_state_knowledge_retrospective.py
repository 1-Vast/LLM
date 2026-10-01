"""Knowledge features and splits must not ingest held-out expression."""
import numpy as np
import pandas as pd

from tools.datasets.state_knowledge_retrospective import (
    chemical_group, frozen_features, kernel_predict, split_indices,
)


def test_salts_and_neutral_parent_stay_in_one_chemical_group():
    assert chemical_group("C[NH3+].[Cl-]") == chemical_group("CN")


def test_plate_holdout_purges_same_drug_on_other_plates():
    frame = pd.DataFrame({"plate": ["p1", "p2", "p2", "p3"], "fold": [0, 1, 1, 2],
                          "chemical_group": ["same", "same", "different", "third"]})
    train, test = split_indices(frame, 0)
    assert list(test) == [0]
    assert list(train) == [2, 3]


def test_poisoning_held_out_outcomes_leaves_predictions_identical():
    features = np.array([[1., 0], [0, 1], [1, 1]])
    kernel = features @ features.T
    outcomes = np.array([[1., 2], [3, 4], [9, 9]])
    a = kernel_predict(kernel, np.array([0, 1]), np.array([2]), outcomes, 1.)
    outcomes[2] = [-1e99, 1e99]
    b = kernel_predict(kernel, np.array([0, 1]), np.array([2]), outcomes, 1.)
    np.testing.assert_array_equal(a, b)


def test_public_annotations_create_numeric_features_without_inferred_targets():
    drugs = pd.DataFrame({"drug": ["a", "b", "c"], "targets": ["A", "B, UNKNOWN", None]})
    graph = pd.DataFrame({"source": ["A", "B"], "target": ["B", "B"], "importance": [0.5, 1.]})
    direct, expanded, provenance, _ = frozen_features(drugs, graph)
    assert (direct @ direct.T).toarray()[0, 1] == 0
    assert (expanded @ expanded.T).toarray()[0, 1] > 0
    assert provenance[1]["unmatched_tokens"] == ["UNKNOWN"]
    assert direct[2].nnz == 0
