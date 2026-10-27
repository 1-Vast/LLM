"""E136: the upper end of the decay curve, via a key-level holdout.

R135's one_seen_only pool was dead because defining it as 'both drugs seen and cell seen' made it a
subset of the training rows. The fix is to hold out keys rather than drugs or cells: every drug and
cell stays in training, so identity has full coverage, and only the specific combination is unseen.

Pre-registered in PROTOCOL_E126.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r136"
LAMBDA = 1.0
REPEATS = 200
N_BOOT = 2000
SEED = 20261039
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
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xpath])
    y = g["emax"].to_numpy(float)
    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        te_idx = []
        for c, idxs in cell_index.items():
            idxs = np.array(idxs)
            perm = rng.permutation(len(idxs))
            half = len(idxs) // 2
            te_idx.extend(idxs[perm[half:]].tolist())
        te = np.array(sorted(te_idx))
        tr = np.setdiff1d(np.arange(len(g)), te)
        if len(tr) < 20000 or len(te) < 5000:
            continue
        ytr = y[tr]
        sc = {}
        for nm, XX in (("identity", Xid), ("plus_pathway", Xboth)):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            sc[nm] = (lambda XXe, mu=mu, sd=sd, w=w, bb=ytr.mean(): bb + ((XXe - mu) / sd) @ w, XX)
        row = {"rep": rep, "n_eval": len(te)}
        preds = {}
        for nm, (f, XX) in sc.items():
            p = f(XX[te]); preds[nm] = p
            row[nm + "_global"] = float(spearmanr(p, y[te]).statistic) if np.std(p) > 0 else np.nan
        # within-cell rank correlation, averaged over cells with enough keys
        within = {nm: [] for nm in preds}
        y_te = y[te]
        cells_te = CELL[te]
        for c in np.unique(cells_te):
            m = cells_te == c
            if m.sum() < 30:
                continue
            yc = y_te[m]
            if np.std(yc) == 0:
                continue
            for nm, p in preds.items():
                pc = p[m]
                if np.std(pc) > 0:
                    within[nm].append(float(spearmanr(pc, yc).statistic))
        for nm in preds:
            row[nm + "_within"] = float(np.mean(within[nm])) if within[nm] else np.nan
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "upper_end_of_the_decay_curve_key_level_holdout",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "results": {}, "files": {}}
    for scale in ("global", "within"):
        a = r["identity_" + scale]; b = r["plus_pathway_" + scale]
        res["results"][scale] = {
            "identity_rho": float(a.mean()), "pathway_rho": float(b.mean()),
            "identity_nan": int(a.isna().sum()), "pathway_nan": int(b.isna().sum()),
            "gain": paired(b, a, 57001 + len(scale))}
    gl = res["results"]["global"]["gain"]
    res["decisions"] = {"H338_no_gain_when_identity_is_fully_supplied": bool(gl["ci95"][0] <= 0),
                        "H339_gain_persists": bool(gl["ci95"][0] > 0)}
    res["decisions"]["verdict"] = (
        "no_gain_when_identity_is_fully_supplied_so_the_decay_curve_is_complete" if gl["ci95"][0] <= 0 else
        "gain_persists_even_when_identity_is_fully_supplied")
    res["limits"] = ["Holding out keys still leaves the same combination observed in other cells.",
                     "Only this resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r136/PROTOCOL_E126.md",
                "research/2026-10-27-agent-cell-identifiability-r136/e136_upper_end.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E136_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E136_rows.csv", index=False)

    print("rows=%d" % len(r))
    for scale, e in res["results"].items():
        g2 = e["gain"]
        print(" [%s] identity %.4f  pathway %.4f  gain %+.4f [%+.4f,%+.4f]  nan id/path %d/%d" % (
            scale, e["identity_rho"], e["pathway_rho"], g2["mean_diff"], g2["ci95"][0], g2["ci95"][1],
            e["identity_nan"], e["pathway_nan"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
