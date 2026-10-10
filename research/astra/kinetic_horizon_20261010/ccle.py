"""DepMap-scale basal priors for 5-day PRISM response (CCLE 19Q4 expression; no outcome of an
evaluated line enters the reference set unless the protocol says so).

* ``kernel``: cosine similarity on the 2,000 most variable genes (variance over all CCLE lines,
  an unsupervised choice), soft top-m kernel over reference lines;
* ``ridge``: PCA (fit on reference lines) + ridge regression of the reference responses.
Lines absent from the expression matrix are refused with ``NO_CCLE_EXPRESSION``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EXPR = ROOT / "data/external/depmap_19q4/CCLE_expression.csv"
N_GENES = 2000


@lru_cache(maxsize=1)
def matrix() -> tuple[dict, np.ndarray]:
    df = pd.read_csv(EXPR, index_col=0)
    X = df.to_numpy(np.float32)
    top = np.argsort(-X.var(0))[:N_GENES]
    X = X[:, top]
    X = (X - X.mean(0)) / (X.std(0) + 1e-6)
    return {d: i for i, d in enumerate(df.index.astype(str))}, X


def available(ids) -> list:
    idx, _ = matrix()
    return [d for d in ids if d in idx]


def kernel(target: str, refs: list, y: np.ndarray, tau: float = 0.1, m: int = 20) -> float:
    idx, X = matrix()
    ok = np.isfinite(y) & np.array([r in idx for r in refs])
    refs = [r for r, k in zip(refs, ok) if k]
    y = y[ok]
    if target not in idx or not refs:
        return np.nan
    B = X[[idx[r] for r in refs]]
    a = X[idx[target]]
    sim = (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a) + 1e-12)
    o = np.argsort(-sim)[:m]
    w = np.exp((sim[o] - sim[o].max()) / tau)
    return float((w * y[o]).sum() / w.sum())


def ridge(targets: list, refs: list, y: np.ndarray, n_pc: int = 50, alpha: float = 10.0) -> np.ndarray:
    idx, X = matrix()
    ok = np.isfinite(y) & np.array([r in idx for r in refs])
    R = X[[idx[r] for r, k in zip(refs, ok) if k]]
    yy = y[ok]
    mu = R.mean(0)
    _, _, vt = np.linalg.svd(R - mu, full_matrices=False)
    V = vt[:n_pc]
    Z = (R - mu) @ V.T
    w = np.linalg.solve(Z.T @ Z + alpha * np.eye(n_pc), Z.T @ (yy - yy.mean()))
    out = np.full(len(targets), np.nan)
    for i, t in enumerate(targets):
        if t in idx:
            out[i] = float(((X[idx[t]] - mu) @ V.T) @ w + yy.mean())
    return out
