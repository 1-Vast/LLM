"""Synthetic checks of the study machinery, run before the freeze; writes SYNTHETIC_TESTS.txt (or --out).

T1-T4 check primitives (log-LR, quadrature, e-BH, allocation). T5 checks world-fit recovery. T6 checks FDR of every
Gate 0 arm under an exactly specified world. T7 measures how often the Gate 1a criteria fail when the noise model is
right (false-fail rate) and T8 how they respond when it is wrong. T9 checks the Gate 1b design e-value. T10 checks the
A1c certificate. T11 runs gate1.py and gate0.py end to end on synthetic inputs.
"""
import argparse
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

from common import ALPHA, CHECK_M, GRID, OUT, import_certification, write_text  # noqa: E402
from evalues import composite_null_check, ebh, log_lr, null_expectation, null_expectation_grid  # noqa: E402
from gate1 import concat_pools, design_evalues, gate1a_pool, pseudo_diffs  # noqa: E402
from replay import Bets, Pool, allocate, run_a1c, run_arm  # noqa: E402
from worldfit import (fit_primary, fit_t, fit_t_invariant, invariant_loglik, npmle, prior_summary,  # noqa: E402
                      read_loglik, residuals)

LINES = []


def report(name, ok, detail):
    LINES.append(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    print(LINES[-1], flush=True)
    return ok


def noise(rng, shape, sigma, size):
    if shape == "t4":
        return sigma * rng.standard_t(4.0, size=size)
    if shape == "gauss":
        return sigma * rng.standard_normal(size)
    if shape == "contaminated":
        z = rng.standard_normal(size)
        return sigma * np.where(rng.random(size) < 0.05, 4.0 * z, z)
    raise ValueError(shape)


def synth_jaaks(seed, K=3000, shape="t4", hetero=False, sigma=0.08):
    rng = np.random.default_rng(seed)
    R = rng.choice([2, 3, 4, 5, 6, 7], size=K, p=[0.68, 0.26, 0.04, 0.01, 0.005, 0.005])
    mu = np.where(rng.random(K) < 0.5, 0.0, np.clip(rng.normal(0.18, 0.10, K), 0.01, 0.8))
    e = noise(rng, shape, sigma, (K, 7))
    if hetero:
        e *= np.where(rng.random(K) < 0.2, 2.5, 1.0)[:, None]
    X = mu[:, None] + e
    X[np.arange(7)[None, :] >= R[:, None]] = np.nan
    n_o = rng.choice([1, 2, 3], size=K, p=[0.5, 0.3, 0.2])
    p = 0.02 + 0.8 * mu + 0.10 / np.sqrt(n_o) * rng.standard_t(4.0, size=K)
    return {"X": X, "mu": mu, "p": p, "n_o": n_o, "R": R}


def shuffled(X, rng):
    """Per-unit random reveal order of the finite reads, left-packed."""
    keys = np.where(np.isnan(X), np.inf, rng.random(X.shape))
    return np.take_along_axis(X, np.argsort(keys, axis=1), axis=1)


def fitted_bets(X):
    """Fitted noise model with every grid-checked bet allowed; T2b is a numerical diagnostic."""
    nz = fit_t_invariant(X)
    return Bets(nz["sigma"], nz["nu"], np.ones(CHECK_M.size, dtype=bool)), nz, None


# ---------------------------------------------------------------- T1-T4

def t1_log_lr():
    x = np.linspace(-3, 3, 25)
    worst = 0.0
    for s, nu, m in ((0.1, 4.0, 0.2), (1.0, 2.5, 3.0), (0.05, 50.0, 0.01), (0.3, 2.1, 1.2)):
        ref = stats.t.logpdf(x - m, nu, scale=s) - stats.t.logpdf(x, nu, scale=s)
        worst = max(worst, float(np.max(np.abs(log_lr(x, m, s, nu) - ref))))
    return report("T1 log-LR equals scipy t log-density difference", worst < 1e-10, f"max abs diff {worst:.2e}")


def t2_quadrature():
    worst = 0.0
    for nu in (2.2, 4.0, 30.0, 100.0):
        for m in (0.05, 1.0, 4.0, 10.0):
            for mu in (0.0, -0.5, -2.0, -5.0):
                worst = max(worst, abs(null_expectation_grid([m], mu, nu)[0] - null_expectation(m, mu, nu)))
    ok = report("T2a tan-mapped trapezoid matches adaptive quadrature", worst < 1e-8, f"max abs diff {worst:.2e}")
    for nu in (2.2, 4.0, 30.0, 100.0):
        c = composite_null_check(nu)
        ok &= report(f"T2b composite-null grid diagnostic for nu={nu}", c["all_valid"] and
                     np.max(np.abs(c["expectation_at_mu0"] - 1)) < 1e-7,
                     f"max E over mu<=0 {c['max_over_grid']:.9f}, max |E0-1| "
                     f"{np.max(np.abs(c['expectation_at_mu0'] - 1)):.1e}")
    return ok


def t3_ebh():
    rng = np.random.default_rng(1)
    bad = 0
    for _ in range(500):
        K = int(rng.integers(1, 60))
        le = rng.normal(2.0, 3.0, K)
        e = np.exp(le)
        srt = np.sort(e)[::-1]
        kstar = max([k for k in range(1, K + 1) if srt[k - 1] >= K / (ALPHA * k)], default=0)
        expect = np.zeros(K, dtype=bool)
        if kstar:
            expect[np.argsort(-e, kind="stable")[:kstar]] = True
        mask, k = ebh(le)
        bad += int(k != kstar or not np.array_equal(mask, expect))
    return report("T3 e-BH equals brute-force definition", bad == 0, f"{bad} mismatches in 500 random cases")


def brute_allocate(order, remaining, budget):
    rem = np.array(remaining, dtype=int).copy()
    out = np.zeros_like(rem)
    while budget > 0 and any(rem[u] > 0 for u in order):
        for u in order:
            if budget == 0:
                break
            if rem[u] > 0:
                rem[u] -= 1
                out[u] += 1
                budget -= 1
    return out


def t4_allocate():
    rng = np.random.default_rng(2)
    bad = 0
    ok1 = np.array_equal(allocate([2, 0, 1], np.array([1, 3, 2]), 4), [1, 1, 2])
    for _ in range(2000):
        K = int(rng.integers(1, 30))
        remaining = rng.integers(0, 5, K)
        order = rng.permutation(K)[: int(rng.integers(0, K + 1))]
        budget = int(rng.integers(0, 40))
        bad += int(not np.array_equal(allocate(order, remaining, budget), brute_allocate(order, remaining, budget)))
    return report("T4 pass allocation equals explicit pass simulation", ok1 and bad == 0,
                  f"worked example {'ok' if ok1 else 'wrong'}, {bad} mismatches in 2000 random cases")


# ---------------------------------------------------------------- T5-T6

def t5a_invariant_quadrature():
    rng = np.random.default_rng(3)
    X = np.full((40, 17), np.nan)
    for i in range(40):
        n = [2, 3, 5, 17][i % 4]
        X[i, :n] = 0.1 * i / 40 + 0.08 * rng.standard_t(3.0, n)
    X[0, :2] = [0.0, 0.9]
    coarse = invariant_loglik(X, 0.08, 3.0, 0.08)
    fine_theta = np.linspace(-np.pi / 2, np.pi / 2, 16003)[1:-1]
    fine = invariant_loglik(X, 0.08, 3.0, 0.08, theta=fine_theta)
    from scipy import integrate
    exact = 0.0
    for row in X[:8]:
        x = row[~np.isnan(row)]
        f = lambda m: float(np.exp(np.sum(stats.t.logpdf(x - m, 3.0, scale=0.08))))
        pts = sorted(set(np.round(x, 6)))
        exact += math.log(integrate.quad(f, -np.inf, np.inf, points=None, limit=500, epsabs=0)[0]
                          if False else sum(integrate.quad(f, a, b, limit=500, epsabs=0)[0]
                                            for a, b in zip([-np.inf] + pts, pts + [np.inf])))
    approx8 = invariant_loglik(X[:8], 0.08, 3.0, 0.08)
    return report("T5a invariant likelihood quadrature", abs(coarse - fine) < 1e-6 * abs(fine) and
                  abs(approx8 - exact) < 1e-6 * abs(exact),
                  f"2001 vs 16001 points: {coarse:.8f} vs {fine:.8f}; 8 units vs adaptive quad: "
                  f"{approx8:.8f} vs {exact:.8f}")


def t5_world_fit():
    ok = True
    for shape in ("t4", "gauss", "contaminated"):
        d = synth_jaaks(10, K=6000, shape=shape)
        nz = fit_t_invariant(d["X"])
        rz = nz["residual_fit"]
        rz_sd = rz["sigma"] * math.sqrt(rz["nu"] / (rz["nu"] - 2))
        model_sd = nz["sigma"] * math.sqrt(nz["nu"] / (nz["nu"] - 2)) if nz["nu"] > 2 else math.inf
        true_sd = {"t4": 0.08 * math.sqrt(2.0), "gauss": 0.08, "contaminated": 0.08 * math.sqrt(0.95 + 0.05 * 16)}[shape]
        LL = read_loglik(d["X"], nz["sigma"], nz["nu"])
        prior = npmle(LL)
        s = prior_summary(prior["weights"])
        prim = fit_primary(d["p"], d["n_o"], LL, prior["weights"], nz["nu"])
        sd_ok = abs(model_sd / true_sd - 1) < 0.15
        mean_ok = abs(s["mean"] - d["mu"].mean()) < 0.01
        w = prior["weights"]
        big_fit, big_true = float(w[GRID > 0.05].sum()), float((d["mu"] > 0.05).mean())
        pos_ok = abs(big_fit - big_true) < 0.05
        b_ok = abs(prim["b"] - 0.8) < 0.15
        passed = sd_ok and mean_ok and pos_ok and b_ok
        name = (f"T5 world-fit recovery ({shape})" if shape != "contaminated" else
                "T5 world fit when the noise is not Student-t (contaminated normal) [informative, no pass rule]")
        ok &= report(name, passed or shape == "contaminated",
                     f"noise sd {model_sd:.4f} vs {true_sd:.4f} (nu {nz['nu']:.1f}); prior mean {s['mean']:.4f} vs "
                     f"{d['mu'].mean():.4f}; P(mu>0.05) {big_fit:.3f} vs {big_true:.3f}; "
                     f"P(mu>0) {s['p_positive']:.3f} vs {(d['mu'] > 0).mean():.3f} (atom at 0 smeared, not scored); "
                     f"b {prim['b']:.3f} vs 0.8, a {prim['a']:.3f} vs 0.02; EM iterations {prior['iterations']}; "
                     f"residual-fit comparison: sd {rz_sd:.4f}, nu {rz['nu']:.1f}")
    return ok


def t6_gate0_fdr(cert):
    d = synth_jaaks(20, K=4000, shape="t4")
    bets, nz, _ = fitted_bets(d["X"])
    LL = read_loglik(d["X"], nz["sigma"], nz["nu"])
    w = npmle(LL)["weights"]
    prim = fit_primary(d["p"], d["n_o"], LL, w, nz["nu"])
    fdp = {a: [] for a in ("A0", "A1", "OA-PF", "ORACLE")}
    disc = {a: [] for a in fdp}
    for r in range(100):
        rng = np.random.default_rng(1000 + r)
        mu = rng.choice(GRID, size=d["X"].shape[0], p=w)
        X = mu[:, None] + nz["sigma"] * rng.standard_t(nz["nu"], size=d["X"].shape)
        X[np.isnan(d["X"])] = np.nan
        p = prim["a"] + prim["b"] * mu + prim["sigma_p"] / np.sqrt(d["n_o"]) * rng.standard_t(nz["nu"], size=mu.size)
        pool = Pool(X, p, 7.0, mu)
        tables = {"pf": bets.pf(X), "oracle": bets.oracle(X, mu)}
        for arm in fdp:
            out = run_arm(arm, pool, bets, pool.K, np.random.default_rng(5000 + r), tables)
            fdp[arm].append(out["fdp"])
            disc[arm].append(out["D"])
    ok = True
    for arm, v in fdp.items():
        v = np.array(v)
        se = v.std(ddof=1) / math.sqrt(v.size)
        ok &= report(f"T6 Gate 0 FDR under the exact model ({arm})", v.mean() <= ALPHA + 2 * se,
                     f"mean FDP {v.mean():.4f} (2SE {2 * se:.4f}), mean discoveries {np.mean(disc[arm]):.1f}")
    a1c = [run_a1c(Pool(d["mu"][:, None] + nz["sigma"] * np.random.default_rng(9000 + r).standard_t(
        nz["nu"], size=(d["mu"].size, 1)), d["p"], 7.0, d["mu"]), np.random.default_rng(r), cert)
        for r in range(100)]
    lab = np.array([x["false_label_fdp"] for x in a1c])
    ok &= report("T10 A1c realised label FDR on held-out reads", lab.mean() <= ALPHA + 2 * lab.std(ddof=1) / 10,
                 f"mean label FDP {lab.mean():.4f}, mean nominated {np.mean([x['D'] for x in a1c]):.1f}, "
                 f"mean truth FDP {np.mean([x['false_truth_fdp'] for x in a1c]):.4f}")
    return ok


# ---------------------------------------------------------------- T7-T8

def gate1_cells_for(d, bets, n_replays, kind, seed):
    """Run all Gate 1a cells for a synthetic dataset: kind P1 (pair differences) or P2 (mirrored null units)."""
    null_units = np.nonzero(d["mu"] == 0)[0]

    def real(r):
        return Pool(shuffled(d["X"], np.random.default_rng([seed, r, 1])), d["p"], 7.0)

    def null(r):
        X = shuffled(d["X"], np.random.default_rng([seed, r, 1]))
        if kind == "P1":
            return Pool(pseudo_diffs(X), d["p"], 14.0)
        return Pool(-X[null_units], d["p"][null_units], 7.0)

    def mixed(r):
        return concat_pools(real(r), null(r))

    cells, diag = gate1a_pool(f"synthetic-{kind}-{seed}", null, mixed, bets, n_replays,
                              "random" if kind == "P1" else "p", "diff" if kind == "P1" else "single")
    return cells, diag


def t7_t8_gate1(n_replays):
    ok = True
    for label, shape, hetero in (("t4", "t4", False), ("gauss", "gauss", False), ("contaminated", "contaminated", False),
                                 ("hetero-t4", "t4", True)):
        fails = {kind: {"a": 0, "b": 0, "c": 0, "cells": 0, "worst_a": -np.inf} for kind in ("P1", "P2")}
        for seed in (31, 32, 33):
            d = synth_jaaks(seed, K=3000, shape=shape, hetero=hetero)
            bets, nz, _ = fitted_bets(d["X"])
            for kind in ("P1", "P2"):
                cells, _ = gate1_cells_for(d, bets, n_replays, kind, seed)
                f = fails[kind]
                for v in cells.values():
                    f["cells"] += 1
                    f["a"] += not v["a_pass"]
                    f["b"] += not v["b_pass"]
                    f["c"] += not v["c_pass"]
                    f["worst_a"] = max(f["worst_a"], v["a_capped_mean_e"] - v["a_limit"])
        for kind, f in fails.items():
            detail = (f"cells {f['cells']}, failing (a) {f['a']}, (b) {f['b']}, (c) {f['c']}; "
                      f"largest (capped mean - limit) {f['worst_a']:+.3f}")
            if hetero or shape == "contaminated":
                report(f"T8 noise family wrong ({label}, {kind}) [informative, no pass rule]", True, detail)
            else:
                ok &= report(f"T7 Gate 1a criteria when the noise family is right ({label}, {kind})",
                             f["a"] + f["b"] + f["c"] == 0, detail)
    return ok


# ---------------------------------------------------------------- T9

def t9_design():
    rng = np.random.default_rng(7)
    e_null, e_shift = [], []
    for _ in range(3000):
        refs = rng.normal(size=114)
        x = rng.normal(size=8)
        e, _ = design_evalues(x, refs, rng)
        e_null.extend(e)
        e2, _ = design_evalues(rng.normal(-0.5, 1.0, size=8), refs, rng)
        e_shift.extend(e2)
        ties = np.round(rng.normal(size=114) * 3)
        e3, _ = design_evalues(np.round(rng.normal(size=8) * 3), ties, rng)
        e_null.extend(e3)
    m0, m1 = float(np.mean(e_null)), float(np.mean(e_shift))
    return report("T9 Gate 1b design e-value: mean 1 under exchangeability (with ties), > 1.25 under a shift",
                  abs(m0 - 1) < 0.05 and m1 > 1.25, f"null mean {m0:.3f}, shifted mean {m1:.3f}")


# ---------------------------------------------------------------- T11 dry run

def t11_dry_run(n_replays):
    rng = np.random.default_rng(11)
    tmp = Path(tempfile.mkdtemp(prefix="cdg_dry_"))
    d = synth_jaaks(41, K=1500, shape="t4")
    K = d["X"].shape[0]
    units = np.array([f"S{u}|A|0.1|L" for u in range(K)])
    bc = np.where(np.isnan(d["X"]), "", np.char.add("B", rng.integers(0, 10**6, d["X"].shape).astype(str)))
    inactive = (d["mu"] == 0) & (rng.random(K) < 0.4)
    np.savez_compressed(tmp / "DATA_JAAKS.npz", unit=units, X=d["X"], barcodes=bc.astype(str), p=d["p"],
                        n_o=d["n_o"], inactive=inactive)
    KA = 1200
    n = np.where(np.arange(KA) < 60, 2 + (np.arange(KA) % 2), np.where(np.arange(KA) < 70, 15, 1))
    mu = np.where(rng.random(KA) < 0.6, 0.0, rng.gamma(2.0, 0.03, KA))
    X = np.full((KA, 17), np.nan)
    for i in range(KA):
        X[i, :n[i]] = mu[i] + 0.04 * rng.standard_t(5.0, n[i])
    wells = np.where(np.isnan(X), np.nan, 49.0)
    bca = np.where(np.isnan(X), "", np.char.add("P", rng.integers(0, 10**6, X.shape).astype(str)))
    group = np.where(n >= 4, 3, np.where(n >= 2, 2, 1))
    np.savez_compressed(tmp / "DATA_AZ.npz", unit=np.array([f"M{i}|1|2" for i in range(KA)]), X=X, wells=wells,
                        barcodes=bca.astype(str), group=group, inactive=(mu == 0) & (rng.random(KA) < 0.5))
    P = 40
    NC = rng.normal(1000, 50, (P, 114)).round()
    wp = np.repeat(np.arange(P), 12)
    np.savez_compressed(tmp / "DATA_JAAKS_RAW.npz", plates=np.array([f"B{i}" for i in range(P)]), NC=NC,
                        well_plate=wp, well_intensity=rng.normal(1000, 50, wp.size).round(),
                        well_drug=np.array(["1"] * wp.size), well_loo_emax=np.full(wp.size, 0.95))
    here = Path(__file__).resolve().parent
    ok = True
    for script in ("gate1.py", "gate0.py"):
        t0 = time.time()
        proc = subprocess.run([sys.executable, "-I", str(here / script), "--synthetic", "--data-dir", str(tmp),
                               "--out-dir", str(tmp), "--replays", str(n_replays)], capture_output=True, text=True)
        good = proc.returncode == 0
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        ok &= report(f"T11 dry run of {script} on synthetic inputs", good,
                     f"{time.time() - t0:.0f} s; " + " / ".join(tail)[:600])
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT / "SYNTHETIC_TESTS.txt"))
    parser.add_argument("--gate1-replays", type=int, default=60)
    parser.add_argument("--dry-replays", type=int, default=4)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    cert = import_certification()
    tests = {"t1": t1_log_lr, "t2": t2_quadrature, "t3": t3_ebh, "t4": t4_allocate,
             "t5a": t5a_invariant_quadrature, "t5": t5_world_fit,
             "t6": lambda: t6_gate0_fdr(cert), "t7": lambda: t7_t8_gate1(args.gate1_replays), "t9": t9_design,
             "t11": lambda: t11_dry_run(args.dry_replays)}
    chosen = [t for t in tests if not args.only or t in args.only.split(",")]
    t0 = time.time()
    results = {t: tests[t]() for t in chosen}
    LINES.append(f"\n{sum(map(bool, results.values()))}/{len(results)} test groups passed in {time.time() - t0:.0f} s")
    write_text(args.out, "\n".join(LINES) + "\n")
    print(LINES[-1])
    return 0 if results and all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
