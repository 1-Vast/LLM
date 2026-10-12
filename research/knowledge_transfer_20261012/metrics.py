"""Functional metrics for block Q (prediction and selective risk), compound-clustered.

* centred cosine: cosine of responses centred by the reference mean (``rkt.centred_cosine``);
* specific cosine: centred cosine after projecting out the line's generic active direction, so a
  prediction earns nothing for reproducing the systematic response shared by most actives;
* AURC: area under the risk-coverage curve when queries are accepted in order of confidence;
* compound-clustered paired comparisons: a compound contributes the mean over its active cells.
"""
from __future__ import annotations

import numpy as np

import rkt
from pool import perp


def specific_cosine(pred: np.ndarray, truth: np.ndarray, G: np.ndarray) -> np.ndarray:
    return rkt.centred_cosine(perp(pred, G), perp(truth, G))


def aurc(conf: np.ndarray, loss: np.ndarray) -> float:
    """Mean selective risk over coverages 1/n..1 accepting the most confident first (lower is better)."""
    order = np.argsort(-np.asarray(conf), kind="stable")
    cum = np.cumsum(np.asarray(loss)[order]) / np.arange(1, len(loss) + 1)
    return float(cum.mean())


def cluster_means(values: np.ndarray, clusters: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-cluster means (clusters sorted by label)."""
    labels, inv = np.unique(clusters, return_inverse=True)
    sums = np.bincount(inv, weights=values)
    counts = np.bincount(inv)
    return labels, sums / counts


def paired_cluster_test(a: np.ndarray, b: np.ndarray, clusters: np.ndarray, *, draws: int = 20000, seed: int = 0,
                        resamples: int = 2000) -> dict:
    """a - b with compounds as clusters: sign-flip p (one-sided a > b), and a percentile bootstrap CI."""
    labels, d = cluster_means(np.asarray(a) - np.asarray(b), clusters)
    rng = np.random.default_rng(seed)
    obs = d.mean()
    flips = rng.choice((-1.0, 1.0), size=(draws, len(d)))
    null = (flips * d[None]).mean(1)
    boot = d[rng.integers(0, len(d), size=(resamples, len(d)))].mean(1)
    return {"estimate": float(obs), "n_clusters": int(len(d)),
            "p_greater": float((np.sum(null >= obs - 1e-12) + 1) / (draws + 1)),
            "p_two_sided": float((np.sum(np.abs(null) >= abs(obs) - 1e-12) + 1) / (draws + 1)),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "favour": int((d > 0).sum()), "oppose": int((d < 0).sum())}


def aurc_difference(conf_a: np.ndarray, conf_b: np.ndarray, loss: np.ndarray, clusters: np.ndarray, *,
                    resamples: int = 2000, seed: int = 0) -> dict:
    """AURC(b) - AURC(a) (positive: a ranks risk better) with a compound-cluster bootstrap."""
    rng = np.random.default_rng(seed)
    labels, inv = np.unique(clusters, return_inverse=True)
    members = [np.flatnonzero(inv == j) for j in range(len(labels))]
    obs = aurc(conf_b, loss) - aurc(conf_a, loss)
    boot = np.empty(resamples)
    for r in range(resamples):
        idx = np.concatenate([members[j] for j in rng.integers(0, len(labels), len(labels))])
        boot[r] = aurc(conf_b[idx], loss[idx]) - aurc(conf_a[idx], loss[idx])
    return {"estimate": float(obs), "aurc_a": aurc(conf_a, loss), "aurc_b": aurc(conf_b, loss),
            "n_clusters": int(len(labels)), "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "p_le_zero": float((np.sum(boot <= 0) + 1) / (resamples + 1))}
