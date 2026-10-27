"""E154: does scaling only a subset of evaluation rows actually change predictions?

R152 and R153 showed uniform rescaling of a column is a no-op for both model families. But scaling
only part of a column breaks the within-column ordering, which is the shape a real unit-mixing accident
takes (some rows in micromolar, others in nanomolar). This tests whether that matters.

Pre-registered in PROTOCOL_E144.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r154"
SEED = 20261055
SCALES = (0.01, 0.1)
FRACS = (0.30,)
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


def ridge_fp(Xtr, ytr, Xte, lam=1.0):
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


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
    n_id = base_id.shape[1]

    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(g)); cut = int(0.8 * len(g))
    tr, te = idx[:cut], idx[cut:]

    ref = {}
    ref["ridge"] = ridge_fp(X[tr], y[tr], X[te])
    m = HistGradientBoostingRegressor(**CFG, early_stopping=False, random_state=SEED)
    m.fit(X[tr], y[tr]); ref["tree"] = m.predict(X[te])

    rows = {}
    for s in SCALES:
        for frac in FRACS:
            X2 = X.copy()
            rr = np.random.default_rng(SEED + int(s * 1000) + int(frac * 100))
            victims = rr.choice(len(te), size=int(frac * len(te)), replace=False)
            X2[np.ix_(te[victims], np.arange(n_id, X.shape[1]))] *= s
            p_r = ridge_fp(X2[tr], y[tr], X2[te])
            mm = HistGradientBoostingRegressor(**CFG, early_stopping=False, random_state=SEED)
            mm.fit(X2[tr], y[tr]); p_t = mm.predict(X2[te])
            key = "s%.2f_f%.2f" % (s, frac)
            rows[key] = {
                "ridge_max_abs_delta": float(np.max(np.abs(p_r - ref["ridge"]))),
                "tree_max_abs_delta": float(np.max(np.abs(p_t - ref["tree"]))),
                "ridge_rho_delta": float(spearmanr(p_r, y[te]).statistic - spearmanr(ref["ridge"], y[te]).statistic),
                "tree_rho_delta": float(spearmanr(p_t, y[te]).statistic - spearmanr(ref["tree"], y[te]).statistic)}
    h374 = all(v["ridge_max_abs_delta"] > 1e-3 and v["tree_max_abs_delta"] > 1e-3 for v in rows.values())
    res = {"kind": "does_partial_rescaling_of_a_column_change_predictions",
           "input_sha256": sha256(ORIG),
           "settings": {"scales": list(SCALES), "fractions": list(FRACS), "seed": SEED},
           "audit": {"keys": int(len(g)), "n_eval": int(len(te))},
           "results": rows,
           "decisions": {"H374_partial_rescaling_matters": bool(h374),
                         "H375_it_does_not": not h374},
           "decisions_verdict": ("partial_rescaling_does_change_predictions_so_it_is_a_real_data_integrity_failure"
                                 if h374 else "partial_rescaling_also_does_not_matter"),
           "limits": ["Only two scale factors and one fraction; only the evaluation side is scaled.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r154/PROTOCOL_E144.md",
                "research/2026-10-27-agent-cell-identifiability-r154/e154_partial_scale.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E154_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    for k, v in rows.items():
        print("  %-14s ridge max|d| %.3e (rho %+.4f)   tree max|d| %.3e (rho %+.4f)" % (
            k, v["ridge_max_abs_delta"], v["ridge_rho_delta"],
            v["tree_max_abs_delta"], v["tree_rho_delta"]))
    print("H374 (partial rescaling matters):", h374)


if __name__ == "__main__":
    main()
