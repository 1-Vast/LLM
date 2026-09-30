"""Profile-prediction metrics after Cell-Eval (State), Tahoe-x1 and PRESAGE, in the validator's geometry.

File summary
- Path: research/incontext_world/metrics.py
- Purpose: score a predicted shift against the measured one, and give the world model the same
  projected-cosine similarity the registered validator uses.
- Core points:
  - `pearson_delta` is Tahoe-x1's and State's Pearson delta. A constant prediction scores 0, the
    null-delta convention.
  - `centred_cosine` is PRESAGE's direction metric: the cosine after subtracting the mean response
    at the target condition. It removes the response every compound shares, which the Pearson delta
    rewards.
  - `discrimination` is State's perturbation discrimination score with Manhattan distance, ties
    counted half, normalised by T - 1 so that a random prediction scores 0 and a perfect one 1.
  - `effect_auroc` is PRESAGE's effect-size stage: the prediction's Euclidean norm as a score for
    whether the target was detected.
  - `projected_cosine` removes the shared axis of the references at a condition before the cosine,
    exactly as `dynamic_world_model.common.heldout_class_scores` does. `phenocopy` is PRESAGE's
    phenocopy idea in that geometry: the overlap of the nearest references of prediction and truth.
- Interfaces: `pearson_delta`, `centred_cosine`, `mse`, `discrimination`, `effect_auroc`,
  `projected_cosine`, `phenocopy`
- Depends on: numpy
"""
from __future__ import annotations

import numpy as np


def _unit(v: np.ndarray) -> np.ndarray | None:
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else None


def pearson_delta(pred: np.ndarray, truth: np.ndarray) -> float:
    a = pred - pred.mean()
    b = truth - truth.mean()
    denom = float(np.sqrt((a @ a) * (b @ b)))
    return float(a @ b) / denom if denom > 1e-12 else 0.0


def centred_cosine(pred: np.ndarray, truth: np.ndarray, centre: np.ndarray) -> float:
    a, b = _unit(pred - centre), _unit(truth - centre)
    return float(a @ b) if a is not None and b is not None else 0.0


def mse(pred: np.ndarray, truth: np.ndarray) -> float:
    return float(np.mean((pred - truth) ** 2))


def discrimination(preds: np.ndarray, truths: np.ndarray) -> np.ndarray:
    """Per-item normalised inverse discrimination: 1 - 2 r_t / (T - 1), r_t = truths closer to pred_t than truth_t."""
    T = len(truths)
    if T < 2:
        return np.full(T, np.nan)
    dist = np.abs(preds[:, None, :] - truths[None, :, :]).sum(-1)
    own = np.diag(dist)[:, None]
    closer = (dist < own - 1e-12).sum(1)
    ties = (np.abs(dist - own) <= 1e-12).sum(1) - 1
    rank = closer + 0.5 * ties
    return 1.0 - 2.0 * rank / (T - 1)


def effect_auroc(scores, labels) -> float:
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, bool)
    pos, neg = scores[labels], scores[~labels]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


def projected_cosine(R: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Cosine of `v` to every row of R after removing R's shared axis (sum of rows) from both."""
    R = np.asarray(R, float)
    v = np.asarray(v, float)
    if len(R) == 0:
        return np.zeros(0)
    u = _unit(R.sum(0))
    if u is None:
        Rp, vp = R, v
    else:
        Rp = R - np.outer(R @ u, u)
        vp = v - (v @ u) * u
    rn = np.linalg.norm(Rp, axis=1)
    vn = float(np.linalg.norm(vp))
    out = np.zeros(len(R))
    ok = (rn > 1e-12) & (vn > 1e-12)
    out[ok] = (Rp[ok] @ vp) / (rn[ok] * vn)
    return out


def projected_gram_cosine(R: np.ndarray) -> np.ndarray:
    """Pairwise projected cosines among the rows of R (same geometry as `projected_cosine`)."""
    R = np.asarray(R, float)
    u = _unit(R.sum(0)) if len(R) else None
    Rp = R - np.outer(R @ u, u) if u is not None else R
    n = np.linalg.norm(Rp, axis=1)
    n = np.where(n > 1e-12, n, np.inf)
    return (Rp @ Rp.T) / np.outer(n, n)


def phenocopy(pred: np.ndarray, truth: np.ndarray, references: np.ndarray, k: int = 5) -> float:
    """Overlap of the k nearest references (projected cosine) of the prediction and of the truth."""
    if len(references) < k:
        return float("nan")
    a = set(np.argsort(-projected_cosine(references, pred), kind="stable")[:k])
    b = set(np.argsort(-projected_cosine(references, truth), kind="stable")[:k])
    return len(a & b) / k
