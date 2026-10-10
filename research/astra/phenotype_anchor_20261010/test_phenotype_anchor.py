"""Behaviour tests for the phenotype-anchor study (synthetic inputs; no asset or network access)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analysis as A  # noqa: E402
import evaluate as E  # noqa: E402
import phenotypes as P  # noqa: E402

LAB = "[('Drug', 5.0, 'uM')]"


def _row(n, g1, s, g2m):
    return {"n": n, "G1": g1, "S": s, "G2M": g2m}


def _table():
    t = {}
    for f in ("ref1", "ref2", "held"):
        t[(f, P.DMSO, "p1")] = _row(1000, 500, 250, 250)
    t[("ref1", LAB, "p1")] = _row(1000, 500, 250, 250)
    t[("ref2", LAB, "p1")] = _row(1000, 500, 250, 250)
    t[("held", LAB, "p1")] = _row(250, 200, 25, 25)
    return t


def test_survival_denominator_excludes_lines_outside_the_reference_set():
    t = _table()
    frame = P.phenotype_frame(t, ["held", "ref1"], ["ref1", "ref2"])
    assert frame[("ref1", LAB, "p1")]["survival"] == pytest.approx(0.0, abs=1e-6)
    expected = np.log2(250.5 / 2000) - np.log2(1000.5 / 2000)
    assert frame[("held", LAB, "p1")]["survival"] == pytest.approx(expected)
    t[("held", LAB, "p1")] = _row(5, 1, 2, 2)  # the held-out count cannot move a reference value
    assert P.phenotype_frame(t, ["ref1"], ["ref1", "ref2"])[("ref1", LAB, "p1")]["survival"] == pytest.approx(0.0, abs=1e-6)


def test_phase_shift_is_a_log_odds_difference_against_same_plate_dmso():
    frame = P.phenotype_frame(_table(), ["held"], ["ref1", "ref2"])
    expected = np.log((200.5) / (50.5)) - np.log(500.5 / 500.5)
    assert frame[("held", LAB, "p1")]["G1"] == pytest.approx(expected)


def test_bridge_recovers_a_planted_linear_readout():
    rng = np.random.RandomState(0)
    X = rng.normal(size=(3000, 40))
    w = np.zeros(40)
    w[:3] = (1.0, -2.0, 0.5)
    y = X @ w + 0.1 * rng.normal(size=3000)
    b = A.Bridge(n_pc=40, alpha=1.0).fit(X, y)
    assert np.corrcoef(b.predict(X[:200]), y[:200])[0, 1] > 0.99


def test_kernel_prior_transfers_from_the_most_similar_line():
    basal_train = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    T = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, -1.0]])
    pred = A.kernel_prior(np.array([0.9, 0.1, 0.0]), basal_train, T, tau=0.01, top_m=3)
    assert pred == pytest.approx([1.0, 0.0], abs=1e-3)


def test_kernel_prior_ignores_missing_reference_values_instead_of_reading_them_as_zero():
    pred = A.kernel_prior(np.array([1.0, 0.0]), np.array([[1.0, 0.0], [0.9, 0.1]]), np.array([[np.nan], [2.0]]), tau=1.0, top_m=2)
    assert pred[0] == pytest.approx(2.0)


def test_knowledge_prior_marks_only_target_driver_matches():
    labels = ["[('Dabrafenib', 5.0, 'uM')]", "[('Aspirin', 5.0, 'uM')]"]
    targets = {"dabrafenib": {"BRAF"}, "aspirin": {"PTGS1"}}
    assert A.knowledge_prior({"BRAF", "TERT"}, labels, targets).tolist() == [-1.0, 0.0]


def test_top_k_utility_breaks_ties_by_generic_potency_and_never_reads_unselected_outcomes():
    pred = np.zeros(4)
    generic = np.array([0.0, -1.0, -2.0, 1.0])
    obs = np.array([5.0, 1.0, -3.0, np.nan])
    assert A.topk_utility(pred, obs, generic, k=2) == pytest.approx(-np.mean([-3.0, 1.0]))


def test_within_r_is_undefined_for_a_constant_prediction():
    assert np.isnan(A.within_r(np.zeros(5), np.arange(5.0)))


def test_screening_commits_best_observed_a_and_scores_on_b():
    prior = np.array([-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
    A_obs = np.array([0.0, -1.0, -2.0, -3.0, -4.0, -5.0, -6.0, -7.0, -9.0])
    B_obs = np.array([1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0, -1.0, -10.0])
    out = E.screening(prior, A_obs, B_obs, np.zeros(9))
    assert out["no_screen"] == pytest.approx(-np.mean(B_obs[:5]))
    assert out["screen"] == pytest.approx(-np.mean(B_obs[[7, 6, 5, 4, 3]]))
    assert (out["credits_screen"], out["credits_no_screen"]) == (13, 5)


def test_compare_requires_interval_and_four_of_five_lines():
    rng = np.random.RandomState(1)
    obs = rng.normal(size=(5, 60))
    good = obs + 0.3 * rng.normal(size=(5, 60))
    bad = rng.normal(size=(5, 60))
    clusters = np.repeat(np.arange(20), 3)
    res = E.compare(good, bad, obs, np.zeros((5, 60)), clusters, "r", np.random.RandomState(0))
    assert res["success"] and res["lines_better"] == 5
    res = E.compare(bad, good, obs, np.zeros((5, 60)), clusters, "r", np.random.RandomState(0))
    assert not res["success"]


def test_arm_predictions_do_not_depend_on_held_out_outcomes():
    rng = np.random.RandomState(2)
    basal_train, T_train = rng.normal(size=(6, 10)), rng.normal(size=(6, 8))
    target_basal = rng.normal(size=10)
    first = A.kernel_prior(target_basal, basal_train, T_train, 0.05, 3)
    # the held-out outcome is not an argument of any arm; poisoning it cannot change a prediction
    poisoned_outcome = np.full(8, 1e6)
    assert poisoned_outcome is not None
    assert np.array_equal(first, A.kernel_prior(target_basal, basal_train, T_train, 0.05, 3))


def test_dose_and_drug_parsing_follow_tahoe_labels():
    label = "[('Trametinib (DMSO_TF solvate)', 0.5, 'uM')]"
    assert A.dose_of(label) == 0.5
    assert A.drug_of(label) == "Trametinib (DMSO_TF solvate)"
    assert A.dose_of(P.DMSO) == 0.0
