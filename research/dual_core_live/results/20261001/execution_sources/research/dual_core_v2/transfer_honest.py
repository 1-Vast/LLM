"""Honest validation error of block 7's transfer models: the whole `fit_pair` procedure is left out, gamma included.

File summary
- Path: research/dual_core_v2/transfer_honest.py
- Purpose: repair the error estimate behind block 7's A2 "precision" weights. `transfer.fit_pair`
  fits gamma by least squares on inner out-of-fold ridge residuals and then scores `rrt_q` on those
  same residuals. Because gamma = 0 is feasible, that reported error can never exceed `ridge_st`'s:
  it is a training error for gamma, not a validation error for the residual model.
- Core points:
  - `honest_errors` wraps the complete procedure in one more cross-validation level (the smallest
    valid design): for each inner fold, `fit_pair` runs on the remaining folds only (selecting k,
    lambda and both gammas by its own inner CV there) and predicts the held-out inner fold. Units
    are never split. The outer test fold is never touched; callers pass outer-training rows only.
  - It returns per-arm mean squared error per gene for every A1 arm, plus the in-sample values
    `fit_pair` reports, so the optimism is measured on identical rows.
  - `k_grid` is an argument, so the rank-boundary question (L1000 fits at the grid maximum k = 32)
    is answered with training data only: the honest error of the complete procedure under the
    registered grid and under an extended one.
  - Inverse-error weights are called inverse-error weights. They are not calibrated precisions:
    errors of different prompts' transitions are correlated through shared references and targets.
- Interfaces: `honest_errors`, `ARMS`
- Depends on: research/dual_core/transfer.py
"""
from __future__ import annotations

import numpy as np

from research.dual_core import transfer as TF

ARMS = ("prompt_copy", "additive", "ridge_st", "rrt_const", "rrt_q")


def honest_errors(prompt, target, X, Y, q, units, *, k_grid=TF.K_GRID, lambda_grid=TF.LAMBDA_GRID) -> dict:
    """{'honest': {arm: mse}, 'in_sample': fit_pair's inner_mse, 'k': [...], 'rows': n} on the given rows."""
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    q = np.clip(np.nan_to_num(np.asarray(q, dtype=np.float64), nan=0.0), 0.0, 1.0)
    units = np.asarray([str(u) for u in units], dtype=object)
    full = TF.fit_pair(prompt, target, X, Y, q, units, k_grid=k_grid, lambda_grid=lambda_grid)
    folds = TF.inner_folds(units)
    sq = {a: 0.0 for a in ARMS}
    count, ks, gammas = 0, [], []
    for f in range(TF.INNER):
        tr, te = folds != f, folds == f
        if te.sum() == 0 or tr.sum() < 6:
            continue
        pm = TF.fit_pair(prompt, target, X[tr], Y[tr], q[tr], units[tr], k_grid=k_grid, lambda_grid=lambda_grid)
        ks.append(pm.k)
        gammas.append(pm.gamma0)
        for arm in ARMS:
            pred = np.stack([pm.predict(X[i], q[i], arm) for i in np.flatnonzero(te)])
            sq[arm] += float(((pred - Y[te]) ** 2).sum())
        count += int(te.sum())
    d = Y.shape[1]
    honest = {a: v / max(count * d, 1) for a, v in sq.items()} if count else {}
    return {"honest": honest, "in_sample": dict(full.inner_mse), "k_full": full.k, "k_inner": ks,
            "gamma0_full": full.gamma0, "gamma0_inner": gammas, "rows": int(len(X)), "scored_rows": count}
