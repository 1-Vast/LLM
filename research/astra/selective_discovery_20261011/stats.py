"""Registered statistics for block P: lineage-cluster bootstrap, family-wise intervals, verdicts.

A campaign is one (library, lineage) pair. Campaigns that share a lineage share its difficulty and
its reference knowledge, so the bootstrap resamples **lineages** (clusters), not campaigns. All
intervals are percentile intervals of the summed paired difference over 4,000 draws with a fixed
seed.

Family-wise control: within a declared family of ``k`` contrasts, each interval is widened to the
Bonferroni level ``alpha / k`` (so a 95% family of 5 contrasts uses 99% per-contrast intervals).

Verdicts, from the family-wise interval of the paired difference:
* ``PASS``   lower bound > 0;
* ``HARM``   upper bound < 0;
* ``NOT_SUPPORTED`` otherwise.
A non-inferiority claim uses ``margin``: ``PASS`` when the lower bound exceeds ``-margin``.
"""
from __future__ import annotations

import numpy as np

DRAWS = 4000
SEED = 20261011


def cluster_bootstrap(diff: np.ndarray, clusters: np.ndarray, alpha: float = 0.05, draws: int = DRAWS,
                      seed: int = SEED) -> dict:
    diff = np.asarray(diff, float)
    clusters = np.asarray(clusters)
    u = np.unique(clusters)
    sums = {c: diff[clusters == c].sum() for c in u}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(u), size=(draws, len(u)))
    table = np.array([sums[c] for c in u])
    est = table[idx].sum(axis=1)
    lo, hi = np.percentile(est, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"estimate": float(diff.sum()), "lower": float(lo), "upper": float(hi), "alpha": alpha,
            "n_clusters": int(len(u)), "n_campaigns": int(len(diff)),
            "per_cluster": {str(c): float(sums[c]) for c in u}}


def cluster_signflip(diff: np.ndarray, clusters: np.ndarray, draws: int = 20000, seed: int = SEED) -> dict:
    """Exact-in-the-limit paired test for few clusters: flip the sign of whole clusters.

    Under the null that the two arms are exchangeable within a cluster, each cluster's summed
    difference is symmetric about zero, so its sign may be flipped. With 14 clusters the exact
    enumeration is 16,384 patterns; all of them are enumerated when there are at most 20 clusters,
    otherwise ``draws`` random patterns are used. Returns one-sided p-values in both directions
    (``p_greater`` for "arm A beats arm B") and the two-sided p-value.
    """
    diff = np.asarray(diff, float)
    clusters = np.asarray(clusters)
    u = np.unique(clusters)
    s = np.array([diff[clusters == c].sum() for c in u])
    obs = float(s.sum())
    n = len(u)
    if n <= 20:
        signs = 1 - 2 * ((np.arange(1 << n)[:, None] >> np.arange(n)) & 1)
        exact = True
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice([-1, 1], size=(draws, n))
        exact = False
    null = signs @ s
    # Ties count as at least as extreme (the conservative convention). The tolerance stops that
    # decision from depending on the summation order's last bit; for integer counts it is a no-op.
    tol = 1e-9 * max(1.0, abs(obs))
    return {"estimate": obs, "n_clusters": n, "exact": exact, "n_patterns": int(len(null)),
            "p_greater": float((null >= obs - tol).mean()), "p_less": float((null <= obs + tol).mean()),
            "p_two_sided": float((np.abs(null) >= abs(obs) - tol).mean())}


def verdict(ci: dict, margin: float = 0.0) -> str:
    if ci["lower"] > -margin and (margin > 0 or ci["lower"] > 0):
        return "PASS"
    if ci["upper"] < 0 and margin == 0:
        return "HARM"
    return "NOT_SUPPORTED"


def family(contrasts: dict, alpha: float = 0.05, margins: dict | None = None, rule: str = "signflip") -> dict:
    """``contrasts``: {name: (diff array, clusters)}.

    Reports, for each contrast, the nominal 95% cluster-bootstrap interval (the effect size), the
    Bonferroni-widened interval, and the cluster sign-flip test. ``rule`` selects which decides the
    verdict: ``"signflip"`` uses the one-sided p-value against ``alpha / k`` (the registered rule,
    chosen because 14 clusters make the bootstrap interval the weaker instrument), ``"interval"``
    uses the family-wise interval. Non-inferiority contrasts (a positive ``margin``) always use the
    interval, since a sign-flip test cannot address a shifted null.
    """
    k = max(len(contrasts), 1)
    out = {}
    for name, (diff, clusters) in contrasts.items():
        nominal = cluster_bootstrap(diff, clusters, alpha=alpha)
        fw = cluster_bootstrap(diff, clusters, alpha=alpha / k)
        sf = cluster_signflip(diff, clusters)
        m = (margins or {}).get(name, 0.0)
        if m > 0:
            v = verdict(fw, m)
        elif rule == "signflip":
            if sf["p_greater"] <= alpha / k:
                v = "PASS"
            elif sf["p_less"] <= alpha / k:
                v = "HARM"
            else:
                v = "NOT_SUPPORTED"
        else:
            v = verdict(fw, m)
        out[name] = {"estimate": nominal["estimate"], "lower": fw["lower"], "upper": fw["upper"],
                     "nominal_lower": nominal["lower"], "nominal_upper": nominal["upper"],
                     "p_greater": sf["p_greater"], "p_less": sf["p_less"], "p_two_sided": sf["p_two_sided"],
                     "exact_signflip": sf["exact"], "n_clusters": nominal["n_clusters"],
                     "n_campaigns": nominal["n_campaigns"], "per_cluster": nominal["per_cluster"],
                     "family_size": k, "alpha_per_contrast": alpha / k, "margin": m, "rule": "interval" if m > 0 else rule,
                     "verdict": v}
    return out
