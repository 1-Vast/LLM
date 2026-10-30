"""E139: give the tree a fair chance before calling the substitution effect linear-only.

R138 used untuned hyperparameters and integer-coded categoricals. This sweeps capacity and adds a
category-aware fit, so that "the tree extracts less" is either supported properly or withdrawn.

Pre-registered in PROTOCOL_E129.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r139"
REPEATS = 20
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261042
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]
CONFIGS = {
    "base": dict(max_iter=200, learning_rate=0.08, max_depth=4, min_samples_leaf=40),
    "strong": dict(max_iter=400, learning_rate=0.05, max_depth=6, min_samples_leaf=10),
    "categorical": dict(max_iter=300, learning_rate=0.06, max_depth=6, min_samples_leaf=20),
}


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
    return {"n": int(m), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def rank_of(pred, y):
    return 0.0 if np.std(pred) == 0 else float(spearmanr(pred, y).statistic)


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
    drugs = sorted(set(A) | set(B)); unseen_code = len(drugs)
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(np.int32)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(np.int32)
    ap_code = pd.Categorical(g["ap"]).codes.astype(np.int32)
    lp_code = pd.Categorical(g["lp"]).codes.astype(np.int32)
    n_ap = int(ap_code.max()) + 1
    lp_code = lp_code + n_ap
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
            perm = rng.permutation(len(idxs)); half = len(idxs) // 2
            te_idx.extend(idxs[perm[half:]].tolist())
        teA = np.array(sorted(te_idx)); trA = np.setdiff1d(np.arange(len(g)), teA)
        ds = drugs[:]; rng.shuffle(ds)
        heldd = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in heldd for x in A]); bu = np.array([z in heldd for z in B])
        teB = np.where(au & bu)[0]; trB = np.where((~au) & (~bu))[0]

        feats = {
            "full_identity": (trA, teA,
                              np.column_stack([a_code, b_code]),
                              np.column_stack([a_code, b_code, ap_code, lp_code])),
            "no_identity": (trB, teB,
                            np.column_stack([np.where(au, unseen_code, a_code),
                                             np.where(bu, unseen_code, b_code)]),
                            np.column_stack([np.where(au, unseen_code, a_code),
                                             np.where(bu, unseen_code, b_code), ap_code, lp_code])),
        }
        for cfg_name, cfg in CONFIGS.items():
            for cond, (tr, te, Xid, Xboth) in feats.items():
                if len(tr) < 15000 or len(te) < 150:
                    continue
                ytr, yte = y[tr], y[te]
                for arm, XX in (("identity", Xid), ("both", Xboth)):
                    kw = dict(cfg, early_stopping=False, random_state=SEED + rep)
                    if cfg_name == "categorical":
                        mask = np.zeros(XX.shape[1], dtype=bool)
                        mask[:2] = True  # drug codes are categorical
                        kw["categorical_features"] = mask
                    m = HistGradientBoostingRegressor(**kw)
                    m.fit(XX[tr], ytr)
                    rows.append({"rep": rep, "config": cfg_name, "condition": cond, "arm": arm,
                                 "rho": rank_of(m.predict(XX[te]), yte)})

    r = pd.DataFrame(rows)
    res = {"kind": "fair_chance_for_the_tree",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "seed": SEED,
                        "configs": {k: v for k, v in CONFIGS.items()}},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_config": {}, "files": {}}
    for cfg_name in CONFIGS:
        res["by_config"][cfg_name] = {}
        for cond in ("full_identity", "no_identity"):
            sub = r[(r.config == cfg_name) & (r.condition == cond)]
            piv = sub.pivot_table(index="rep", columns="arm", values="rho")
            if len(piv) < 3:
                continue
            res["by_config"][cfg_name][cond] = {
                "n": int(len(piv)),
                "identity_rho": float(piv["identity"].mean()),
                "both_rho": float(piv["both"].mean()),
                "gain": paired(piv["both"], piv["identity"], 60001 + len(cfg_name) + len(cond))}
        if "full_identity" in res["by_config"][cfg_name] and "no_identity" in res["by_config"][cfg_name]:
            pv = {}
            for cond in ("full_identity", "no_identity"):
                s2 = r[(r.config == cfg_name) & (r.condition == cond)].pivot_table(
                    index="rep", columns="arm", values="rho")
                pv[cond] = s2["both"] - s2["identity"]
            res["by_config"][cfg_name]["gain_difference"] = paired(pv["no_identity"],
                                                                   pv["full_identity"], 61001)

    diffs = {c: res["by_config"][c].get("gain_difference") for c in CONFIGS}
    h344 = any(d and d["ci95"][0] > 0 for d in diffs.values())
    res["decisions"] = {"gain_differences": {c: (d["mean_diff"], d["ci95"]) if d else None
                                             for c, d in diffs.items()},
                        "H344_substitution_appears_when_fair": h344,
                        "H345_still_no_substitution": not h344}
    res["decisions"]["verdict"] = (
        "with_a_fair_tree_the_substitution_effect_appears" if h344 else
        "even_a_fair_tree_shows_no_substitution_so_C106_is_hardened")
    res["limits"] = ["Twenty splits, so power is limited.",
                     "The reserved category id is one encoding of a missing identity.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r139/PROTOCOL_E129.md",
                "research/2026-10-27-agent-cell-identifiability-r139/e139_fair_tree.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E139_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E139_rows.csv", index=False)

    print("rows=%d" % len(r))
    for cfg_name, e in res["by_config"].items():
        for cond in ("full_identity", "no_identity"):
            if cond in e:
                g2 = e[cond]["gain"]
                print(" [%-12s %-14s] identity %.4f  both %.4f  gain %+.4f [%+.4f,%+.4f]" % (
                    cfg_name, cond, e[cond]["identity_rho"], e[cond]["both_rho"],
                    g2["mean_diff"], g2["ci95"][0], g2["ci95"][1]))
        d2 = e.get("gain_difference")
        if d2:
            print("      gain difference (absent - full): %+.4f [%+.4f,%+.4f]" % (
                d2["mean_diff"], d2["ci95"][0], d2["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
