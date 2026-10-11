"""Selective killing profile of a compound by transfer from transcriptionally similar screened drugs.

For a query compound with an L1000 response, the prior for its viability profile across cell lines
is a similarity-weighted mean of the profiles of the ``k`` screened reference drugs whose responses
are most similar.
* Similarity is the mean cosine over the line x time conditions measured for both drugs.
* Weights are the clipped similarities.
* Missing reference values are skipped, never read as zero.

The top similarity is returned as the prior's trust score.

Scope of the evidence: 2026-10-11 block N, ``research/astra/mechanism_routing_20261011``, frozen
2026-10-10T18:02:47Z and run once on 421 sealed drugs.
* Inputs:
  * GSE92742 landmark responses at 10 uM, 9 lines x 6/24 h;
  * PRISM Repurposing 19Q4 log fold change at 2.5 uM, 578 lines;
  * score: selective r, after removing the generic killing profile.
* Unseen mechanism class (101 killers), against Repurposing Hub target kNN and Morgan chemical kNN:
  * +0.116 [+0.053, +0.181] over targets;
  * +0.100 [+0.030, +0.177] over chemistry.

  Both intervals are family-wise at 99.375%. The result replicated on the independent secondary
  screen (+0.103 over targets).
* Added to ridge on a 160-line partial screen of the compound itself: +0.049 [+0.004, +0.097].
* Ranking by top similarity: the most-trusted quarter has utility +0.097 above the mean.

Not shown:
* It did not beat ridge on a 40-line partial screen at the family level.
* An LLM critic, forecaster or explainer did not improve it; the critic and the forecaster harmed it.

Elsewhere this function is an uncalibrated prior. It is not a mechanism-of-action claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

VALIDATED_SCOPE = "prism19q4_selective_lfc_2.5uM_from_gse92742_landmark_10uM_9lines_6h24h"


@dataclass(frozen=True)
class TranscriptionalTransfer:
    values: np.ndarray | None          # predicted profile over the reference profiles' columns
    neighbours: np.ndarray | None      # indices of the k references used, most similar first
    similarities: np.ndarray | None    # their similarities
    trust: float | None                # top similarity (higher: the prior is more often right)
    refusal: str | None = None
    scope: str = VALIDATED_SCOPE


def signature_similarity(query: np.ndarray, references: np.ndarray) -> np.ndarray:
    """Mean cosine over conditions measured for both (query: conditions x genes; references: n x conditions x genes).

    A condition is unmeasured when its first gene is not finite (an L1000 signature is all or none).
    Returns NaN for a reference sharing no measured condition with the query.
    """
    q = np.asarray(query, dtype=float)
    R = np.asarray(references, dtype=float)
    q_have, r_have = np.isfinite(q[..., 0]), np.isfinite(R[..., 0])
    qf, Rf = np.nan_to_num(q), np.nan_to_num(R)
    num = np.einsum("og,pog->po", qf, Rf)
    den = np.linalg.norm(qf, axis=-1)[None] * np.linalg.norm(Rf, axis=-1)
    ok = q_have[None] & r_have & (den > 0)
    cos = np.where(ok, num / np.maximum(den, 1e-12), 0.0)
    n = ok.sum(axis=1)
    return np.where(n > 0, cos.sum(axis=1) / np.maximum(n, 1), np.nan)


def transfer_profile(query_signature: np.ndarray, reference_signatures: np.ndarray, reference_profiles: np.ndarray,
                     *, k: int = 5) -> TranscriptionalTransfer:
    """Prior viability profile for the query from the ``k`` most similar references."""
    q = np.asarray(query_signature, dtype=float)
    R = np.asarray(reference_signatures, dtype=float)
    Y = np.asarray(reference_profiles, dtype=float)
    if R.ndim != 3 or len(R) == 0:
        return TranscriptionalTransfer(None, None, None, None, "NO_REFERENCE_DRUGS")
    if q.shape != R.shape[1:] or Y.ndim != 2 or len(Y) != len(R):
        return TranscriptionalTransfer(None, None, None, None, "SIGNATURE_AXIS_MISMATCH")
    if not np.isfinite(q[..., 0]).any():
        return TranscriptionalTransfer(None, None, None, None, "NO_QUERY_SIGNATURE")
    if k < 1:
        raise ValueError("k must be at least 1")
    sim = signature_similarity(q, R)
    usable = np.isfinite(sim)
    if not usable.any():
        return TranscriptionalTransfer(None, None, None, None, "NO_SHARED_CONDITION")
    order = np.argsort(-np.where(usable, sim, -np.inf), kind="stable")[: min(k, int(usable.sum()))]
    w = np.clip(sim[order], 0.0, None)
    if w.sum() <= 0:  # no positively similar reference: unweighted mean of the nearest
        w = np.ones(len(order))
    X = Y[order]
    have = np.isfinite(X)
    den = (w[:, None] * have).sum(axis=0)
    values = np.where(den > 0, (w[:, None] * np.where(have, X, 0.0)).sum(axis=0) / np.maximum(den, 1e-12), np.nan)
    return TranscriptionalTransfer(values, order, sim[order], float(sim[order[0]]))


def residualise(profile: np.ndarray, generic: np.ndarray) -> np.ndarray:
    """Profile minus its least-squares projection on the generic killing profile (both centred)."""
    y, g = np.asarray(profile, dtype=float), np.asarray(generic, dtype=float)
    ok = np.isfinite(y) & np.isfinite(g)
    out = np.full(len(y), np.nan)
    yc, gc = y[ok] - y[ok].mean(), g[ok] - g[ok].mean()
    out[ok] = yc - float(np.dot(yc, gc) / max(np.dot(gc, gc), 1e-12)) * gc
    return out


def selective_r(predicted: np.ndarray, observed: np.ndarray, generic: np.ndarray, *, min_lines: int = 50) -> float:
    """Pearson r between predicted and observed after removing the generic profile from each (NaN if undefined)."""
    a, b = residualise(predicted, generic), residualise(observed, generic)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < min_lines or np.std(a[ok]) < 1e-10 or np.std(b[ok]) < 1e-10:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])
