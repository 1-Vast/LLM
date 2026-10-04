"""Behaviour tests of the design workstream on the frozen builder's synthetic release (no real outcome is read).

File summary
- Path: research/astra/confirmation_campaign_20261004/design/test_design.py
- Purpose: check the contract v2 implementation in campaign.py / feedback.py / stages.py: legal reveals
  (poisoned unpurchased outcomes give identical purchases), no screens in the final round, spend <= cap,
  verification only of earlier-round screen hits, E lines never in any history or world, the target's
  other role assignment never used, condition identity, integer arithmetic, the exact tie-break,
  history formulas against a brute-force loop, the P3 reserve rule, the decision rule, the bootstrap
  scheme, reproducibility, and a complete dry run of every stage.
- Interfaces: `pytest -o addopts= research/astra/confirmation_campaign_20261004/design/test_design.py`
- Depends on: pytest, numpy; the frozen jaaks builder (synthetic_release) and replay.load_design.
"""
from __future__ import annotations

import copy
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from research.astra.confirmation_campaign_20261004.design import campaign as cp
from research.astra.confirmation_campaign_20261004.design import feedback as fb
from research.astra.confirmation_campaign_20261004.design import stages as sg


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    from research.astra.feedback_validation_20261003 import jaaks
    from research.astra.reproducible_allocation_20261003.allocation import replay as rp

    d = tmp_path_factory.mktemp("synthetic")
    src = jaaks.synthetic_release(d / "synthetic_release.csv", lines=10, drugs=12)
    ticket = {"freeze_sha256": "TEST_NOT_A_VAULT", "data_sha256": cp.sha256_file(src)}
    panels, report, candidates = jaaks.build_panels(ticket, src)
    design = rp.load_design(src)
    tissues = cp.build_tissues(panels, candidates, design)
    part = sg.synthetic_partition(tissues)
    data = {"ticket": ticket, "panels": panels, "report": report, "candidates": candidates, "design": design,
            "tissues": tissues, "event_of": None, "seconds": 0.0}
    return {"src": src, "data": data, "part": part}


def _hd(synth):
    return list(sg.hd_targets(synth["data"], synth["part"]))


def _e(synth):
    return list(sg.e_targets(synth["data"], synth["part"]))


def _all_runs(tg, truth):
    out = []
    for arm in cp.ARMS:
        for fp in (10, 35, 60):
            out.append(cp.run_p2(tg, truth, arm, fp))
            out.append(cp.run_p2(tg, truth, arm, fp, unit="wells"))
        out.append(cp.run_p3(tg, truth, arm))
    return out


def _poison(truth, rec):
    """Copy of the truth with every outcome the campaign did not buy replaced by its opposite."""
    t = copy.deepcopy(truth)
    screened = set(rec["screens"])
    verified = set(rec["verifies"])
    for i in range(t["y_s"].size):
        if i not in screened:
            t["y_s"][i] = -t["y_s"][i] + 1000.0
            t["h_s"][i] = ~t["h_s"][i]
        if i not in verified:
            t["y_v"][i] = -t["y_v"][i] - 1000.0
            t["h_v"][i] = ~t["h_v"][i]
    return t


# ----------------------------------------------------------------------------------------- identity
def test_condition_identity(synth):
    data = synth["data"]
    for t, T in data["tissues"].items():
        sv, vs = T.arrays["SV"], T.arrays["VS"]
        assert np.array_equal(sv["y_s"], vs["y_v"]) and np.array_equal(sv["y_v"], vs["y_s"])
        assert np.array_equal(sv["h_s"], vs["h_v"]) and np.array_equal(sv["h_v"], vs["h_s"])
        assert np.array_equal(T.cost["SV"]["cost_s"], T.cost["VS"]["cost_v"])
        orient = data["design"]["orient"]
        for row in range(0, T.n_rows, 7):
            s, v = T.pairs[row]
            sidm = T.lines[T.c[row]]
            assert T.cost["SV"]["cost_s"][row] == 14 * orient[(t, sidm, s, v)][0]      # S anchored, V titrated
            assert T.cost["SV"]["cost_v"][row] == 14 * orient[(t, sidm, v, s)][0]
            assert not set(T.barcodes["SV"]["screen"][row]) & set(T.barcodes["SV"]["verify"][row])
        panel = data["panels"][f"{t}_SV"]
        assert np.array_equal(sv["y_s"], panel.library.y) and np.array_equal(sv["y_v"], panel.valid_y)


def test_integer_arithmetic_and_caps(synth):
    for n in range(1, 2000):
        assert cp.cap_M(n) == math.ceil(Fraction(n, 5))
    for fp in cp.FP_GRID:
        for M in range(1, 400):
            assert ((100 - fp) * M) // 100 == math.floor(Fraction(100 - fp, 100) * M)
    tg, truth = _hd(synth)[0]
    assert tg.M == (tg.n + 4) // 5
    assert tg.W == math.ceil(Fraction(tg.M) * Fraction(int(tg.cost_s.sum() + tg.cost_v.sum()), 2 * tg.n))
    rec = cp.run_p2(tg, truth, "R", 35)
    assert rec["n1"] == ((100 - 35) * tg.M) // 100 and rec["n_screens"] == rec["n1"]
    rec3 = cp.run_p3(tg, truth, "R")
    assert rec3["n_r1"] == (tg.M + 1) // 2


def test_tie_break_exact(synth):
    tg, _ = _hd(synth)[3]
    perm = np.random.default_rng([20261004, tg.code, tg.line_index, tg.role_index]).permutation(tg.n)
    rank = np.empty(tg.n, int)
    rank[perm] = np.arange(tg.n)
    assert np.array_equal(rank, tg.rank)
    assert tg.line_index == synth["data"]["tissues"][tg.tissue].lines.index(tg.sidm)
    const = np.full(tg.n, 0.3)
    assert np.array_equal(tg.order(const), np.argsort(rank))
    noisy = const + 1e-14 * np.arange(tg.n)              # differences below 12 decimals are ties
    assert np.array_equal(tg.order(noisy), np.argsort(rank))
    s = tg.scores["R"][0]
    assert np.array_equal(tg.order(s), np.lexsort((rank, -np.round(s, 12))))


def test_history_formulas_brute_force(synth):
    data, part = synth["data"], synth["part"]
    for tg, truth in _hd(synth)[:4] + _e(synth)[:4]:
        T = data["tissues"][tg.tissue]
        H_lines = set(tg.history_lines)
        A = T.arrays[tg.role]
        hrows = [i for i in range(T.n_rows) if T.lines[T.c[i]] in H_lines]
        hs = np.array([A["h_s"][i] for i in hrows], float)
        hv = np.array([A["h_v"][i] for i in hrows], float)
        pooled = {"p_s": hs.mean(), "p_v": hv.mean(), "p_sv": (hs * hv).mean(),
                  "S": np.mean([A["y_s"][i] for i in hrows]), "L_v": np.mean([A["y_v"][i] for i in hrows]),
                  "S_both": np.mean([(A["y_s"][i] + A["y_v"][i]) / 2 for i in hrows])}
        pooled_vs = (hs * hv).sum() / hs.sum() if hs.sum() else hv.mean()
        for j, p in enumerate(tg.pid):
            rows = [i for i in hrows if T.pid[i] == p]
            n = len(rows)
            ref = {"p_s": (sum(A["h_s"][i] for i in rows) + 2 * pooled["p_s"]) / (n + 2),
                   "p_v": (sum(A["h_v"][i] for i in rows) + 2 * pooled["p_v"]) / (n + 2),
                   "p_sv": (sum(A["h_s"][i] and A["h_v"][i] for i in rows) + 2 * pooled["p_sv"]) / (n + 2),
                   "S": (sum(A["y_s"][i] for i in rows) + 2 * pooled["S"]) / (n + 2),
                   "L_v": (sum(A["y_v"][i] for i in rows) + 2 * pooled["L_v"]) / (n + 2),
                   "S_both": (sum((A["y_s"][i] + A["y_v"][i]) / 2 for i in rows) + 2 * pooled["S_both"]) / (n + 2),
                   "p_v_s": (sum(A["h_s"][i] and A["h_v"][i] for i in rows) + 2 * pooled_vs)
                   / (sum(A["h_s"][i] for i in rows) + 2)}
            for k, v in ref.items():
                assert abs(tg.q[k][j] - v) < 1e-9, (k, j)
        sc = tg.scores
        assert np.allclose(sc["C_prod"][0], tg.q["p_s"] * tg.q["p_v"]) and np.allclose(sc["C_prod"][1], tg.q["p_v"])
        assert np.allclose(sc["C_mean"][0], (tg.q["p_s"] + tg.q["p_v"]) / 2)
        assert np.array_equal(sc["R"][0], tg.q["p_sv"]) and np.array_equal(sc["R"][1], tg.q["p_v_s"])


# ----------------------------------------------------------------------------------------- leakage
def test_e_lines_never_history(synth):
    part = synth["part"]
    for tg, _ in _hd(synth):
        E = set(part[tg.tissue]["E"])
        assert not set(tg.history_lines) & E and tg.sidm not in tg.history_lines
        assert set(tg.history_lines) == set(part[tg.tissue]["HD"]) - {tg.sidm}
    for tg, _ in _e(synth):
        assert set(tg.history_lines) == set(part[tg.tissue]["HD"])
    T = next(iter(synth["data"]["tissues"].values()))
    E = synth["part"][T.tissue]["E"]
    with pytest.raises(AssertionError):
        cp.make_target(T, cp.restrict(T, set(T.lines) - {E[0]}), E[0], "SV", allowed_history=set(T.lines),
                       forbidden=set(E))


def test_poisoning_e_lines_and_target_other_role_changes_nothing(synth):
    """Overwrite outcomes of E lines and of the target line (both roles) in the panels: HD campaigns,
    their scores and purchases must be unchanged; E campaigns must be unchanged by other E lines."""
    data, part = synth["data"], synth["part"]
    base = {(tg.tissue, tg.sidm, tg.role): (tg, truth) for tg, truth in _hd(synth) + _e(synth)}
    poisoned = copy.deepcopy(data)
    rng = np.random.default_rng(5)
    for t, T in poisoned["tissues"].items():
        E = set(part[t]["E"])
        rows = np.flatnonzero(np.isin(T.c, [T.lines.index(s) for s in E]))
        for role in cp.ROLES:
            A = T.arrays[role]
            A["y_s"][rows] = rng.normal(0, 100, rows.size)
            A["y_v"][rows] = rng.normal(0, 100, rows.size)
            A["h_s"][rows] = rng.random(rows.size) < 0.5
            A["h_v"][rows] = rng.random(rows.size) < 0.5
    for tg2, truth2 in sg.hd_targets(poisoned, part):
        tg, truth = base[(tg2.tissue, tg2.sidm, tg2.role)]
        for k in tg.q:
            assert np.array_equal(tg.q[k], tg2.q[k])
        for arm in cp.PREDICTORS:
            assert cp.run_p2(tg, truth, arm, 35)["screens"] == cp.run_p2(tg2, truth2, arm, 35)["screens"]
    # E target: poison every OTHER E line and the target's own outcomes (both roles): scores unchanged
    for tg, truth in _e(synth)[:6]:
        p2 = copy.deepcopy(data)
        T = p2["tissues"][tg.tissue]
        E = set(part[tg.tissue]["E"])
        rows = np.flatnonzero(np.isin(T.c, [T.lines.index(s) for s in E]))
        for role in cp.ROLES:
            T.arrays[role]["h_s"][rows] = ~T.arrays[role]["h_s"][rows]
            T.arrays[role]["y_v"][rows] = T.arrays[role]["y_v"][rows] + 500
        H = cp.restrict(T, set(part[tg.tissue]["HD"]))
        tg2 = cp.make_target(T, H, tg.sidm, tg.role, allowed_history=set(part[tg.tissue]["HD"]), forbidden=E)
        for k in tg.q:
            assert np.array_equal(tg.q[k], tg2.q[k])


def test_target_other_role_never_used(synth):
    """The SV campaign's verification measurements are the VS campaign's screens: poisoning every outcome of
    the target line in both role arrays leaves its scores (history) unchanged."""
    data, part = synth["data"], synth["part"]
    for tg, truth in _hd(synth)[:8]:
        p2 = copy.deepcopy(data)
        T = p2["tissues"][tg.tissue]
        rows = np.flatnonzero(T.c == tg.line_index)
        for role in cp.ROLES:
            T.arrays[role]["h_s"][rows] = ~T.arrays[role]["h_s"][rows]
            T.arrays[role]["h_v"][rows] = ~T.arrays[role]["h_v"][rows]
            T.arrays[role]["y_s"][rows] += 300.0
            T.arrays[role]["y_v"][rows] -= 300.0
        HD = set(part[tg.tissue]["HD"])
        T_hd = cp.restrict(T, HD)
        tg2 = cp.make_target(T_hd, cp.restrict(T_hd, HD - {tg.sidm}), tg.sidm, tg.role,
                             allowed_history=HD - {tg.sidm}, forbidden=set(part[tg.tissue]["E"]) | {tg.sidm})
        for k in tg.q:
            assert np.array_equal(tg.q[k], tg2.q[k])
        assert np.array_equal(tg.rank, tg2.rank)


def test_legal_reveals_poisoned_unpurchased(synth):
    for tg, truth in _hd(synth)[:6] + _e(synth)[:6]:
        for rec in _all_runs(tg, truth):
            if rec["arm"] == cp.ORACLE:
                continue                                    # the oracle reads the truth by definition
            bad = _poison(truth, rec)
            if rec["policy"] == "P2":
                again = cp.run_p2(tg, bad, rec["arm"], rec["fp"], unit=rec["unit"])
            else:
                again = cp.run_p3(tg, bad, rec["arm"])
            assert again["screens"] == rec["screens"] and again["verifies"] == rec["verifies"]


def test_rules_no_final_screens_cap_verify_only_hits(synth):
    for tg, truth in _hd(synth) + _e(synth)[:10]:
        for rec in _all_runs(tg, truth):
            deadline = 2 if rec["policy"] == "P2" else 3
            assert all(r < deadline for r in rec["screen_rounds"])
            assert rec["spent"] <= rec["cap"]
            if rec["unit"] == "measurement":
                assert rec["spent"] == rec["n_screens"] + rec["n_verifications"]
            screened_round = dict(zip(rec["screens"], rec["screen_rounds"]))
            for entry in rec["rounds"]:
                for i in entry["verifies"]:
                    assert i in screened_round and screened_round[i] < entry["round"]
                    assert bool(truth["h_s"][i])
            assert rec["confirmed"] == sum(1 for i in rec["verifies"] if truth["h_s"][i] and truth["h_v"][i])
            assert rec["missed_unscreened"] + rec["missed_screened_not_verified"] + rec["confirmed"] == \
                rec["menu_joint_hits"]
            if rec["policy"] == "P2" and rec["unit"] == "measurement":
                hits = [i for i in rec["screens"] if truth["h_s"][i]]
                order = [int(i) for i in tg.order(cp.arm_scores(tg, rec["arm"], truth)[1]) if i in set(hits)]
                assert rec["verifies"] == order[:tg.M - rec["n1"]]


def test_lab_refuses_illegal_purchases(synth):
    tg, truth = _hd(synth)[0]
    one = np.ones(tg.n, np.int64)
    hit = int(np.flatnonzero(truth["h_s"])[0])
    miss = int(np.flatnonzero(~truth["h_s"])[0])
    lab = cp.Lab(truth, one, one, 4, deadline=2)
    with pytest.raises(cp.IllegalPurchase):
        lab.run_round(1, [hit], [hit])                       # verify in the same round
    lab = cp.Lab(truth, one, one, 4, deadline=2)
    lab.run_round(1, [hit, miss], [])
    for screens, verifies in (([hit], []), ([], [miss]), ([], [int(np.flatnonzero(truth["h_s"])[1])])):
        with pytest.raises(cp.IllegalPurchase):
            lab.run_round(2, screens, verifies)
    lab = cp.Lab(truth, one, one, 2, deadline=3)
    lab.run_round(1, [hit, miss], [])
    with pytest.raises(cp.IllegalPurchase):
        lab.run_round(2, [], [hit])                          # over the cap
    lab = cp.Lab(truth, one, one, 10, deadline=3)
    lab.run_round(1, [hit], [])
    with pytest.raises(cp.IllegalPurchase):
        lab.run_round(1, [], [hit])                          # round not increasing


def test_p3_reserve_rule():
    p = np.array([0.4, 0.4, 0.4, 0.05, 0.9])
    # B2 = 4: j0: 1 + ceil(0.4) = 2 ok; j1: 2 + ceil(0.8) = 3 ok; j2: 3 + ceil(1.2) = 5 > 4 stop (no skipping)
    assert cp.p3_reserve_screens([0, 1, 2, 3, 4], p, 4) == [0, 1]
    assert cp.p3_reserve_screens([3, 0], p, 2) == [3]           # 1 + 1 = 2; then 2 + ceil(0.45) = 3 > 2
    assert cp.p3_reserve_screens([0], p, 0) == []
    q = np.array([0.1] * 10)                                     # float sum 0.30000000000000004 -> 0.3 after rounding
    assert cp.p3_reserve_screens(list(range(10)), q, 4) == [0, 1, 2]


def test_reproducible(synth):
    a = [json.dumps(cp.jsonable(r), sort_keys=True) for tg, truth in _hd(synth)[:4] for r in _all_runs(tg, truth)]
    b = [json.dumps(cp.jsonable(r), sort_keys=True) for tg, truth in _hd(synth)[:4] for r in _all_runs(tg, truth)]
    assert a == b


def test_decision_rule_and_bootstrap():
    def c(L, U, zero=0):
        return {"relative_gain_ci": [L, U], "mean_diff_ci": [L, U], "resamples": 10000,
                "resamples_zero_denominator": zero, "mean_y": 1.0}
    cases = {(-0.2, -0.01): "HARM", (-0.02, 0.0): "WORTHWHILE_EXCLUDED", (-0.02, 0.049): "WORTHWHILE_EXCLUDED",
             (-0.02, 0.05): "UNRESOLVED", (0.0, 0.2): "UNRESOLVED", (0.01, 0.04): "SMALL_BENEFIT",
             (0.01, 0.05): "BENEFIT_DETECTED", (0.05, 0.2): "BENEFIT_DETECTED", (0.051, 0.2): "WORTHWHILE"}
    for (L, U), cat in cases.items():
        assert cp.decision(c(L, U))["verdict"] == "EXPLORATORY_" + cat
    assert cp.decision(c(0.01, 0.04, zero=200))["interval_used"].startswith("absolute")
    keys = [("Breast", "B1"), ("Breast", "B2"), ("Colon", "C1"), ("Colon", "C2"), ("Colon", "C3"), ("Pancreas", "P1")]
    idx = cp.boot_indices(keys, resamples=50)
    rng = np.random.default_rng(20261004)
    for b in range(50):
        manual = np.concatenate([np.array(g)[rng.integers(0, len(g), len(g))] for g in ([0, 1], [2, 3, 4], [5])])
        assert np.array_equal(manual, idx[b])
    x, y = np.array([1, 2, 0, 1, 3, 2.]), np.array([1, 1, 1, 1, 2, 2.])
    r = cp.boot_contrast(x, y, keys, idx)
    rel = [x[i].sum() / y[i].sum() - 1 for i in idx]
    assert np.allclose(r["relative_gain_ci"], np.percentile(rel, [2.5, 97.5]))
    assert abs(r["relative_gain"] - (9 / 8 - 1)) < 1e-12


def test_auc_ties_and_undefined():
    assert cp.auc(np.array([0.1, 0.2, 0.3]), np.array([0, 0, 1], bool)) == 1.0
    assert cp.auc(np.array([0.5, 0.5]), np.array([0, 1], bool)) == 0.5
    assert cp.auc(np.array([0.5, 0.4]), np.array([1, 1], bool)) is None


# ----------------------------------------------------------------------------------------- feedback
def test_feedback_world_and_signal_legal(synth):
    data, part = synth["data"], synth["part"]
    tg, truth = _hd(synth)[0]
    E = set(part[tg.tissue]["E"])
    with pytest.raises(AssertionError):
        fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], set(data["tissues"][tg.tissue].lines), tg.sidm, E)
    world, present = fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], set(part[tg.tissue]["HD"]), tg.sidm, E)
    assert not set(present) & E
    sig = fb.Signal(world)
    st = fb.round1_state(tg, truth)
    d1 = fb.Decision2(tg, sig, st)
    bad = _poison(truth, {"screens": list(np.flatnonzero(st.screened)), "verifies": []})
    d2 = fb.Decision2(tg, sig, fb.round1_state(tg, bad))
    assert np.array_equal(d1.F, d2.F) and d1.m == d2.m
    assert abs(d1.f[d1.eligible].mean()) < 1e-9


def test_feedback_models_identical_round1_and_F0_equals_R(synth):
    data, part = synth["data"], synth["part"]
    rows, camps = {}, []
    for tg, truth in _hd(synth):
        world, _ = fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], set(part[tg.tissue]["HD"]), tg.sidm,
                                set(part[tg.tissue]["E"]))
        sig = fb.Signal(world)
        rows[(tg.tissue, tg.sidm, tg.role)] = fb.collect(tg, truth, sig)
        camps.append((tg, truth, sig))
    keys = cp.sort_keys({(k[0], k[1]) for k in rows})
    fit = fb.fit_models(rows, keys, resamples=50)
    assert fit["F0"]["beta"][1] > 0
    for tg, truth, sig in camps[:6]:
        ev, logs = fb.evaluate_campaign(tg, truth, sig, fit)
        assert ev["identical_round1"]
        assert ev["F0_equals_R_purchases"]
        for rec in logs.values():
            assert rec["spent"] <= rec["cap"] and all(r < 3 for r in rec["screen_rounds"])
            bad = _poison(truth, rec)
        hook_rec = logs["Ff"]
        def hook(state):
            dd = fb.Decision2(tg, sig, state)
            p = fb.predictions(dd, tg, fit)["Ff"]
            return tg.order(p), p
        again = cp.run_p3(tg, _poison(truth, hook_rec), "R", round2_order=hook)
        assert again["screens"] == hook_rec["screens"] and again["verifies"] == hook_rec["verifies"]


def test_logistic_fit_recovers_coefficients():
    rng = np.random.default_rng(1)
    x = rng.normal(size=20000)
    m = rng.normal(size=20000)
    y = (rng.random(20000) < 1 / (1 + np.exp(-(-1.0 + 0.8 * x + 0.5 * m)))).astype(float)
    beta = fb.fit_constrained(x, m[:, None], y)["beta"]
    assert np.allclose(beta, [-1.0, 0.8, 0.5], atol=0.08)
    neg = fb.fit_constrained(x, None, 1 - (rng.random(20000) < 1 / (1 + np.exp(-x))).astype(float))
    assert neg["b_constrained"] and neg["beta"][1] == fb.B_FLOOR


# ----------------------------------------------------------------------------------------- dry run
def test_all_stages_dry_run(tmp_path):
    sg.main(["all_dry", "--dry", str(tmp_path / "dry")])
    base = tmp_path / "dry"
    sel = json.loads((base / "selection.json").read_text(encoding="utf-8"))
    assert isinstance(sel["fp_star"], int) and sel["fp_star"] in cp.FP_GRID and sel["C_star"] in cp.SIMPLE
    gate = json.loads((base / "feedback_gate.json").read_text(encoding="utf-8"))
    assert "pass" in gate
    add = json.loads((base / "plan_addendum_1.json").read_text(encoding="utf-8"))
    assert add["selection_sha256"] == cp.sha256_file(base / "selection.json")
    ev = next((base / "results").glob("eval_*")) / "eval_summary.json"
    summary = json.loads(ev.read_text(encoding="utf-8"))
    assert summary["primary"]["verdict"]["verdict"].startswith("EXPLORATORY_")
    with pytest.raises(SystemExit):                       # selection never overwritten
        sg.stage_dev(sg.make_ctx(base))
