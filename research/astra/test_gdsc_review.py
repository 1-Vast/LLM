"""Scientific boundaries of the fixed-policy contribution and CI reproduction."""
import numpy as np
import pandas as pd
import pytest

from research.astra.gdsc_review import contribution_table, crossed_mean, grouped_contributions, unit_weights


def frame():
    return pd.DataFrame({"BARCODE": list("abcde"), "unit": ["u1", "u1", "u2", "u3", "u4"],
                         "date_cluster": ["d1", "d2", "d1", "d2", "d3"],
                         "tissue": ["lung", "lung", "skin", "lung", "skin"], "growth": ["A"]*5,
                         "medium": ["R"]*5, "log2_density": np.arange(5),
                         **{a + "_action": [0, 0, 0, 0, 0] for a in ["fixed", "C", "CS", "shuffle"]},
                         **{a + "_observed_utility": [0., .2, .1, .3, .4] for a in ["fixed", "C", "CS", "shuffle"]}})


def test_repeated_plate_does_not_increase_unit_weight():
    f = frame()
    w = unit_weights(f)
    assert w.sum() == pytest.approx(1.)
    assert pd.Series(w).groupby(f.unit).sum().to_numpy() == pytest.approx([.25]*4)


def test_duplicate_records_leave_interval_unchanged():
    f, values = frame(), np.array([.1, -.2, .3, .4, -.5])
    a = crossed_mean(f, values, .05)
    b = crossed_mean(pd.concat([f]*5, ignore_index=True), np.tile(values, 5), .05)
    assert a["mean"] == pytest.approx(b["mean"])
    assert a["se"] == pytest.approx(b["se"])
    assert a["df"] == b["df"] == 2


def test_unchanged_action_cannot_gain_realized_utility():
    f = frame()
    f.loc[0, "C_observed_utility"] = 99.
    with pytest.raises(ValueError, match="unchanged action"):
        contribution_table(f)


def test_all_groups_sum_to_original_gain_including_negative_contribution():
    f = frame()
    f.loc[0, "C_action"] = 1
    f.loc[0, "C_observed_utility"] = -.2
    f.loc[2, "C_action"] = 2
    f.loc[2, "C_observed_utility"] = .8
    table = contribution_table(f)
    groups = grouped_contributions(table, "tissue")
    assert len(groups) == 2 and any(r["C-fixed_contribution_pp"] < 0 for r in groups)
    assert sum(r["C-fixed_contribution_pp"] for r in groups) == pytest.approx(
        crossed_mean(f, f.C_observed_utility - f.fixed_observed_utility, .05)["mean"]*100)


def test_missing_or_single_cluster_has_no_interval():
    f = frame()
    f["date_cluster"] = "one_date"
    assert crossed_mean(f, np.ones(5), .05)["ci"] is None
    with pytest.raises(ValueError, match="finite paired"):
        crossed_mean(f, [1., np.nan, 0., 0., 0.], .05)
