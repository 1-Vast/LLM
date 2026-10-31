"""Similarity and transfer arms for the generic-axis transfer study (GAT, 2026-10-31).

Signatures are arrays of shape (compounds, options, genes); an option (line x time) is unmeasured when its
first gene is not finite. Profiles are arrays of shape (compounds, lines) with NaN for missing values.
"""
from __future__ import annotations

import numpy as np


def generic_directions(signatures: np.ndarray, d: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Per option: the mean signature and the top ``d`` principal directions (rows) of the measured ones."""
    out = []
    for o in range(signatures.shape[1]):
        have = np.isfinite(signatures[:, o, 0])
        A = signatures[have, o].astype(float)
        mu = A.mean(axis=0) if len(A) else np.zeros(signatures.shape[2])
        if d == 0 or len(A) < 2:
            out.append((mu, np.zeros((0, signatures.shape[2]))))
            continue
        C = A - mu
        vals, vecs = np.linalg.eigh(C.T @ C)
        top = np.argsort(vals)[::-1][:d]
        out.append((mu, vecs[:, top].T))
    return out


def remove_generic(signatures: np.ndarray, directions: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    """Centre each option on its reference mean and remove the given directions."""
    out = np.full(signatures.shape, np.nan)
    for o, (mu, V) in enumerate(directions):
        have = np.isfinite(signatures[:, o, 0])
        C = signatures[have, o].astype(float) - mu
        out[have, o] = C - (C @ V.T) @ V
    return out


def mean_cosine(query: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Mean cosine over options measured for both (query x reference); NaN when none is shared."""
    num = np.zeros((len(query), len(reference)))
    cnt = np.zeros((len(query), len(reference)))
    for o in range(query.shape[1]):
        hq, hr = np.isfinite(query[:, o, 0]), np.isfinite(reference[:, o, 0])
        Q = np.nan_to_num(query[:, o].astype(float))
        R = np.nan_to_num(reference[:, o].astype(float))
        nq, nr = np.linalg.norm(Q, axis=1), np.linalg.norm(R, axis=1)
        Q /= np.maximum(nq, 1e-12)[:, None]
        R /= np.maximum(nr, 1e-12)[:, None]
        m = (hq & (nq > 0))[:, None] & (hr & (nr > 0))[None, :]
        num += np.where(m, Q @ R.T, 0.0)
        cnt += m
    return np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)


def tanimoto(query_bits: np.ndarray, reference_bits: np.ndarray) -> np.ndarray:
    """Tanimoto similarity between binary fingerprints (query x reference); NaN for missing fingerprints."""
    q, r = query_bits.astype(float), reference_bits.astype(float)
    inter = q @ r.T
    union = q.sum(1)[:, None] + r.sum(1)[None, :] - inter
    S = np.where(union > 0, inter / np.maximum(union, 1e-12), 0.0)
    qmiss, rmiss = ~np.isfinite(q).all(1) | (q.sum(1) == 0), ~np.isfinite(r).all(1) | (r.sum(1) == 0)
    S[qmiss] = np.nan
    S[:, rmiss] = np.nan
    return S


def knn_transfer(similarity: np.ndarray, reference_profiles: np.ndarray, k: int) -> np.ndarray:
    """The maintained transfer rule for each query row: clipped-similarity-weighted mean of the top ``k``."""
    P = np.full((len(similarity), reference_profiles.shape[1]), np.nan)
    for i, s in enumerate(similarity):
        ok = np.isfinite(s)
        if not ok.any():
            continue
        order = np.argsort(-np.where(ok, s, -np.inf), kind="stable")[: min(k, int(ok.sum()))]
        w = np.clip(s[order], 0.0, None)
        if w.sum() <= 0:
            w = np.ones(len(order))
        X = reference_profiles[order]
        have = np.isfinite(X)
        den = (w[:, None] * have).sum(axis=0)
        P[i] = np.where(den > 0, (w[:, None] * np.where(have, X, 0.0)).sum(axis=0) / np.maximum(den, 1e-12), np.nan)
    return P


def selective_hit_precision(predicted: np.ndarray, observed: np.ndarray, generic: np.ndarray, sign: float,
                            *, top_fraction: float = 0.10, min_lines: int = 40) -> float:
    """Shared fraction of the top ``top_fraction`` lines by predicted and by observed selective sensitivity.

    Sensitivity is ``sign`` times the profile residual on the generic profile (sign -1 for log fold change,
    +1 for an activity z-score). NaN when fewer than ``min_lines`` lines are shared or the prediction is flat.
    """
    from virtual_cell.transcriptional_transfer import residualise

    a, b = residualise(predicted, generic), residualise(observed, generic)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < min_lines or np.std(a[ok]) < 1e-10:
        return float("nan")
    m = max(1, int(round(top_fraction * ok.sum())))
    pa, pb = sign * a[ok], sign * b[ok]
    top_a = set(np.argsort(-pa, kind="stable")[:m])
    top_b = set(np.argsort(-pb, kind="stable")[:m])
    return len(top_a & top_b) / m
