"""E174 (v2): can this model rank CELL LINES, or only drug combinations?

The first attempt produced a within-pair variance of 0.309 for the identity arm, which is impossible:
that arm contains no cell feature at all, and a direct one-rep check showed its prediction is constant
across the both-unseen evaluation set (sd 8.7e-21). The aggregation was therefore wrong, so this version
measures the quantity with plain numpy grouping and reports the raw within-pair spread instead of a
pandas groupby-transform ratio.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r174"
REPS = 20
SEED = 20261070
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


def within_pair_spread(pred, groups):
    """Plain numpy grouping: how much does the prediction vary ACROSS CELLS of one drug pair?"""
    order = np.argsort(groups, kind="stable")
    g_sorted = groups[order]; p_sorted = pred[order]
    bounds = np.flatnonzero(np.diff(g_sorted)) + 1
    starts = np.concatenate([[0], bounds]); ends = np.concatenate([bounds, [len(g_sorted)]])
    spreads, sizes = [], []
    for s, e in zip(starts, ends):
        seg = p_sorted[s:e]
        if len(seg) < 2:
            continue
        spreads.append(float(np.max(seg) - np.min(seg)))
        sizes.append(int(len(seg)))
    if not spreads:
        return {"n_pairs": 0, "max_spread": None, "mean_spread": None, "frac_pairs_varying": None}
    spreads = np.asarray(spreads)
    return {"n_pairs": int(len(spreads)), "max_spread": float(spreads.max()),
            "mean_spread": float(spreads.mean()),
            "frac_pairs_varying": float(np.mean(spreads > 1e-12)),
            "mean_cells_per_pair": float(np.mean(sizes))}


def variance_split(pred, groups):
    grand = float(np.mean(pred))
    order = np.argsort(groups, kind="stable")
    g_sorted = groups[order]; p_sorted = pred[order]
    bounds = np.flatnonzero(np.diff(g_sorted)) + 1
    starts = np.concatenate([[0], bounds]); ends = np.concatenate([bounds, [len(g_sorted)]])
    between = 0.0; within = 0.0
    for s, e in zip(starts, ends):
        seg = p_sorted[s:e]
        m = float(np.mean(seg))
        between += len(seg) * (m - grand) ** 2
        within += float(np.sum((seg - m) ** 2))
    total = between + within
    return {"between": between, "within": within,
            "between_frac": (between / total) if total > 0 else None,
            "within_frac": (within / total) if total > 0 else None}


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
    g["pair_code"] = g.groupby(["a", "b"]).ngroup().to_numpy()
    pair = g["pair_code"].to_numpy()

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
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr = y[tr]
        for nm, XX in (("identity", Xid), ("identity_pathway", Xboth)):
            p = fit_arm(XX[tr], ytr, XX[te], LAMBDAS, SEED + rep)
            sp = within_pair_spread(p, pair[te])
            vs = variance_split(p, pair[te])
            rho = spearmanr(p, y[te]).statistic
            rows.append({"rep": rep, "arm": nm, "n_eval": int(len(te)),
                         "n_pairs": sp["n_pairs"], "max_spread": sp["max_spread"],
                         "mean_spread": sp["mean_spread"],
                         "frac_pairs_varying": sp["frac_pairs_varying"],
                         "between_frac": vs["between_frac"], "within_frac": vs["within_frac"],
                         "rho": 0.0 if not np.isfinite(rho) else float(rho)})

    r = pd.DataFrame(rows)
    res = {"kind": "can_the_model_rank_cells_or_only_combinations",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "lambdas": list(LAMBDAS), "folds": FOLDS},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_arm": {}, "files": {}}
    for nm in ("identity", "identity_pathway"):
        sub = r[r.arm == nm]
        if len(sub) < 5:
            continue
        res["by_arm"][nm] = {
            "n": int(len(sub)), "mean_eval": float(sub["n_eval"].mean()),
            "mean_pairs": float(sub["n_pairs"].mean()),
            "max_spread_over_reps": float(sub["max_spread"].max()),
            "mean_spread": float(sub["mean_spread"].mean()),
            "frac_pairs_varying": float(sub["frac_pairs_varying"].mean()),
            "between_frac": float(sub["between_frac"].mean()),
            "within_frac": float(sub["within_frac"].mean()),
            "rho": float(sub["rho"].mean())}
    wp = res["by_arm"].get("identity_pathway", {})
    h412 = bool(wp and wp["max_spread_over_reps"] is not None
                and wp["max_spread_over_reps"] < 1e-12)
    res["decisions"] = {"H412_ranks_combinations_only": h412,
                        "H413_also_ranks_cells": bool(wp and not h412)}
    res["decisions"]["verdict"] = (
        "the_prediction_is_constant_across_the_cells_of_each_drug_pair_so_the_model_ranks_combinations_only"
        if h412 else "the_prediction_varies_across_cells_of_a_pair_so_the_model_ranks_cells_too")
    res["a_correction_worth_recording"] = {
        "what_happened": ("the first version reported a within-pair variance fraction of 0.309 for the identity arm. That arm has no cell feature, so the figure was impossible, "
                          "and a direct one-rep check showed the prediction was constant to 8.7e-21."),
        "cause": "the aggregation path, not the model",
        "fix": "plain numpy grouping with an explicit within-pair range, plus a raw max-spread column that cannot hide behind a ratio",
        "note": "the raw spread is the right statistic here: a ratio can look nonzero from floating-point residue when the true value is exactly constant"}
    res["why_this_is_structural"] = {
        "reason": "neither arm contains a cell-level feature. Identity is a drug indicator and the pathway block is a drug annotation, so with no cell covariate the prediction cannot depend on the cell.",
        "so": "the result is forced by the design; its value is in naming the boundary, not in surprise",
        "what_would_lift_it": "a cell-level covariate usable when both drugs are unseen, which this resource cannot supply; C90 already showed the tissue block is unreliable under holdout"}
    res["limits"] = ["Only ridge and one resource; two feature sets.",
                     "The result follows from the feature design.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r174/PROTOCOL_E162.md",
                "research/2026-10-27-agent-cell-identifiability-r174/e174_cell_axis_v2.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E174_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E174_rows.csv", index=False)

    for nm, e in res["by_arm"].items():
        print("  [%-16s] rho %+.4f | pairs %.1f | max within-pair spread %.3e | mean %.3e | frac varying %.3f" % (
            nm, e["rho"], e["mean_pairs"], e["max_spread_over_reps"], e["mean_spread"], e["frac_pairs_varying"]))
        print("      between_frac %.6f  within_frac %s" % (
            e["between_frac"], ("%.6e" % e["within_frac"]) if e["within_frac"] is not None else "undefined"))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
