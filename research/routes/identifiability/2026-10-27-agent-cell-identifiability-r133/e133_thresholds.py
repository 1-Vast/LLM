"""E133: is the frozen claim sensitive to the criterion threshold?

The frozen claim is measured against the top quartile of delta EMAX, and 25 percent was never
justified. This sweeps the threshold so that a result driven by the cut point cannot hide.

Pre-registered in PROTOCOL_E123.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r133"
LAMBDA = 1.0
K = 20
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261036
TAUS = (0.10, 0.20, 0.25, 0.33, 0.50)
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
        if len(tr) < 15000 or len(pool) < 120:
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
        if len(pe) < 60:
            continue
        yp = y[pe]
        qs = np.argsort(-yp)
        for tau in TAUS:
            cut = max(1, int(round(tau * len(yp))))
            keep = qs[:cut]
            row = {"rep": rep, "tau": tau, "cut": cut, "n_eval": len(pe)}
            for nm, (f, XX) in sc.items():
                pred = np.argsort(-f(XX[pe]))[:K]
                row[nm] = float(np.isin(pred, keep).mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "threshold_sensitivity_of_the_frozen_claim",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "taus": list(TAUS), "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_tau": {}, "files": {}}
    for tau in TAUS:
        sub = r[r.tau == tau].set_index("rep")
        if len(sub) < 10:
            continue
        e = {"n": int(len(sub)),
             "identity": float(sub["identity"].mean()),
             "plus_pathway": float(sub["plus_pathway"].mean()),
             "plus_random": float(sub["plus_random"].mean()),
             "pathway_gain": paired(sub["plus_pathway"], sub["identity"], 54001 + int(tau * 100)),
             "random_gain": paired(sub["plus_random"], sub["identity"], 54101 + int(tau * 100))}
        e["mde_80pct"] = float(2.802 * e["pathway_gain"]["sd"] / np.sqrt(len(sub)))
        res["by_tau"][f"{tau:.2f}"] = e

    sig = [t for t, e in res["by_tau"].items() if e["pathway_gain"]["ci95"][0] > 0]
    rnd_sig = [t for t, e in res["by_tau"].items() if e["random_gain"]["ci95"][0] > 0]
    res["decisions"] = {"pathway_significant_taus": sig, "random_significant_taus": rnd_sig,
                        "H332_robust_across_taus": len(sig) == len(res["by_tau"]),
                        "H333_threshold_dependent": len(sig) < len(res["by_tau"])}
    res["decisions"]["verdict"] = (
        "the_claim_is_robust_across_thresholds" if len(sig) == len(res["by_tau"]) else
        "the_claim_depends_on_the_threshold_and_must_be_downgraded" if sig else
        "the_claim_fails_at_every_threshold")
    res["limits"] = ["Only the both_unseen cell; elsewhere identity has no headroom.",
                     "Extreme thresholds shrink the hit rate and may lose power.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r133/PROTOCOL_E123.md",
                "research/2026-10-27-agent-cell-identifiability-r133/e133_thresholds.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E133_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E133_rows.csv", index=False)

    print("%-6s %4s %8s %8s %8s %9s %9s" % ("tau", "n", "identity", "+path", "+rand", "path_gain", "MDE80"))
    for t, e in res["by_tau"].items():
        g2 = e["pathway_gain"]
        print("%-6s %4d %8.4f %8.4f %8.4f  %+.4f [%+.4f,%+.4f]  %.4f" % (
            t, e["n"], e["identity"], e["plus_pathway"], e["plus_random"],
            g2["mean_diff"], g2["ci95"][0], g2["ci95"][1], e["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
