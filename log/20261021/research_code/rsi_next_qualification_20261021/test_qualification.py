"""Small invariants for the exposed-data attribution calculation."""
import numpy as np
import pandas as pd
import pytest

import blend_qualification as q


def test_top_five_tie_break_does_not_depend_on_release_row_order():
    frame = pd.DataFrame({"cell": ["A"] * 6, "perts": list("fedcba"),
                          "y": [0, 0, 0, 0, 0, 1], "in_pool": True, "p": 0.5})
    a = q.metrics(frame, "p").iloc[0]
    b = q.metrics(frame.iloc[::-1], "p").iloc[0]
    assert a.selected_drugs == b.selected_drugs == "a|b|c|d|e"
    assert a.hits5 == b.hits5 == 1


def test_two_stocks_do_not_count_as_two_independent_lineages():
    table = pd.DataFrame({"lineage": ["A", "A", "B"], "arm": ["x"] * 3,
                          "prec5": [1.0, 1.0, 0.0]})
    assert q.macro(table, "x") == 0.5


def test_cluster_difference_is_lineage_weighted_and_reproducible():
    table = pd.DataFrame({"lineage": ["A", "A", "B"] * 2,
                          "arm": ["a"] * 3 + ["b"] * 3,
                          "prec5": [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]})
    result = q.contrast(table, "a", "b")
    assert result["difference_prec5"] == 0.5
    assert result["n_lineages"] == 2
    assert result == q.contrast(table, "a", "b")


def test_cached_prediction_label_disagreement_is_rejected(monkeypatch):
    d = pd.DataFrame({"cell": ["A"], "perts": ["d"], "y": [1.0]})
    def fake(stage, variant, seed):
        return pd.DataFrame({"cell": ["A"], "perts": ["d"], "y": [0.0], variant: [0.5]}), []
    monkeypatch.setattr(q, "predictions", fake)
    with pytest.raises(RuntimeError, match="labels disagree"):
        q.attach_world(d, "final", 0)


def test_duplicate_prediction_keys_cannot_silently_multiply_observations(monkeypatch):
    d = pd.DataFrame({"cell": ["A"], "perts": ["d"], "y": [1.0]})
    def fake(stage, variant, seed):
        return pd.DataFrame({"cell": ["A", "A"], "perts": ["d", "d"], "y": [1.0, 1.0], variant: [0.5, 0.5]}), []
    monkeypatch.setattr(q, "predictions", fake)
    with pytest.raises(pd.errors.MergeError):
        q.attach_world(d, "final", 0)


def test_selection_ties_prefer_zero_new_score_weight():
    frame = pd.DataFrame({"cell": ["A"] * 6, "perts": list("abcdef"),
                          "y": [1, 1, 1, 0, 0, 0], "in_pool": True,
                          "b1": np.arange(6, 0, -1) / 7})
    for name in ("full", "no_traj", "lr", "hgb"):
        frame[name] = frame.b1
    weights, grid = q.choose_weights(frame)
    assert set(weights.values()) == {0.0}
    assert len(grid) == 20


def test_windows_peak_counter_is_real_and_positive():
    assert q.peak_memory() > 1024 * 1024
