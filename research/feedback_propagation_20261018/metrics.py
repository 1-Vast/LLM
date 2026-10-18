"""Utilities and uncertainty analysis shared by development and the comparison.

File summary
- Path: research/feedback_propagation_20261018/metrics.py
- Purpose: compact per-arm records from `loop.grade_lists` results, and the registered uncertainty analysis.
- Registered analysis (PROTOCOL.md section 9):
  - Unit of analysis: the 64-compound campaign; incomplete trailing campaigns are run but excluded from the
    campaign statistics.
  - Estimate: mean paired difference per 64 compounds, from per-compound hit differences d_c:
    sum(d_c) / (compounds / 64).
  - Interval: cluster bootstrap over MoA families (families never cross folds and are the independent
    chemistry-biology groups; campaigns mix families and are not independent units); 4,000 draws, fixed seed,
    percentile 95% interval. One-sided p: sign-flip of family sums (mean > 0).
  - Secondary: paired sign-flip over complete campaigns.
- Interfaces: `compact`, `family_summary`, `paired_family`, `campaign_sign_flip`, `holm`.
"""
from __future__ import annotations

import numpy as np

SEED = 20261018
DRAWS = 4000
CAMPAIGN = 64


def compact(res: dict) -> dict:
    out = {}
    for kind in ("unmeasured", "any"):
        g = res[kind]
        camp = g["campaigns"]
        out[kind] = {
            "hits": int(sum(c["hits"] for c in camp)), "unique": int(sum(c["unique"] for c in camp)),
            "unknown": int(sum(c["unknown"] for c in camp)), "listed": int(sum(c["listed"] for c in camp)),
            "lineage_hits": int(sum(c["lineage_hits"] for c in camp)),
            "campaign_hits": [int(c["hits"]) for c in camp], "campaign_unique": [int(c["unique"]) for c in camp],
            "campaign_compounds": [int(c["compounds"]) for c in camp],
            "hits_c": [int(v) for v in g["hits_c"]], "measured_hits_c": [int(v) for v in g["measured_hits_c"]],
            "unknown_c": [int(v) for v in g["unknown_c"]]}
    return out


def complete_mask(camp_sizes: list, fold_campaign_index: list) -> np.ndarray:
    """Boolean per compound: member of a complete 64-compound campaign."""

    n = int(sum(camp_sizes))
    m = np.zeros(n, dtype=bool)
    for size, idx in zip(camp_sizes, fold_campaign_index):
        if size == CAMPAIGN:
            m[np.asarray(idx)] = True
    return m


def family_sums(d: np.ndarray, family: np.ndarray, keep: np.ndarray):
    fam = np.asarray(family)[keep]
    dd = np.asarray(d, dtype=float)[keep]
    labels, inv = np.unique(fam, return_inverse=True)
    sums = np.bincount(inv, weights=dd, minlength=len(labels))
    sizes = np.bincount(inv, minlength=len(labels)).astype(float)
    return labels, sums, sizes


def paired_family(d: np.ndarray, family: np.ndarray, keep: np.ndarray, *, draws: int = DRAWS, seed: int = SEED) -> dict:
    """Mean difference per 64 compounds with a family-cluster bootstrap interval and a family sign-flip p."""

    labels, sums, sizes = family_sums(d, family, keep)
    nf = len(labels)
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, nf, size=(draws, nf))
    boots = sums[picks].sum(1) / (sizes[picks].sum(1) / CAMPAIGN)
    est = float(sums.sum() / (sizes.sum() / CAMPAIGN))
    signs = rng.choice([-1.0, 1.0], size=(draws, nf))
    null = (signs * sums).sum(1) / (sizes.sum() / CAMPAIGN)
    p = float((1 + (null >= est - 1e-12).sum()) / (draws + 1))
    sd_family = float(np.std(sums / np.maximum(sizes, 1) * CAMPAIGN, ddof=1)) if nf > 1 else None
    return {"mean": est, "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "p_one_sided": p, "n_families": int(nf), "n_compounds": int(sizes.sum()),
            "campaigns_equivalent": float(sizes.sum() / CAMPAIGN), "sd_family_rate": sd_family}


def campaign_sign_flip(diff: np.ndarray, draws: int = 20000, seed: int = SEED) -> dict:
    d = np.asarray(diff, dtype=float)
    n = len(d)
    if n == 0:
        return {"n": 0, "mean": None, "p": None}
    obs = d.mean()
    if 2 ** n <= draws:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1) * 2 - 1
    else:
        signs = np.random.default_rng(seed).choice([-1, 1], size=(draws, n))
    null = (signs * d).mean(1)
    return {"n": n, "mean": float(obs), "sd": float(d.std(ddof=1)) if n > 1 else None,
            "p": float((1 + (null >= obs - 1e-12).sum()) / (len(null) + 1)),
            "positive": int((d > 0).sum()), "negative": int((d < 0).sum())}


def holm(ps: dict) -> dict:
    keys = sorted(ps, key=lambda k: ps[k])
    m = len(keys)
    adj, run = {}, 0.0
    for i, k in enumerate(keys):
        run = max(run, min(1.0, (m - i) * ps[k]))
        adj[k] = run
    return adj
