"""E148: re-test C106 without dead features on either side.

C106 claimed the monotone decay is linear-model specific, on the strength of a tree that reached only
0.032 in the no-identity condition. R147 showed that tree carried drug identity codes which were all
the reserved code -1 on the evaluation rows - a dead feature. With the grouping alone the tree
reaches 0.1074. This recomputes both gains in one run with no dead features anywhere.

Pre-registered in PROTOCOL_E138.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r148"
REPEATS = 60
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261051
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]
CFG = dict(max_iter=200, learning_rate=0.08, max_depth=4, min_samples_leaf=40)


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


def fit_rho(Xtr, ytr, Xte, yte, seed):
    m = HistGradientBoostingRegressor(**CFG, early_stopping=False, random_state=seed)
    m.fit(Xtr, ytr)
    p = m.predict(Xte)
    return 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)


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
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(np.int32)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(np.int32)
    ap_code = pd.Categorical(g["ap"]).codes.astype(np.int32)
    lp_code = pd.Categorical(g["lp"]).codes.astype(np.int32)
    y = g["emax"].to_numpy(float)
    n_p = int(ap_code.max()) + 1
    cell_index = {}
    for i, c in enumerate(CELL):
        cell_index.setdefault(c, []).append(i)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        # condition A: key-level holdout, all drugs present in training
        te_idx = []
        for c, idxs in cell_index.items():
            idxs = np.array(idxs)
            perm = rng.permutation(len(idxs)); half = len(idxs) // 2
            te_idx.extend(idxs[perm[half:]].tolist())
        teA = np.array(sorted(te_idx)); trA = np.setdiff1d(np.arange(len(g)), teA)
        row = {"rep": rep}
        if len(trA) >= 20000 and len(teA) >= 5000:
            ya, yb = y[trA], y[teA]
            row["A_drug_only"] = fit_rho(np.column_stack([a_code, b_code])[trA], ya,
                                         np.column_stack([a_code, b_code])[teA], yb, SEED + rep)
            row["A_drug_path"] = fit_rho(np.column_stack([a_code, b_code, ap_code, lp_code])[trA], ya,
                                         np.column_stack([a_code, b_code, ap_code, lp_code])[teA], yb, SEED + rep)
        # condition B: drug holdout, both drugs unseen, NO drug identity features at all
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        teB = np.where(au & bu)[0]; trB = np.where((~au) & (~bu))[0]
        if len(trB) >= 15000 and len(teB) >= 150:
            yb_tr, yb_te = y[trB], y[teB]
            row["B_pathway_only"] = fit_rho(np.column_stack([ap_code, lp_code])[trB], yb_tr,
                                            np.column_stack([ap_code, lp_code])[teB], yb_te, SEED + rep)
            rg_a = rng.integers(0, n_p, size=len(g)).astype(np.int32)
            rg_b = rng.integers(0, n_p, size=len(g)).astype(np.int32)
            row["B_random_only"] = fit_rho(np.column_stack([rg_a, rg_b])[trB], yb_tr,
                                           np.column_stack([rg_a, rg_b])[teB], yb_te, SEED + rep)
        rows.append(row)

    r = pd.DataFrame(rows)
    ok = r.dropna(subset=["A_drug_only", "A_drug_path", "B_pathway_only"])
    gain_A = ok["A_drug_path"] - ok["A_drug_only"]
    gain_B = ok["B_pathway_only"] - 0.0          # a constant predictor has rank correlation zero
    res = {"kind": "re_test_of_C106_without_dead_features",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "seed": SEED,
                        "tree_config": CFG, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r)), "usable": int(len(ok))},
           "rho": {"A_drug_only": float(ok["A_drug_only"].mean()),
                   "A_drug_path": float(ok["A_drug_path"].mean()),
                   "B_pathway_only": float(ok["B_pathway_only"].mean()),
                   "B_random_only": float(ok["B_random_only"].mean())},
           "gains": {"gain_A": {"mean": float(gain_A.mean()),
                                "ci95": [float(np.quantile([np.mean(rng.choice(gain_A.to_numpy(), size=len(gain_A), replace=True))
                                                            for _ in range(N_BOOT)], 0.025)),
                                         float(np.quantile([np.mean(rng.choice(gain_A.to_numpy(), size=len(gain_A), replace=True))
                                                            for _ in range(N_BOOT)], 0.975))]},
                     "gain_B": {"mean": float(gain_B.mean())}},
           "gain_difference_AB": paired(gain_B, gain_A, 67001),
           "files": {}}
    gd = res["gain_difference_AB"]
    h362 = bool(gd["ci95"][0] > 0)
    res["decisions"] = {"gain_A_fully_informed": res["gains"]["gain_A"]["mean"],
                        "gain_B_identity_absent": res["gains"]["gain_B"]["mean"],
                        "gain_difference": gd["mean_diff"],
                        "H362_decay_holds_under_tree_too": h362,
                        "H363_decay_still_linear_only": not h362}
    res["decisions"]["verdict"] = (
        "with_dead_features_removed_the_decay_holds_under_the_tree_so_C106_is_withdrawn" if h362 else
        "even_without_dead_features_the_tree_shows_no_decay_so_C106_stands")
    res["limits"] = ["Sixty splits, one untuned tree configuration, integer coding.",
                     "Conditions A and B use different evaluation pools, so this compares gains rather than arms within one pool.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r148/PROTOCOL_E138.md",
                "research/2026-10-27-agent-cell-identifiability-r148/e148_retest_c106.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E148_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E148_rows.csv", index=False)

    print("rows=%d usable=%d" % (len(r), len(ok)))
    for k, v in res["rho"].items():
        print("  %-16s rho %+.4f" % (k, v))
    print("  gain_A (fully informed) %+.4f" % res["gains"]["gain_A"]["mean"])
    print("  gain_B (identity absent) %+.4f" % res["gains"]["gain_B"]["mean"])
    print("  difference B-A %+.4f [%+.4f,%+.4f]" % (gd["mean_diff"], gd["ci95"][0], gd["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
