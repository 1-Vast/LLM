"""Small, fixed-capacity transfer baseline: no target outcomes or LLM calls."""
from __future__ import annotations
import numpy as np
from scipy.linalg import solve

METHODS = ('drug_id', 'annotation', 'network', 'permuted_network')
WEIGHTS = (0., .25, .5)
RIDGE = 2.


def pair_kernel(drug_kernel, pairs, ids):
    """PSD symmetric pair kernel: equal additive and interaction blocks."""
    index = {str(d): i for i, d in enumerate(ids)}
    aa = np.array([index[str(p[0])] for p in pairs])
    bb = np.array([index[str(p[1])] for p in pairs])
    ac, ad = drug_kernel[np.ix_(aa, aa)], drug_kernel[np.ix_(aa, bb)]
    bc, bd = drug_kernel[np.ix_(bb, aa)], drug_kernel[np.ix_(bb, bb)]
    additive = ac + ad + bc + bd
    interaction = ac * bd + ad * bc

    def unit_diagonal(k):
        d = np.sqrt(np.maximum(np.diag(k), 1e-12))
        return k / np.outer(d, d)
    return .5 * unit_diagonal(additive) + .5 * unit_diagonal(interaction)


def transfer(kernel, pair_ids, observations, ridge=RIDGE):
    """Weighted kernel ridge on observed pair means, centred on history mean.

    observations = mean of the two binary orientation calls. Each biological
    history line is one observation, not two independent orientation replicates.
    """
    pair_ids = np.asarray(pair_ids, dtype=int)
    y = np.asarray(observations, dtype=float)
    if y.size != pair_ids.size or y.size == 0 or not np.isfinite(y).all():
        raise ValueError('invalid history')
    n = np.bincount(pair_ids, minlength=kernel.shape[0]).astype(float)
    sums = np.bincount(pair_ids, weights=y, minlength=kernel.shape[0])
    obs = np.flatnonzero(n)
    root = np.sqrt(n[obs])
    mean = y.mean()
    centred = sums[obs] / n[obs] - mean
    gram = kernel[np.ix_(obs, obs)] * np.outer(root, root)
    beta = solve(gram + ridge * np.eye(len(obs)), root * centred, assume_a='pos')
    return np.clip(mean + kernel[:, obs] @ (root * beta), 0, 1)


def history_lines(development, target, count, seed, tissue_code):
    """Nested samples within seed; target always removed before sampling."""
    lines = sorted(set(development) - {target})
    if count is None:
        return lines
    perm = np.random.default_rng([20261004, tissue_code, seed]).permutation(len(lines))
    return sorted(lines[i] for i in perm[:min(count, len(lines))])
