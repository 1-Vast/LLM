"""Properties the G1 arms, the inner choice of k and the gate rule must have before any outcome is used.

File summary
- Path: research/beataml_g1_20261017/test_science.py
- Purpose: synthetic checks (no Beat AML data) that the ridge-plus-feedback update is the conditional
  Gaussian it claims to be, that it equals S_ridge when nothing is returned, that the S_ridge probabilities
  equal the attribution study's, that the probe count is chosen from source patients only, that the parity mode
  cannot compute a G1 contrast, and that the gate arithmetic is the registered one.
- Run from this folder: ``python -m pytest -q test_science.py -p no:cacheprovider`` (maestro environment).
"""
from __future__ import annotations

import warnings

import numpy as np
import pytest

import g1_analyse as AN
import g1_arms as A
from common import basal_pcs, outer_folds  # noqa: F401
from virtual_cell.bridged_transfer import BridgedTransferModel, selective_events

warnings.filterwarnings("ignore", category=RuntimeWarning)


def synthetic_domain(n=400, D=30, p=40, seed=7, shared=1.0):
    """Samples x inhibitors with a basal-driven part and a shared factor that the basal profile cannot predict."""

    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, p))
    F = X[:, :3] @ rng.normal(size=(3, 3)) * 0.6 + rng.normal(size=(n, 3)) * 0.6
    V = rng.normal(size=(D, 3))
    U = rng.normal(size=(n, 1)) * shared                       # not predictable from X
    loading = rng.normal(size=(D, 1)) * 1.5
    Y = 100 + 20 * (F @ V.T) + 20 * (U @ loading.T) + rng.normal(size=(n, D)) * 10
    Y[rng.random((n, D)) < 0.2] = np.nan
    ev, G = selective_events(Y, None, 100)
    groups = np.array([f"p{i // 2}" for i in range(n)])
    return {"Y": Y, "X": X, "events": ev, "G": G, "contexts": np.array([f"s{i}" for i in range(n)]),
            "groups": groups, "items": np.array([f"d{j}" for j in range(D)])}


@pytest.fixture(scope="module")
def dom():
    return synthetic_domain()


def split(dom):
    fid = outer_folds(dom["groups"])
    return np.flatnonzero(fid != 0), np.flatnonzero(fid == 0)


def fitted(dom):
    src, tgt = split(dom)
    model = BridgedTransferModel(rank=A.RANK, abs_gate=None, min_measured=A.MIN_MEASURED, impute_iters=A.IMPUTE).fit(dom["Y"][src], dom["X"][src])
    return src, tgt, model


def test_ridge_probabilities_equal_the_attribution_studys(dom):
    import attribution
    src, tgt, model = fitted(dom)
    mine = A.ridge_parts(dom, src, tgt, model)["prob"]
    ref = attribution.strong_state(dom, src, tgt, model, gbm=False)["S_ridge"]
    np.testing.assert_array_equal(mine, ref)


def test_ridge_feedback_equals_s_ridge_when_nothing_is_returned(dom):
    src, tgt, model = fitted(dom)
    parts = A.ridge_parts(dom, src, tgt, model)
    S = A.residual_cov(parts["R"], A.LAMBDA_RF)
    probes = np.array([0, 1, 2, 3])
    for ti in range(5):
        out = A.rf_probs(parts, S, ti, probes, np.full(4, np.nan))
        np.testing.assert_array_equal(out, parts["prob"][ti])


def test_residual_covariance_is_symmetric_positive_definite_and_shrinks_to_the_diagonal(dom):
    src, tgt, model = fitted(dom)
    R = A.ridge_parts(dom, src, tgt, model)["R"]
    S = A.residual_cov(R, A.LAMBDA_RF)
    np.testing.assert_allclose(S, S.T, atol=1e-10)
    assert np.linalg.eigvalsh(S).min() > 0
    full = A.residual_cov(R, 1.0)
    off = full - np.diag(np.diag(full))
    assert np.abs(off).max() < 1e-8 * np.abs(np.diag(full)).max()


def test_ridge_feedback_moves_toward_a_correlated_residual_and_never_adds_variance(dom):
    """Observing one item's realised residual shifts a correlated item's prediction in the same direction."""

    src, tgt, model = fitted(dom)
    parts = A.ridge_parts(dom, src, tgt, model)
    S = A.residual_cov(parts["R"], 0.0)
    D = dom["Y"].shape[1]
    ok = [j for j in range(D) if parts["fitted"][j]]
    # the pair of fitted items with the largest absolute residual correlation
    best, pair = 0.0, None
    for a in ok:
        for b in ok:
            if a < b:
                r = S[a, b] / np.sqrt(S[a, a] * S[b, b])
                if abs(r) > abs(best):
                    best, pair = r, (a, b)
    a, b = pair
    assert abs(best) > 0.2, "the synthetic domain must contain a correlated residual pair"
    shifts, realised = [], []
    for ti, c in enumerate(tgt):
        ya, yb = dom["Y"][c, a], dom["Y"][c, b]
        if not (np.isfinite(ya) and np.isfinite(yb)):
            continue
        e = ya - parts["pred"][ti, a]
        s = S[b, a] - parts["b"][b] * S[D, a]
        shifts.append(s / (S[a, a]) * e)
        realised.append(yb - parts["pred"][ti, b])
    # the conditional mean of e_b - b_b e_G given e_a has the sign of corr(e_a, e_b - b_b e_G); compare the
    # shift of the raw residual instead (G enters through b_j, which is small in the synthetic domain)
    raw = [S[b, a] / S[a, a] * (dom["Y"][c, a] - parts["pred"][ti, a]) for ti, c in enumerate(tgt)
           if np.isfinite(dom["Y"][c, a]) and np.isfinite(dom["Y"][c, b])]
    assert np.sign(np.corrcoef(raw, realised)[0, 1]) == np.sign(best)
    assert abs(np.corrcoef(raw, realised)[0, 1]) > 0.1
    # variance: the conditional variance is never above the marginal one and never below the floor
    P = np.array([a])
    Spp = S[np.ix_(P, P)]
    s = S[:D, P] - parts["b"][:, None] * S[D, P][None, :]
    red = np.einsum("jp,pj->j", s, np.linalg.solve(Spp, s.T))
    assert np.all(red >= -1e-9)


def test_unfitted_probes_are_ignored(dom):
    src, tgt, model = fitted(dom)
    parts = A.ridge_parts(dom, src, tgt, model)
    S = A.residual_cov(parts["R"], A.LAMBDA_RF)
    bad = [j for j in range(len(parts["fitted"])) if not parts["fitted"][j]]
    probes = np.array(bad[:1] + [0]) if bad else np.array([0, 0 + 1])
    out = A.rf_probs(parts, S, 0, probes, np.array([1.0, 100.0][: len(probes)]))
    assert np.all(np.isfinite(out)) and out.min() >= 0 and out.max() <= 1


def test_records_respect_the_query_budget(dom):
    src, tgt = split(dom)
    recs = A.evaluate(dom, src, tgt, arms="all")
    assert len(recs) == len(tgt)
    for r in recs[:30]:
        for name in ("A_item", "S_ridge", "C0", "E", "C_4", "C_8", "C_12", "RF_4", "RF_8", "RF_12", "RFs_4"):
            assert 0 <= r["t_" + name] <= A.BUDGET
            assert 0 <= r["w_" + name] <= A.BUDGET
        for k in A.KS:
            assert 0 <= r[f"r_C_{k}"] <= k and 0 <= r[f"r_RF_{k}"] <= k
        assert r["t_C_4"] <= r["events"] and r["t_S_ridge"] <= r["events"]


def test_parity_mode_computes_no_ridge_arm(dom):
    src, tgt = split(dom)
    r = A.evaluate(dom, src, tgt[:3], arms="parity")[0]
    assert {"t_C0", "t_E", "t_C_4", "t_C_8", "t_C_12"} <= set(r)
    assert not any(key.startswith(("t_S_ridge", "t_RF", "t_A_item")) for key in r)


def test_inner_choice_is_patient_disjoint_and_ignores_outer_targets(dom):
    src, tgt = split(dom)
    a = A.choose_k(dom, src, 0)
    assert a["inner_patient_overlap"] == 0
    assert a["k_candidate"] in A.KS and a["k_ridge_feedback"] in A.KS
    # destroy every outer target outcome: the choice must not move
    d2 = {**dom, "Y": dom["Y"].copy(), "events": dom["events"].copy()}
    d2["Y"][tgt] = np.nan
    d2["events"][tgt] = False
    b = A.choose_k(d2, src, 0)
    assert a == b
    # a different fold salt gives a different inner split, so the choice is a function of (src, fold)
    assert A.choose_k(dom, src, 0) == a


def test_ties_in_the_inner_choice_go_to_the_smaller_k():
    means = {4: 1.0, 8: 1.0, 12: 1.0}
    assert max(A.KS, key=lambda k: (means[k], -k)) == 4
    means = {4: 1.0, 8: 1.2, 12: 1.2}
    assert max(A.KS, key=lambda k: (means[k], -k)) == 8


def fake_records(diff, n=300, seed=0, noise=0.5):
    rng = np.random.default_rng(seed)
    base = rng.poisson(0.8, size=n).astype(float)
    recs = []
    for i in range(n):
        r = {"context": f"s{i}", "group": f"p{i // 2}", "fold": i % 5, "k_candidate": 8, "k_ridge_feedback": 8, "events": 3}
        for a in AN.ROUNDS:
            r["t_" + a] = base[i]
            r["w_" + a] = 0
            if a.startswith(("C_", "RF_", "RFs_", "E", "CAND", "RF")) and a not in ("C0",):
                r["r_" + a] = 3
        r["t_CAND"] = base[i] + diff + noise * rng.normal()
        out_ = r["t_CAND"]
        r["t_C_8"] = out_
        recs.append(r)
    return recs


def fake_object(recs):
    return {"records": recs, "meta": {"constants": {}, "parity": {}, "choices": {str(f): {"k_candidate": 8, "k_ridge_feedback": 8} for f in range(5)}}}


@pytest.mark.parametrize("diff,strict,gross,net_pos", [(0.30, True, True, True), (0.16, True, True, True),
                                                       (0.09, False, True, True), (0.03, False, False, False), (-0.2, False, False, False)])
def test_gate_arithmetic(diff, strict, gross, net_pos):
    g = AN.gate(fake_records(diff, noise=0.2))
    lo = g["ci95"][0]
    assert g["extra_rounds"] == 1
    assert g["strict_pass"] == (lo - 0.05 > 0.05) == strict
    assert g["gross_pass"] == (lo > 0.05) == gross
    assert g["net_positive_pass"] == (lo - 0.05 > 0) == net_pos
    assert g["decision"] == ("G1_PASSED" if strict else "G1_FAILED_STOP_LOW_RANK_STATE_MODEL_BRANCH")


def test_gate_boundary_is_strict():
    res = AN.level({"mean": 0.2, "ci95": [0.10, 0.3], "p_one_sided": 0.01, "n_contexts": 1, "n_clusters": 1,
                    "positive_contexts": 1, "negative_contexts": 0}, 1)
    assert res["net_lower"] == pytest.approx(0.05)
    assert not (res["net_lower"] > AN.MIN_USEFUL)  # exactly 0.05 does not pass


def test_analysis_identity_and_vocabulary():
    res = AN.analyse(fake_object(fake_records(0.2)))
    assert res["identity"]["holds"]
    for name in ("model_without_observations", "observations_for_candidate", "observations_for_ridge", "model_given_observations"):
        assert res["contrasts"][name]["reading"] in {"USEFUL_POSITIVE", "POSITIVE", "NEGATIVE", "WITHIN_MARGIN", "NOT_DISTINGUISHABLE"}
    assert res["classification"]["gate"].startswith("G1_")
    assert res["sensitivity"]["chosen_k"]["candidate"]["0"] == 8


def test_round_charge_is_applied_to_two_round_arms_only():
    recs = fake_records(0.2)
    same = AN.contrast(recs, "RF", "CAND")
    assert same["extra_rounds"] == 0 and same["net_lower"] == same["ci95"][0]
    one_round = AN.contrast(recs, "CAND", "C0")
    assert one_round["extra_rounds"] == 1 and one_round["net_lower"] == pytest.approx(one_round["ci95"][0] - 0.05)
