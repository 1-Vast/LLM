"""E169: how many measurements would a prospective test need?

The programme has used minimum detectable effects to say "this experiment cannot resolve the effect".
This inverts that: subsample the evaluation pool to k keys, which stands in for "a future study that
measured k new cell-by-pair combinations", and measure how often the gain's interval excludes zero.

Pre-registered in PROTOCOL_E157.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r169"
REPS = 20
SUBSAMPLES = 10
N_BOOT = 300
SEED = 20261069
KS = (50, 100, 200, 400, 800, 1600)
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
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
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
        if len(tr) < 15000 or len(te) < max(KS):
            continue
        ytr = y[tr]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, SEED + rep)
        yte = y[te]
        for k in KS:
            for s in range(SUBSAMPLES):
                idx = rng.choice(len(te), size=k, replace=False)
                yt = yte[idx]
                if np.std(yt) == 0:
                    continue
                ri = spearmanr(p_id[idx], yt).statistic
                rp = spearmanr(p_pa[idx], yt).statistic
                gain = (0.0 if not np.isfinite(rp) else float(rp)) - (0.0 if not np.isfinite(ri) else float(ri))
                rng2 = np.random.default_rng(SEED + 7000 + rep * 97 + k + s)
                vals = []
                for _ in range(N_BOOT):
                    bidx = rng2.integers(0, k, size=k)
                    yb = yt[bidx]
                    if np.std(yb) == 0:
                        vals.append(0.0); continue
                    rb_i = spearmanr(p_id[idx][bidx], yb).statistic
                    rb_p = spearmanr(p_pa[idx][bidx], yb).statistic
                    vals.append((0.0 if not np.isfinite(rb_p) else float(rb_p))
                                - (0.0 if not np.isfinite(rb_i) else float(rb_i)))
                rows.append({"rep": rep, "k": k, "sub": s, "gain": gain,
                             "ci_lo": float(np.quantile(vals, 0.025)),
                             "ci_hi": float(np.quantile(vals, 0.975)),
                             "sig": bool(np.quantile(vals, 0.025) > 0)})

    r = pd.DataFrame(rows)
    res = {"kind": "prospective_power_curve_over_measurement_count",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "subsamples": SUBSAMPLES, "n_boot": N_BOOT, "seed": SEED,
                        "ks": list(KS), "lambdas": list(LAMBDAS), "folds": FOLDS},
           "audit": {"keys": int(len(g)), "cells_drawn": int(len(r))}, "by_k": {}, "files": {}}
    for k in KS:
        sub = r[r.k == k]
        if len(sub) < 10:
            continue
        res["by_k"][str(k)] = {"n": int(len(sub)),
                                "power": float(sub["sig"].mean()),
                                "mean_gain": float(sub["gain"].mean()),
                                "sd_gain": float(sub["gain"].std(ddof=1)),
                                "median_ci_width": float((sub["ci_hi"] - sub["ci_lo"]).median())}
    ks_sorted = sorted(int(k) for k in res["by_k"])
    reached = [k for k in ks_sorted if res["by_k"][str(k)]["power"] >= 0.80]
    res["decisions"] = {"power_by_k": {k: res["by_k"][str(k)]["power"] for k in ks_sorted},
                        "smallest_k_with_80pct_power": reached[0] if reached else None,
                        "H402_200_or_fewer": bool(reached and reached[0] <= 200),
                        "H403_needs_400_or_more": bool(reached and reached[0] >= 400)}
    res["decisions"]["verdict"] = (
        "a_prospective_test_needs_about_%d_measured_combinations_for_80pct_power" % reached[0] if reached
        else "no_subsampled_size_reached_80pct_power_within_the_range_tested")
    res["limits"] = ["Subsampling draws from the existing evaluation pool, whose composition may differ from newly measured combinations; this is the main external-validity limit.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r169/PROTOCOL_E157.md",
                "research/2026-10-27-agent-cell-identifiability-r169/e169_power.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E169_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E169_rows.csv", index=False)

    print("cells drawn: %d" % len(r))
    print("  %6s %8s %10s %9s %14s" % ("k", "power", "mean gain", "sd", "median CI width"))
    for k in ks_sorted:
        e = res["by_k"][str(k)]
        print("  %6d %8.2f %+10.4f %9.4f %14.4f" % (
            k, e["power"], e["mean_gain"], e["sd_gain"], e["median_ci_width"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
