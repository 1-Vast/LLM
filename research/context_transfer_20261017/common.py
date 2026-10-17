"""Shared paths, the registered endpoint, folds and paired statistics for the context-transfer study.

File summary
- Path: research/context_transfer_20261017/common.py
- Purpose: one place for every rule that the development domain (PRISM 19Q4 cell lines) and the
  confirmation domain (Beat AML 2.0 primary patient samples) must apply identically.
- Core points:
  - A domain is a context x item response matrix Y (lower = stronger effect), a context feature
    matrix X (basal expression), context groups (dependence clusters) and item keys.
  - The endpoint is the selective event inherited from research/knowledge_reality_20261013 s5:
    robust z of the item's residual on the generic context profile <= -3, plus a unit-specific
    absolute gate (PRISM: log2 FC <= -1; Beat AML: none, because AUC has no comparable constant).
  - Folds and tie-breaks come from salted SHA-256 hashes of keys, never from outcomes.
- Interfaces: paths, `write_json`, `sha256`, `h`, `residualise`, `robust_z`, `selective_events`,
  `folds`, `tie_order`, `paired`, `cluster_means`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "tmp" / "context_transfer_20261017"
PRISM_RAW = ROOT / "data/external/prism_19q4/raw"
DEPMAP = ROOT / "data/external/depmap_19q4"
BEATAML = ROOT / "data/external/beataml2_20261017"

SEED = 20261017
Z_EVENT = -3.0
N_FOLDS = 5


def write_json(path, data) -> None:
    """LF bytes, so a digest does not depend on the platform."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(data, indent=1, default=_plain) + "\n").encode("utf-8"))


def _plain(x):
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.bool_):
        return bool(x)
    raise TypeError(type(x))


def sha256(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def h(key: str, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}:{key}".encode()).hexdigest(), 16)


def residualise(M: np.ndarray, G: np.ndarray, min_finite: int = 10):
    """Per item row: remove the least-squares intercept and slope on G over finite entries.

    Returns the residual matrix (NaN where M is NaN) and the (intercept, slope) per row.
    """

    out = np.full(M.shape, np.nan)
    coef = np.full((M.shape[0], 2), np.nan)
    for i, y in enumerate(M):
        f = np.isfinite(y) & np.isfinite(G)
        if f.sum() < min_finite:
            continue
        A = np.column_stack([np.ones(f.sum()), G[f]])
        beta, *_ = np.linalg.lstsq(A, y[f], rcond=None)
        coef[i] = beta
        out[i, f] = y[f] - A @ beta
    return out, coef


def robust_z(S: np.ndarray):
    """Per row robust z; also returns the row median and scaled MAD."""

    med = np.nanmedian(S, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(S - med), axis=1, keepdims=True) * 1.4826
    mad = np.maximum(mad, 1e-6)
    return (S - med) / mad, med[:, 0], mad[:, 0]


def selective_events(Y: np.ndarray, abs_gate: float | None, min_measured: int):
    """The registered endpoint on a context x item matrix Y (lower = stronger).

    G is the per-context median over items. For each item with at least `min_measured` finite
    contexts, the residual on [1, G] is robust-z scored across contexts; an event is z <= -3 and,
    when `abs_gate` is given, Y <= abs_gate. Unmeasured pairs are never events.
    """

    G = np.nanmedian(Y, axis=1)
    S, _ = residualise(Y.T, G)
    Z, _, _ = robust_z(S)
    measured = np.isfinite(Y.T).sum(1) >= min_measured
    with np.errstate(invalid="ignore"):
        ev = (Z <= Z_EVENT) & measured[:, None]
        if abs_gate is not None:
            ev &= Y.T <= abs_gate
    return ev.T & np.isfinite(Y), G


def folds(keys, salt: str, n: int = N_FOLDS) -> np.ndarray:
    return np.array([h(str(k), salt) % n for k in keys])


def tie_order(keys, salt: str) -> np.ndarray:
    """A fixed pseudo-random value per key in [0, 1), used only to break exact ties."""

    return np.array([(h(str(k), salt) % (10 ** 12)) / 1e12 for k in keys])


def cluster_means(values: np.ndarray, groups) -> tuple[np.ndarray, list]:
    groups = np.asarray(groups)
    labels = sorted(set(groups.tolist()))
    return np.array([values[groups == g].mean() for g in labels]), labels


def paired(diff: np.ndarray, groups, draws: int = 10000, boot: int = 2000, seed: int = SEED) -> dict:
    """Paired comparison over contexts with dependence clusters.

    Mean of per-context differences; cluster bootstrap 95% interval (clusters resampled with
    replacement, contexts kept intact); one-sided sign-flip p over cluster means (mean > 0).
    """

    d = np.asarray(diff, dtype=float)
    groups = np.asarray(groups)
    labels = sorted(set(groups.tolist()))
    index = [np.flatnonzero(groups == g) for g in labels]
    rng = np.random.default_rng(seed)
    sums = np.array([d[i].sum() for i in index])
    sizes = np.array([len(i) for i in index])
    picks = rng.integers(0, len(labels), size=(boot, len(labels)))
    boots = sums[picks].sum(1) / sizes[picks].sum(1)
    cm = sums / sizes
    signs = rng.choice([-1.0, 1.0], size=(draws, len(labels)))
    w = sizes / sizes.sum()
    obs = float((cm * w).sum())
    null = (signs * cm * w).sum(1)
    p = float((1 + (null >= obs - 1e-12).sum()) / (draws + 1))
    return {
        "n_contexts": int(len(d)),
        "n_clusters": int(len(labels)),
        "mean": float(d.mean()),
        "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "p_one_sided": p,
        "positive_contexts": int((d > 0).sum()),
        "negative_contexts": int((d < 0).sum()),
    }
