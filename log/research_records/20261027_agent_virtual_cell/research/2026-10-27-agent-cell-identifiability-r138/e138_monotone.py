"""E138: under boosting, does the coarsening gain also grow as identity is removed?

R133-R136 established a monotone decay for linear models, with a hard zero at full information.
R137 showed the fully-informed end is not zero for boosting but +0.0152. This asks whether the
monotonicity survives the model change, which would give one unified statement.

Pre-registered in PROTOCOL_E128.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r138"
REPEATS = 30
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261041
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
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(np.int32)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(np.int32)
    ap_code = pd.Categorical(g["ap"]).codes.astype(np.int32)
    lp_code = pd.Categorical(g["lp"]).codes.astype(np.int32)
    y = g["emax"].to_numpy(float)

    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        # --- condition A: full identity (key-level holdout) ---
        te_idx = []
        for c, idxs in cell_index.items():
            idxs = np.array(idxs)
            perm = rng.permutation(len(idxs)); half = len(idxs) // 2
            te_idx.extend(idxs[perm[half:]].tolist())
        teA = np.array(sorted(te_idx)); trA = np.setdiff1d(np.arange(len(g)), teA)
        XA_id = np.column_stack([a_code, b_code])
        XA_both = np.column_stack([a_code, b_code, ap_code, lp_code])
        # --- condition B: no identity (drug-level holdout) ---
        ds = drugs[:]; rng.shuffle(ds)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        teB = np.where(au & bu)[0]
        trB = np.where((~au) & (~bu))[0]
        XB_id = np.column_stack([np.where(au, -1, a_code), np.where(bu, -1, b_code)])
        XB_both = np.column_stack([np.where(au, -1, a_code), np.where(bu, -1, b_code), ap_code, lp_code])

        row = {"rep": rep}
        for cond, tr, te, Xid, Xboth in (("full_identity", trA, teA, XA_id, XA_both),
                                          ("no_identity", trB, teB, XB_id, XB_both)):
            if len(tr) < 15000 or len(te) < 150:
                row[cond + "_identity"] = np.nan
                row[cond + "_both"] = np.nan
                continue
            ytr, yte = y[tr], y[te]
            for nm, XX in (("identity", Xid), ("both", Xboth)):
                m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=4,
                                                  min_samples_leaf=40, early_stopping=False,
                                                  random_state=SEED + rep)
                m.fit(XX[tr], ytr)
                pred = m.predict(XX[te])
                # a constant scorer carries no rank information, so its correlation is zero by
                # convention rather than undefined. This matters in no_identity, where every
                # evaluation row carries the reserved code and the identity arm is necessarily flat.
                row["%s_%s" % (cond, nm)] = (0.0 if np.std(pred) == 0
                                             else float(spearmanr(pred, yte).statistic))
                row["%s_%s_const" % (cond, nm)] = bool(np.std(pred) == 0)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "does_the_boosting_gain_also_grow_as_identity_is_removed",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "seed": SEED, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_condition": {}, "files": {}}
    for cond in ("full_identity", "no_identity"):
        res["by_condition"][cond] = {
            "identity_rho": float(r[cond + "_identity"].mean()),
            "both_rho": float(r[cond + "_both"].mean()),
            "gain": paired(r[cond + "_both"], r[cond + "_identity"], 59001 + len(cond))}
    diff = paired(r["no_identity_both"] - r["no_identity_identity"],
                  r["full_identity_both"] - r["full_identity_identity"], 59501)
    res["gain_difference"] = diff
    fi = res["by_condition"]["full_identity"]["gain"]; ni = res["by_condition"]["no_identity"]["gain"]
    h342 = bool(diff and diff["ci95"][0] > 0)
    res["decisions"] = {"H342_unified_monotone_under_boosting": h342,
                        "H343_not_unified": not h342}
    res["decisions"]["verdict"] = (
        "the_coarsening_gain_grows_as_identity_is_removed_under_boosting_too" if h342 else
        "boosting_does_not_show_the_same_monotonicity")
    res["limits"] = ["A reserved code of -1 is one way to represent a drug with no identity information, not the only one.",
                     "Thirty splits.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r138/PROTOCOL_E128.md",
                "research/2026-10-27-agent-cell-identifiability-r138/e138_monotone.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E138_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E138_rows.csv", index=False)

    print("rows=%d" % len(r))
    for cond, e in res["by_condition"].items():
        g2 = e["gain"]
        print(" [%-14s] identity %.4f  both %.4f  gain %+.4f [%+.4f,%+.4f]" % (
            cond, e["identity_rho"], e["both_rho"], g2["mean_diff"], g2["ci95"][0], g2["ci95"][1]))
    if diff:
        print(" gain difference (no_identity - full): %+.4f [%+.4f,%+.4f]" % (
            diff["mean_diff"], diff["ci95"][0], diff["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
