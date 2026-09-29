"""Cross-condition response models with strict nested (inner group) validation, by information regime.

File summary
- Path: research/dual_core/transfer.py
- Purpose: the observation backend of the dual-core world model. It predicts a compound's pseudobulk
  shift at a target condition c.
- Core points:
  - Regimes are kept apart:
    - A0: no response of the query compound has been measured. Models are zero, global mean,
      context mean, chemical Tanimoto-kernel ridge and chemical k-nearest neighbours.
    - A1: one purchased prompt at condition p. Models are prompt copy, additive (Stack's PerturbMean),
      `ridge_st` (block 6, now selected by inner group CV) and the residual-retaining transfers
      `rrt_const` and `rrt_q`.
    - A2: several prompts. Per-prompt predictions are aggregated by equal weight, by the single most
      reliable prompt, or by inverse inner-CV error (`precision`).
  - Diagnosed failure behind `rrt`. `ridge_st` recovers the shared direction but loses
    compound-specific signal: block 6 found its discrimination below prompt copying. `rrt` keeps the
    low-rank transition and adds back the part of the centred prompt outside the transition's
    subspace:
        y_hat = m_c + B (x - m_p) + gamma * P_perp (x - m_p)
    - `rrt_const`: gamma is one constant.
    - `rrt_q`: gamma = gamma0 * q, where q is the prompt's measured replicate quality in [0, 1]
      (SciPlex3: split-half Pearson; L1000: cc_q75).
    Both gammas are fitted by least squares on inner out-of-fold predictions.
  - Strict nesting. Every outcome-dependent component (context means, principal components, ridge
    maps, gamma, kernel-ridge weights, the neighbour count) is refitted on each inner training
    split. Inner splits are by independent unit (`inner_folds`). The outer held-out fold is never
    touched. The feature space is fixed in advance and not learned from outcomes: SciPlex3's 2,473
    genes were chosen from vehicle controls, L1000's are the 978 landmarks.
- Interfaces: `inner_folds`, `PairModel`, `fit_pair`, `TargetModel`, `fit_target`, `aggregate`,
  `A0_ARMS`, `A1_ARMS`, `A2_ARMS`
- Depends on: numpy
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

K_GRID = (1, 2, 4, 8, 16, 32)
LAMBDA_GRID = (0.01, 0.1, 1.0, 10.0)
KRR_GRID = (0.01, 0.1, 1.0, 10.0)
KNN_GRID = (1, 3, 5, 10)
INNER = 4
A0_ARMS = ("zero", "global_mean", "context_mean", "chem_ridge", "chem_knn")
A1_ARMS = ("prompt_copy", "additive", "ridge_st", "rrt_const", "rrt_q")
A2_ARMS = ("prompt_mean", "additive_mean", "rrt_mean", "rrt_best_single", "rrt_precision")


def inner_folds(units, k: int = INNER, salt: str = "dual-core-inner") -> np.ndarray:
    """Inner fold index per row, dealt by independent unit (never splitting a unit), deterministic."""
    units = [str(u) for u in units]
    order = sorted(set(units), key=lambda u: hashlib.sha256(f"{salt}|{u}".encode()).hexdigest())
    assign = {u: i % k for i, u in enumerate(order)}
    return np.asarray([assign[u] for u in units], dtype=int)


def _svd(Xc):
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    keep = S > 1e-8 * max(S[0] if len(S) else 0.0, 1e-12)
    return U[:, keep], S[keep], Vt[keep]


def _ridge_fit(X, Y, k, mult):
    """(mp, mt, basis d x k, weights k x d) of the ridge transition fitted on rows X -> Y."""
    mp, mt = X.mean(0), Y.mean(0)
    Xc, Yc = X - mp, Y - mt
    U, S, Vt = _svd(Xc)
    k = min(k, len(S))
    if k == 0:
        return mp, mt, np.zeros((X.shape[1], 0)), np.zeros((0, Y.shape[1]))
    s = S[:k]
    lam = mult * float((s ** 2).mean())
    weights = (s / (s ** 2 + lam))[:, None] * (U[:, :k].T @ Yc)
    return mp, mt, Vt[:k].T, weights


def _ridge_predict(fit, X):
    mp, mt, basis, weights = fit
    Xc = np.atleast_2d(X) - mp
    return mt + (Xc @ basis) @ weights if basis.shape[1] else np.broadcast_to(mt, (len(Xc), len(mt))).copy()


def _perp(fit, X):
    mp, _, basis, _ = fit
    Xc = np.atleast_2d(X) - mp
    return Xc - (Xc @ basis) @ basis.T if basis.shape[1] else Xc


def _gamma(residual, component, lower=0.0, upper=1.0):
    denom = float((component * component).sum())
    return float(np.clip((residual * component).sum() / denom, lower, upper)) if denom > 1e-12 else 0.0


@dataclass
class PairModel:
    """Fitted A1 models for prompt condition p -> target condition c."""

    prompt: tuple
    target: tuple
    references: int
    fit: tuple
    k: int
    mult: float
    gamma_const: float
    gamma0: float
    inner_mse: dict = field(default_factory=dict)      # arm -> inner out-of-fold mean squared error per gene
    selection: dict = field(default_factory=dict)

    def predict(self, x, q, arm):
        x = np.asarray(x, dtype=np.float64)
        mp, mt = self.fit[0], self.fit[1]
        if arm == "prompt_copy":
            return x.copy()
        if arm == "additive":
            return x + mt - mp
        base = _ridge_predict(self.fit, x)[0]
        if arm == "ridge_st":
            return base
        perp = _perp(self.fit, x)[0]
        if arm == "rrt_const":
            return base + self.gamma_const * perp
        if arm == "rrt_q":
            return base + self.gamma0 * float(np.clip(q, 0.0, 1.0)) * perp
        raise ValueError(arm)


def fit_pair(prompt, target, X, Y, q, units, *, k_grid=K_GRID, lambda_grid=LAMBDA_GRID) -> PairModel:
    """Fit the A1 models on references measured at both conditions, with inner group CV."""
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    q = np.clip(np.nan_to_num(np.asarray(q, dtype=np.float64), nan=0.0), 0.0, 1.0)
    n = len(X)
    if n < 6:
        fit = (X.mean(0) if n else np.zeros(X.shape[1]), Y.mean(0) if n else np.zeros(Y.shape[1]),
               np.zeros((X.shape[1], 0)), np.zeros((0, Y.shape[1])))
        return PairModel(tuple(prompt), tuple(target), n, fit, 0, 0.0, 0.0, 0.0, {}, {"reason": "fewer_than_6_references"})
    folds = inner_folds(units)
    # 1. (k, lambda) of the ridge transition by inner out-of-fold squared error
    errors = {}
    for f in range(INNER):
        tr, te = folds != f, folds == f
        if te.sum() == 0 or tr.sum() < 3:
            continue
        mp, mt = X[tr].mean(0), Y[tr].mean(0)
        U, S, Vt = _svd(X[tr] - mp)
        UtY = U.T @ (Y[tr] - mt)
        Zte = (X[te] - mp) @ Vt.T
        for k in k_grid:
            if k > min(len(S), tr.sum() - 2):
                continue
            s = S[:k]
            for mult in lambda_grid:
                lam = mult * float((s ** 2).mean())
                W = (s / (s ** 2 + lam))[:, None] * UtY[:k]
                pred = mt + Zte[:, :k] @ W
                errors.setdefault((k, mult), []).append(((pred - Y[te]) ** 2).sum())
    valid = {key: sum(v) for key, v in errors.items() if len(v) == len({f for f in range(INNER) if (folds == f).any()})}
    if not valid:
        valid = {key: sum(v) for key, v in errors.items()}
    k, mult = min(valid, key=lambda key: (valid[key], key[0], -key[1]))
    # 2. gammas from inner out-of-fold ridge predictions with the chosen (k, lambda)
    res, comp, compq, mse = [], [], [], {"ridge_st": 0.0, "additive": 0.0, "prompt_copy": 0.0}
    count = 0
    for f in range(INNER):
        tr, te = folds != f, folds == f
        if te.sum() == 0 or tr.sum() < 3:
            continue
        fit = _ridge_fit(X[tr], Y[tr], k, mult)
        pred = _ridge_predict(fit, X[te])
        perp = _perp(fit, X[te])
        res.append(Y[te] - pred)
        comp.append(perp)
        compq.append(perp * q[te][:, None])
        mse["ridge_st"] += float(((pred - Y[te]) ** 2).sum())
        mse["additive"] += float(((X[te] + fit[1] - fit[0] - Y[te]) ** 2).sum())
        mse["prompt_copy"] += float(((X[te] - Y[te]) ** 2).sum())
        count += int(te.sum())
    R, P, Pq = np.vstack(res), np.vstack(comp), np.vstack(compq)
    g_const, g0 = _gamma(R, P), _gamma(R, Pq)
    mse["rrt_const"] = float(((R - g_const * P) ** 2).sum())
    mse["rrt_q"] = float(((R - g0 * Pq) ** 2).sum())
    d = Y.shape[1]
    inner_mse = {a: v / max(count * d, 1) for a, v in mse.items()}
    fit = _ridge_fit(X, Y, k, mult)
    return PairModel(tuple(prompt), tuple(target), n, fit, k, mult, g_const, g0, inner_mse,
                     {"errors": {f"{kk}|{mm}": float(v) for (kk, mm), v in valid.items()}})


def _tanimoto(A, B):
    inter = A @ B.T
    union = A.sum(1)[:, None] + B.sum(1)[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


@dataclass
class TargetModel:
    """Fitted A0 models for target condition c (no measured response of the query compound)."""

    target: tuple
    references: int
    mean: np.ndarray
    global_mean: np.ndarray
    fp: np.ndarray
    Y: np.ndarray
    alpha: np.ndarray            # kernel-ridge dual coefficients on centred targets
    krr: float
    knn: int
    has_fp: np.ndarray

    def predict(self, fp_query, arm):
        if arm == "zero":
            return np.zeros_like(self.mean)
        if arm == "global_mean":
            return self.global_mean.copy()
        if arm == "context_mean":
            return self.mean.copy()
        if fp_query is None or not np.asarray(fp_query).any() or not self.has_fp.any():
            return self.mean.copy()                    # no structure: explicit fallback to the context mean
        sim = _tanimoto(np.atleast_2d(fp_query), self.fp)[0] * self.has_fp
        if arm == "chem_ridge":
            return self.mean + sim @ self.alpha
        if arm == "chem_knn":
            order = np.argsort(-sim, kind="stable")[: self.knn]
            w = sim[order]
            return self.mean + (w @ (self.Y[order] - self.mean)) / w.sum() if w.sum() > 0 else self.mean.copy()
        raise ValueError(arm)


def fit_target(target, fp, Y, units, global_mean) -> TargetModel:
    """Chemical kernel ridge and kNN at one condition, hyperparameters by inner group CV."""
    fp = np.asarray(fp, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    has = fp.any(axis=1)
    n = len(Y)
    folds = inner_folds(units)
    err_krr = {m: 0.0 for m in KRR_GRID}
    err_knn = {k: 0.0 for k in KNN_GRID}
    for f in range(INNER):
        tr, te = folds != f, folds == f
        if te.sum() == 0 or tr.sum() < 3:
            continue
        mt = Y[tr].mean(0)
        K = _tanimoto(fp[tr], fp[tr]) * np.outer(has[tr], has[tr])
        Kte = _tanimoto(fp[te], fp[tr]) * np.outer(has[te], has[tr])
        for m in KRR_GRID:
            alpha = np.linalg.solve(K + m * np.eye(len(K)), Y[tr] - mt)
            err_krr[m] += float(((mt + Kte @ alpha - Y[te]) ** 2).sum())
        order = np.argsort(-Kte, axis=1, kind="stable")
        for k in KNN_GRID:
            idx = order[:, :k]
            w = np.take_along_axis(Kte, idx, 1)
            pred = np.where(w.sum(1, keepdims=True) > 0,
                            mt + np.einsum("ik,ikd->id", w, Y[tr][idx] - mt) / np.maximum(w.sum(1, keepdims=True), 1e-12), mt)
            err_knn[k] += float(((pred - Y[te]) ** 2).sum())
    krr = min(err_krr, key=lambda m: (err_krr[m], -m))
    knn = min(err_knn, key=lambda k: (err_knn[k], -k))
    mean = Y.mean(0) if n else np.zeros(Y.shape[1])
    K = _tanimoto(fp, fp) * np.outer(has, has)
    alpha = np.linalg.solve(K + krr * np.eye(n), Y - mean) if n else np.zeros((0, Y.shape[1]))
    return TargetModel(tuple(target), n, mean, np.asarray(global_mean, float), fp, Y, alpha, krr, knn, has)


def aggregate(predictions: list, errors: list, arm: str):
    """Combine per-prompt predictions: equal weight, most reliable single prompt, or inverse inner-CV error."""
    P = np.stack(predictions)
    e = np.asarray(errors, dtype=np.float64)
    if arm in ("prompt_mean", "additive_mean", "rrt_mean"):
        return P.mean(0), np.full(len(P), 1.0 / len(P))
    if arm == "rrt_best_single":
        w = np.zeros(len(P))
        w[int(np.argmin(e))] = 1.0
        return P[int(np.argmin(e))], w
    if arm == "rrt_precision":
        w = 1.0 / np.maximum(e, 1e-12)
        w = w / w.sum()
        return (w[:, None] * P).sum(0), w
    raise ValueError(arm)
