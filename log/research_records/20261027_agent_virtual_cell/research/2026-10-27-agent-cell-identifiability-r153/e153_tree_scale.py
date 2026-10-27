"""E153: is a gradient-boosted tree also invariant to uniform rescaling of one block?

R152 showed a standardising linear model is exactly invariant. The theoretical expectation for a tree
is the same, since rescaling preserves ordering and HistGradientBoosting bins by quantile. This tests
it, so that the SCALE_SHRUNK note is either deleted or kept with a stated condition.

Pre-registered in PROTOCOL_E143.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r153"
SEED = 20261055
SCALES = (1.0, 0.5, 0.1, 0.01, 0.001)
CFG = dict(max_iter=200, learning_rate=0.08, max_depth=4, min_samples_leaf=40)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False,
                    usecols=["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY",
                             "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"])
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    a_code = pd.Categorical(g["a"], categories=drugs).codes.astype(float)
    b_code = pd.Categorical(g["b"], categories=drugs).codes.astype(float)
    ap_code = pd.Categorical(g["ap"]).codes.astype(float)
    lp_code = pd.Categorical(g["lp"]).codes.astype(float)
    base_id = np.column_stack([a_code, b_code])
    path = np.column_stack([ap_code, lp_code])
    X = np.hstack([base_id, path])
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(g)); cut = int(0.8 * len(g))
    tr, te = idx[:cut], idx[cut:]

    rows = {}
    ref_pred = None
    for s in SCALES:
        X2 = X.copy()
        X2[:, base_id.shape[1]:] = X2[:, base_id.shape[1]:] * s
        m = HistGradientBoostingRegressor(**CFG, early_stopping=False, random_state=SEED)
        m.fit(X2[tr], y[tr])
        p = m.predict(X2[te])
        if ref_pred is None:
            ref_pred = p
            rows["%.3f" % s] = {"max_abs_delta": 0.0, "rho": float(spearmanr(p, y[te]).statistic),
                                "rho_delta": 0.0}
        else:
            rows["%.3f" % s] = {"max_abs_delta": float(np.max(np.abs(p - ref_pred))),
                                "rho": float(spearmanr(p, y[te]).statistic),
                                "rho_delta": float(spearmanr(p, y[te]).statistic
                                                   - spearmanr(ref_pred, y[te]).statistic)}
    h372 = all(v["max_abs_delta"] < 1e-9 and abs(v["rho_delta"]) < 1e-6
               for k, v in rows.items() if float(k) < 1.0)
    res = {"kind": "is_a_tree_invariant_to_uniform_rescaling_of_one_block",
           "input_sha256": sha256(ORIG),
           "settings": {"scales": list(SCALES), "seed": SEED, "tree_config": CFG},
           "audit": {"keys": int(len(g)), "n_eval": int(len(te))},
           "results": rows,
           "decisions": {"H372_tree_is_also_invariant": bool(h372),
                         "H373_tree_changes": not h372},
           "decisions_verdict": ("the_tree_is_also_invariant_so_the_scale_note_can_be_removed"
                                 if h372 else "the_tree_reacts_to_rescaling_so_the_note_stays_as_an_option"),
           "limits": ["One tree configuration and integer coding.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r153/PROTOCOL_E143.md",
                "research/2026-10-27-agent-cell-identifiability-r153/e153_tree_scale.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E153_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    for k, v in rows.items():
        print("  scale %-7s max|delta| %.3e  rho %+.6f  rho_delta %+.2e" % (
            k, v["max_abs_delta"], v["rho"], v["rho_delta"]))
    print("H372 (tree invariant):", h372)


if __name__ == "__main__":
    main()
