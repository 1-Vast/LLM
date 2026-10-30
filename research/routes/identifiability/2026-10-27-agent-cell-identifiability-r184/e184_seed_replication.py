"""E184: seed replication of the headline number.

R183 found that one stratum's significance flipped between seeds. Every confidence interval in this
programme is a bootstrap over splits, and a new seed draws a whole new set of splits. So the number the
whole document rests on should be checked under fresh seeds: do their point estimates fall inside the
interval reported at R163?

Pre-registered in PROTOCOL_E172.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r184"
SEEDS = (20261074, 20261075, 20261076)
R163_CI = [0.0947, 0.1409]
R163_POINT = 0.1183
REPS = 40
N_BOOT = 2000
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


def run_seed(d, g, A, B, Xid, Xboth, y, seed):
    rng = np.random.default_rng(seed)
    drugs = sorted(set(A) | set(B))
    gains = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr = y[tr]; yte = y[te]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, seed + rep)
        p_pa = fit_arm(Xboth[tr], ytr, Xboth[te], LAMBDAS, seed + rep)
        ri = spearmanr(p_id, yte).statistic
        rp = spearmanr(p_pa, yte).statistic
        gains.append((0.0 if not np.isfinite(rp) else float(rp))
                     - (0.0 if not np.isfinite(ri) else float(ri)))
    v = np.asarray(gains)
    rng2 = np.random.default_rng(seed + 7)
    bs = [float(np.mean(rng2.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(v)), "gain": float(v.mean()),
            "ci95": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))],
            "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(v)))}


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

    res = {"kind": "seed_replication_of_the_headline_number",
           "input_sha256": sha256(ORIG),
           "settings": {"seeds": list(SEEDS), "reps": REPS, "lambdas": list(LAMBDAS), "folds": FOLDS,
                        "n_boot": N_BOOT},
           "reference": {"source": "R163", "point": R163_POINT, "ci95": R163_CI},
           "audit": {"keys": int(len(g))}, "by_seed": {}, "files": {}}
    for s in SEEDS:
        res["by_seed"][str(s)] = run_seed(d, g, A, B, Xid, Xboth, y, s)
    pts = [v["gain"] for v in res["by_seed"].values()]
    inside = [R163_CI[0] <= p <= R163_CI[1] for p in pts]
    res["summary"] = {"mean_of_seed_points": float(np.mean(pts)),
                      "sd_between_seeds": float(np.std(pts, ddof=1)),
                      "r163_ci_width": R163_CI[1] - R163_CI[0],
                      "all_inside_r163_ci": bool(all(inside)),
                      "inside": inside}
    h432 = bool(all(inside))
    res["decisions"] = {"H432_headline_stable_across_seeds": h432,
                        "H433_ci_too_narrow": not h432}
    res["decisions"]["verdict"] = (
        "all_three_fresh_seeds_land_inside_the_reported_interval" if h432 else
        "at_least_one_fresh_seed_lands_outside_the_reported_interval_so_the_interval_is_optimistic")
    res["limits"] = ["Only ridge and one resource; forty splits per seed.",
                     "Seeds are fresh for this protocol but not for the programme as a whole.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r184/PROTOCOL_E172.md",
                "research/2026-10-27-agent-cell-identifiability-r184/e184_seed_replication.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E184_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    for s, v in res["by_seed"].items():
        print("  seed %s | n=%2d gain %+.4f [%+.4f,%+.4f] MDE %.4f | inside R163 CI: %s" % (
            s, v["n"], v["gain"], v["ci95"][0], v["ci95"][1], v["mde_80pct"],
            R163_CI[0] <= v["gain"] <= R163_CI[1]))
    print("  R163 reference: %+.4f [%+.4f,%+.4f]" % (R163_POINT, R163_CI[0], R163_CI[1]))
    print("  between-seed sd %.4f vs R163 CI width %.4f" % (
        res["summary"]["sd_between_seeds"], res["summary"]["r163_ci_width"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
