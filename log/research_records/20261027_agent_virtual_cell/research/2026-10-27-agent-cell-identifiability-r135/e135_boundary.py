"""E135: where exactly does identity degenerate to a constant?

R134 found identity producing a constant score in 65 of 200 splits of the both-unseen pool. The
frozen claim's premise is that identity carries no signal there, so the boundary of that premise
should be measured rather than assumed.

Pre-registered in PROTOCOL_E125.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r135"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261038
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
    Xboth = np.hstack([Xid, Xpath])
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
        if len(tr) < 15000:
            continue
        pools = {"one_unseen": np.where((au ^ bu) & (~cu))[0],
                 "cell_unseen": np.where(cu & (au | bu))[0],
                 "one_seen_only": np.where((~au) & (~bu) & (~cu))[0],
                 "both_seen_cell": np.where(au & bu & (~cu))[0],
                 "both_unseen_cell": np.where(au & bu & cu)[0]}
        ytr = y[tr]
        sc = {}
        for nm, XX in (("identity", Xid), ("plus_pathway", Xboth)):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            sc[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
        for pname, pool in pools.items():
            pool = pool[np.isfinite(y[pool])]
            if len(pool) < 120:
                continue
            perm = rng.permutation(len(pool)); half = len(pool) // 2
            pe = pool[perm[half:]]
            if len(pe) < 100:
                continue
            yp = y[pe]
            row = {"rep": rep, "pool": pname, "n_eval": len(pe)}
            for nm, (f, XX) in sc.items():
                p = f(XX[pe])
                row[nm + "_sd"] = float(np.std(p))
                row[nm + "_const"] = bool(np.std(p) == 0.0)
                row[nm + "_rho"] = float(spearmanr(p, yp).statistic) if np.std(p) > 0 else np.nan
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "boundary_of_the_identity_degeneracy",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_pool": {}, "files": {}}
    for pname in ("one_unseen", "cell_unseen", "one_seen_only", "both_seen_cell", "both_unseen_cell"):
        sub = r[r.pool == pname]
        if len(sub) < 10:
            continue
        res["by_pool"][pname] = {
            "n": int(len(sub)),
            "identity_const_rate": float(sub["identity_const"].mean()),
            "pathway_const_rate": float(sub["plus_pathway_const"].mean()),
            "identity_rho": float(sub["identity_rho"].mean()),
            "pathway_rho": float(sub["plus_pathway_rho"].mean()),
            "rho_gain": paired(sub["plus_pathway_rho"], sub["identity_rho"], 56001 + len(pname))}

    low = ["one_unseen", "cell_unseen", "one_seen_only"]
    high = ["both_seen_cell", "both_unseen_cell"]
    bp = res["by_pool"]
    ok_low = all(bp[p]["identity_const_rate"] < 0.10 for p in low if p in bp)
    ok_high = all(bp[p]["identity_const_rate"] > 0.50 for p in high if p in bp)
    h336 = bool(ok_low and ok_high)
    h337 = bool(sum(1 for p, e in bp.items() if e["identity_const_rate"] > 0.50) >= 3)
    res["decisions"] = {"low_pool_rates": {p: bp[p]["identity_const_rate"] for p in low if p in bp},
                        "high_pool_rates": {p: bp[p]["identity_const_rate"] for p in high if p in bp},
                        "H336_degeneracy_only_when_both_drugs_unseen": h336,
                        "H337_degeneracy_broader": h337}
    res["decisions"]["verdict"] = (
        "identity_degenerates_exactly_when_both_drugs_are_unseen" if h336 else
        "identity_degenerates_more_broadly" if h337 else "mixed")
    res["limits"] = ["Only this resource; pools are key-level cuts.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r135/PROTOCOL_E125.md",
                "research/2026-10-27-agent-cell-identifiability-r135/e135_boundary.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E135_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E135_rows.csv", index=False)

    print("%-18s %5s %14s %14s %9s %9s" % ("pool", "n", "identity_const", "pathway_const", "id_rho", "path_rho"))
    for pname, e in res["by_pool"].items():
        print("%-18s %5d %13.3f %14.3f %+9.4f %+9.4f" % (
            pname, e["n"], e["identity_const_rate"], e["pathway_const_rate"],
            e["identity_rho"], e["pathway_rho"]))
        g2 = e["rho_gain"]
        if g2:
            print("      rho gain %+.4f [%+.4f,%+.4f] (n=%d)" % (g2["mean_diff"], g2["ci95"][0], g2["ci95"][1], g2["n"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
