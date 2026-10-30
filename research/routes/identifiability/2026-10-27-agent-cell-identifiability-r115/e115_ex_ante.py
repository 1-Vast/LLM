"""E115: can the conditional rule be applied EX ANTE, without measuring any keys?

R114 showed a probe cannot identify the regime. Its proposal was to use an ex ante estimate of
prior strength instead. This asks whether tissue - known before any measurement - predicts how
strong the prior is for a cell, and whether it straddles the roughly 11% crossover.

Pre-registered in PROTOCOL_E110.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r115"
LAMBDA = 1.0
K = 20
M = 200
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def boot_ci(vals, seed):
    vals = np.asarray([v for v in vals if np.isfinite(v)], float)
    if len(vals) < 3:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    bs = [float(np.mean(rng.choice(vals, size=len(vals), replace=True))) for _ in range(N_BOOT)]
    return [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]


def onehot(vals, levels):
    idx = {v: j for j, v in enumerate(levels)}
    Mt = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            Mt[t, j] = 1.0
    return Mt


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])
    Xcombo = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)
    cell_tissue = g.groupby("cell")["tissue"].first().to_dict()

    rng = np.random.default_rng(SEED)
    rows = []
    for held in cells:
        po = np.where(CELL == held)[0]
        tr = np.where(CELL != held)[0]
        if len(po) < M + 2 * K or len(tr) < 20000:
            continue
        ytr = y[tr].astype(float)
        Xt = Xcombo[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
        Z = (Xt - mu) / sd
        w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
        base = ytr.mean() + ((Xcombo[po] - mu) / sd) @ w
        pos = {v: j for j, v in enumerate(po)}
        perm = rng.permutation(len(po))
        meas = po[perm[:M]]
        rest = po[perm[M:]]
        if len(rest) < 2 * K:
            continue
        res_meas = np.array([y[i] - base[pos[i]] for i in meas])
        acc = {}
        for i, rr in zip(meas, res_meas):
            acc.setdefault(A[i], []).append(rr)
            acc.setdefault(B[i], []).append(rr)
        reff = {k: float(np.mean(v)) for k, v in acc.items()}
        sc_base = np.array([base[pos[i]] for i in rest])
        sc_pers = np.array([base[pos[i]] + 0.5 * (reff.get(A[i], 0.0) + reff.get(B[i], 0.0))
                            for i in rest])
        hit = y[rest].astype(float)
        rows.append({"cell": held, "tissue": cell_tissue.get(held, "NA"),
                     "prior": float(hit[np.argsort(-sc_base)[:K]].mean()),
                     "pers": float(hit[np.argsort(-sc_pers)[:K]].mean())})

    r = pd.DataFrame(rows)
    r["gain"] = r["pers"] - r["prior"]
    res = {"kind": "can_prior_strength_be_estimated_ex_ante_from_tissue",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "m": M, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "cells": int(len(r)), "tissues": sorted(r["tissue"].unique())},
           "by_tissue": {}, "files": {}}

    for t in sorted(r["tissue"].unique()):
        sub = r[r.tissue == t]
        if len(sub) < 3:
            continue
        res["by_tissue"][t] = {
            "n": int(len(sub)),
            "prior": float(sub["prior"].mean()), "prior_ci": boot_ci(sub["prior"], 45001 + len(t)),
            "sd": float(sub["prior"].std(ddof=1)),
            "gain": float(sub["gain"].mean()), "gain_ci": boot_ci(sub["gain"], 45101 + len(t))}

    # variance decomposition on prior strength (one-way ANOVA form)
    grand = float(r["prior"].mean())
    ss_between = sum(len(s) * (s["prior"].mean() - grand) ** 2 for _, s in r.groupby("tissue"))
    ss_total = float(((r["prior"] - grand) ** 2).sum())
    icc = float(ss_between / ss_total) if ss_total > 0 else float("nan")
    res["variance"] = {"grand_prior": grand, "icc_tissue": icc,
                       "min_tissue_prior": float(min(v["prior"] for v in res["by_tissue"].values())),
                       "max_tissue_prior": float(max(v["prior"] for v in res["by_tissue"].values()))}

    spread_crosses = bool(res["variance"]["min_tissue_prior"] < 0.11 < res["variance"]["max_tissue_prior"])
    h288 = bool(icc >= 0.30 and spread_crosses)
    h289 = bool(icc < 0.30 or not spread_crosses)
    res["decisions"] = {"icc": icc, "tissue_spread_crosses_11pct": spread_crosses,
                        "H288_tissue_identifies_regime": h288,
                        "H289_tissue_cannot": h289}
    res["decisions"]["verdict"] = (
        "rule_can_be_applied_ex_ante_by_tissue" if h288 else
        "ex_ante_application_also_has_no_basis")
    res["limits"] = [
        "Only three tissues, so the between-group estimate is very coarse.",
        "Tissue and prior strength may both be confounded with other cell properties.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r115/PROTOCOL_E110.md",
                "research/2026-10-27-agent-cell-identifiability-r115/e115_ex_ante.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E115_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E115_rows.csv", index=False)

    print("cells=%d tissues=%s" % (len(r), res["audit"]["tissues"]))
    for t, e in res["by_tissue"].items():
        print("  [%-9s] n=%2d prior %.4f [%.4f,%.4f] sd %.4f | gain %+.4f [%+.4f,%+.4f]" % (
            t, e["n"], e["prior"], e["prior_ci"][0], e["prior_ci"][1], e["sd"],
            e["gain"], e["gain_ci"][0], e["gain_ci"][1]))
    print("  grand prior %.4f | ICC(tissue) %.3f | spread [%.4f,%.4f] crosses 11%%: %s" % (
        grand, icc, res["variance"]["min_tissue_prior"], res["variance"]["max_tissue_prior"], spread_crosses))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
