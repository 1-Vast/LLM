"""E137: is the perfect redundancy of the coarsening an artefact of the linear model?

R136 found identity and identity+pathway give numerically identical ridge predictions, because the
pathway is a deterministic function of the drug. But that was ridge with one-hot encoding. A tree
can use a coarser feature as a lower-cardinality split, which may act as regularisation, so the
zero may be model-specific.

Pre-registered in PROTOCOL_E127.md.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r137"
REPEATS = 30
N_BOOT = 2000
SEED = 20261040
LAMBDA = 1.0
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


def ridge_fit_predict(Xtr, ytr, Xte, lam=LAMBDA):
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

    a_idx = pd.Categorical(g["a"]).codes.astype(np.int32)
    b_idx = pd.Categorical(g["b"]).codes.astype(np.int32)
    ap_idx = pd.Categorical(g["ap"]).codes.astype(np.int32)
    lp_idx = pd.Categorical(g["lp"]).codes.astype(np.int32)
    codes = {"identity": np.column_stack([a_idx, b_idx]),
             "both": np.column_stack([a_idx, b_idx, ap_idx, lp_idx])}
    drugs = sorted(set(g["a"]) | set(g["b"]))
    didx = {v: i for i, v in enumerate(drugs)}
    n = len(g)
    Xid_oh = np.zeros((n, 2 * len(drugs)))
    for i, (x, z) in enumerate(zip(g["a"], g["b"])):
        Xid_oh[i, didx[x]] = 1.0
        Xid_oh[i, len(drugs) + didx[z]] = 1.0
    ap_lv = {v: i for i, v in enumerate(sorted(g["ap"].unique()))}
    lp_lv = {v: i for i, v in enumerate(sorted(g["lp"].unique()))}
    Xpa_oh = np.zeros((n, len(ap_lv) + len(lp_lv)))
    for i, (x, z) in enumerate(zip(g["ap"], g["lp"])):
        Xpa_oh[i, ap_lv[x]] = 1.0
        Xpa_oh[i, len(ap_lv) + lp_lv[z]] = 1.0
    Xboth_oh = np.hstack([Xid_oh, Xpa_oh])

    y = g["emax"].to_numpy(float)
    cell_index = {}
    for i, c in enumerate(g["cell"]):
        cell_index.setdefault(c, []).append(i)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        te_idx = []
        for c, idxs in cell_index.items():
            idxs = np.array(idxs)
            perm = rng.permutation(len(idxs)); half = len(idxs) // 2
            te_idx.extend(idxs[perm[half:]].tolist())
        te = np.array(sorted(te_idx)); tr = np.setdiff1d(np.arange(n), te)
        if len(tr) < 20000 or len(te) < 5000:
            continue
        ytr, yte = y[tr], y[te]
        row = {"rep": rep, "n_eval": len(te)}
        # ridge, one-hot (reproduce R136)
        row["ridge_oh_identity"] = float(spearmanr(ridge_fit_predict(Xid_oh[tr], ytr, Xid_oh[te]), yte).statistic)
        row["ridge_oh_both"] = float(spearmanr(ridge_fit_predict(Xboth_oh[tr], ytr, Xboth_oh[te]), yte).statistic)
        # boosting, integer codes
        for arm in ("identity", "both"):
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08,
                                              max_depth=4, min_samples_leaf=40,
                                              early_stopping=False, random_state=SEED + rep)
            m.fit(codes[arm][tr], ytr)
            row["boost_" + arm] = float(spearmanr(m.predict(codes[arm][te]), yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "is_the_redundancy_a_linear_model_artefact",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "seed": SEED, "n_boot": N_BOOT},
           "audit": {"keys": n, "rows": len(r)}, "by_model": {}, "files": {}}
    pairs = [("ridge_oh", "ridge_oh_identity", "ridge_oh_both"),
             ("boost", "boost_identity", "boost_both")]
    for name, a, b in pairs:
        res["by_model"][name] = {
            "identity_rho": float(r[a].mean()), "both_rho": float(r[b].mean()),
            "gain": paired(r[b], r[a], 58001 + len(name))}
        sd = res["by_model"][name]["gain"]["sd"]
        res["by_model"][name]["mde_80pct"] = float(2.802 * sd / np.sqrt(len(r)))
    bg = res["by_model"]["boost"]["gain"]
    res["decisions"] = {"H340_redundancy_is_model_specific": bool(bg["ci95"][0] > 0),
                        "H341_redundancy_is_feature_algebra": bool(bg["ci95"][0] <= 0)}
    res["decisions"]["verdict"] = (
        "the_coarsening_helps_boosting_so_the_zero_was_model_specific" if bg["ci95"][0] > 0 else
        "the_coarsening_is_redundant_even_for_boosting_so_it_is_feature_algebra")
    res["limits"] = ["Integer coding suits trees and not linear models, so the ridge rows are references only.",
                     "Only thirty splits, so power is lower than in the ridge rounds.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r137/PROTOCOL_E127.md",
                "research/2026-10-27-agent-cell-identifiability-r137/e137_nonlinear.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E137_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E137_rows.csv", index=False)

    print("rows=%d" % len(r))
    for name, e in res["by_model"].items():
        g2 = e["gain"]
        print(" [%-9s] identity %.4f  both %.4f  gain %+.4f [%+.4f,%+.4f]  MDE80 %.4f" % (
            name, e["identity_rho"], e["both_rho"], g2["mean_diff"], g2["ci95"][0], g2["ci95"][1], e["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
