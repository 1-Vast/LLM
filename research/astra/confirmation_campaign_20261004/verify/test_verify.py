"""Behaviour tests for the verify workstream's independent P2 implementation (synthetic data only).

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/test_verify.py
- Purpose: check integer budgets, the registered tie-break, the shrinkage formulas, history
  exclusion of the target and of E lines, P2 budget and legality, the poisoning test's power to
  catch a leaky policy, bootstrap determinism and the decision-rule table. No real outcome is read.
- Interfaces: pytest tests.
"""
from __future__ import annotations

from fractions import Fraction
import math

import numpy as np
import pytest

from research.astra.confirmation_campaign_20261004.verify import independent_check as ic


def synthetic(seed: int = 0, lines: int = 10, tissue: str = "Breast", role: str = "SV") -> ic.RoleData:
    rng = np.random.default_rng(seed)
    drugs = tuple(f"D{i}" for i in range(8))
    pairs = [(a, b) for a in range(4) for b in range(4, 8)]
    pair, line = [], []
    for c in range(lines):
        for a, b in pairs:
            pair.append(a * len(drugs) + b)
            line.append(c)
    n = len(pair)
    base = rng.random(len(pairs))
    p = np.tile(base, lines)
    sh = rng.random(n) < p
    vh = np.where(sh, rng.random(n) < 0.7, rng.random(n) < 0.2)
    return ic.RoleData(tissue, role, tuple(f"SIDM{c:05d}" for c in range(lines)), drugs, np.array(pair, np.int64),
                       np.array(line, np.int64), sh, vh, rng.normal(10, 20, n), rng.normal(10, 20, n))


def test_integer_arithmetic_matches_exact_rationals():
    assert ic.cap_m(15) == 3 and ic.cap_m(16) == 4 and ic.cap_m(1) == 1 and ic.cap_m(5) == 1
    assert ic.n_screen(30, 90) == 63 and ic.n_screen(55, 60) == 27 and ic.n_screen(20, 5) == 4
    for fp in ic.FP_GRID:
        for m in range(0, 400):
            assert ic.n_screen(fp, m) == math.floor(Fraction(100 - fp, 100) * m)
    for menu in range(0, 2000):
        assert ic.cap_m(menu) == math.ceil(Fraction(menu, 5))
    with pytest.raises(ValueError):
        ic.n_screen(12, 10)


def test_tie_break_is_registered_and_deterministic():
    r1 = ic.tie_rank("Colon", 3, "VS", 20)
    r2 = ic.tie_rank("Colon", 3, "VS", 20)
    assert np.array_equal(r1, r2) and sorted(r1) == list(range(20))
    perm = np.random.default_rng([20261004, 2, 3, 1]).permutation(20)
    assert all(r1[perm[k]] == k for k in range(20))
    score = np.array([0.5, 0.5 + 1e-15, 0.9, 0.1])          # first two tie after rounding to 12 decimals
    rank = np.array([3, 1, 2, 0])
    assert list(ic.order(score, rank)) == [2, 1, 0, 3]


def test_shrinkage_hand_example():
    drugs = ("A", "B", "C", "D")
    # pairs: 0*4+2 = (A,C), 1*4+3 = (B,D); lines 0,1 history, line 2 target
    pair = np.array([2, 7, 2, 7, 2, 7], np.int64)
    line = np.array([0, 0, 1, 1, 2, 2], np.int64)
    sh = np.array([1, 0, 1, 1, 1, 1], bool)
    vh = np.array([1, 0, 0, 1, 0, 0], bool)
    ys = np.array([10., 0., 20., 30., 99., 99.])
    yv = np.array([30., 0., 0., 10., 99., 99.])
    rd = ic.RoleData("Breast", "SV", ("L0", "L1", "L2"), drugs, pair, line, sh, vh, ys, yv)
    rows = np.array([4, 5])
    sc = ic.shrunk_scores(rd, ic.history_mask(rd, 2, np.array([0, 1, 2])), rows)
    pooled_ps, pooled_pv, pooled_psv = 3 / 4, 2 / 4, 2 / 4
    pooled_pvs = 2 / 3
    assert sc["C_s"][0][0] == pytest.approx((2 + 2 * pooled_ps) / 4)      # (A,C): 2 screen hits in 2 lines
    assert sc["C_s"][0][1] == pytest.approx((1 + 2 * pooled_ps) / 4)
    assert sc["R"][0][0] == pytest.approx((1 + 2 * pooled_psv) / 4)
    assert sc["R"][1][0] == pytest.approx((1 + 2 * pooled_pvs) / (2 + 2))
    assert sc["R"][1][1] == pytest.approx((1 + 2 * pooled_pvs) / (1 + 2))
    assert sc["C_prod"][0][1] == pytest.approx(sc["C_s"][0][1] * sc["C_v"][0][1])
    yb = (ys[:4] + yv[:4]) / 2
    assert sc["S_both"][0][0] == pytest.approx((yb[0] + yb[2] + 2 * yb.mean()) / 4)
    assert sc["S"][0][1] == pytest.approx((0 + 30 + 2 * ys[:4].mean()) / 4)
    assert sc["L_v"][0][0] == pytest.approx((30 + 0 + 2 * yv[:4].mean()) / 4)


def test_pooled_v_given_s_falls_back_when_history_has_no_screen_hit():
    rd = synthetic(1)
    rd.screen_hit[:] = False
    rows = np.flatnonzero(rd.line == 0)
    sc = ic.shrunk_scores(rd, ic.history_mask(rd, 0, np.arange(10)), rows)
    assert np.allclose(sc["R"][1], sc["_pooled"]["pv"])


def test_history_ignores_target_and_e_lines():
    rd = synthetic(2)
    hd = np.arange(5)
    rows = np.flatnonzero(rd.line == 7)
    a = ic.shrunk_scores(rd, ic.history_mask(rd, 7, hd), rows)
    bad = rd.copy()
    m = bad.line >= 5                                # target and every E line
    bad.screen_hit[m] = ~bad.screen_hit[m]
    bad.valid_hit[m] = ~bad.valid_hit[m]
    bad.ys[m] += 1000
    bad.yv[m] -= 1000
    b = ic.shrunk_scores(bad, ic.history_mask(bad, 7, hd), rows)
    for p in ic.PREDICTORS:
        assert np.array_equal(a[p][0], b[p][0]) and np.array_equal(a[p][1], b[p][1])
    # leave-one-line-out for an HD target
    h = ic.history_mask(rd, 2, hd)
    assert not h[rd.line == 2].any() and h[rd.line == 3].all() and not h[rd.line == 6].any()


@pytest.mark.parametrize("seed", range(5))
def test_p2_budget_and_legality(seed):
    rd = synthetic(seed, lines=8)
    hd = np.arange(4)
    for t in range(4, 8):
        for p in ic.PREDICTORS + ("oracle",):
            for fp in ic.FP_GRID:
                r = ic.campaign(rd, t, hd, p, fp)
                assert r["M"] == ic.cap_m(16) == 4 and r["n1"] == ic.n_screen(fp, 4)
                assert r["spent"] <= r["M"] and len(r["screens"]) == r["n1"]
                assert set(r["verifies"]) <= set(r["screen_hits"])
                assert all(rnd == 1 for k, _, rnd in r["purchase_log"] if k == "screen")
                assert all(rnd == 2 for k, _, rnd in r["purchase_log"] if k == "verify")
                assert len(r["verifies"]) == min(len(r["screen_hits"]), r["M"] - r["n1"])
                rows = np.flatnonzero(rd.line == t)
                truth = rd.screen_hit[rows] & rd.valid_hit[rows]
                assert r["confirmed"] == int(sum(truth[i] for i in r["verifies"]))


def test_market_refuses_illegal_purchases():
    m = ic.Market(np.array([True, False]), np.array([True, True]))
    with pytest.raises(RuntimeError):
        m.verify(0, 2)                                  # not screened
    m.screen(0, 1)
    with pytest.raises(RuntimeError):
        m.verify(0, 1)                                  # same round
    m.screen(1, 1)
    with pytest.raises(RuntimeError):
        m.verify(1, 2)                                  # screen non-hit
    assert m.verify(0, 2) is True
    with pytest.raises(RuntimeError):
        m.screen(0, 2)                                  # re-screen


def test_poisoning_keeps_legal_purchases_and_catches_a_leak():
    rd = synthetic(3, lines=12)
    hd, e = np.arange(6), np.arange(6, 12)
    t = 8
    ref = ic.campaign(rd, t, hd, "R", 30)
    bad = ic.poison(rd, t, set(ref["screens"]), set(ref["verifies"]), e, seed=1)
    again = ic.campaign(bad, t, hd, "R", 30)
    assert again["purchase_log"] == ref["purchase_log"] and again["confirmed"] == ref["confirmed"]
    # a leaky score (target's own hidden joint call) must be caught by the same test
    rows = np.flatnonzero(rd.line == t)
    leak = {"R": ((rd.screen_hit[rows] & rd.valid_hit[rows]).astype(float),) * 2}
    leak_bad = {"R": ((bad.screen_hit[rows] & bad.valid_hit[rows]).astype(float),) * 2}
    caught = False
    for fp in ic.FP_GRID:
        a = ic.campaign(rd, t, hd, "R", fp, leak)
        b0 = ic.poison(rd, t, set(a["screens"]), set(a["verifies"]), e, seed=2)
        leak_bad = {"R": ((b0.screen_hit[rows] & b0.valid_hit[rows]).astype(float),) * 2}
        b = ic.campaign(b0, t, hd, "R", fp, leak_bad)
        caught |= a["purchase_log"] != b["purchase_log"]
    assert caught


def test_role_symmetric_predictors_rank_identically():
    sv = synthetic(4)
    vs = ic.RoleData(sv.tissue, "VS", sv.lines, sv.drugs, sv.pair, sv.line, sv.valid_hit.copy(), sv.screen_hit.copy(),
                     sv.yv.copy(), sv.ys.copy())
    rows = np.flatnonzero(sv.line == 9)
    a = ic.shrunk_scores(sv, ic.history_mask(sv, 9, np.arange(5)), rows)
    b = ic.shrunk_scores(vs, ic.history_mask(vs, 9, np.arange(5)), rows)
    for p in ("R", "S_both", "C_mean", "C_prod"):
        assert np.allclose(a[p][0], b[p][0])
    assert np.allclose(a["C_s"][0], b["C_v"][0])


def test_verdict_table_is_complete():
    tau = 0.05
    assert ic.verdict(-0.3, -0.01) == "EXPLORATORY_HARM"
    assert ic.verdict(-0.02, 0.03) == "EXPLORATORY_WORTHWHILE_EXCLUDED"
    assert ic.verdict(0.01, 0.04) == "EXPLORATORY_SMALL_BENEFIT"
    assert ic.verdict(0.01, 0.2) == "EXPLORATORY_BENEFIT_DETECTED"
    assert ic.verdict(tau, 0.2) == "EXPLORATORY_BENEFIT_DETECTED"
    assert ic.verdict(0.06, 0.2) == "EXPLORATORY_WORTHWHILE"
    assert ic.verdict(-0.01, 0.2) == "EXPLORATORY_UNRESOLVED"
    assert ic.verdict(0.0, 0.2) == "EXPLORATORY_UNRESOLVED"


def test_bootstrap_is_deterministic_and_stratified():
    rng = np.random.default_rng(0)
    r = {t: rng.integers(0, 5, 10).astype(float) for t in ic.TISSUES}
    c = {t: rng.integers(0, 5, 10).astype(float) for t in ic.TISSUES}
    a = ic.bootstrap(r, c, n_boot=500)
    b = ic.bootstrap(r, c, n_boot=500)
    assert a == b and a["n_lines"] == 30
    same = ic.bootstrap(c, c, n_boot=200)
    assert same["relative_95"] == [0.0, 0.0] and same["absolute_95"] == [0.0, 0.0]


def test_development_selection_tie_rules():
    part = {t: {"HD": [f"{t}{i}" for i in range(2)], "E": []} for t in ic.TISSUES}
    dev = {}
    for t in ic.TISSUES:
        for i in range(2):
            for role in ic.ROLES:
                for p in ic.PREDICTORS:
                    for fp in ic.FP_GRID:
                        val = 1 if (p in ("L_v", "C_s") and fp in (20, 40)) else 0
                        dev[(p, fp, f"{t}{i}", role)] = {"confirmed": val}
    sel = ic.development_table(dev, part)
    assert sel["C_star"] == "L_v" and sel["fp_star"] == 20 and sel["best_fp"]["R"] == 10
