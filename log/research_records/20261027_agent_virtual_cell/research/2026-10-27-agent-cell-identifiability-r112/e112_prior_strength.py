"""E112: does the sign of personalisation depend on prior strength, with strength MANIPULATED?

R111 argued the R76 conflict is explained by prior strength, but strength was only a concomitant
variable there. Here the prior is deliberately weakened by training it on a fraction of the
other cells, on a fixed cell set and at a fixed m, so strength becomes the controlled variable.

Pre-registered in PROTOCOL_E107.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r112"
LAMBDA = 1.0
K = 20
M = 200
FRACTIONS = (0.10, 0.25, 0.50, 1.00)
REPS = 3
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


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


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

    rng = np.random.default_rng(SEED)
    rows = []
    sanity = {"checked": 0, "differed": 0}
    for held in cells:
        po = np.where(CELL == held)[0]
        other = [c for c in cells if c != held]
        if len(po) < 2 * M + 2 * K or len(other) < 20:
            continue
        for frac in FRACTIONS:
            keep = max(10, int(round(frac * len(other))))
            chosen = rng.choice(other, size=keep, replace=False)
            tr = np.where(np.isin(CELL, chosen))[0]
            if len(tr) < 2000:
                continue
            ytr = y[tr].astype(float)
            Xt = Xcombo[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            base = ytr.mean() + ((Xcombo[po] - mu) / sd) @ w
            pos = {v: j for j, v in enumerate(po)}
            for _ in range(REPS):
                perm = rng.permutation(len(po))
                meas = po[perm[:M]]
                rest = po[perm[M:]]
                res_meas = np.array([y[i] - base[pos[i]] for i in meas])
                acc = {}
                for i, rr in zip(meas, res_meas):
                    acc.setdefault(A[i], []).append(rr)
                    acc.setdefault(B[i], []).append(rr)
                reff = {k: float(np.mean(v)) for k, v in acc.items()}
                sc_base = np.array([base[pos[i]] for i in rest])
                sc_pers = np.array([base[pos[i]] + 0.5 * (reff.get(A[i], 0.0) + reff.get(B[i], 0.0))
                                    for i in rest])
                sanity["checked"] += 1
                if not np.array_equal(np.argsort(-sc_base)[:K], np.argsort(-sc_pers)[:K]):
                    sanity["differed"] += 1
                rows.append({"cell": held, "frac": frac, "keep_cells": keep,
                             "prior": float(y[rest][np.argsort(-sc_base)[:K]].mean()),
                             "pers": float(y[rest][np.argsort(-sc_pers)[:K]].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "prior_strength_manipulated_personalisation_sign",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "m": M, "fractions": list(FRACTIONS), "reps": REPS,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "cells_used": int(r["cell"].nunique()) if len(r) else 0,
                     "units": int(len(r)), "sanity_checks": sanity["checked"],
                     "top_k_changed": sanity["differed"],
                     "sanity_passed": bool(sanity["checked"] > 0
                                           and sanity["differed"] / max(sanity["checked"], 1) > 0.5)},
           "by_fraction": {}, "files": {}}

    for frac in FRACTIONS:
        sub = r[r.frac == frac]
        if len(sub) < 5:
            continue
        res["by_fraction"][f"{frac:.2f}"] = {
            "n": int(len(sub)), "mean_keep_cells": float(sub["keep_cells"].mean()),
            "prior": float(sub["prior"].mean()), "pers": float(sub["pers"].mean()),
            "gain": paired(sub["pers"], sub["prior"], 42001 + int(frac * 100))}

    series = [(f, res["by_fraction"][f"{f:.2f}"]) for f in FRACTIONS if f"{f:.2f}" in res["by_fraction"]]
    priors = [e["prior"] for _, e in series]
    gains = [e["gain"]["mean_diff"] for _, e in series]
    sig_pos = [f for f, e in series if e["gain"]["ci95"][0] > 0]
    sig_neg = [f for f, e in series if e["gain"]["ci95"][1] < 0]
    monotone_prior = all(priors[i] <= priors[i + 1] + 0.01 for i in range(len(priors) - 1))
    crossover = bool(sig_pos and sig_neg and min(sig_pos) > max(sig_neg))
    res["decisions"] = {"sanity_passed": res["audit"]["sanity_passed"],
                        "prior_strength_rises_with_data": monotone_prior,
                        "prior_levels": [round(p, 4) for p in priors],
                        "gains": [round(g, 4) for g in gains],
                        "sig_positive_fractions": [round(f, 2) for f in sig_pos],
                        "sig_negative_fractions": [round(f, 2) for f in sig_neg],
                        "H285_sign_crossover": crossover}
    res["decisions"]["verdict"] = (
        "INVALID_sanity_failed" if not res["audit"]["sanity_passed"] else
        "sign_crossover_confirms_prior_strength_controls_the_effect" if crossover else
        "no_clean_crossover")
    res["limits"] = [
        "Weakening the prior by training on fewer cells also changes its noise structure, not only its strength.",
        "m is fixed at 200, so the result is specific to that sample size.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r112/PROTOCOL_E107.md",
                "research/2026-10-27-agent-cell-identifiability-r112/e112_prior_strength.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E112_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E112_rows.csv", index=False)

    print("cells=%d units=%d sanity %d/%d passed=%s" % (
        res["audit"]["cells_used"], len(r), sanity["differed"], sanity["checked"],
        res["audit"]["sanity_passed"]))
    for f, e in series:
        c = e["gain"]
        print("  frac %.2f (cells~%.0f) prior %.4f pers %.4f | gain %+.4f [%+.4f,%+.4f]" % (
            f, e["mean_keep_cells"], e["prior"], e["pers"], c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
