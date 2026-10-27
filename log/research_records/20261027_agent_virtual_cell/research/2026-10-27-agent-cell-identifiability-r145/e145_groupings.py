"""E145: which grouping is the better prior - pathway, target, or both?

R144's next step asked for a shrunk marginal baseline, but that is structurally unreachable: an
unseen drug has n = 0, so any shrinkage collapses to the grand mean. The only source of information
for an unseen drug is a grouping, so the meaningful competitor is a different grouping. Target
annotation is the natural one: also a coarsening of the drug, also available for unseen drugs.

Pre-registered in PROTOCOL_E135.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r145"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261048
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
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
    return {"n": int(m), "mean_diff": float(dif.mean()),
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
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpath = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xtgt = np.hstack([oh(g["at"].to_numpy(), sorted(g["at"].unique())),
                      oh(g["lt"].to_numpy(), sorted(g["lt"].unique()))])
    y = g["emax"].to_numpy(float)
    dims = {"identity": Xid.shape[1], "pathway": Xpath.shape[1], "target": Xtgt.shape[1]}

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        te = np.where(au & bu)[0]; tr = np.where((~au) & (~bu))[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr, yte = y[tr], y[te]
        Xrand = rng.normal(size=(len(g), Xpath.shape[1]))
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_target": np.hstack([Xid, Xtgt]),
                "plus_both": np.hstack([Xid, Xpath, Xtgt]),
                "plus_random": np.hstack([Xid, Xrand])}
        row = {"rep": rep, "n_eval": len(te)}
        for nm, XX in arms.items():
            p = ridge_fp(XX[tr], ytr, XX[te])
            row[nm] = 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "which_grouping_is_the_better_prior",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)), "dims": dims},
           "arms": {nm: float(r[nm].mean()) for nm in
                    ("identity", "plus_pathway", "plus_target", "plus_both", "plus_random")},
           "contrasts": {}, "files": {}}
    res["contrasts"] = {
        "pathway_minus_identity": paired(r["plus_pathway"], r["identity"], 64001),
        "target_minus_identity": paired(r["plus_target"], r["identity"], 64101),
        "both_minus_identity": paired(r["plus_both"], r["identity"], 64201),
        "random_minus_identity": paired(r["plus_random"], r["identity"], 64301),
        "target_minus_pathway": paired(r["plus_target"], r["plus_pathway"], 64401),
        "both_minus_pathway": paired(r["plus_both"], r["plus_pathway"], 64501)}
    tp = res["contrasts"]["target_minus_pathway"]
    h356 = bool(tp["ci95"][0] > 0 or tp["ci95"][1] < 0)
    res["decisions"] = {"target_vs_pathway_diff": tp["mean_diff"],
                        "H356_groupings_differ": h356, "H357_groupings_equivalent": not h356}
    res["decisions"]["which_is_better"] = (
        "target" if tp["mean_diff"] > 0 else "pathway") if h356 else "equivalent"
    res["decisions"]["verdict"] = (
        f"target_is_the_better_prior" if h356 and tp["mean_diff"] > 0 else
        f"pathway_is_the_better_prior" if h356 else
        "the_two_groupings_are_equivalent_so_any_reasonable_partition_would_do")
    res["limits"] = ["Only this resource and only ridge.",
                     "Target has 40+58 levels against pathway's 38, so the dimension differs and is reported.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r145/PROTOCOL_E135.md",
                "research/2026-10-27-agent-cell-identifiability-r145/e145_groupings.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E145_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E145_rows.csv", index=False)

    print("dims:", dims, "| rows:", len(r))
    for nm, v in res["arms"].items():
        print("  %-14s rho %.4f" % (nm, v))
    for k, c in res["contrasts"].items():
        print("  %-24s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps({k: v for k, v in res["decisions"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
