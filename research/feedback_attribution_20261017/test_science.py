"""Properties the development scorer and planner must have before any outcome is used.

Run from this folder: ``python -m pytest -q test_science.py`` (maestro environment).
"""
from __future__ import annotations

import numpy as np
import pytest

import common  # noqa: F401
from coherent import CoherentScorer, derange, global_posterior, martingale_gap, mc_event_prob
from planner import choose_design, design_values
from virtual_cell.bridged_transfer import BridgedTransferModel, BridgeState


def one_factor_three_items():
    """The synthetic counterexample: one factor, three items with equal loadings."""

    m = BridgedTransferModel.__new__(BridgedTransferModel)
    m.rank, m.abs_gate = 1, None
    m.V = np.ones((3, 1))
    m.mu = np.zeros(3)
    m.s2 = np.full(3, 0.04)
    m.a, m.b = np.zeros(3), np.ones(3)
    m.med, m.mad = np.zeros(3), np.full(3, 1 / 3)
    m.threshold_ok = np.ones(3, bool)
    m.measured_rate = np.ones(3)
    return m


def synthetic(n=400, D=60, r=4, p=12, seed=0, missing=0.3):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, p))
    F = X[:, :r] @ rng.normal(size=(r, r)) * 0.5 + rng.normal(size=(n, r)) * 0.7
    V = rng.normal(size=(D, r))
    V[:, 0] = np.abs(V[:, 0]) + 0.5  # a shared sensitivity direction, as in drug screens
    Y = 5 + F @ V.T + rng.normal(size=(n, D)) * 0.5
    Y[rng.random((n, D)) < missing] = np.nan
    model = BridgedTransferModel(rank=r, n_pcs=6, n_genes=p, min_measured=50, impute_iters=5).fit(Y, X)
    return model, Y, X


def test_promoted_score_reproduces_the_counterexample():
    m = one_factor_three_items()
    st = BridgeState(np.zeros(1), np.eye(1), np.array([], int))
    assert m.event_prob(st)[1] == pytest.approx(0.16340, abs=5e-5)
    for y in (-4, -2, 0, 2, 4):
        post = m.posterior(st, [0], [y])
        assert m.event_prob(post)[1] == pytest.approx(0.000178, abs=5e-6)


def test_promoted_score_is_not_a_martingale_on_the_counterexample():
    m = one_factor_three_items()
    st = BridgeState(np.zeros(1), np.eye(1), np.array([], int))
    gap = martingale_gap(m, m.event_prob, st, [0], 400, np.random.default_rng(1))
    assert gap[1] < -0.15


def test_coherent_score_is_a_martingale():
    model, Y, X = synthetic()
    sc = CoherentScorer(model, Y)
    st = model.prior(X[0])
    idx = np.argsort(-sc.event_prob(st))[:4]
    rng = np.random.default_rng(2)
    gap = martingale_gap(model, sc.event_prob, st, idx, 3000, rng)
    p0 = sc.event_prob(st)
    # a posterior probability lies in [0, 1] with mean p0, so its Monte Carlo SE is at most
    # sqrt(p0 (1 - p0) / draws)
    assert np.all(np.abs(gap) < 4 * np.sqrt(p0 * (1 - p0) / 3000) + 1e-6)
    promoted = martingale_gap(model, model.event_prob, st, idx, 3000, np.random.default_rng(2))
    assert np.max(np.abs(promoted)) > 5 * np.max(np.abs(gap))


def test_coherent_score_tracks_the_exact_endpoint():
    model, Y, X = synthetic(D=120, missing=0.2)
    sc = CoherentScorer(model, Y)
    st = model.prior(X[1])
    exact = mc_event_prob(model, st, 20000, np.random.default_rng(3))
    lin = sc.event_prob(st)
    promoted = model.event_prob(st)
    assert np.corrcoef(exact, lin)[0, 1] > 0.9
    assert np.mean(np.abs(exact - lin)) < 0.1 * np.mean(np.abs(exact - promoted))


def test_no_readout_means_no_update_and_no_information():
    model, Y, X = synthetic()
    sc = CoherentScorer(model, Y)
    st = model.prior(X[2])
    nan = np.full(4, np.nan)
    for post in (model.posterior(st, [0, 1, 2, 3], nan), global_posterior(model, sc.g, st, [0, 1, 2, 3], nan)):
        np.testing.assert_array_equal(post.m, st.m)
        np.testing.assert_array_equal(post.S, st.S)
    order = np.linspace(0, 1, len(model.mu))
    # every readout has a 1e-12 chance of returning: candidates are still ranked, nothing comes back
    vals = design_values(model, sc.event_prob, st, np.full(len(model.mu), 1e-12), 16, (2, 4), order, 50,
                         np.random.default_rng(4))
    assert len(vals) == 3
    for v in vals[1:]:
        assert v.returned_share == 0.0
        assert v.evsi == 0.0


def test_design_value_terms_add_up_and_opportunity_cost_is_non_negative():
    model, Y, X = synthetic()
    sc = CoherentScorer(model, Y)
    st = model.prior(X[3])
    order = np.linspace(0, 1, len(model.mu))
    vals = design_values(model, sc.event_prob, st, model.measured_rate, 16, (2, 4, 8), order, 64,
                         np.random.default_rng(5), round_cost=0.05)
    assert vals[0].k == 0 and vals[0].delta == 0.0
    for v in vals[1:]:
        assert v.delta == pytest.approx(v.evsi - v.opportunity_cost - v.round_cost)
        assert v.opportunity_cost >= -1e-12
    best = choose_design(vals)
    assert best.delta >= 0.0


def test_global_update_changes_the_covariance_in_one_direction_only():
    model, Y, X = synthetic()
    sc = CoherentScorer(model, Y)
    st = model.prior(X[4])
    post = global_posterior(model, sc.g, st, [0, 1, 2], Y[4, :3] if np.isfinite(Y[4, :3]).all() else [5.0, 5.0, 5.0])
    dS = post.S - st.S
    assert np.linalg.matrix_rank(dS, tol=1e-10) == 1
    assert sc.g @ post.S @ sc.g < sc.g @ st.S @ sc.g


def test_derangement_keeps_mask_count_and_values():
    y = np.array([1.0, np.nan, 3.0, 4.0, np.nan])
    order = np.array([0.5, 0.1, 0.2, 0.9, 0.3])
    z = derange(y, order)
    np.testing.assert_array_equal(np.isfinite(z), np.isfinite(y))
    assert sorted(z[np.isfinite(z)]) == sorted(y[np.isfinite(y)])
    assert np.all(z[np.isfinite(y)] != y[np.isfinite(y)])
    one = np.array([np.nan, 2.0])
    np.testing.assert_array_equal(derange(one, order[:2]), one)


def synthetic_domain(n=260, D=30, p=40, seed=7):
    from virtual_cell.bridged_transfer import selective_events
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, p))
    F = X[:, :3] @ rng.normal(size=(3, 3)) * 0.6 + rng.normal(size=(n, 3)) * 0.6
    V = rng.normal(size=(D, 3))
    Y = 100 + 20 * (F @ V.T) + rng.normal(size=(n, D)) * 15
    Y[rng.random((n, D)) < 0.2] = np.nan
    ev, G = selective_events(Y, None, 100)
    groups = np.array([f"p{i // 2}" for i in range(n)])
    return {"Y": Y, "X": X, "events": ev, "G": G, "contexts": np.array([f"s{i}" for i in range(n)]),
            "groups": groups, "items": np.array([f"d{j}" for j in range(D)])}


def test_attribution_runs_end_to_end_on_a_synthetic_domain(monkeypatch):
    import attribution
    monkeypatch.setattr(attribution, "DRAWS", 8)
    d = synthetic_domain()
    sched = np.isfinite(d["Y"]) | (np.random.default_rng(0).random(d["Y"].shape) < 0.5)
    for config in ("primary", "design", "panel80", "probes_vc"):
        recs = attribution.run(config, d, sched)
        assert len(recs) == len(d["contexts"])
        r = recs[0]
        assert all(len(set(x["probe"])) == len(x["probe"]) for x in recs)
        for g in attribution.GROUPS:
            assert r["h_" + g] >= 0
        if config == "primary":
            for g in attribution.STRONG + attribution.COHERENT:
                assert "h_" + g in r
            assert r["k_plan_l0"] in (0,) + attribution.K_OPTIONS
            # hits never exceed the queries actually spent
            assert all(x["probe_hits"] + x["h_D"] <= 16 for x in recs)


def test_calibrated_selector_adopts_only_on_a_positive_lower_bound():
    from tuned import RANKS, calibrated
    rng = np.random.default_rng(8)
    contexts = [f"s{i}" for i in range(400)]
    patient_of = {c: f"p{i // 2}" for i, c in enumerate(contexts)}

    def inner(gain):
        # zero-mean noise around the gain
        return {r: [{"context": c, "vc0": 1,
                     "b_exploit": 1 + gain + int(rng.random() < 0.1) - int(rng.random() < 0.1),
                     "b_lookahead": 1} for c in contexts] for r in RANKS}

    clear = calibrated(inner(1), patient_of, 0.05)
    assert clear["procedure"] == "b_exploit" and clear["candidates"]["b_exploit"]["lcb"] > 0
    none = calibrated(inner(0), patient_of, 0.05)
    assert none["procedure"] == "vc0"
    gen, cal = none["generation_contexts"], none["calibration_contexts"]
    assert gen + cal == len(contexts) and min(gen, cal) > 100
