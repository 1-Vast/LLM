"""E134: does the annotation improve the ranking globally, or only its head?

R133 saw the hit-rate gain grow as the threshold loosened and I read that as a ranking-wide
improvement. But hit rate mechanically drifts toward tau as k grows, so that inference has a hole.
The clean test is global rank correlation, which does not depend on a cut.

Pre-registered in PROTOCOL_E124.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r134"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261037
TOPKS = (20, 50, 100)
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]


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
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()), "sd": float(dif.std(ddof=1)),
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
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds); cs = cells[:]; rng.shuffle(cs)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        heldc = set(cs[: max(3, int(round(HOLDOUT * len(cs))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        cu = np.array([c in heldc for c in CELL])
        tr = np.where((~cu) & (~au) & (~bu) & np.isfinite(y))[0]
        pool = np.where(au & bu & np.isfinite(y))[0]
        if len(tr) < 15000 or len(pool) < 150:
            continue
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_random": np.hstack([Xid, rng.normal(size=(len(g), Xpath.shape[1]))])}
        ytr = y[tr]
        sc = {}
        for nm, XX in arms.items():
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            sc[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
        perm = rng.permutation(len(pool)); half = len(pool) // 2
        pe = pool[perm[half:]]
        if len(pe) < 100:
            continue
        yp = y[pe]
        row = {"rep": rep, "n_eval": len(pe)}
        preds = {}
        for nm, (f, XX) in sc.items():
            p = f(XX[pe]); preds[nm] = p
            row[nm + "_rho"] = float(spearmanr(p, yp).statistic)
        order_true = np.argsort(-yp)
        for k in TOPKS:
            if k >= len(pe):
                continue
            keep = set(order_true[: max(1, int(round(0.25 * len(yp))))].tolist())
            for nm, p in preds.items():
                sel = np.argsort(-p)[:k]
                row["%s_hit%d" % (nm, k)] = float(np.isin(sel, list(keep)).mean())
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "global_ranking_vs_head_only",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "topks": list(TOPKS),
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "primary": {}, "secondary": {}, "files": {}}

    for nm in ("identity", "plus_pathway", "plus_random"):
        res["primary"][nm + "_rho"] = float(r[nm + "_rho"].mean())
    res["primary"]["pathway_minus_identity"] = paired(r["plus_pathway_rho"], r["identity_rho"], 55001)
    res["primary"]["random_minus_identity"] = paired(r["plus_random_rho"], r["identity_rho"], 55101)
    for nm in ("plus_pathway", "plus_random"):
        res["primary"]["mde_" + nm] = float(
            2.802 * res["primary"]["pathway_minus_identity"]["sd"] / np.sqrt(len(r)))

    for k in TOPKS:
        key = "%s_hit%d"
        if (key % ("identity", k)) not in r:
            continue
        res["secondary"][str(k)] = {
            "identity": float(r[key % ("identity", k)].mean()),
            "plus_pathway": float(r[key % ("plus_pathway", k)].mean()),
            "plus_random": float(r[key % ("plus_random", k)].mean()),
            "pathway_gain": paired(r[key % ("plus_pathway", k)], r[key % ("identity", k)], 55201 + k)}

    pr = res["primary"]
    h334 = bool(pr["pathway_minus_identity"]["ci95"][0] > 0 and pr["random_minus_identity"]["ci95"][0] <= 0)
    h335 = bool(pr["pathway_minus_identity"]["ci95"][0] <= 0)
    res["decisions"] = {"spearman_pathway_gain": pr["pathway_minus_identity"]["mean_diff"],
                        "H334_ranking_improves_globally": h334,
                        "H335_only_the_head_improves": h335}
    res["decisions"]["verdict"] = (
        "the_ranking_improves_globally_not_only_at_the_head" if h334 else
        "the_gain_is_confined_to_the_head_and_R133s_reading_must_be_withdrawn" if h335 else
        "ambiguous")
    res["limits"] = ["Only the both_unseen cell.",
                     "A single rank correlation can hide local shape.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r134/PROTOCOL_E124.md",
                "research/2026-10-27-agent-cell-identifiability-r134/e134_ranking.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E134_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E134_rows.csv", index=False)

    print("rows=%d" % len(r))
    print("  rho: identity %.4f  pathway %.4f  random %.4f" % (
        res["primary"]["identity_rho"], res["primary"]["plus_pathway_rho"], res["primary"]["plus_random_rho"]))
    a = pr["pathway_minus_identity"]; b = pr["random_minus_identity"]
    print("  pathway-id %+.4f [%+.4f,%+.4f] | random-id %+.4f [%+.4f,%+.4f]" % (
        a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    for k, e in res["secondary"].items():
        g2 = e["pathway_gain"]
        print("  top-%-4s identity %.4f  pathway %.4f  gain %+.4f [%+.4f,%+.4f]" % (
            k, e["identity"], e["plus_pathway"], g2["mean_diff"], g2["ci95"][0], g2["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
