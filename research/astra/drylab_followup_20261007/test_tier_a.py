"""Synthetic cross-component boundaries, not scientific efficacy tests."""
import numpy as np
import pandas as pd
import pytest

from research.astra.drylab_followup_20261007.reproduce import load_replay
from research.astra.drylab_followup_20261007.tier_a import DESIGN, build_features, dose_vectors, evaluate, reference_groups, ridge_scores, support


def mono_fixture():
    return pd.DataFrame([dict(sidm=f"history{i}", drug_id="1", cmp_tissue="Breast",
                              cell_excluded_from_mono=False, min_conc=.01, max_conc=10.,
                              ln_ic50=20. if i == 0 else 0., auc=.5) for i in range(6)] +
                        [dict(sidm="target", drug_id="1", cmp_tissue="Breast",
                              cell_excluded_from_mono=True, min_conc=.01, max_conc=10., ln_ic50=-20., auc=0.)])


def menu_fixture():
    return pd.DataFrame([dict(Tissue="Breast", SIDM="target", ANCHOR_ID="1", LIBRARY_ID="1",
                              anchor_set="1;10", LIBRARY_CONC="10", SEEDING_DENSITY="625")])


def test_target_mono_poisoning_cannot_change_features():
    m = mono_fixture()
    ids = pd.DataFrame([dict(jaaks_id="1", status="mapped")])
    before, _ = build_features(menu_fixture(), m, ids)
    m.loc[m.sidm.eq("target"), ["ln_ic50", "auc"]] = [999., 999.]
    after, _ = build_features(menu_fixture(), m, ids)
    pd.testing.assert_frame_equal(before, after)


def test_target_not_marked_excluded_is_rejected():
    m = mono_fixture()
    m.loc[m.sidm.eq("target"), "cell_excluded_from_mono"] = False
    with pytest.raises(AssertionError, match="target_mono_not_excluded"):
        build_features(menu_fixture(), m, pd.DataFrame([dict(jaaks_id="1", status="mapped")]))


def test_extrapolation_is_flagged_not_censored():
    groups, _ = reference_groups(mono_fixture())
    values = support(groups, "1", "Breast", 10., True)
    assert values["ic50_supported"] == pytest.approx(5 / 6)
    assert values["n_reference_cells"] == 6
    assert support(groups, "1", "Breast", 1000., True) is None


def test_composite_is_retained_with_static_fallback():
    menu = menu_fixture()
    menu.loc[0, "ANCHOR_ID"] = "1|2"
    menu.loc[0, "anchor_set"] = "1|.1;10|1"
    f, meta = build_features(menu, mono_fixture(), pd.DataFrame([dict(jaaks_id="1", status="mapped")]))
    assert len(f) == 1 and f.composite.iloc[0] and not f.eligible.iloc[0]
    assert meta["fallback_rows"] == 1


def test_unresolved_composite_library_dose_is_not_split_or_dropped():
    menu = menu_fixture()
    menu.loc[0, "LIBRARY_ID"] = "1|2"
    f, meta = build_features(menu, mono_fixture(), pd.DataFrame([dict(jaaks_id="1", status="mapped")]))
    assert len(f) == 1 and not f.eligible.iloc[0]
    assert meta["unresolved_composite_library_doses"] == 1


@pytest.mark.parametrize("value", ["0;1", "nan;1", "1|2;3|4", "inf;2"])
def test_unrepresentable_doses_rejected(value):
    with pytest.raises(ValueError):
        dose_vectors("1", value)


def test_residual_fit_cannot_read_test_labels_and_falls_back_on_missing():
    features = pd.DataFrame({k: [1., 2., 3., 4.] for k in DESIGN})
    features["eligible"] = [True, True, True, False]
    labels = pd.DataFrame(dict(SIDM=["a", "b", "target", "target"], role=["SV"] * 4,
                               joint=[0, 1, 0, 0], prior_control_score=[.1, .8, .5, .5]))
    before = ridge_scores([0, 1], [2, 3], features, DESIGN, 1., labels)
    labels.loc[[2, 3], ["joint", "prior_control_score"]] = 999.
    after = ridge_scores([0, 1], [2, 3], features, DESIGN, 1., labels)
    np.testing.assert_array_equal(before, after)
    assert before[1] == 0.


def test_replay_confirmation_order_is_static_and_follows_paid_screen():
    replay = load_replay()
    truth = pd.DataFrame({k: ["x"] * 20 for k in replay.PUBLIC})
    truth["pair"] = [str(i) for i in range(20)]
    truth["prior_control_score"] = np.arange(20, dtype=float)
    truth["hit1"] = True
    truth["hit2"] = True
    truth["raw_y1"] = 0.
    scores = np.arange(20, dtype=float)
    scores[0] = 100.
    result = evaluate(replay, truth, scores)
    assert result["screen_ids"] == [0, 19]
    assert result["spent"] == result["budget"] == 4
    confirms = [z for z in result["trace"] if z["stage"] == "confirm"]
    assert [z["index"] for z in confirms] == [19, 0]


def test_planted_condition_signal_changes_screen_and_increases_confirmations():
    replay = load_replay()
    # Eight synthetic cells share an informative public binary condition.
    labels = pd.DataFrame({k: ["x"] * 160 for k in replay.PUBLIC})
    labels["SIDM"] = np.repeat([f"c{i}" for i in range(8)], 20)
    labels["role"] = "SV"
    labels["pair"] = np.tile([f"p{i:02}" for i in range(20)], 8)
    signal = np.tile(np.arange(20) < 10, 8)
    labels["prior_control_score"] = np.tile(.5 + np.arange(20) * .0001, 8)
    labels["hit1"] = labels["hit2"] = labels["joint"] = signal
    labels["raw_y1"] = 0.
    features = pd.DataFrame({k: signal.astype(float) for k in DESIGN})
    features["eligible"] = True
    train, test = np.arange(140), np.arange(140, 160)
    delta = ridge_scores(train, test, features, DESIGN, 1., labels)
    before = evaluate(replay, labels.loc[test], labels.loc[test, "prior_control_score"].to_numpy())
    after = evaluate(replay, labels.loc[test], labels.loc[test, "prior_control_score"].to_numpy() + delta)
    assert before["confirmations"] == 0 and after["confirmations"] == 2
    assert before["screen_ids"] != after["screen_ids"]
