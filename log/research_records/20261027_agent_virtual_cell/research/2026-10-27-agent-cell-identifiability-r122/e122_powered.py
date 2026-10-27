"""E122: power up the one surviving cell - both_unseen by the dense criterion.

R120 gave pathway +8.58 pp (significant) and R121 +5.12 pp (not significant) on this cell. Same
sign twice, significant once. This round spends its whole budget on that cell with 200 splits.

Pre-registered in PROTOCOL_E115.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r122"
LAMBDA = 1.0
K = 20
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261029
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
        tissue=("Tissue", "first"), syn=("syn", "mean"), emax=("emax", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xtis = onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))
    ysyn = g["syn"].to_numpy(bool); yemax = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        pool = np.where(au & bu)[0]
        pool = pool[np.isfinite(yemax[pool])]
        if len(pool) < 60:
            continue
        perm = rng.permutation(len(pool)); half = len(pool) // 2
        # training set excludes held-out drugs entirely
        tr = np.where(~au & ~bu)[0]
        tr = tr[np.isfinite(yemax[tr])]
        if len(tr) < 20000:
            continue
        Xrand = np.hstack([Xid, rng.normal(size=(len(g), Xpath.shape[1]))])
        arms = {"identity": Xid, "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_tissue": np.hstack([Xid, Xtis]), "plus_random": Xrand}
        for crit, yt in (("dEMAX", yemax), ("Synergy", ysyn.astype(float))):
            ytr = yt[tr]
            scorers = {}
            for nm, XX in arms.items():
                Xt = XX[tr]
                mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
                Z = (Xt - mu) / sd
                w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
                scorers[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
            p_eval = pool[perm[half:]]
            if len(p_eval) < 40:
                continue
            yp = yt[p_eval]
            hit = (yp >= np.quantile(yp, 0.75)).astype(float) if crit == "dEMAX" else yp
            row = {"rep": rep, "criterion": crit, "n_eval": len(p_eval)}
            for nm, (f, XX) in scorers.items():
                row[nm] = float(hit[np.argsort(-f(XX[p_eval]))[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "powered_test_of_pathway_increment_on_both_unseen_dense_criterion",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)),
                     "identity_dims": int(Xid.shape[1]), "pathway_dims": int(Xpath.shape[1])},
           "by_criterion": {}, "files": {}}

    for crit in ("dEMAX", "Synergy"):
        sub = r[r.criterion == crit].set_index("rep")
        if len(sub) < 10:
            continue
        e = {"n": int(len(sub)),
             **{nm: float(sub[nm].mean()) for nm in ("identity", "plus_pathway", "plus_tissue", "plus_random")},
             "pathway_minus_identity": paired(sub["plus_pathway"], sub["identity"], 49001),
             "tissue_minus_identity": paired(sub["plus_tissue"], sub["identity"], 49101),
             "random_minus_identity": paired(sub["plus_random"], sub["identity"], 49201)}
        # effect size detectable at 80% power for a paired design
        sd = e["pathway_minus_identity"]["sd"]
        e["mde_80pct"] = float(2.802 * sd / np.sqrt(max(len(sub), 2)))
        res["by_criterion"][crit] = e

    de = res["by_criterion"].get("dEMAX", {})
    h303 = bool(de and de["pathway_minus_identity"]["ci95"][0] > 0)
    h304 = bool(h303 and de["tissue_minus_identity"]["ci95"][1] > 0)
    res["decisions"] = {"H303_pathway_adds_on_this_cell": h303,
                        "H304_pathway_adds_while_tissue_does_not": h304,
                        "H305_no_increment": not h303}
    res["decisions"]["verdict"] = (
        "pathway_adds_on_both_unseen_with_the_dense_criterion" if h303 else
        "no_increment_on_the_cell_that_looked_promising")
    res["limits"] = [
        "A single pool and a single dense criterion; nothing here transfers to other settings.",
        "The dense criterion is a quartile, not a clinical endpoint.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r122/PROTOCOL_E115.md",
                "research/2026-10-27-agent-cell-identifiability-r122/e122_powered.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E122_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E122_rows.csv", index=False)

    print("rows=%d repeats=%d" % (len(r), REPEATS))
    for crit, e in res["by_criterion"].items():
        a = e["pathway_minus_identity"]; b = e["tissue_minus_identity"]; c = e["random_minus_identity"]
        print(" [%s] n=%d id %.4f +path %.4f +tis %.4f +rand %.4f | MDE80 %.4f" % (
            crit, e["n"], e["identity"], e["plus_pathway"], e["plus_tissue"], e["plus_random"], e["mde_80pct"]))
        print("     path-id %+.4f [%+.4f,%+.4f] | tis-id %+.4f [%+.4f,%+.4f] | rand-id %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1],
            c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
