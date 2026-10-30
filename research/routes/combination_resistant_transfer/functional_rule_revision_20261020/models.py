"""Models for the pilot: fixed-structure ridge, edited/full-dictionary ridge, FM and boosted-tree comparators.

Target everywhere is the reference residual R = A_obs - A_ref; predicted activity is A_ref + R_hat.
All learners use one shared feature definition (built from identities and the monotherapy panel
only) so that "same preprocessing, functional information and candidate pool" holds by construction.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

import design as D

LAMBDA_BASE = (1.0, 30.0, 300.0)
LAMBDA_THETA = (1.0, 3.0, 10.0, 30.0)
RIDGE_CONFIGS = [(b, t) for b in LAMBDA_BASE for t in LAMBDA_THETA]          # 12
GBM_CONFIGS = [(d, lr, it) for d in (4, 6, 8) for lr in (0.05, 0.1) for it in (300, 600)]   # 12
FM_CONFIGS = [(r, lam) for r in (2, 4) for lam in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0)]        # 12
N_FOLDS = 5
CV_REPEATS = 2


# --------------------------------------------------------------------------- shared feature store
@dataclass
class FeatureStore:
    X: sp.csr_matrix              # all groups x columns
    names: list
    kind: np.ndarray              # 'intercept' | 'base' | 'theta' | 'edit'
    edit_index: dict              # rule id -> column
    dense: np.ndarray             # (n, 3) standardised A_ref, a_min, a_max
    gbm: np.ndarray               # features for the tree learner
    gbm_categorical: list
    fm_ids: sp.csr_matrix         # one-hot id fields (cell, drug, drug)
    pair: np.ndarray
    cell: np.ndarray
    group_ids: np.ndarray

    def cols(self, edits=()):
        keep = [k for k in range(len(self.names)) if self.kind[k] != "edit"]
        keep += [self.edit_index[e] for e in edits]
        return np.array(sorted(keep))


def build_features(T, module, gates, rules, scale_mask):
    """Feature store for every group. `scale_mask` marks rows (source groups) used for standardisation."""
    n = len(T.g_pair)
    nd, nc, nm = len(T.drugs), len(T.cells), int(module.max()) + 1
    i, j, c = T.g_i, T.g_j, T.g_cell
    p, q = module[i], module[j]
    rows = np.arange(n)
    blocks, names, kinds = [], [], []

    def add(matrix, label, kind):
        blocks.append(sp.csr_matrix(matrix))
        names.extend(f"{label}{k}" for k in range(matrix.shape[1]))
        kinds.extend([kind] * matrix.shape[1])

    add(np.ones((n, 1)), "intercept", "intercept")
    cell_oh = sp.csr_matrix((np.ones(n), (rows, c)), shape=(n, nc))
    add(cell_oh, "cell", "base")
    drug_oh = sp.csr_matrix((np.ones(n), (rows, i)), shape=(n, nd)) + sp.csr_matrix((np.ones(n), (rows, j)), shape=(n, nd))
    add(drug_oh, "drug", "base")
    mod_oh = sp.csr_matrix((np.ones(n), (rows, p)), shape=(n, nm)) + sp.csr_matrix((np.ones(n), (rows, q)), shape=(n, nm))
    add(mod_oh, "module", "base")
    within = (p == q).astype(float)
    add(np.column_stack([within, 1 - within]), "shared_", "base")
    a_min, a_max = np.minimum(T.a_mono_i, T.a_mono_j), np.maximum(T.a_mono_i, T.a_mono_j)
    raw = np.column_stack([T.a_ref, a_min, a_max])
    raw = np.where(np.isfinite(raw), raw, np.nanmean(raw[scale_mask], axis=0))
    mean, std = raw[scale_mask].mean(axis=0), raw[scale_mask].std(axis=0) + 1e-9
    dense = (raw - mean) / std
    add(dense, "num", "base")
    theta = sp.csr_matrix((np.ones(n), (rows, i * nc + c)), shape=(n, nd * nc)) + \
        sp.csr_matrix((np.ones(n), (rows, j * nc + c)), shape=(n, nd * nc))
    add(theta, "theta", "theta")
    edit_index = {}
    for rule in rules:
        column = D.rule_column(rule, i, j, c, module, gates)
        edit_index[rule.id] = sum(b.shape[1] for b in blocks)
        add(column[:, None], f"edit_{rule.id}_", "edit")
    X = sp.hstack(blocks).tocsr()

    gate_matrix = np.column_stack([gates[k][c] for k in sorted(gates)])
    gbm = np.column_stack([T.a_ref, a_min, a_max, c, i, j, np.minimum(p, q), np.maximum(p, q), gate_matrix])
    fm = sp.hstack([cell_oh, drug_oh]).tocsr()
    return FeatureStore(X, names, np.array(kinds), edit_index, dense, gbm, [3, 4, 5], fm, T.g_pair, c, np.arange(n))


# --------------------------------------------------------------------------- folds
def pair_folds(pairs, salt, n_folds=N_FOLDS):
    ordered = sorted(set(int(p) for p in pairs), key=lambda p: hashlib.sha256(f"{salt}|{p}".encode()).hexdigest())
    return {p: k % n_folds for k, p in enumerate(ordered)}


# --------------------------------------------------------------------------- ridge
def penalty_vector(store: FeatureStore, cols, lam_base, lam_theta):
    out = np.empty(len(cols))
    for k, col in enumerate(cols):
        kind = store.kind[col]
        out[k] = 1e-6 if kind == "intercept" else lam_theta if kind == "theta" else lam_base
    return out


def ridge_fit_cols(gram, xty, store, cols, lam_base, lam_theta):
    sub = gram[np.ix_(cols, cols)] + np.diag(penalty_vector(store, cols, lam_base, lam_theta))
    return cho_solve(cho_factor(sub, lower=True), xty[cols])


def gram_of(store, rows, y):
    Xr = store.X[rows]
    return (Xr.T @ Xr).toarray(), np.asarray(Xr.T @ y).ravel()


def ridge_predict(store, cols, weights, rows):
    return store.X[rows][:, cols] @ weights


@dataclass
class RidgeModel:
    cols: np.ndarray
    weights: np.ndarray
    config: tuple
    edits: tuple

    def predict(self, store, rows):
        return ridge_predict(store, self.cols, self.weights, rows)


def fold_assignments(pairs_of_rows, salts):
    return [pair_folds(np.unique(pairs_of_rows), s) for s in salts]


def cv_ridge(store, rows, y, edits_list, configs, salts, masks=None):
    """Grouped (by pair) cross-validation mean squared error for several structures and configurations.

    Returns {(edits_tuple, config): {"all": mse, <mask name>: mse on the masked held-out rows}} averaged over repeats.
    """
    masks = masks or {}
    pair_of_row = store.pair[rows]
    n = len(rows)
    sums = {}
    for salt in salts:
        fold_of_pair = pair_folds(np.unique(pair_of_row), salt)
        fold = np.array([fold_of_pair[int(p)] for p in pair_of_row])
        for f in range(N_FOLDS):
            test_mask = fold == f
            train, test = rows[~test_mask], rows[test_mask]
            gram, xty = gram_of(store, train, y[~test_mask])
            for edits in edits_list:
                cols = store.cols(edits)
                for config in configs:
                    w = ridge_fit_cols(gram, xty, store, cols, *config)
                    err2 = (y[test_mask] - ridge_predict(store, cols, w, test)) ** 2
                    entry = sums.setdefault((tuple(edits), config), {"all": 0.0, **{m: 0.0 for m in masks}})
                    entry["all"] += float(err2.sum())
                    for name, mask in masks.items():
                        entry[name] += float(err2[mask[test_mask]].sum())
    totals = {name: float(mask.sum()) for name, mask in masks.items()}
    out = {}
    for key, entry in sums.items():
        out[key] = {"all": entry["all"] / n / len(salts), **{m: entry[m] / totals[m] / len(salts) for m in masks}}
    return out


def fit_ridge(store, rows, y, edits, config):
    cols = store.cols(edits)
    gram, xty = gram_of(store, rows, y)
    return RidgeModel(cols, ridge_fit_cols(gram, xty, store, cols, *config), config, tuple(edits))


def tune_ridge(store, rows, y, edits, salts, configs=RIDGE_CONFIGS):
    scores = cv_ridge(store, rows, y, [tuple(edits)], configs, salts)
    best = min(configs, key=lambda cfg: (scores[(tuple(edits), cfg)]["all"], cfg))
    return best, {cfg: scores[(tuple(edits), cfg)]["all"] for cfg in configs}


# --------------------------------------------------------------------------- gradient boosting
def fit_gbm(store, rows, y, config, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor
    depth, lr, iters = config
    model = HistGradientBoostingRegressor(max_depth=depth, learning_rate=lr, max_iter=iters, l2_regularization=1.0,
                                          min_samples_leaf=40, categorical_features=store.gbm_categorical_mask(), random_state=seed,
                                          early_stopping=False)
    model.fit(store.gbm[rows], y)
    return model


def _gbm_mask(self):
    mask = np.zeros(self.gbm.shape[1], dtype=bool)
    mask[self.gbm_categorical] = True
    return mask


FeatureStore.gbm_categorical_mask = _gbm_mask


# --------------------------------------------------------------------------- factorisation machine
class FMModel:
    """Second-order factorisation machine over one-hot cell and (multi-hot) drug fields plus linear dense terms.

    A symmetric, orientation-free interaction-capable learner: y = w0 + w.x + b.z + sum_{f<g} <v_f, v_g> x_f x_g.
    """

    def __init__(self, rank, lam, seed=0, max_iter=200):
        self.rank, self.lam, self.seed, self.max_iter = rank, lam, seed, max_iter

    def _unpack(self, theta, nf, nz):
        k = self.rank
        w0 = theta[0]
        w = theta[1:1 + nf]
        b = theta[1 + nf:1 + nf + nz]
        V = theta[1 + nf + nz:].reshape(nf, k)
        return w0, w, b, V

    def _forward(self, theta, X, Z):
        nf, nz = X.shape[1], Z.shape[1]
        w0, w, b, V = self._unpack(theta, nf, nz)
        XV = X @ V
        X2 = X.multiply(X)
        inter = 0.5 * (XV ** 2 - X2 @ (V ** 2)).sum(axis=1)
        return w0 + X @ w + Z @ b + np.asarray(inter).ravel(), XV, X2

    def fit(self, X, Z, y):
        n, nf, nz, k = X.shape[0], X.shape[1], Z.shape[1], self.rank
        rng = np.random.default_rng(self.seed)
        theta0 = np.concatenate([[y.mean()], np.zeros(nf), np.zeros(nz), 0.05 * rng.standard_normal(nf * k)])
        lam = self.lam / n

        def objective(theta):
            pred, XV, X2 = self._forward(theta, X, Z)
            err = pred - y
            w0, w, b, V = self._unpack(theta, nf, nz)
            loss = 0.5 * float(err @ err) / n + 0.5 * lam * (float(w @ w) + float(b @ b) + float((V ** 2).sum()))
            g_w0 = err.mean()
            g_w = np.asarray(X.T @ err).ravel() / n + lam * w
            g_b = np.asarray(Z.T @ err).ravel() / n + lam * b
            g_V = (np.asarray(X.T @ (err[:, None] * XV)) - np.asarray(X2.T @ err)[:, None] * V) / n + lam * V
            return loss, np.concatenate([[g_w0], g_w, g_b, g_V.ravel()])

        res = minimize(objective, theta0, jac=True, method="L-BFGS-B", options={"maxiter": self.max_iter})
        self.theta = res.x
        self.shape = (nf, nz)
        return self

    def predict(self, X, Z):
        return self._forward(self.theta, X, Z)[0]


def fm_inputs(store, rows):
    return store.fm_ids[rows], sp.csr_matrix(store.dense[rows])


def cv_generic(rows, y, store, salts, fit_predict, configs):
    """Grouped CV MSE for a learner given as fit_predict(config, train_rows, y_train, test_rows) -> predictions."""
    pair_of_row = store.pair[rows]
    n = len(rows)
    scores = {cfg: 0.0 for cfg in configs}
    for salt in salts:
        fold_of_pair = pair_folds(np.unique(pair_of_row), salt)
        fold = np.array([fold_of_pair[int(p)] for p in pair_of_row])
        for f in range(N_FOLDS):
            for cfg in configs:
                pred = fit_predict(cfg, rows[fold != f], y[fold != f], rows[fold == f])
                err = y[fold == f] - pred
                scores[cfg] += float(err @ err) / n / len(salts)
    return scores
