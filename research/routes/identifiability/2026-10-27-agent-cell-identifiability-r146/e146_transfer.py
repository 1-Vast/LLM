"""E146: does pathway remain the better prior than target when a whole tissue is held out?

R145 compared the two groupings within distribution: pathway 0.1254 against target 0.0536. This asks
whether that ranking survives a distribution shift, since target might be the more portable of the
two and pathway the more tissue-specific.

Pre-registered in PROTOCOL_E136.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r146"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261049
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "ANCHOR_TARGET", "LIBRARY_TARGET", "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    m = len(j)
    if m < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=m, replace=True))) for _ in range(N_BOOT)]
    return {"n": int(m), "mean_diff": float(dif.mean()), "sd": float(dif.std(ddof=1)),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def oh(vals, levels):
    idx = {v: j for j, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            M[t, j] = 1.0
    return M


def ridge_fp(Xtr, ytr, Xte, lam=LAMBDA):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        tissue=("Tissue", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"), emax=("emax", "mean"))
    for c in ("tissue", "a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); TIS = g["tissue"].to_numpy()
    drugs = sorted(set(A) | set(B)); tissues = sorted(set(TIS))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpath = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xtgt = np.hstack([oh(g["at"].to_numpy(), sorted(g["at"].unique())),
                      oh(g["lt"].to_numpy(), sorted(g["lt"].unique()))])
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        held_tissue = tissues[rep % len(tissues)]
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tu = TIS == held_tissue
        tr = np.where((~au) & (~bu) & (~tu))[0]
        te = np.where(au & bu & tu)[0]
        if len(tr) < 15000 or len(te) < 100:
            continue
        ytr, yte = y[tr], y[te]
        Xrand = rng.normal(size=(len(g), Xpath.shape[1]))
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_target": np.hstack([Xid, Xtgt]),
                "plus_random": np.hstack([Xid, Xrand])}
        row = {"rep": rep, "tissue": held_tissue, "n_eval": len(te)}
        for nm, XX in arms.items():
            p = ridge_fp(XX[tr], ytr, XX[te])
            row[nm] = 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "does_pathway_stay_the_better_prior_under_tissue_holdout",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)),
                     "mean_eval": float(r["n_eval"].mean()) if len(r) else None},
           "arms": {nm: float(r[nm].mean()) for nm in
                    ("identity", "plus_pathway", "plus_target", "plus_random")} if len(r) else {},
           "contrasts": {}, "files": {}}
    for key, a, b, off in (("pathway_minus_identity", "plus_pathway", "identity", 65001),
                            ("target_minus_identity", "plus_target", "identity", 65101),
                            ("pathway_minus_target", "plus_pathway", "plus_target", 65201),
                            ("random_minus_identity", "plus_random", "identity", 65301)):
        c = paired(r[a], r[b], off)
        if c:
            c["mde_80pct"] = float(2.802 * c["sd"] / np.sqrt(len(r)))
        res["contrasts"][key] = c
    pt = res["contrasts"].get("pathway_minus_target") or {}
    pi = res["contrasts"].get("pathway_minus_identity") or {}
    under = bool(pt and pt["mde_80pct"] > abs(pt["mean_diff"]))
    h358 = bool(pt and pt["ci95"][0] > 0)
    res["decisions"] = {"pathway_minus_target": pt.get("mean_diff") if pt else None,
                        "underpowered": under,
                        "H358_ranking_preserved": h358,
                        "H359_ranking_not_preserved": bool(pt and pt["ci95"][0] <= 0)}
    res["decisions"]["verdict"] = (
        "UNDERPOWERED_on_the_pathway_versus_target_contrast" if under else
        "pathway_remains_the_better_prior_under_tissue_holdout" if h358 else
        "the_ranking_does_not_survive_tissue_holdout")
    res["limits"] = ["The double holdout leaves a small evaluation set, so the minimum detectable effect is reported.",
                     "Only ridge.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r146/PROTOCOL_E136.md",
                "research/2026-10-27-agent-cell-identifiability-r146/e146_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E146_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E146_rows.csv", index=False)

    print("rows=%d  mean eval size=%.0f" % (len(r), res["audit"]["mean_eval"] or 0))
    for nm, v in res["arms"].items():
        print("  %-14s rho %+.4f" % (nm, v))
    for k, c in res["contrasts"].items():
        if c:
            print("  %-24s %+.4f [%+.4f,%+.4f]  MDE80 %.4f" % (
                k, c["mean_diff"], c["ci95"][0], c["ci95"][1], c["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
