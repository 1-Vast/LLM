"""E177: at a fixed measurement budget, is it better to cover more drug pairs or more cells per pair?

R169 costed a prospective test at about 1,600 measurements. R174 showed the prediction is constant across
the cells of a pair. Together those raise a design question nobody has asked here: with a fixed budget,
spend it on more pairs or on more cells per pair? This measures detection power under three allocations of
the same total.

Pre-registered in PROTOCOL_E165.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r177"
REPS = 20
SUBSAMPLES = 10
N_BOOT = 300
SEED = 20261071
BUDGET = 1000
CONFIGS = (("wide", 28, 36), ("mid", 50, 20), ("narrow", 68, 15))
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def solve_path(G, b, lams):
    out = {}
    d = np.diag(G).copy()
    for lam in lams:
        out[lam] = np.linalg.solve(G + np.diag(lam + 1e-9 * (d + 1.0)), b)
    return out


def fit_arm(Xtr, ytr, Xte, lams, seed, folds=FOLDS):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    Zte = (Xte - mu) / sd
    rng = np.random.default_rng(seed)
    chunks = np.array_split(rng.permutation(len(Z)), folds)
    score = {lam: [] for lam in lams}
    for f in range(folds):
        va = chunks[f]
        tr = np.setdiff1d(np.arange(len(Z)), va)
        ym = ytr[tr].mean()
        w = solve_path(Z[tr].T @ Z[tr], Z[tr].T @ (ytr[tr] - ym), lams)
        yv = ytr[va]
        for lam, ww in w.items():
            p = ym + Z[va] @ ww
            s = spearmanr(p, yv).statistic if np.std(p) > 0 else -2.0
            score[lam].append(0.0 if not np.isfinite(s) else float(s))
    best = max(lams, key=lambda lam: float(np.mean(score[lam])))
    ym = ytr.mean()
    ww = solve_path(Z.T @ Z, Z.T @ (ytr - ym), [best])[best]
    return ym + Zte @ ww


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"),
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)
    g["pair_code"] = g.groupby(["a", "b"]).ngroup().to_numpy()

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); pair = g["pair_code"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(tr) < 15000 or len(te) < BUDGET:
            continue
        ytr = y[tr]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
        # pool of evaluation pairs, each with its cell indices
        by_pair = {}
        for pos, idx in enumerate(te):
            by_pair.setdefault(pair[idx], []).append(pos)
        usable = {k: v for k, v in by_pair.items() if len(v) >= 15}
        if len(usable) < 68:
            pairs_sorted = sorted(usable, key=lambda k: -len(usable[k]))
        else:
            pairs_sorted = sorted(usable)
        for name, p_n, c_n in CONFIGS:
            if len(usable) < p_n:
                continue
            for s in range(SUBSAMPLES):
                r2 = np.random.default_rng(SEED + 3000 + rep * 31 + s + p_n)
                chosen = r2.choice(len(pairs_sorted), size=p_n, replace=False)
                picked = []
                for ci in chosen:
                    key = pairs_sorted[ci]
                    cells = usable[key]
                    take = min(c_n, len(cells))
                    picked.extend(r2.choice(cells, size=take, replace=False).tolist())
                idx = np.array(picked)
                yt = y[te][idx]
                if np.std(yt) == 0:
                    continue
                ri = spearmanr(p_id[idx], yt).statistic
                rp = spearmanr(p_pa[idx], yt).statistic
                gain = (0.0 if not np.isfinite(rp) else float(rp)) - (0.0 if not np.isfinite(ri) else float(ri))
                r3 = np.random.default_rng(SEED + 9000 + rep * 31 + s)
                vals = []
                for _ in range(N_BOOT):
                    bi = r3.integers(0, len(idx), size=len(idx))
                    yb = yt[bi]
                    if np.std(yb) == 0:
                        vals.append(0.0); continue
                    a1 = spearmanr(p_id[idx][bi], yb).statistic
                    a2 = spearmanr(p_pa[idx][bi], yb).statistic
                    vals.append((0.0 if not np.isfinite(a2) else float(a2))
                                - (0.0 if not np.isfinite(a1) else float(a1)))
                rows.append({"rep": rep, "config": name, "pairs": p_n, "cells": c_n,
                             "n_keys": int(len(idx)), "gain": gain,
                             "ci_lo": float(np.quantile(vals, 0.025)),
                             "ci_hi": float(np.quantile(vals, 0.975)),
                             "sig": bool(np.quantile(vals, 0.025) > 0)})

    r = pd.DataFrame(rows)
    res = {"kind": "fixed_budget_allocation_more_pairs_versus_more_cells",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "subsamples": SUBSAMPLES, "n_boot": N_BOOT, "seed": SEED,
                        "budget": BUDGET, "configs": [list(c) for c in CONFIGS]},
           "audit": {"keys": int(len(g)), "draws": int(len(r))}, "by_config": {}, "files": {}}
    for name, p_n, c_n in CONFIGS:
        sub = r[r.config == name]
        if len(sub) < 10:
            continue
        res["by_config"][name] = {"pairs": p_n, "cells": c_n, "n": int(len(sub)),
                                   "mean_keys": float(sub["n_keys"].mean()),
                                   "power": float(sub["sig"].mean()),
                                   "mean_gain": float(sub["gain"].mean()),
                                   "median_ci_width": float((sub["ci_hi"] - sub["ci_lo"]).median())}
    p_by = {k: v["power"] for k, v in res["by_config"].items()}
    h418 = bool(len(p_by) == 3 and p_by.get("narrow", 0) > p_by.get("mid", 0) > p_by.get("wide", 0))
    h419 = bool(len(p_by) == 3 and p_by.get("wide", 0) > p_by.get("mid", 0) > p_by.get("narrow", 0))
    res["decisions"] = {"power_by_config": p_by, "H418_more_pairs_wins": h418, "H419_more_cells_wins": h419}
    res["decisions"]["verdict"] = (
        "at_a_fixed_budget_spreading_across_more_pairs_detects_better_than_densifying_cells" if h418 else
        "at_a_fixed_budget_densifying_cells_detects_better_than_spreading_pairs" if h419 else
        "the_allocation_does_not_change_power_monotonically_over_this_range")
    res["limits"] = ["Cells per pair are capped near 36 by the evaluation pool itself, so the wide configuration cannot go further.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r177/PROTOCOL_E165.md",
                "research/2026-10-27-agent-cell-identifiability-r177/e177_allocation.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E177_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E177_rows.csv", index=False)

    print("draws: %d" % len(r))
    for name, e in res["by_config"].items():
        print("  %-7s %2d pairs x %2d cells (%4.0f keys) | power %.2f | gain %+.4f | CI width %.4f" % (
            name, e["pairs"], e["cells"], e["mean_keys"], e["power"], e["mean_gain"], e["median_ci_width"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
