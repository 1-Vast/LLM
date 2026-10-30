"""E079: can a three-feature advance model reach AUC 0.65 for "never benefits from personal data"?

Leave-one-cell-out logistic regression on (B0, base, tissue). Pre-registered in PROTOCOL_E076.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler

R = Path(r"D:\MAESTRO\research")
SRC = R / "2026-10-27-agent-cell-identifiability-r78" / "E078_cells.csv"
OUT = R / "2026-10-27-agent-cell-identifiability-r79"
SEED = 20261027

cd = pd.read_csv(SRC)
cd["never"] = cd["m_abs"].isna().astype(int)

def build(features):
    parts = []
    for f in features:
        if f == "tissue":
            d = pd.get_dummies(cd["tissue"], prefix="tis").astype(float)
            parts.append(d.to_numpy())
        else:
            parts.append(cd[[f]].to_numpy(float))
    return np.hstack(parts)

y = cd["never"].to_numpy(int)
loo = LeaveOneOut()

def loo_auc(X):
    pred = np.zeros(len(y))
    for tr, te in loo.split(X):
        sc = StandardScaler().fit(X[tr])
        m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
        pred[te] = m.predict_proba(sc.transform(X[te]))[:, 1]
    return roc_auc_score(y, pred), pred

X3 = build(["B0", "base", "tissue"])
X1 = build(["B0"])
a3, p3 = loo_auc(X3)
a1, p1 = loo_auc(X1)

rng = np.random.default_rng(SEED)
def boot_auc(pred):
    vals = []
    for _ in range(2000):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        vals.append(roc_auc_score(y[idx], pred[idx]))
    return [float(np.quantile(vals, .025)), float(np.quantile(vals, .975))]

def boot_diff(pa, pb):
    vals = []
    for _ in range(2000):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        vals.append(roc_auc_score(y[idx], pa[idx]) - roc_auc_score(y[idx], pb[idx]))
    return float(np.mean(vals)), [float(np.quantile(vals, .025)), float(np.quantile(vals, .975))]

res = {
    "kind": "three_feature_advance_model_for_never_benefiting_cells",
    "n_cells": int(len(cd)), "n_never": int(y.sum()),
    "features": ["B0", "base", "tissue"],
    "loo_auc_three_feature": float(a3), "ci_three": boot_auc(p3),
    "loo_auc_B0_only": float(a1), "ci_B0": boot_auc(p1),
    "diff_mean_ci": boot_diff(p3, p1),
    "tissue_levels": sorted(cd["tissue"].unique().tolist()),
}
d_mean, d_ci = res["diff_mean_ci"]
h200 = bool(a3 >= 0.65)
h201 = bool(a3 > a1 and d_ci[0] > 0)
res["decisions"] = {"H200_three_feature_reaches_065": h200,
                    "H201_beats_B0_alone": h201,
                    "verdict": ("advance_rule_is_usable" if h200 and h201 else
                                "advance_identification_still_not_usable")}
res["limits"] = [
    "32 positives in 123 cells makes the AUC variance large; bootstrap CIs are reported.",
    "No feature search was performed, to avoid overfitting the 32 positives.",
    "Tissue has only three levels, so it contributes at most a small offset.",
    "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
]
(OUT / "E079_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(res, indent=2, ensure_ascii=False))
