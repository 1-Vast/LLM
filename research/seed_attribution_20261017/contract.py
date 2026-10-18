"""One evaluation contract for the PRISM confirmation endpoint: aggregation, status, reference, threshold.

File summary
- Path: research/seed_attribution_20261017/contract.py
- Purpose: a single implementation of what `program_revision_20261017` states in its PROTOCOL.md and
  implements twice. `common.qualified_hits` (labels) aggregates the available X2/X3 replicates with a
  mean, so a pair with one replicate is known. `engine.Domain.__init__` (scores) builds the reference
  median from `(X2 + X3) / 2`, which is NaN for every one-replicate pair. This module is the one place
  that defines both.
- Contract (identical for labels and for score thresholds):
  - Aggregate: m = mean of the available confirmation replicates X2, X3 (at least one).
    ``n_rep`` is 0, 1 or 2. X1 never enters the endpoint (it is the probe readout).
  - Status: a pair is KNOWN iff n_rep >= 1. An unknown pair is never inactive and never a hit.
  - Reference median of drug d: the median of m over the KNOWN pairs of d on the reference lines
    (``ref_lines``). One-replicate pairs are included, because they are known pairs of the endpoint.
  - Threshold: thr_d = min(-1, median_d - 1), a log2 fold-change units value.
  - Qualified hit: KNOWN, every available replicate < 0, m <= thr_d.
  - A drug with no known pair on the reference lines has an UNDEFINED reference. Its threshold is NaN
    and it cannot be scored or labelled; `require_defined` refuses it by name (UNDEFINED_REFERENCE)
    rather than letting NaN sort a drug out of every ranking.
- Which historical observations may estimate the reference: the confirmation means of the SOURCE
  lines that are in the fitted history of the decision (training lines). A target line's own X2/X3
  must not enter, so a prospective-style use requires ``ref_lines`` disjoint from the target lines
  (`assert_prospective`). In the frozen Stage B/C the targets are non-source lines, so this holds.
  In the frozen development Bench the targets are source lines that are also in ``ref_lines``: that is
  reserved-outcome use, measured in `audit.py`.
- What the Gaussian score is: `crossing_probability(mean, var, thr)` is P(Normal(mean, var) <= thr).
  That is the probability that a latent mean falls below the threshold. It is not the probability of the
  complete qualified-hit event unless the sign condition, the single-replicate noise and the target
  mismatch (the models are trained on the mean of X1-X3, the endpoint is the mean of X2-X3) are
  modelled and validated. `sign_discordance` measures the sign condition on data; calibration is a
  reported diagnostic, never assumed.
- Interfaces: `replicate_summary`, `reference_median`, `threshold`, `Endpoint`, `endpoint`,
  `require_defined`, `assert_prospective`, `sign_discordance`, `crossing_probability`, `UNDEFINED_REFERENCE`.
- Depends on: numpy only (scipy is imported lazily for the normal CDF).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

HIT_LFC = -1.0
RELATIVE_MARGIN = 1.0
UNDEFINED_REFERENCE = "UNDEFINED_REFERENCE"
RESERVED_OVERLAP = "RESERVED_REFERENCE_OVERLAP"


def replicate_summary(X2, X3):
    """(m, n_rep): mean of the available replicates (NaN if none) and how many were available."""

    X2 = np.asarray(X2, dtype=float)
    X3 = np.asarray(X3, dtype=float)
    ok2, ok3 = np.isfinite(X2), np.isfinite(X3)
    n = ok2.astype(int) + ok3.astype(int)
    total = np.where(ok2, X2, 0.0) + np.where(ok3, X3, 0.0)
    m = np.where(n > 0, total / np.maximum(n, 1), np.nan)
    return m, n


def _mask(ref_lines, width: int) -> np.ndarray:
    ref = np.asarray(ref_lines)
    if ref.dtype == bool:
        if ref.shape != (width,):
            raise ValueError("reference mask has the wrong length")
        return ref
    mask = np.zeros(width, bool)
    mask[ref.astype(int)] = True
    return mask


def reference_median(m: np.ndarray, ref_lines) -> np.ndarray:
    """Per-drug median of the known confirmation means over the reference lines (NaN if none)."""

    cols = _mask(ref_lines, m.shape[1])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmedian(m[:, cols], axis=1)


def threshold(med: np.ndarray) -> np.ndarray:
    """thr = min(-1, median - 1); NaN stays NaN (an undefined reference is not silently a threshold)."""

    med = np.asarray(med, dtype=float)
    return np.where(np.isfinite(med), np.minimum(HIT_LFC, med - RELATIVE_MARGIN), np.nan)


@dataclass(frozen=True)
class Endpoint:
    """Labels and thresholds of one (X2, X3) matrix against one reference."""

    m: np.ndarray
    n_rep: np.ndarray
    known: np.ndarray
    negative: np.ndarray
    med: np.ndarray
    thr: np.ndarray
    hit: np.ndarray
    ref_mask: np.ndarray

    @property
    def undefined_reference(self) -> np.ndarray:
        return ~np.isfinite(self.thr)

    def singleton_share(self) -> float:
        """Share of known pairs that rest on one replicate."""

        k = int(self.known.sum())
        return float((self.n_rep == 1).sum() / k) if k else float("nan")


def endpoint(X2, X3, ref_lines) -> Endpoint:
    X2 = np.asarray(X2, dtype=float)
    X3 = np.asarray(X3, dtype=float)
    m, n = replicate_summary(X2, X3)
    known = n >= 1
    negative = np.where(np.isfinite(X2), X2 < 0, True) & np.where(np.isfinite(X3), X3 < 0, True)
    med = reference_median(m, ref_lines)
    thr = threshold(med)
    with np.errstate(invalid="ignore"):
        hit = known & negative & (m <= thr[:, None])
    return Endpoint(m, n, known, negative, med, thr, hit, _mask(ref_lines, X2.shape[1]))


def require_defined(ep: Endpoint, drug_rows) -> None:
    """Refuse by name when a decision drug has no reference (never rank it as 'worst')."""

    rows = np.asarray(drug_rows)
    bad = rows[ep.undefined_reference[rows]]
    if len(bad):
        raise ValueError(f"{UNDEFINED_REFERENCE}: {len(bad)} drugs have no known pair on the reference lines")


def assert_prospective(ref_lines, target_lines, width: int) -> None:
    """The reference must not contain a target line, or a target's own outcome shapes its threshold."""

    overlap = _mask(ref_lines, width) & _mask(target_lines, width)
    if overlap.any():
        raise ValueError(f"{RESERVED_OVERLAP}: {int(overlap.sum())} target lines are reference lines")


def sign_discordance(ep: Endpoint, line_mask=None) -> dict:
    """Known pairs with m <= thr that fail the every-replicate-negative condition."""

    with np.errstate(invalid="ignore"):
        crossing = ep.known & (ep.m <= ep.thr[:, None])
    if line_mask is not None:
        crossing = crossing & np.asarray(line_mask, bool)[None, :]
    failed = crossing & ~ep.negative
    n = int(crossing.sum())
    return {"threshold_crossing_pairs": n, "fail_sign_condition": int(failed.sum()),
            "share": float(failed.sum() / n) if n else float("nan")}


def crossing_probability(mean, var, thr):
    """P(latent mean <= thr) under a Gaussian predictive; NOT a calibrated qualified-hit probability."""

    from scipy.special import ndtr

    return ndtr((thr - mean) / np.sqrt(np.maximum(var, 1e-6)))
