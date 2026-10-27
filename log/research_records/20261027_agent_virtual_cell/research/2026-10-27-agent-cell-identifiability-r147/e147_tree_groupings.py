"""E147: is 'pathway beats target' model-dependent too?

R145 and R146 established the ranking under ridge, in distribution and under tissue holdout. But
C106 and C107 showed the two model families behave very differently on the same features, so the
ranking might be a ridge property.

Pre-registered in PROTOCOL_E137.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r147"
REPEATS = 60
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261050
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "ANCHOR_TARGET", "LIBRARY_TARGET", "SYNERGY_DELTA_EMAX"]
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(np.int32)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(np.int32)
    ap_code = pd.Categorical(g["ap"]).codes.astype(np.int32)
    lp_code = pd.Categorical(g["lp"]).codes.astype(np.int32)
    at_code = pd.Categorical(g["at"]).codes.astype(np.int32)
    lt_code = pd.Categorical(g["lt"]).codes.astype(np.int32)
    y = g["emax"].to_numpy(float)
    n_p, n_t = int(ap_code.max()) + 1, int(at_code.max()) + 1

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        te = np.where(au & bu)[0]; tr = np.where((~au) & (~bu))[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr, yte = y[tr], y[te]
        # Both drugs are unseen, so the drug identity codes carry no usable information and
        # integer coding would route them arbitrarily. The grouping codes, by contrast, do appear
        # in training via the other drugs of the same group, so the grouping is the only input.
        rg_a = rng.integers(0, n_p, size=len(g)).astype(np.int32)
        rg_b = rng.integers(0, n_p, size=len(g)).astype(np.int32)
        arms = {"pathway_only": np.column_stack([ap_code, lp_code]),
                "target_only": np.column_stack([at_code, lt_code]),
                "random_only": np.column_stack([rg_a, rg_b])}
        row = {"rep": rep, "n_eval": len(te)}
        for nm, XX in arms.items():
            m = HistGradientBoostingRegressor(**CFG, early_stopping=False, random_state=SEED + rep)
            m.fit(XX[tr], ytr)
            p = m.predict(XX[te])
            row[nm] = 0.0 if np.std(p) == 0 else float(spearmanr(p, yte).statistic)
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "pathway_versus_target_under_a_tree_with_the_grouping_as_the_only_input",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "seed": SEED,
                        "tree_config": CFG, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))},
           "arms": {nm: float(r[nm].mean()) for nm in
                    ("pathway_only", "target_only", "random_only")} if len(r) else {},
           "contrasts": {}, "files": {}}
    for key, a, b, off in (("pathway_minus_target", "pathway_only", "target_only", 66201),
                            ("pathway_minus_random", "pathway_only", "random_only", 66301),
                            ("target_minus_random", "target_only", "random_only", 66401)):
        c = paired(r[a], r[b], off)
        if c:
            c["mde_80pct"] = float(2.802 * c["sd"] / np.sqrt(len(r)))
        res["contrasts"][key] = c
    pt = res["contrasts"].get("pathway_minus_target") or {}
    under = bool(pt and pt["mde_80pct"] > abs(pt["mean_diff"]))
    h360 = bool(pt and pt["ci95"][0] > 0)
    res["decisions"] = {"pathway_minus_target": pt.get("mean_diff") if pt else None,
                        "underpowered": under,
                        "H360_ranking_robust_across_models": h360,
                        "H361_ranking_is_model_specific": bool(pt and pt["ci95"][0] <= 0)}
    res["decisions"]["verdict"] = (
        "UNDERPOWERED_under_the_tree" if under else
        "pathway_beats_target_under_a_tree_too_so_the_ranking_is_model_independent" if h360 else
        "the_ranking_is_model_specific_to_ridge")
    res["limits"] = ["Twenty splits, so power is lower than the ridge rounds.",
                     "One untuned tree configuration; a null here would need a capacity check before being believed.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r147/PROTOCOL_E137.md",
                "research/2026-10-27-agent-cell-identifiability-r147/e147_tree_groupings.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E147_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E147_rows.csv", index=False)

    print("rows=%d" % len(r))
    for nm, v in res["arms"].items():
        print("  %-14s rho %+.4f" % (nm, v))
    for k, c in res["contrasts"].items():
        if c:
            print("  %-24s %+.4f [%+.4f,%+.4f]  MDE80 %.4f" % (
                k, c["mean_diff"], c["ci95"][0], c["ci95"][1], c["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
