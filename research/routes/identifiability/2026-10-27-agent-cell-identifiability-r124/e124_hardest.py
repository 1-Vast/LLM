"""E123: the full three-pool table on the dense criterion, 200 splits.

R122 showed the sparse boolean criterion cannot resolve this question (identity 1.30 percent with
a minimum detectable effect of 1.02 pp), so the R120/R121 sparse table is unusable. This rebuilds
the table on the dense criterion and asks whether the pathway increment is general or confined to
the both-unseen pool.

Pre-registered in PROTOCOL_E117.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r124"
LAMBDA = 1.0
K = 20
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261031
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
        tissue=("Tissue", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xtis = onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        cs = cells[:]; rng.shuffle(cs)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        heldc = set(cs[: max(3, int(round(HOLDOUT * len(cs))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        cu = np.array([c in heldc for c in CELL])
        tr = np.where((~cu) & (~au) & (~bu) & np.isfinite(y))[0]
        if len(tr) < 20000:
            continue
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_tissue": np.hstack([Xid, Xtis]),
                "plus_random": np.hstack([Xid, rng.normal(size=(len(g), Xpath.shape[1]))])}
        ytr = y[tr]
        scorers = {}
        for nm, XX in arms.items():
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            scorers[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
        pools = {"both_seen_cell": np.where(au & bu & (~cu))[0],
                 "both_unseen_cell": np.where(au & bu & cu)[0]}
        for pname, pool in pools.items():
            pool = pool[np.isfinite(y[pool])]
            if len(pool) < 80:
                continue
            perm = rng.permutation(len(pool)); half = len(pool) // 2
            pe = pool[perm[half:]]
            if len(pe) < 60:
                continue
            yp = y[pe]
            hit = (yp >= np.quantile(yp, 0.75)).astype(float)
            row = {"rep": rep, "pool": pname, "n_eval": len(pe)}
            for nm, (f, XX) in scorers.items():
                row[nm] = float(hit[np.argsort(-f(XX[pe]))[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "hardest_cell_both_drugs_and_cell_unseen",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)),
                     "identity_dims": int(Xid.shape[1]), "pathway_dims": int(Xpath.shape[1])},
           "by_pool": {}, "files": {}}

    for pname in ("both_seen_cell", "both_unseen_cell"):
        sub = r[r.pool == pname].set_index("rep")
        if len(sub) < 10:
            continue
        e = {"n": int(len(sub)),
             **{nm: float(sub[nm].mean()) for nm in ("identity", "plus_pathway", "plus_tissue", "plus_random")},
             "pathway_minus_identity": paired(sub["plus_pathway"], sub["identity"], 50001 + len(pname)),
             "tissue_minus_identity": paired(sub["plus_tissue"], sub["identity"], 50101 + len(pname)),
             "random_minus_identity": paired(sub["plus_random"], sub["identity"], 50201 + len(pname)),
             "room": float(sub["identity"].mean() - 0.25)}
        sd = e["pathway_minus_identity"]["sd"]
        e["mde_80pct"] = float(2.802 * sd / np.sqrt(max(len(sub), 2)))
        res["by_pool"][pname] = e

    hard = res["by_pool"].get("both_unseen_cell")
    seen = res["by_pool"].get("both_seen_cell")
    h309 = bool(hard and hard["pathway_minus_identity"]["ci95"][0] > 0)
    underpowered = bool(hard and hard["mde_80pct"] > max(abs(hard["pathway_minus_identity"]["mean_diff"]), 1e-9))
    res["decisions"] = {
        "H309_increment_survives_the_hardest_cell": h309,
        "H310_increment_disappears_when_cell_unseen": bool(
            (not h309) and seen and seen["pathway_minus_identity"]["ci95"][0] > 0),
        "hardest_cell_underpowered": underpowered,
        "hardest_mde_pct": hard["mde_80pct"] if hard else None,
        "hardest_observed_gain": hard["pathway_minus_identity"]["mean_diff"] if hard else None}
    res["decisions"]["verdict"] = (
        "UNDERPOWERED_cannot_judge_the_hardest_cell" if underpowered else
        "pathway_increment_survives_both_drugs_and_cell_unseen" if h309 else
        "pathway_increment_does_not_survive_an_unseen_cell")
    res["limits"] = [
        "Dense criterion only; nothing here speaks to the sparse flag.",
        "The both_unseen pool has the fewest keys.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r123/PROTOCOL_E117.md",
                "research/2026-10-27-agent-cell-identifiability-r123/e124_hardest.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E124_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E124_rows.csv", index=False)

    print("rows=%d repeats=%d" % (len(r), REPEATS))
    for pname, e in res["by_pool"].items():
        a = e["pathway_minus_identity"]; b = e["tissue_minus_identity"]; c = e["random_minus_identity"]
        print(" [%-12s] n=%3d id %.4f +path %.4f +tis %.4f +rand %.4f | room %+.4f | MDE80 %.4f" % (
            pname, e["n"], e["identity"], e["plus_pathway"], e["plus_tissue"], e["plus_random"],
            e["room"], e["mde_80pct"]))
        print("      path-id %+.4f [%+.4f,%+.4f] | tis-id %+.4f [%+.4f,%+.4f] | rand-id %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1],
            c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
