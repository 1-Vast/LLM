"""Phenotype transfer to an unseen context from reference contexts with similar basal state.

For an unseen cell context, the prior for a per-condition phenotype is a softmax-weighted mean of
the measured phenotype of reference contexts. The weights come from the correlation between basal
profiles, each centred on the reference mean. Missing reference values are skipped, never read as
zero.

Scope of the evidence (2026-10-10 phenotype-anchor block,
``research/astra/phenotype_anchor_20261010``):

* Endpoint: Tahoe-100M relative-survival selectivity at 5 uM, 24 h, measured in pooled spheroids.
* Leave-one-reference-line-out over 40 lines: within-line r = 0.53.
* Five checkpoint-held-out lines, versus generic potency ranking: top-10 selectivity gain
  +0.56 log2 [0.24, 0.82], better in 5 of 5 lines.
* On those lines it also beat frozen STATE zero-shot readouts.

The evidence is limited to that endpoint, assay and panel. Elsewhere this function is an
uncalibrated prior. It is not a mechanism or engagement claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

VALIDATED_SCOPE = "tahoe100m_relative_survival_selectivity_5uM_24h_pooled_spheroid"


@dataclass(frozen=True)
class TransferPrior:
    values: np.ndarray | None
    weights: np.ndarray | None
    refusal: str | None = None
    scope: str = VALIDATED_SCOPE


def transfer_prior(target_basal: np.ndarray, reference_basal: np.ndarray, reference_outcomes: np.ndarray,
                   *, tau: float = 0.1, top_m: int | None = None) -> TransferPrior:
    """Prior for every condition column of ``reference_outcomes`` (references x conditions)."""
    target = np.asarray(target_basal, dtype=float)
    basal = np.asarray(reference_basal, dtype=float)
    outcomes = np.asarray(reference_outcomes, dtype=float)
    if basal.ndim != 2 or len(basal) == 0:
        return TransferPrior(None, None, "NO_REFERENCE_CONTEXTS")
    if target.shape != basal.shape[1:] or outcomes.shape[0] != basal.shape[0]:
        return TransferPrior(None, None, "BASAL_AXIS_MISMATCH")
    if not (np.isfinite(target).all() and np.isfinite(basal).all()):
        return TransferPrior(None, None, "NONFINITE_BASAL")
    if not (np.isfinite(tau) and tau > 0):
        raise ValueError("tau must be a positive finite number")
    center = basal.mean(0)
    a, B = target - center, basal - center
    sim = (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a) + 1e-12)
    order = np.argsort(-sim)[: (top_m or len(sim))]
    w = np.zeros(len(sim))
    w[order] = np.exp((sim[order] - sim[order].max()) / tau)
    observed = np.isfinite(outcomes)
    numerator = (w[:, None] * np.where(observed, outcomes, 0.0)).sum(0)
    denominator = (w[:, None] * observed).sum(0)
    values = np.where(denominator > 0, numerator / np.maximum(denominator, 1e-12), np.nan)
    return TransferPrior(values, w / w.sum())
