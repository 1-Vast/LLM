"""Coverage, missingness and observational claim boundaries."""
import numpy as np
import pandas as pd
import pytest

from research.astra.decision_space import (
    ACTIONS, CONTROL, PERT, condition_table, coverage_table, describe, prediction_agreement, sampling_diagnostics,
)


def records():
    return pd.DataFrame([dict(plate=p, **{PERT:a}, EGR1=v, sample=s, pass_filter="full")
                         for p, a, v, s in [("p1", ACTIONS[0], 2., "s1"), ("p1", CONTROL, 1., "c1"),
                                            ("p2", ACTIONS[1], 1., "s2"), ("p2", CONTROL, .5, "c2")]])


def test_cross_plate_actions_do_not_create_complete_menu():
    table = coverage_table(records(), ACTIONS)
    assert not any(r["complete_menu_with_control"] for r in table)
    assert table[0]["measured_cell_counts"] == [1, 0, 0]
    assert all(r["independent_parent_cultures"] is None for r in table)


def test_same_plate_complete_menu_does_not_certify_physical_replication():
    rows = records()
    extra = pd.DataFrame([dict(plate="p1", **{PERT:a}, EGR1=.3, sample="s", pass_filter="full") for a in ACTIONS[1:]])
    table = coverage_table(pd.concat([rows, extra]), ACTIONS)
    assert table[0]["complete_menu_with_control"]
    assert table[0]["independent_parent_cultures"] is None


def test_control_missing_and_nonfinite_never_imputed():
    rows = records()
    rows = rows[rows[PERT] != CONTROL]
    conditions = condition_table(rows, ACTIONS)
    assert all(r["matched_plate_difference"] is None for r in conditions)
    assert describe([])["mean"] is None
    with pytest.raises(ValueError, match="no zero imputation"):
        describe([np.nan])


def test_predictions_do_not_fill_missing_observed_actions():
    summary = dict(action_labels=ACTIONS, rows=[dict(pool="p1", seed=17, endpoint_scores=[0., 0., 0.])])
    result = prediction_agreement(condition_table(records(), ACTIONS), summary)
    assert result[0]["observed_mean"] == 2. and result[0]["absolute_difference"] == 2.
    assert result[1]["observed_mean"] is None and result[2]["absolute_difference"] is None
    assert all(r["actual_state_gain"] is None and r["exposure"] == "unknown" for r in result)


def test_native_samples_filter_strata_and_cells_do_not_become_replicates():
    rows = records()
    extra = rows.iloc[[0]].copy()
    extra["pass_filter"] = "minimal"
    extra["EGR1"] = 0.
    conditions = condition_table(pd.concat([rows, extra]), ACTIONS)
    first = conditions[0]
    assert first["native_sample_ids"] == ["s1"]
    assert first["filter_strata"]["minimal"]["cells"] == 1
    assert first["observed_EGR1"]["mean"] == 1.
    assert first["intervention_utility"] is None and first["physical_CI"] is None


def test_solvate_identity_is_not_merged_into_trametinib_menu():
    rows = records()
    extra = rows.iloc[[0]].copy()
    extra[PERT] = str([("Trametinib (DMSO_TF solvate)", .05, "uM")])
    extra["EGR1"] = 999.
    conditions = condition_table(pd.concat([rows, extra]), ACTIONS)
    assert conditions[0]["observed_EGR1"]["mean"] == 2.


def test_seed_omission_exposes_fragility_without_new_sampling_or_biological_claim():
    rows = [dict(pool="plate10", seed=s, endpoint_scores=e,
                 trace=dict(calls=[dict(paired=True, basal_sha256=str(s)) for _ in range(3)]))
            for s, e in zip([17, 42, 103], [[0., 0., .03], [.003, 0., 0.], [.15, 0., 0.]])]
    result = sampling_diagnostics(dict(rows=rows))[0]
    assert result["uniform_K3"]["selected"] == 1
    assert result["leave_one_seed_out"][0]["selected"] is None
    assert result["biological_variance"] is None and result["model_bias"] is None
    rows[0]["trace"]["calls"][0]["basal_sha256"] = "changed"
    with pytest.raises(ValueError, match="pairing"):
        sampling_diagnostics(dict(rows=rows))
