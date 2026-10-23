"""Gate 1: development noise-model and plate-rank diagnostics, not mathematical certification.

Writes WORLD_FIT.json/.npz and GATE1_RESULTS.json.
"""
import argparse
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

from common import (ALPHA, BOOT_SEED, DATA, GATE1_BUDGETS, MIN_INACTIVE_UNITS, N_BOOT, N_REPLAYS, OUT,  # noqa: E402
                    replay_rng, require_freeze, write_json)
from evalues import composite_null_check, ebh, log_lr  # noqa: E402
from replay import Bets, Pool, gate1_run, read_orders, reorder  # noqa: E402
from worldfit import fit_primary, fit_t_invariant, npmle, prior_summary, read_loglik  # noqa: E402

BETTORS = ("pf", "fixed3", "portfolio")
REQUIRED_POOLS = ("J-P1", "J-P2", "AZ-P1", "AZ-P2")
FWER_LIMIT = ALPHA + 2 * math.sqrt(ALPHA * (1 - ALPHA) / N_REPLAYS)
MEAN_E_POINT, MEAN_E_UPPER = 1.10, 1.25
CAP = 20.0
CAP_SE_MULTIPLE = 3.0
CALIBRATION_MULTIPLES = (0.5, 1.0, 2.0, 3.0, 4.0)


# ---------------------------------------------------------------- data and world fit

def load(data_dir):
    J = dict(np.load(Path(data_dir) / "DATA_JAAKS.npz", allow_pickle=False))
    A = dict(np.load(Path(data_dir) / "DATA_AZ.npz", allow_pickle=False))
    return J, A


def unit_wells(wells):
    """One wells-per-read figure per unit: the most common matrix size among its reads."""
    out = np.empty(wells.shape[0])
    for i, row in enumerate(wells):
        vals, counts = np.unique(row[np.isfinite(row)], return_counts=True)
        out[i] = vals[np.argmax(counts)]
    return out


def world_fit(J, A):
    fit = {}
    noise = fit_t_invariant(J["X"])
    LL = read_loglik(J["X"], noise["sigma"], noise["nu"])
    prior = npmle(LL)
    primary = fit_primary(J["p"], J["n_o"], LL, prior["weights"], noise["nu"])
    fit["jaaks"] = {"noise": noise, "prior": {k: v for k, v in prior.items() if k != "weights"},
                    "prior_summary": prior_summary(prior["weights"]), "primary": primary, "units": int(len(J["p"]))}
    weights = {"jaaks": prior["weights"]}
    rep = A["group"] >= 2
    noise_a = fit_t_invariant(A["X"][rep])
    LLa = read_loglik(A["X"], noise_a["sigma"], noise_a["nu"])
    prior_a = npmle(LLa)
    fit["az"] = {"noise": noise_a,
                 "noise_g2_only": fit_t_invariant(A["X"][A["group"] == 2]),
                 "noise_g3_only": fit_t_invariant(A["X"][A["group"] == 3]),
                 "prior": {k: v for k, v in prior_a.items() if k != "weights"},
                 "prior_summary": prior_summary(prior_a["weights"]), "units": int(len(A["group"]))}
    weights["az"] = prior_a["weights"]
    for asset in ("jaaks", "az"):
        check = composite_null_check(fit[asset]["noise"]["nu"])
        fit[asset]["composite_null_check"] = {k: v for k, v in check.items()
                                              if k in ("nu", "all_valid", "max_over_grid")}
        fit[asset]["composite_null_check"]["n_valid_bets"] = int(check["valid"].sum())
        fit[asset]["composite_null_check"]["max_abs_deviation_at_mu0"] = float(
            np.max(np.abs(check["expectation_at_mu0"] - 1.0)))
        weights[f"{asset}_valid"] = check["valid"]
    return fit, weights


def bets_for(fit, weights, asset):
    return Bets(fit[asset]["noise"]["sigma"], fit[asset]["noise"]["nu"], weights[f"{asset}_valid"])


# ---------------------------------------------------------------- pools

def pseudo_diffs(X):
    """Disjoint consecutive pairs in reveal order: z_k = (x_(2k-1) - x_(2k)) / sqrt(2)."""
    n = (~np.isnan(X)).sum(axis=1)
    k = n // 2
    Z = np.full((X.shape[0], max(1, int(k.max()))), np.nan)
    for j in range(Z.shape[1]):
        ok = k > j
        Z[ok, j] = (X[ok, 2 * j] - X[ok, 2 * j + 1]) / math.sqrt(2.0)
    return Z


def concat_pools(real, pseudo):
    width = max(real.X.shape[1], pseudo.X.shape[1])

    def pad(X):
        return np.hstack([X, np.full((X.shape[0], width - X.shape[1]), np.nan)])

    pool = Pool(np.vstack([pad(real.X), pad(pseudo.X)]), np.concatenate([real.p, pseudo.p]),
                np.concatenate([real.wells, pseudo.wells]))
    mask = np.zeros(pool.K, dtype=bool)
    mask[real.K:] = True
    return pool, mask


class Builders:
    """Per-replay real and pseudo-null pools of both assets."""

    def __init__(self, J, A, n_replays):
        self.J, self.A = J, A
        self.j_orders = read_orders(J["unit"], J["barcodes"], n_replays)
        self.rep = np.nonzero(A["group"] >= 2)[0]
        self.g2 = np.nonzero(A["group"][self.rep] == 2)[0]
        self.a_orders = read_orders(A["unit"], A["barcodes"], n_replays)
        self.a_wells_all = unit_wells(A["wells"])
        self.a_mean_all = np.nanmean(A["X"], axis=1)
        self.a_wells = self.a_wells_all[self.rep]
        self.a_mean = self.a_mean_all[self.rep]
        self.inactive = np.asarray(J["inactive"], dtype=bool)
        self.az_inactive = np.asarray(A["inactive"], dtype=bool)

    def jaaks_real(self, r):
        return Pool(reorder(self.J["X"], self.j_orders[r]), self.J["p"], 7.0)

    def az_all(self, r):
        return reorder(self.A["X"], self.a_orders[r])

    def az_rep(self, r):
        return self.az_all(r)[self.rep]

    def az_matched_real(self, r):
        X = self.az_rep(r)[self.g2]
        return Pool(X[:, 1:], X[:, 0], self.a_wells[self.g2])

    def null(self, name, r):
        if name == "J-P1":
            return Pool(pseudo_diffs(self.jaaks_real(r).X), self.J["p"], 14.0)
        if name == "J-P2":
            X = self.jaaks_real(r).X[self.inactive]
            return Pool(-X, self.J["p"][self.inactive], 7.0)
        if name == "AZ-P1":
            return Pool(pseudo_diffs(self.az_rep(r)), self.a_mean, 2.0 * self.a_wells)
        if name == "AZ-P2":
            X = self.az_all(r)[self.az_inactive]
            return Pool(-X, self.a_mean_all[self.az_inactive], self.a_wells_all[self.az_inactive])
        raise ValueError(name)

    def mixed(self, name, r):
        real = self.az_matched_real(r) if name.startswith("AZ") else self.jaaks_real(r)
        return concat_pools(real, self.null(name, r))


# ---------------------------------------------------------------- Gate 1a

def upper_mean_ratio(sum_e, count, rng, n_boot=N_BOOT):
    """Pooled mean e (sum over units / reads over units) and its 95% bootstrap upper bound, resampling units."""
    point, upper, _ = pooled_mean_boot(sum_e, count, rng, n_boot)
    return point, upper


def pooled_mean_boot(sum_e, count, rng, n_boot=N_BOOT, chunk=250):
    """Pooled mean, 97.5% bootstrap quantile and bootstrap SE, resampling units (in chunks to bound memory)."""
    keep = count > 0
    s, c = sum_e[keep], count[keep]
    point = float(s.sum() / c.sum())
    boots = []
    for lo in range(0, n_boot, chunk):
        idx = rng.integers(0, s.size, size=(min(chunk, n_boot - lo), s.size))
        boots.append(s[idx].sum(axis=1) / c[idx].sum(axis=1))
    boots = np.concatenate(boots)
    return point, float(np.quantile(boots, 0.975)), float(boots.std(ddof=1))


def read_calibration(X, bets, multiples=CALIBRATION_MULTIPLES):
    """Mean of LR(x; m) over pseudo-null reads for fixed bets, with its standard error (reads are independent)."""
    x = X[~np.isnan(X)]
    out = {}
    for k in multiples:
        m = float(bets.clip(k * bets.sigma))
        v = np.exp(log_lr(x, m, bets.sigma, bets.nu))
        out[str(k)] = {"kappa": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(v.size))}
    return out


def simulate_like(template, bets, rng, kind):
    """Pseudo-null reads drawn from the fitted model with the template's structure: single reads, or pair
    differences (t1 - t2) / sqrt(2) when the template's pseudo-reads are pair differences."""
    shape = template.X.shape
    X = bets.sigma * rng.standard_t(bets.nu, size=shape)
    if kind == "diff":
        X = (X - bets.sigma * rng.standard_t(bets.nu, size=shape)) / math.sqrt(2.0)
    X[np.isnan(template.X)] = np.nan
    return Pool(X, template.p, template.wells)


def gate1a_pool(name, null_of, mixed_of, bets, n_replays, round1, sim_kind, budgets=GATE1_BUDGETS, bettors=BETTORS,
                trace=None):
    """All cells of one pseudo-null pool. null_of(r) -> Pool; mixed_of(r) -> (Pool, pseudo mask).

    Criterion (a) compares the capped (at CAP) pooled mean stopped e-value of the real pseudo-null pool with the same
    statistic on pools simulated from the fitted model with identical structure and allocation."""
    first = null_of(0)
    K0 = first.K
    cells = {}
    acc, sim = {}, {}
    for b in bettors:
        for c in budgets:
            acc[(b, c)] = {"sum": np.zeros((2, K0)), "cap": np.zeros((2, K0)), "cnt": np.zeros((2, K0)),
                           "big": np.zeros(2), "any": np.zeros((2, n_replays)), "fdp": np.zeros((2, n_replays)),
                           "kp_over_k": 0.0}
            sim[(b, c)] = {"cap": np.zeros((2, n_replays)), "mean": np.zeros((2, n_replays)),
                           "big": np.zeros((2, n_replays))}
    reads_seen = first.X[~np.isnan(first.X)]
    for r in range(n_replays):
        null = first if r == 0 else null_of(r)
        mixed, mask = mixed_of(r)
        simulated = simulate_like(first, bets, replay_rng(name, "simulated", r), sim_kind)
        cache_n, cache_m, cache_s = {}, {}, {}
        for b in bettors:
            for c in budgets:
                a = acc[(b, c)]
                out = gate1_run(null, bets, b, min(c * null.K, int(null.R.sum())),
                                replay_rng(name, "null", b, c, r), round1=round1, round2="current_e", cache=cache_n)
                if trace is not None and r == 0 and c == 1:
                    for key in ("n1", "le1", "n", "le"):
                        trace[f"{name}|null|{b}|{key}"] = out[key]
                    trace[f"{name}|null|X"], trace[f"{name}|null|p"] = null.X, null.p
                for s, (n, le, k) in enumerate(((out["n1"], out["le1"], out["k1"]), (out["n"], out["le"], out["k"]))):
                    read = n > 0
                    e = np.exp(np.minimum(le, 700.0))
                    a["sum"][s] += np.where(read, e, 0.0)
                    a["cap"][s] += np.where(read, np.minimum(e, CAP), 0.0)
                    a["cnt"][s] += read
                    a["big"][s] += float((read & (le >= math.log(CAP))).sum())
                    a["any"][s, r] = k >= 1
                outs = gate1_run(simulated, bets, b, min(c * simulated.K, int(simulated.R.sum())),
                                 replay_rng(name, "sim-run", b, c, r), round1=round1, round2="current_e", cache=cache_s)
                for s, (n, le) in enumerate(((outs["n1"], outs["le1"]), (outs["n"], outs["le"]))):
                    read = n > 0
                    e = np.exp(np.minimum(le[read], 700.0))
                    sim[(b, c)]["cap"][s, r] = np.minimum(e, CAP).mean()
                    sim[(b, c)]["mean"][s, r] = e.mean()
                    sim[(b, c)]["big"][s, r] = (le[read] >= math.log(CAP)).mean()
                outm = gate1_run(mixed, bets, b, min(c * mixed.K, int(mixed.R.sum())),
                                 replay_rng(name, "mixed", b, c, r), round1="p", round2="a1", cache=cache_m)
                if trace is not None and r == 0 and c == 1:
                    for key in ("n1", "le1", "n", "le"):
                        trace[f"{name}|mixed|{b}|{key}"] = outm[key]
                    trace[f"{name}|mixed|X"], trace[f"{name}|mixed|mask"] = mixed.X, mask
                for s, le in enumerate((outm["le1"], outm["le"])):
                    rej, k = ebh(le)
                    a["fdp"][s, r] = (rej & mask).sum() / max(k, 1)
                a["kp_over_k"] = mask.sum() / mask.size
    boot = np.random.default_rng(BOOT_SEED)
    for (b, c), a in acc.items():
        for s in (0, 1):
            point, upper = upper_mean_ratio(a["sum"][s], a["cnt"][s], boot)
            cap_point, _, cap_se = pooled_mean_boot(a["cap"][s], a["cnt"][s], boot)
            sc = sim[(b, c)]["cap"][s]
            sim_cap, sim_se = float(sc.mean()), float(sc.std(ddof=1) / math.sqrt(n_replays))
            cap_limit = sim_cap + CAP_SE_MULTIPLE * math.sqrt(cap_se ** 2 + sim_se ** 2)
            fwer = float(a["any"][s].mean())
            fdp = a["fdp"][s]
            limit = ALPHA * a["kp_over_k"] + 2 * fdp.std(ddof=1) / math.sqrt(n_replays)
            crit = {"a_capped_mean_e": cap_point, "a_capped_se": cap_se, "a_simulated_capped_mean_e": sim_cap,
                    "a_simulated_se": sim_se, "a_limit": cap_limit, "a_pass": cap_point <= cap_limit,
                    "b_fwer": fwer, "b_limit": FWER_LIMIT, "b_pass": fwer <= FWER_LIMIT,
                    "c_mean_pseudo_fdp": float(fdp.mean()), "c_limit": float(limit),
                    "c_pass": float(fdp.mean()) <= limit,
                    "diag_mean_e": point, "diag_mean_e_upper": upper,
                    "diag_simulated_mean_e": float(sim[(b, c)]["mean"][s].mean()),
                    "diag_p_e_ge_cap": float(a["big"][s] / max(a["cnt"][s].sum(), 1)),
                    "diag_simulated_p_e_ge_cap": float(sim[(b, c)]["big"][s].mean())}
            crit["pass"] = crit["a_pass"] and crit["b_pass"] and crit["c_pass"]
            cells[f"{name}|{b}|c{c}|stop{s + 1}"] = crit
    sim_reads = simulate_like(first, bets, replay_rng(name, "simulated", 0), sim_kind).X
    diag = {"units": int(K0), "pseudo_reads_replay0": int(reads_seen.size), "simulation_kind": sim_kind,
            "mean_pseudo_read_over_sigma": float(reads_seen.mean() / bets.sigma),
            "median_pseudo_read_over_sigma": float(np.median(reads_seen) / bets.sigma),
            "se_mean_over_sigma": float(reads_seen.std(ddof=1) / math.sqrt(reads_seen.size) / bets.sigma),
            "ks_vs_model_simulated": float(stats.ks_2samp(reads_seen, sim_reads[~np.isnan(sim_reads)]).statistic),
            "sd_over_model_sd": float(reads_seen.std(ddof=1) / (bets.sigma * math.sqrt(bets.nu / (bets.nu - 2)))),
            "read_calibration": read_calibration(first.X, bets),
            "read_calibration_model_simulated": read_calibration(sim_reads, bets)}
    return cells, diag


# ---------------------------------------------------------------- Gate 1b

def design_evalues(x, refs, rng):
    """Bottom-5% rank bet of x against reference wells with random tie-breaks; expectation 1 under exchangeability."""
    refs = np.sort(refs[np.isfinite(refs)])
    k = refs.size
    less = np.searchsorted(refs, x, side="left")
    equal = np.searchsorted(refs, x, side="right") - less
    rank = 1 + less + np.floor(rng.random(np.size(x)) * (equal + 1)).astype(int)
    bottom = math.ceil(0.05 * (k + 1))
    u = (rank - rng.random(np.size(x))) / (k + 1)
    return np.where(rank <= bottom, (k + 1) / bottom, 0.0), u


def gate1b(raw, n_boot=N_BOOT):
    NC = raw["NC"]
    plates = NC.shape[0]
    out = {}
    per_plate = {"N": [[] for _ in range(plates)], "L": [[] for _ in range(plates)]}
    us = {"N": [], "L": []}
    for i in range(plates):
        refs = NC[i][np.isfinite(NC[i])]
        rng = replay_rng("jaaks", "gate1b", i)
        pick = rng.choice(refs.size, size=min(10, refs.size), replace=False)
        for j in pick:
            e, u = design_evalues(np.array([refs[j]]), np.delete(refs, j), rng)
            per_plate["N"][i].append(float(e[0]))
            us["N"].append(float(u[0]))
        sel = (raw["well_plate"] == i) & (raw["well_loo_emax"] >= 0.9)
        if sel.any():
            e, u = design_evalues(raw["well_intensity"][sel], refs, rng)
            per_plate["L"][i].extend(e.tolist())
            us["L"].extend(u.tolist())
    boot = np.random.default_rng(BOOT_SEED)
    for kind in ("N", "L"):
        sums = np.array([sum(v) for v in per_plate[kind]])
        cnts = np.array([len(v) for v in per_plate[kind]], dtype=float)
        point, upper = upper_mean_ratio(sums, cnts, boot, n_boot)
        u = np.array(us[kind])
        out[kind] = {"wells": int(cnts.sum()), "plates": int((cnts > 0).sum()), "mean_e": point, "upper": upper,
                     "pass": point <= MEAN_E_POINT and upper <= MEAN_E_UPPER,
                     "ks_uniform": float(stats.kstest(u, "uniform").statistic) if u.size else None,
                     "bottom_5pct_frequency": float((u <= 0.05).mean()) if u.size else None,
                     "top_5pct_frequency": float((u > 0.95).mean()) if u.size else None}
    return out


# ---------------------------------------------------------------- main

def gate1a_decision(cells, not_testable, valid_bets):
    """Fail closed on skipped/incomplete diagnostics; empirical passes never establish a guarantee."""
    expected = {f"{pool}|{bettor}|c{budget}|stop{stop}"
                for pool in REQUIRED_POOLS for bettor in BETTORS for budget in GATE1_BUDGETS for stop in (1, 2)}
    missing = sorted(expected - cells.keys())
    failing = sorted(k for k, v in cells.items() if not v["pass"])
    complete = not missing and not not_testable
    label = ("GATE1_DIAGNOSTIC_INCOMPLETE" if not complete else
             "GATE1_DIAGNOSTIC_PASS" if not failing and valid_bets else "GATE1_DIAGNOSTIC_FAIL")
    return {"gate1a_label": label, "gate1a_missing_cells": missing, "gate1a_failing_cells": failing,
            "gate1a_diagnostic_complete": complete, "mathematical_certification": "NOT_ESTABLISHED"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(DATA))
    parser.add_argument("--out-dir", default=str(OUT))
    parser.add_argument("--replays", type=int, default=N_REPLAYS)
    parser.add_argument("--synthetic", action="store_true", help="dry run on synthetic inputs; skips the freeze check")
    args = parser.parse_args()
    if not args.synthetic:
        require_freeze()
    data_dir, out_dir = Path(args.data_dir), Path(args.out_dir)
    t0 = time.time()
    J, A = load(data_dir)
    fit, weights = world_fit(J, A)
    np.savez_compressed(data_dir / "WORLD_FIT.npz", **weights)
    write_json(out_dir / "WORLD_FIT.json", fit)
    print("world fit", round(time.time() - t0, 1), "s", flush=True)
    builders = Builders(J, A, args.replays)
    jb, ab = bets_for(fit, weights, "jaaks"), bets_for(fit, weights, "az")
    results = {"world_fit_valid_bets": {a: fit[a]["composite_null_check"] for a in ("jaaks", "az")}, "cells": {},
               "diagnostics": {}, "not_testable": {}}
    pools = [("J-P1", jb, "random"), ("J-P2", jb, "p"), ("AZ-P1", ab, "random"), ("AZ-P2", ab, "random")]
    trace = {}
    inactive_counts = {"J-P2": int(builders.inactive.sum()), "AZ-P2": int(builders.az_inactive.sum())}
    results["inactive_units"] = inactive_counts
    for name, bets, round1 in pools:
        if name in inactive_counts and inactive_counts[name] < MIN_INACTIVE_UNITS:
            results["not_testable"][name] = f"{inactive_counts[name]} inactive units < {MIN_INACTIVE_UNITS}"
            continue
        cells, diag = gate1a_pool(name, lambda r, n=name: builders.null(n, r), lambda r, n=name: builders.mixed(n, r),
                                  bets, args.replays, round1, "diff" if name.endswith("P1") else "single",
                                  trace=trace)
        results["cells"].update(cells)
        results["diagnostics"][name] = diag
        print(name, "done", round(time.time() - t0, 1), "s", flush=True)
    for name, bets in (("J-P2", jb), ("AZ-P2", ab)):
        if name in results["diagnostics"]:
            results["diagnostics"][f"{name}_right_tail"] = right_tail(builders, bets, args.replays, name)
    np.savez_compressed(data_dir / "GATE1_TRACE.npz", **trace)
    raw_path = data_dir / "DATA_JAAKS_RAW.npz"
    if raw_path.exists():
        results["gate1b"] = gate1b(dict(np.load(raw_path, allow_pickle=False)))
    valid = all(fit[a]["composite_null_check"]["all_valid"] for a in ("jaaks", "az"))
    results.update(gate1a_decision(results["cells"], results["not_testable"], valid))
    if "gate1b" in results:
        results["gate1b_label"] = ("PLATE_RANK_DIAGNOSTIC_PASS" if results["gate1b"]["L"]["pass"]
                                   else "PLATE_RANK_DIAGNOSTIC_FAIL")
    results["replays"] = args.replays
    results["seconds"] = round(time.time() - t0, 1)
    write_json(out_dir / "GATE1_RESULTS.json", results)
    print(results["gate1a_label"], results.get("gate1b_label"), "failing:", results["gate1a_failing_cells"])


def right_tail(builders, bets, n_replays, name):
    """Descriptive: e-BH discoveries among inactive units on their real (not mirrored) reads, PF, c = 1."""
    ks = []
    for r in range(n_replays):
        pool = builders.null(name, r)
        pool = Pool(-pool.X, pool.p, pool.wells)
        out = gate1_run(pool, bets, "pf", min(pool.K, int(pool.R.sum())), replay_rng(f"{name}-right", r),
                        round1="p" if name == "J-P2" else "random", round2="current_e")
        ks.append(out["k"])
    return {"mean_discoveries": float(np.mean(ks)), "replays_with_any": float(np.mean(np.array(ks) > 0))}


if __name__ == "__main__":
    main()
