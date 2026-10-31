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

Option: generic-axis removal (``fit_generic_axes`` on the references, then ``transfer_profile(...,
generic_axes=...)``). Before the similarity search each condition is centred on the reference mean and the
references' leading principal directions are projected out. Many compounds share these directions (largely a
cell-death and proliferation programme), so raw cosine pairs unrelated cytotoxic drugs by toxicity strength.
The default behaviour is unchanged.

Scope of the evidence: 2026-10-31, ``research/routes/functional_prediction/2026-10-31-generic-axis-transfer``,
frozen 2026-10-31T04:53:24Z and run once with 5 axes and k = 20.
* NCI-60 (CellMiner GI50 z-scores, 60 lines; 419 compounds with L1000, 293 active; references from the other
  nine folds): selective r 0.405 against 0.365 for the default, +0.041 [+0.023, +0.059]; +0.046
  [+0.029, +0.064] over raw cosine with k = 20, so the gain is not the larger k.
* PRISM 24Q2 REP.1M (101 new compounds, 32 active; references: the 19Q4 pool): +0.015 [-0.008, +0.037] over
  the default, the same direction but not significant.
* Independently re-derived by a verifier that never saw the run code: 139 of 139 checks passed.

Not shown:
* Better top-10% hit selection: +0.009 on NCI-60 and +0.007 on 24Q2, neither significant.
* The trust score on this scale (similarities after removal are smaller).
* Other transcriptomic platforms, doses, or lines outside the nine L1000 core lines.
* Learned alternatives did not beat it in development: two contrastive encoders and kernel ridge.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

VALIDATED_SCOPE = "prism19q4_selective_lfc_2.5uM_from_gse92742_landmark_10uM_9lines_6h24h"
GENERIC_AXES_SCOPE = "nci60_selective_gi50_z_from_gse92742_landmark_10uM_9lines_6h24h_generic_axes5_k20"
UNVALIDATED_SCOPE = "unvalidated_configuration"


@dataclass(frozen=True)
class TranscriptionalTransfer:
    values: np.ndarray | None          # predicted profile over the reference profiles' columns
    neighbours: np.ndarray | None      # indices of the k references used, most similar first
    similarities: np.ndarray | None    # their similarities
    trust: float | None                # top similarity (higher: the prior is more often right)
    refusal: str | None = None
    scope: str = VALIDATED_SCOPE


@dataclass(frozen=True)
class GenericAxes:
    means: np.ndarray          # conditions x genes: mean reference signature (NaN where no reference is measured)
    directions: np.ndarray     # conditions x n_axes x genes: leading principal directions (zero rows if fewer exist)
    n_axes: int


def fit_generic_axes(reference_signatures: np.ndarray, n_axes: int = 5) -> GenericAxes:
    """Per condition: the mean of the measured reference signatures and their ``n_axes`` leading principal directions."""
    R = np.asarray(reference_signatures, dtype=float)
    if n_axes < 0:
        raise ValueError("n_axes must be non-negative")
    conditions, genes = R.shape[1:]
    means = np.full((conditions, genes), np.nan)
    directions = np.zeros((conditions, n_axes, genes))
    for o in range(conditions):
        A = R[np.isfinite(R[:, o, 0]), o]
        if len(A) == 0:
            continue
        means[o] = A.mean(axis=0)
        m = min(n_axes, len(A) - 1)
        if m > 0:
            C = A - means[o]
            vals, vecs = np.linalg.eigh(C.T @ C)
            directions[o, :m] = vecs[:, np.argsort(vals)[::-1][:m]].T
    return GenericAxes(means, directions, n_axes)


def remove_generic_axes(signatures: np.ndarray, axes: GenericAxes) -> np.ndarray:
    """Centre each condition on the reference mean and project out the generic directions (unmeasured stays NaN)."""
    C = np.asarray(signatures, dtype=float) - axes.means
    proj = np.einsum("...og,oag->...oa", np.nan_to_num(C), axes.directions)
    return C - np.einsum("...oa,oag->...og", proj, axes.directions)


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
                     *, k: int = 5, generic_axes: GenericAxes | None = None) -> TranscriptionalTransfer:
    """Prior viability profile for the query from the ``k`` most similar references.

    With ``generic_axes`` (``fit_generic_axes`` on these references), similarity is computed after removing the
    shared directions. The validated configuration is 5 axes and k = 20; any other carries UNVALIDATED_SCOPE.
    """
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
    scope = VALIDATED_SCOPE
    if generic_axes is not None:
        if generic_axes.means.shape != q.shape:
            return TranscriptionalTransfer(None, None, None, None, "SIGNATURE_AXIS_MISMATCH")
        keep = np.isfinite(q[:, 0])  # only conditions measured for the query can contribute to similarity
        axes = GenericAxes(generic_axes.means[keep], generic_axes.directions[keep], generic_axes.n_axes)
        q, R = remove_generic_axes(q[keep], axes), remove_generic_axes(R[:, keep], axes)
        scope = GENERIC_AXES_SCOPE if (generic_axes.n_axes, k) == (5, 20) else UNVALIDATED_SCOPE
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
    return TranscriptionalTransfer(values, order, sim[order], float(sim[order[0]]), scope=scope)


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
