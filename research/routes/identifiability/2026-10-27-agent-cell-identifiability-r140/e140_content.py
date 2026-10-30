"""E140: is the substitution about the pathway's content, or would any coarsening do?

R136 reframed the claim as 'the pathway is a coarsening of identity that substitutes when identity
is missing'. White noise was already ruled out, but a RANDOM coarsening with the same cardinality
and structure has not been. If a random grouping substitutes just as well, the result is about
dimensionality reduction rather than about pathways.

Pre-registered in PROTOCOL_E130.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r140"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261043
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]


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


def onehot_vals(vals, levels):
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
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    ap_lv = sorted(g["ap"].unique()); lp_lv = sorted(g["lp"].unique())
    Xid = np.hstack([onehot_vals(A, drugs), onehot_vals(B, drugs)])
    Xpath = np.hstack([onehot_vals(g["ap"].to_numpy(), ap_lv), onehot_vals(g["lp"].to_numpy(), lp_lv)])
    y = g["emax"].to_numpy(float)

    # real group counts per side
    n_ap = len(ap_lv); n_lp = len(lp_lv)
    a_real = pd.Categorical(g["a"], categories=drugs).codes
    b_real = pd.Categorical(g["b"], categories=drugs).codes

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        te = np.where(au & bu)[0]; tr = np.where((~au) & (~bu))[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr, yte = y[tr], y[te]
        # random coarsening: assign each drug to a group, same group counts as the real blocks
        a_grp = rng.integers(0, n_ap, size=len(drugs))
        b_grp = rng.integers(0, n_lp, size=len(drugs))
        Xcoarse = np.hstack([onehot_vals(a_grp[a_real], list(range(n_ap))),
                             onehot_vals(b_grp[b_real], list(range(n_lp)))])
        Xnoise = rng.normal(size=(len(g), Xpath.shape[1]))
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_randomcoarse": np.hstack([Xid, Xcoarse]),
                "plus_noise": np.hstack([Xid, Xnoise])}
        row = {"rep": rep, "n_eval": len(te)}
        for nm, XX in arms.items():
            p = ridge_fp(XX[tr], ytr, XX[te])
            row[nm] = 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "content_or_any_coarsening",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "arms": {}, "files": {}}
    for nm in ("identity", "plus_pathway", "plus_randomcoarse", "plus_noise"):
        res["arms"][nm] = float(r[nm].mean())
    res["contrasts"] = {
        "pathway_minus_identity": paired(r["plus_pathway"], r["identity"], 62001),
        "randomcoarse_minus_identity": paired(r["plus_randomcoarse"], r["identity"], 62101),
        "noise_minus_identity": paired(r["plus_noise"], r["identity"], 62201),
        "pathway_minus_randomcoarse": paired(r["plus_pathway"], r["plus_randomcoarse"], 62301)}
    pc = res["contrasts"]
    h346 = bool(pc["pathway_minus_randomcoarse"]["ci95"][0] > 0)
    h347 = bool(pc["pathway_minus_randomcoarse"]["ci95"][0] <= 0
                and pc["pathway_minus_identity"]["ci95"][0] > 0
                and pc["randomcoarse_minus_identity"]["ci95"][0] > 0)
    res["decisions"] = {"H346_content_matters": h346, "H347_any_coarsening_would_do": h347}
    res["decisions"]["verdict"] = (
        "the_pathway_content_matters" if h346 else
        "any_random_coarsening_substitutes_so_it_is_dimensionality_reduction" if h347 else
        "neither_clean")
    res["limits"] = ["Only the both-unseen condition and only ridge.",
                     "The random coarsening is redrawn per split, which integrates over groupings.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r140/PROTOCOL_E130.md",
                "research/2026-10-27-agent-cell-identifiability-r140/e140_content.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E140_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E140_rows.csv", index=False)

    print("rows=%d" % len(r))
    for nm, v in res["arms"].items():
        print("  %-20s rho %.4f" % (nm, v))
    for k, c in pc.items():
        print("  %-28s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
