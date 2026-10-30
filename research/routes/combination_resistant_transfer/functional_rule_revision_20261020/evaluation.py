"""Decision metrics, uncertainty, retention rule and verdict logic (all frozen before C is disclosed)."""
from __future__ import annotations

import numpy as np

K = 5


class Pool:
    """Held-out pool arranged as [pair, cell] matrices (every pair is eligible in every cell)."""

    def __init__(self, pair_ids, cells, rows_by_pair_cell, drug_pairs=None):
        self.pair_ids = np.asarray(pair_ids)          # ascending pair ids (tie-break order)
        self.cells = cells
        self.rows = rows_by_pair_cell                  # (n_pairs, n_cells) group row indices
        self.drug_pairs = drug_pairs                   # pair id -> (drug_i, drug_j)

    @classmethod
    def from_rows(cls, rows, g_pair, g_cell, n_cells, drug_pairs=None):
        pair_ids = np.unique(g_pair[rows])
        index = {int(p): k for k, p in enumerate(pair_ids)}
        mat = -np.ones((len(pair_ids), n_cells), dtype=np.int64)
        for r in rows:
            mat[index[int(g_pair[r])], g_cell[r]] = r
        return cls(pair_ids, n_cells, mat, drug_pairs)

    def matrix(self, values_by_group):
        out = np.full(self.rows.shape, np.nan)
        ok = self.rows >= 0
        out[ok] = values_by_group[self.rows[ok]]
        return out


def top_k(pred: np.ndarray, k: int = K):
    """Per-column top-k pair indices; ties go to the smaller row (= smaller pair id)."""
    order = np.argsort(-pred, axis=0, kind="stable")
    return order[:k]


def utility(pred: np.ndarray, truth: np.ndarray, subset=None, cells=None, k: int = K):
    """Macro-cell mean true activity of each cell's shortlist. NaN truth/pred cells are eligible only if finite."""
    if subset is not None:
        pred, truth = pred[subset], truth[subset]
    if cells is not None:
        pred, truth = pred[:, cells], truth[:, cells]
    sel = top_k(np.where(np.isfinite(pred) & np.isfinite(truth), pred, -np.inf), k)
    picked = np.take_along_axis(truth, sel, axis=0)
    return float(np.mean(np.mean(picked, axis=0)))


def oracle_utility(truth, subset=None, cells=None, k: int = K):
    return utility(truth, truth, subset, cells, k)


def paired_bootstrap(preds: dict, truth: np.ndarray, contrasts, n_boot=2000, seed=0, scheme="pair"):
    """Resample whole pairs (all their cells), reselect shortlists inside each resample, return contrast draws.

    `preds` maps method -> [pair, cell] prediction matrix. `contrasts` is a list of (a, b) meaning U(a) - U(b).
    Resampled pools contain the distinct drawn pairs; the ranking functional is recomputed each time.
    """
    rng = np.random.default_rng(seed)
    n_pairs, n_cells = truth.shape
    draws = {c: np.empty(n_boot) for c in contrasts}
    util_draws = {m: np.empty(n_boot) for m in preds}
    regret_oracle = np.empty(n_boot)
    for b in range(n_boot):
        if scheme == "pair":
            subset = np.unique(rng.integers(0, n_pairs, n_pairs))
            cells = None
        elif scheme == "cell":
            subset = None
            cells = rng.integers(0, n_cells, n_cells)
        else:
            raise ValueError(scheme)
        u = {m: utility(p, truth, subset, cells) for m, p in preds.items()}
        for c in contrasts:
            draws[c][b] = u[c[0]] - u[c[1]]
        for m in preds:
            util_draws[m][b] = u[m]
        regret_oracle[b] = oracle_utility(truth, subset, cells)
    return draws, util_draws, regret_oracle


def drug_jackknife(preds: dict, truth: np.ndarray, pair_ids, drug_pairs, contrasts):
    """Delete-one-drug jackknife: remove every pair containing the drug and recompute each contrast."""
    drugs = sorted({d for p in pair_ids for d in drug_pairs[int(p)]})
    full = {c: utility(preds[c[0]], truth) - utility(preds[c[1]], truth) for c in contrasts}
    reps = {c: [] for c in contrasts}
    for d in drugs:
        keep = np.array([d not in drug_pairs[int(p)] for p in pair_ids])
        idx = np.nonzero(keep)[0]
        for c in contrasts:
            reps[c].append(utility(preds[c[0]], truth, idx) - utility(preds[c[1]], truth, idx))
    out = {}
    m = len(drugs)
    for c in contrasts:
        r = np.array(reps[c])
        out[c] = {"estimate": full[c], "jackknife_se": float(np.sqrt((m - 1) / m * ((r - r.mean()) ** 2).sum())),
                  "n_drug_clusters": m}
    return out


def mse_ratio(candidate_pred, refit_pred, truth, mask=None):
    """Mean squared activity error of the candidate relative to the refit on the (optionally masked) groups."""
    err_c, err_r = (candidate_pred - truth) ** 2, (refit_pred - truth) ** 2
    if mask is not None:
        err_c, err_r = err_c[mask], err_r[mask]
    return float(np.nanmean(err_c) / np.nanmean(err_r))
