"""E080: nested validation of the triage rule - the threshold is selected INSIDE each
outer fold, so the reported precision and recall are not read off the same predictions
that chose the threshold.

Pre-registered in PROTOCOL_E077.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler

R = Path(r"D:\MAESTRO\research")
SRC = R / "2026-10-27-agent-cell-identifiability-r78" / "E078_cells.csv"
OUT = R / "2026-10-27-agent-cell-identifiability-r80"
SEED = 20261027

cd = pd.read_csv(SRC)
cd["never"] = cd["m_abs"].isna().astype(int)
X = np.hstack([cd[["B0", "base"]].to_numpy(float),
               pd.get_dummies(cd["tissue"], prefix="tis").astype(float).to_numpy()])
y = cd["never"].to_numpy(int)
n = len(y)


def fit_predict(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(Xtr), ytr)
    return m.predict_proba(sc.transform(Xte))[:, 1]


def choose_threshold(probs, labels, prec_floor=0.50, grid=40):
    """Among thresholds whose precision >= floor, take the one with best recall;
    if none qualifies, take the threshold with the best precision."""
    best = None
    best_prec_only = None
    for t in np.linspace(0.05, 0.95, grid):
        flag = probs >= t
        if flag.sum() == 0:
            continue
        prec = labels[flag].mean()
        rec = labels[flag].sum() / max(labels.sum(), 1)
        cand = {"threshold": float(t), "precision": float(prec), "recall": float(rec),
                "n_flagged": int(flag.sum())}
        if prec >= prec_floor and (best is None or rec > best["recall"]):
            best = cand
        if best_prec_only is None or prec > best_prec_only["precision"] or (
                abs(prec - best_prec_only["precision"]) < 1e-12 and rec > best_prec_only["recall"]):
            best_prec_only = cand
    return best if best is not None else best_prec_only


outer = []
for i in range(n):
    tr = np.array([j for j in range(n) if j != i])
    Xtr, ytr = X[tr], y[tr]
    # inner LOO on the training cells
    inner = np.zeros(len(tr))
    for a, b in LeaveOneOut().split(Xtr):
        inner[b] = fit_predict(Xtr[a], ytr[a], Xtr[b])
    chosen = choose_threshold(inner, ytr)
    if chosen is None:
        continue
    p_out = fit_predict(Xtr, ytr, X[i:i + 1])[0]
    outer.append({"cell": cd.iloc[i]["cell"], "y": int(y[i]), "p": float(p_out),
                  "threshold": chosen["threshold"], "flagged": bool(p_out >= chosen["threshold"]),
                  "inner_precision": chosen["precision"], "inner_recall": chosen["recall"]})

od = pd.DataFrame(outer)
flag = od["flagged"].to_numpy(bool)
yy = od["y"].to_numpy(int)
tp = int((flag & (yy == 1)).sum())
n_flag = int(flag.sum())
prec = float(tp / n_flag) if n_flag else float("nan")
rec = float(tp / yy.sum()) if yy.sum() else float("nan")

base_rate = float(yy.mean())
res = {
    "kind": "nested_validation_of_the_triage_rule",
    "n_outer_folds": int(len(od)), "n_positive": int(yy.sum()),
    "base_rate": base_rate,
    "n_flagged": n_flag, "flagged_frac": float(n_flag / len(od)),
    "true_positives": tp,
    "nested_precision": prec, "nested_recall": rec,
    "in_sample_comparison": {"R79_threshold_0.2_precision": 0.44, "R79_threshold_0.2_recall": 0.94},
    "thresholds_chosen": {
        "mean": float(od["threshold"].mean()), "median": float(od["threshold"].median()),
        "min": float(od["threshold"].min()), "max": float(od["threshold"].max())},
    "inner_expected": {"mean_inner_precision": float(od["inner_precision"].mean()),
                       "mean_inner_recall": float(od["inner_recall"].mean())},
}
h202 = bool(prec < 0.44)
h203 = bool(rec >= 0.70)
h204 = bool(prec >= 0.70)
res["decisions"] = {"H202_precision_drops_when_nested": h202,
                    "H203_still_useful_for_triage": h203,
                    "H204_usable_for_exclusion": h204}
res["decisions"]["verdict"] = (
    "rule_survives_nested_validation_for_exclusion" if h204 else
    "rule_survives_nested_validation_for_triage_only" if h203 else
    "rule_does_not_survive_nested_validation")
res["limits"] = [
    "32 positives across 123 cells makes every nested estimate noisy.",
    "The threshold rule was fixed before running (precision floor 0.50, then maximise recall).",
    "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
]
(OUT / "E080_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
od.to_csv(OUT / "E080_folds.csv", index=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
