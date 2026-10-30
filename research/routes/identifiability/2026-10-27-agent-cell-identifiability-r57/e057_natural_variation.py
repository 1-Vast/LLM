"""E057: test the strength-moderator hypothesis using NATURAL between-cell variation instead
of a manipulation that four earlier rounds failed to build.

For each of the 125 GDSC cell lines: train on all other cells, pool that cell's keys, then
record prediction rho and mix-minus-exploit at k=20. Pre-registered in PROTOCOL_E056.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r57"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
K = 20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rank_corr(a, b):
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def onehot(vals, levels):
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
    return M


def partial_corr(x, y, z):
    """Spearman partial correlation of x and y controlling z (via ranks + linear residualisation)."""
    rx = pd.Series(x).rank().to_numpy(float)
    ry = pd.Series(y).rank().to_numpy(float)
    rz = pd.Series(z).rank().to_numpy(float)
    Z = np.column_stack([np.ones_like(rz), rz])
    bx = np.linalg.lstsq(Z, rx, rcond=None)[0]
    by = np.linalg.lstsq(Z, ry, rcond=None)[0]
    ex = rx - Z @ bx
    ey = ry - Z @ by
    den = np.sqrt((ex ** 2).sum() * (ey ** 2).sum())
    return float((ex * ey).sum() / den) if den > 0 else np.nan


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), tissue=("Tissue", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        synergy=(METRIC, "mean"))
    for c in ("cell", "tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv), onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
    y = d.synergy.to_numpy(float)
    cells = d["cell"].to_numpy()

    rows = []
    for c in sorted(pd.unique(cells)):
        po = np.where(cells == c)[0]
        tr = np.where(cells != c)[0]
        if len(po) < 200 or len(tr) < 5000:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Xp = (X[po] - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())
        pred = ytr.mean() + Xp @ w
        var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
        yp = y[po]
        strong = yp >= np.quantile(yp, 0.90)
        rp = pd.Series(pred).rank(pct=True).to_numpy()
        rv = pd.Series(var).rank(pct=True).to_numpy()
        mix = rp + rv
        e = float(strong[np.argsort(-rp)[:K]].mean())
        m = float(strong[np.argsort(-mix)[:K]].mean())
        rows.append({"cell": c, "n_pool": int(len(po)), "rho": rank_corr(pred, yp),
                     "exploit": e, "mix": m, "diff": m - e})

    r = pd.DataFrame(rows)
    res = {"kind": "natural_variation_test_of_strength_moderator",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"k": K, "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED,
                        "design": "leave one cell line out, pool = that cell's keys"},
           "audit": {"keys": int(len(y)), "cells_scored": int(len(r)),
                     "features": int(X.shape[1])},
           "cells": r.to_dict(orient="records"), "files": {}}

    sp = rank_corr(r["rho"], r["diff"])
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(r), len(r))
        sub = r.iloc[idx]
        if sub["rho"].std() > 0 and sub["diff"].std() > 0:
            boots.append(rank_corr(sub["rho"], sub["diff"]))
    res["analysis"] = {
        "spearman_rho_vs_diff": sp,
        "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
        "partial_controlling_pool_size": partial_corr(r["rho"], r["diff"], r["n_pool"]),
        "spearman_poolsize_vs_diff": rank_corr(r["n_pool"], r["diff"]),
        "n": int(len(r))}

    r["quartile"] = pd.qcut(r["rho"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    q = r.groupby("quartile", observed=True).agg(rho=("rho", "mean"), diff=("diff", "mean"),
                                                 n=("diff", "size"), n_pool=("n_pool", "mean"))
    res["by_quartile"] = {str(k): {c: float(v) for c, v in row.items()} for k, row in q.iterrows()}
    q4 = float(q.loc["Q4", "diff"]) if "Q4" in q.index else np.nan
    q1 = float(q.loc["Q1", "diff"]) if "Q1" in q.index else np.nan

    h146 = bool(sp > 0 and res["analysis"]["ci95"] and res["analysis"]["ci95"][0] > 0)
    h147 = bool(res["analysis"]["partial_controlling_pool_size"] > 0)
    h148 = bool(q4 - q1 > 0.02)
    res["decisions"] = {"H146_strength_moderates": h146, "H147_survives_pool_control": h147,
                        "H148_quartile_gap": h148, "quartile_gap": q4 - q1}
    res["decisions"]["verdict"] = ("strength_moderator_supported_by_natural_variation" if h146 and h147 else
                                   "strength_moderator_not_supported")
    res["limits"] = [
        "Pool size varies across cells (~400-2000), so rho and pool size are naturally related; a partial correlation is reported.",
        "The training set changes with each fold, which affects both rho and the pool.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r57/PROTOCOL_E056.md",
                "research/2026-10-27-agent-cell-identifiability-r57/e057_natural_variation.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E057_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E057_cells.csv", index=False)

    print("cells scored=%d features=%d" % (len(r), res["audit"]["features"]))
    print("rho range: %.3f to %.3f | diff range: %+.4f to %+.4f | pool range: %d to %d" % (
        r["rho"].min(), r["rho"].max(), r["diff"].min(), r["diff"].max(),
        r["n_pool"].min(), r["n_pool"].max()))
    print("spearman(rho, diff) = %+.4f  CI %s" % (sp, res["analysis"]["ci95"]))
    print("partial controlling pool size = %+.4f" % res["analysis"]["partial_controlling_pool_size"])
    print("spearman(pool, diff) = %+.4f" % res["analysis"]["spearman_poolsize_vs_diff"])
    print("by quartile:")
    for kk, row in res["by_quartile"].items():
        print("   %s rho=%.3f pool=%.0f n=%d | diff %+.4f" % (kk, row["rho"], row["n_pool"], row["n"], row["diff"]))
    print("quartile gap Q4-Q1 = %+.4f" % (q4 - q1))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
