"""E126: the permutation test the strongest claim has not had.

R122-R125 established that the pathway annotation adds 4.7 to 8.6 pp when both drugs are unseen.
The random-block control rules out capacity, but white noise does not preserve the block's shape.
This permutes the drug-to-pathway mapping instead: the level distribution and block geometry stay,
only the assignment breaks.

Pre-registered in PROTOCOL_E119.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r126"
LAMBDA = 1.0
K = 20
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261033
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
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    ap_lv = sorted(g["ap"].unique()); lp_lv = sorted(g["lp"].unique())
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), ap_lv), onehot(g["lp"].to_numpy(), lp_lv)])
    y = g["emax"].to_numpy(float)

    # drug -> pathway map, for permutation
    amap = g.groupby("a")["ap"].first().to_dict()
    bmap = g.groupby("b")["lp"].first().to_dict()

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
        # permuted drug -> pathway assignment (values shuffled among compounds)
        av = [amap.get(x, "NA") for x in drugs]
        bv = [bmap.get(z, "NA") for z in drugs]
        rng.shuffle(av); rng.shuffle(bv)
        amap_p = dict(zip(drugs, av)); bmap_p = dict(zip(drugs, bv))
        ap_p = np.array([amap_p.get(x, "NA") for x in A]); lp_p = np.array([bmap_p.get(z, "NA") for z in B])
        Xperm = np.hstack([onehot(ap_p, sorted(set(ap_p) | set(ap_lv))), onehot(lp_p, sorted(set(lp_p) | set(lp_lv)))])

        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_permuted": np.hstack([Xid, Xperm]),
                "plus_random": np.hstack([Xid, rng.normal(size=(len(g), Xpath.shape[1]))])}
        ytr = y[tr]
        scorers = {}
        for nm, XX in arms.items():
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            scorers[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
        pools = {"seen_cell": np.where(au & bu & (~cu))[0],
                 "unseen_cell": np.where(au & bu & cu)[0]}
        for pname, pool in pools.items():
            pool = pool[np.isfinite(y[pool])]
            if len(pool) < 60:
                continue
            perm = rng.permutation(len(pool)); half = len(pool) // 2
            pe = pool[perm[half:]]
            if len(pe) < 50:
                continue
            yp = y[pe]
            hit = (yp >= np.quantile(yp, 0.75)).astype(float)
            row = {"rep": rep, "pool": pname, "n_eval": len(pe)}
            for nm, (f, XX) in scorers.items():
                row[nm] = float(hit[np.argsort(-f(XX[pe]))[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "permutation_test_of_the_pathway_mapping",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)),
                     "identity_dims": int(Xid.shape[1]), "pathway_dims": int(Xpath.shape[1])},
           "by_pool": {}, "files": {}}

    for pname in ("seen_cell", "unseen_cell"):
        sub = r[r.pool == pname].set_index("rep")
        if len(sub) < 10:
            continue
        e = {"n": int(len(sub)),
             **{nm: float(sub[nm].mean()) for nm in ("identity", "plus_pathway", "plus_permuted", "plus_random")},
             "pathway_minus_identity": paired(sub["plus_pathway"], sub["identity"], 52001 + len(pname)),
             "permuted_minus_identity": paired(sub["plus_permuted"], sub["identity"], 52101 + len(pname)),
             "random_minus_identity": paired(sub["plus_random"], sub["identity"], 52201 + len(pname)),
             "pathway_minus_permuted": paired(sub["plus_pathway"], sub["plus_permuted"], 52301 + len(pname))}
        res["by_pool"][pname] = e

    real_sig = [p for p, e in res["by_pool"].items() if e["pathway_minus_identity"]["ci95"][0] > 0]
    perm_sig = [p for p, e in res["by_pool"].items() if e["permuted_minus_identity"]["ci95"][0] > 0]
    res["decisions"] = {"real_significant_pools": real_sig, "permuted_significant_pools": perm_sig,
                        "H313_gain_from_the_real_mapping": bool(len(real_sig) >= 1 and len(perm_sig) == 0),
                        "H314_permuted_also_gains": bool(len(perm_sig) >= 1)}
    res["decisions"]["verdict"] = (
        "the_gain_requires_the_real_drug_pathway_mapping" if res["decisions"]["H313_gain_from_the_real_mapping"] else
        "a_permuted_block_also_gains_so_the_claim_must_be_downgraded" if res["decisions"]["H314_permuted_also_gains"] else
        "neither_clean")
    res["limits"] = [
        "Permutation preserves the marginal level distribution but not every structural property of the block.",
        "Dense criterion only.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r126/PROTOCOL_E119.md",
                "research/2026-10-27-agent-cell-identifiability-r126/e126_permutation.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E126_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E126_rows.csv", index=False)

    print("rows=%d repeats=%d" % (len(r), REPEATS))
    for pname, e in res["by_pool"].items():
        a = e["pathway_minus_identity"]; p2 = e["permuted_minus_identity"]; c = e["random_minus_identity"]
        d2 = e["pathway_minus_permuted"]
        print(" [%-12s] n=%3d id %.4f real %.4f perm %.4f rand %.4f" % (
            pname, e["n"], e["identity"], e["plus_pathway"], e["plus_permuted"], e["plus_random"]))
        print("      real-id %+.4f [%+.4f,%+.4f] | perm-id %+.4f [%+.4f,%+.4f] | rand-id %+.4f [%+.4f,%+.4f] | real-perm %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], p2["mean_diff"], p2["ci95"][0], p2["ci95"][1],
            c["mean_diff"], c["ci95"][0], c["ci95"][1], d2["mean_diff"], d2["ci95"][0], d2["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
