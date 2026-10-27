"""E131: the resolution matrix - three pools by two criteria, each cell with its own MDE.

R122 concluded that the sparse boolean criterion has no resolution and I wrote that as a general
statement about the criterion. But the boolean criterion reaches 8 to 10 percent identity in the
other pools, where it clearly does resolve. This fills in all six cells so that which criterion
resolves in which pool is on record rather than remembered.

Pre-registered in PROTOCOL_E122.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r131"
LAMBDA = 1.0
K = 20
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261035
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy", "SYNERGY_DELTA_EMAX"]


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
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        syn=("syn", "mean"), emax=("emax", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xpath])
    ysyn = g["syn"].to_numpy(float); yemax = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        cs = cells[:]; rng.shuffle(cs)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        heldc = set(cs[: max(3, int(round(HOLDOUT * len(cs))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        cu = np.array([c in heldc for c in CELL])
        pools = {"one_unseen": np.where((au ^ bu) & (~cu))[0],
                 "cell_unseen": np.where(cu & (au | bu))[0],
                 "both_unseen": np.where(au & bu)[0]}
        usable = all(np.isfinite(yemax[p]).sum() > 100 for p in pools.values())
        if not usable:
            continue
        tr_mask = (~cu) & (~au) & (~bu)
        tr = np.where(tr_mask)[0]
        for crit, yt in (("Synergy", ysyn), ("dEMAX", yemax)):
            trk = tr[np.isfinite(yt[tr])]
            if len(trk) < 15000:
                continue
            ytr = yt[trk]
            sc = {}
            for nm, XX in (("identity", Xid), ("plus_pathway", Xboth)):
                Xt = XX[trk]
                mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
                Z = (Xt - mu) / sd
                w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
                sc[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
            for pname, pool in pools.items():
                pool = pool[np.isfinite(yt[pool])]
                if len(pool) < 80:
                    continue
                perm = rng.permutation(len(pool)); half = len(pool) // 2
                pe = pool[perm[half:]]
                if len(pe) < 60:
                    continue
                yp = yt[pe]
                if crit == "dEMAX":
                    hit = (yp >= np.quantile(yp, 0.75)).astype(float); chance = 0.25
                else:
                    hit = yp; chance = float(yp.mean())
                row = {"rep": rep, "criterion": crit, "pool": pname, "chance": chance}
                for nm, (f, XX) in sc.items():
                    row[nm] = float(hit[np.argsort(-f(XX[pe]))[:K]].mean())
                rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "resolution_matrix_three_pools_by_two_criteria",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))},
           "cells": {}, "files": {}}
    for crit in ("Synergy", "dEMAX"):
        for pname in ("one_unseen", "cell_unseen", "both_unseen"):
            sub = r[(r.criterion == crit) & (r.pool == pname)].set_index("rep")
            if len(sub) < 10:
                continue
            gain = paired(sub["plus_pathway"], sub["identity"], 53001 + len(crit) + len(pname))
            ident = float(sub["identity"].mean()); chance = float(sub["chance"].mean())
            mde = float(2.802 * gain["sd"] / np.sqrt(len(sub)))
            resolvable = bool(mde < max(ident - chance, 1e-9))
            res["cells"]["%s|%s" % (crit, pname)] = {
                "n": int(len(sub)), "chance": chance, "identity": ident,
                "room": ident - chance, "mde_80pct": mde,
                "pathway_gain": gain, "resolvable": resolvable,
                "ratio_to_chance": (ident / chance) if chance > 0 else None}
    flag = {k: v for k, v in res["cells"].items()}
    h327 = all(flag["%s|%s" % (c, p)]["resolvable"] for c in ("Synergy",) for p in ("one_unseen", "cell_unseen")) \
        and not flag["Synergy|both_unseen"]["resolvable"]
    h328 = all(not v["resolvable"] for k, v in flag.items() if k.startswith("Synergy|"))
    res["decisions"] = {"H327_boolean_underpowered_only_in_both_unseen": bool(h327),
                        "H328_boolean_underpowered_everywhere": bool(h328)}
    res["limits"] = ["Two arms only; the random and permuted controls were established in R126.",
                     "Covers only this resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r131/PROTOCOL_E122.md",
                "research/2026-10-27-agent-cell-identifiability-r131/e131_matrix.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E131_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E131_rows.csv", index=False)

    print("%-22s %-6s %6s %8s %8s %8s  %-10s" % ("cell", "n", "chance", "identity", "room", "MDE80", "resolvable"))
    for k, e in res["cells"].items():
        print("%-22s %6d %8.4f %8.4f %+8.4f %8.4f  %s" % (
            k, e["n"], e["chance"], e["identity"], e["room"], e["mde_80pct"], e["resolvable"]))
        g2 = e["pathway_gain"]
        print("    pathway %+.4f [%+.4f,%+.4f]" % (g2["mean_diff"], g2["ci95"][0], g2["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
