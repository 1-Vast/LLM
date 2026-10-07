"""Mono-level baselines and action-comparison metrics on held-out cells (GDSC2 single-drug labels only).

File summary
- Path: research/astra/mono_pretraining_20261005/mono.py
- Purpose: stage S1 diagnostics that need no combination label. They ask whether context-dependent
  single-drug models carry *action-comparison* information for a new cell, against strong simple
  predictors, before anything is transferred to combinations.
- Core points:
  - Records are (cell, drug, y) with y the frozen mono target; every predictor is fitted on training
    cells only and scored on cells never seen (grouped by cell entity).
  - Metrics: (a) within-cell drug ranking (mean Spearman over held-out cells): which drug to apply;
    (b) per-drug cross-cell correlation (context dependence); (c) pooled RMSE for completeness only.
  - Baselines: global per-drug mean; lineage x drug mean shrunk to the drug mean; per-drug ridge on the
    14 context scores; lineage-mean + ridge on its residual; the pretrained rank-k head is compared by the
    caller.
- Interfaces: `Records`, `drug_mean`, `lineage_mean`, `ridge_per_drug`, `lineage_ridge`, `score`.
- Depends on: numpy, scipy.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata


@dataclass
class Records:
    cell: np.ndarray      # int row index into the cell tables
    drug: np.ndarray      # int
    y: np.ndarray         # float target
    z: np.ndarray         # cells x features (standardised on training cells)
    lineage: np.ndarray   # int per cell
    n_drugs: int


def _drug_means(tr: Records, k0: float = 0.0):
    s = np.bincount(tr.drug, weights=tr.y, minlength=tr.n_drugs)
    n = np.bincount(tr.drug, minlength=tr.n_drugs).astype(float)
    return s / np.maximum(n, 1)


def drug_mean(tr: Records, te: Records) -> np.ndarray:
    return _drug_means(tr)[te.drug]


def lineage_mean(tr: Records, te: Records, k0: float = 5.0) -> np.ndarray:
    base = _drug_means(tr)
    L = int(max(tr.lineage.max(), te.lineage.max())) + 1
    key = tr.lineage[tr.cell] * tr.n_drugs + tr.drug
    s = np.bincount(key, weights=tr.y - base[tr.drug], minlength=L * tr.n_drugs)
    n = np.bincount(key, minlength=L * tr.n_drugs).astype(float)
    shift = s / (n + k0)
    return base[te.drug] + shift[te.lineage[te.cell] * te.n_drugs + te.drug]


def ridge_per_drug(tr: Records, te: Records, alpha: float = 30.0, offset: np.ndarray | None = None) -> np.ndarray:
    """Per-drug ridge on the context scores (intercept free); `offset` = predictions to add back."""
    out = np.zeros(len(te.drug))
    f = tr.z.shape[1]
    for d in range(tr.n_drugs):
        m, mt = tr.drug == d, te.drug == d
        if not mt.any():
            continue
        if m.sum() < 5:
            out[mt] = tr.y[m].mean() if m.any() else 0.0
            continue
        X = tr.z[tr.cell[m]]
        mu = tr.y[m].mean()
        xm = X.mean(0)
        Xc = X - xm
        w = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(f), Xc.T @ (tr.y[m] - mu))
        out[mt] = mu + (te.z[te.cell[mt]] - xm) @ w
    return out


def lineage_ridge(tr: Records, te: Records, alpha: float = 30.0) -> np.ndarray:
    """Lineage-mean prediction plus per-drug ridge on the residual (context beyond lineage)."""
    base_tr = lineage_mean(tr, tr)
    tr2 = Records(tr.cell, tr.drug, tr.y - base_tr, tr.z, tr.lineage, tr.n_drugs)
    return lineage_mean(tr, te) + ridge_per_drug(tr2, te, alpha)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 4 or np.ptp(b) == 0:
        return np.nan                 # undefined truth
    if np.ptp(a) == 0:
        return 0.0                    # a constant prediction carries no ordering information
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def score(te: Records, pred: np.ndarray, min_drugs: int = 8, min_cells: int = 20) -> dict:
    """Held-out action-comparison metrics; NaN cells/drugs (constant or too few) are skipped and counted."""
    within, per_cell = [], {}
    for c in np.unique(te.cell):
        m = te.cell == c
        if m.sum() >= min_drugs:
            r = _spearman(pred[m], te.y[m])
            if np.isfinite(r):
                within.append(r)
                per_cell[int(c)] = r
    across = []
    for d in np.unique(te.drug):
        m = te.drug == d
        if m.sum() >= min_cells:
            r = _spearman(pred[m], te.y[m])
            if np.isfinite(r):
                across.append(r)
    return {"within_cell_spearman": float(np.mean(within)) if within else float("nan"),
            "n_cells": len(within), "per_drug_spearman": float(np.mean(across)) if across else float("nan"),
            "n_drugs": len(across), "rmse": float(np.sqrt(np.mean((pred - te.y) ** 2))),
            "per_cell": per_cell}
