"""Functional metrics for transcriptional response transfer and profiling campaigns.

File summary
- Path: tools/evaluation/transfer_metrics.py
- Purpose: score predicted response directions the way block Q (2026-10-12) registered them, with a
  compound, not a cell, as the statistical unit.
- Core points:
  - Centred cosine: cosine of responses centred by the reference mean. A prediction equal to the
    mean scores 0.
  - Specific cosine: centred cosine after projecting out a line's generic active direction, so
    reproducing the systematic response shared by most active compounds (the Systema warning)
    earns nothing.
  - AURC: mean selective risk when queries are accepted most-confident first. It tells a
    certificate that ranks errors from one that does not.
  - Compound-clustered paired comparisons: each compound contributes the mean over its active
    cells, a sign-flip p-value and a percentile bootstrap interval.
  - Map utility: the campaign score. A profiled active cell counts 1; an unprofiled active cell
    counts the centred cosine of its fill; non-responsive cells do not count.
- Interfaces: `centred_cosine`, `specific_cosine`, `aurc`, `paired_cluster_test`,
  `aurc_difference`, `map_utility`.
- Depends on: numpy.
"""
from __future__ import annotations

import numpy as np


def centred_cosine(pred: np.ndarray, true: np.ndarray) -> np.ndarray:
    """Row-wise cosine; 0 where either vector is zero (a prediction of no change)."""
    pred, true = np.asarray(pred, dtype=float), np.asarray(true, dtype=float)
    num = (pred * true).sum(-1)
    den = np.linalg.norm(pred, axis=-1) * np.linalg.norm(true, axis=-1)
    return np.where(den > 1e-9, num / np.maximum(den, 1e-12), 0.0)


def _unit(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return np.where(n > 0, x / np.maximum(n, 1e-12), 0.0)


def specific_cosine(pred: np.ndarray, true: np.ndarray, generic: np.ndarray) -> np.ndarray:
    """Centred cosine after removing the component along each row's generic direction."""
    g = _unit(np.asarray(generic, dtype=float))
    pred, true = np.asarray(pred, dtype=float), np.asarray(true, dtype=float)
    return centred_cosine(pred - (pred * g).sum(-1, keepdims=True) * g, true - (true * g).sum(-1, keepdims=True) * g)


def aurc(confidence: np.ndarray, loss: np.ndarray) -> float:
    """Area under the risk-coverage curve, accepting the most confident first (lower is better)."""
    loss = np.asarray(loss, dtype=float)
    if loss.size == 0:
        raise ValueError("no queries to score")
    order = np.argsort(-np.asarray(confidence, dtype=float), kind="stable")
    return float((np.cumsum(loss[order]) / np.arange(1, loss.size + 1)).mean())


def _cluster_means(values: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    _, inv = np.unique(np.asarray(clusters), return_inverse=True)
    return np.bincount(inv, weights=np.asarray(values, dtype=float)) / np.bincount(inv)


def paired_cluster_test(a: np.ndarray, b: np.ndarray, clusters: np.ndarray, *, draws: int = 20000, seed: int = 0,
                        resamples: int = 2000) -> dict:
    """a - b, one value per cluster (its mean): sign-flip p-values and a percentile bootstrap interval."""
    d = _cluster_means(np.asarray(a, dtype=float) - np.asarray(b, dtype=float), clusters)
    if d.size < 2:
        raise ValueError("need at least two clusters")
    rng = np.random.default_rng(seed)
    obs = float(d.mean())
    null = (rng.choice((-1.0, 1.0), size=(draws, d.size)) * d[None]).mean(1)
    boot = d[rng.integers(0, d.size, size=(resamples, d.size))].mean(1)
    return {"estimate": obs, "n_clusters": int(d.size),
            "p_greater": float((np.sum(null >= obs - 1e-12) + 1) / (draws + 1)),
            "p_two_sided": float((np.sum(np.abs(null) >= abs(obs) - 1e-12) + 1) / (draws + 1)),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "favour": int((d > 0).sum()), "oppose": int((d < 0).sum())}


def aurc_difference(confidence_a: np.ndarray, confidence_b: np.ndarray, loss: np.ndarray, clusters: np.ndarray, *,
                    resamples: int = 2000, seed: int = 0) -> dict:
    """AURC(b) - AURC(a): positive when a ranks risk better; whole clusters are resampled."""
    ca, cb, loss = (np.asarray(x, dtype=float) for x in (confidence_a, confidence_b, loss))
    labels, inv = np.unique(np.asarray(clusters), return_inverse=True)
    if labels.size < 2:
        raise ValueError("need at least two clusters")
    members = [np.flatnonzero(inv == j) for j in range(labels.size)]
    rng = np.random.default_rng(seed)
    boot = np.empty(resamples)
    for r in range(resamples):
        idx = np.concatenate([members[j] for j in rng.integers(0, labels.size, labels.size)])
        boot[r] = aurc(cb[idx], loss[idx]) - aurc(ca[idx], loss[idx])
    return {"estimate": aurc(cb, loss) - aurc(ca, loss), "aurc_a": aurc(ca, loss), "aurc_b": aurc(cb, loss),
            "n_clusters": int(labels.size), "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "p_le_zero": float((np.sum(boot <= 0) + 1) / (resamples + 1))}


def map_utility(profiled: np.ndarray, fills: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """Campaign score of a completed compound x line map.

    ``profiled`` and ``active`` are compounds x lines booleans, and ``fills`` and ``truth`` are
    compounds x lines x genes centred responses. A profiled active cell earns 1, an unprofiled
    active cell earns the centred cosine of its fill, and other cells are not scored.
    """
    profiled, active = np.asarray(profiled, bool), np.asarray(active, bool)
    p = truth.shape[-1]
    cos = centred_cosine(np.asarray(fills, dtype=float).reshape(-1, p),
                         np.nan_to_num(np.asarray(truth, dtype=float)).reshape(-1, p)).reshape(active.shape)
    credit = np.where(profiled, 1.0, cos)[active]
    if credit.size == 0:
        return {"utility": None, "usable": None, "n_active": 0, "wells": int(profiled.sum()), "refusal": "NO_ACTIVE_CELLS"}
    return {"utility": float(credit.mean()), "usable": float((credit >= 0.5).mean()), "n_active": int(credit.size),
            "wells": int(profiled.sum()), "refusal": None}
