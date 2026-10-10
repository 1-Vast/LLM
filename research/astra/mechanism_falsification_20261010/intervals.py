"""Interval helpers for block M: Wilson intervals and paired cluster bootstrap over drugs.

Drugs are the units; drugs of the same mechanism class are resampled together (clusters), because
they share a class model and calibration bucket. Seed 20261010, 2,000 draws unless stated.
"""
from __future__ import annotations

import numpy as np


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - h), float(c + h)


def cluster_bootstrap(values: np.ndarray, clusters: np.ndarray, n_boot: int = 2000, seed: int = 20261010,
                      stat=np.mean) -> tuple[float, float, float]:
    """Point estimate and 95% percentile interval of ``stat(values)`` resampling clusters."""
    values = np.asarray(values, float)
    clusters = np.asarray(clusters)
    keys, inv = np.unique(clusters, return_inverse=True)
    groups = [np.where(inv == i)[0] for i in range(len(keys))]
    rng = np.random.default_rng(seed)
    est = float(stat(values))
    draws = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(groups), size=len(groups))
        idx = np.concatenate([groups[i] for i in pick])
        draws[b] = stat(values[idx])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return est, float(lo), float(hi)


def paired_difference(a: np.ndarray, b: np.ndarray, clusters: np.ndarray, **kw) -> dict:
    """Mean of a - b per drug with a cluster-bootstrap 95% interval."""
    d = np.asarray(a, float) - np.asarray(b, float)
    est, lo, hi = cluster_bootstrap(d, clusters, **kw)
    return {"n": int(len(d)), "mean_difference": est, "ci95": [lo, hi], "share_a_smaller": float(np.mean(d < 0)),
            "share_a_larger": float(np.mean(d > 0))}
