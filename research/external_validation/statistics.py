"""Cluster-bootstrap rates and paired differences, bounds, and forecast calibration metrics.

File summary
- Path: research/external_validation/statistics.py
- Purpose: the inference the protocol registers, in one place, so every report and every gate
  reads the same numbers.
- Core points:
  - The bootstrap resamples independent units (never episodes) with replacement; a rate or a
    paired difference is a ratio of unit sums, so units with more episodes weigh more, exactly as
    the point estimate does.
  - All comparisons within one tier draw the same unit indices (one seed, one sorted unit list),
    so their intervals share random numbers.
  - Calibration intercept and slope are logistic recalibration fits.  Well-supported strata use
    the historical unpenalised fit; thin or separated strata use a bounded ridge fallback so a
    diagnostic cannot overflow or claim an implausibly precise fit.
- Depends on: numpy, pandas
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

SEED = 20260927
DRAWS = 2000
EPISODE = ["compound", "h1", "h2"]


def outcome_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-episode endpoint indicators from the runner's `final` field."""
    out = frame.copy()
    out["correct"] = (out.final == "correct").astype(float)
    out["wrong"] = out.final.isin(("wrong", "exhausted")).astype(float)
    out["decided"] = out.final.isin(("correct", "wrong", "exhausted")).astype(float)
    out["deferred"] = (out.final == "deferred").astype(float)
    return out


def draws(n_units: int, *, seed: int = SEED, n: int = DRAWS) -> np.ndarray:
    return np.random.default_rng(seed).integers(n_units, size=(n, n_units))


def _interval(sums: np.ndarray, counts: np.ndarray, index: np.ndarray, level: float) -> list[float]:
    boot = sums[index].sum(axis=1) / np.maximum(counts[index].sum(axis=1), 1e-12)
    tail = (1 - level) / 2
    return np.quantile(boot, [tail, 1 - tail]).tolist()


def rate(frame: pd.DataFrame, metric: str, unit: str, *, level: float = 0.95, seed: int = SEED) -> dict:
    """Mean of `metric` over episodes with a unit-cluster bootstrap interval."""
    blocks = frame.groupby(frame[unit].astype(str))[metric].agg(["sum", "size"]).sort_index()
    sums, counts = blocks["sum"].to_numpy(float), blocks["size"].to_numpy(float)
    index = draws(len(blocks), seed=seed)
    return {"estimate": float(frame[metric].mean()), "ci": _interval(sums, counts, index, level),
            "level": level, "units": int(len(blocks)), "episodes": int(len(frame))}


def paired(frame: pd.DataFrame, left: str, right: str, metric: str, unit: str, *, level: float = 0.95,
           seed: int = SEED, policy: str = "policy") -> dict:
    """Mean paired difference left - right over identical episodes, clustered by `unit`."""
    a = frame[frame[policy] == left].set_index(EPISODE)
    b = frame[frame[policy] == right].set_index(EPISODE)
    if len(a) != len(b) or not a.index.sort_values().equals(b.index.sort_values()):
        raise ValueError(f"{left} and {right} were not run on the same episodes")
    delta = pd.DataFrame({"delta": a[metric] - b[metric].reindex(a.index), "unit": a[unit].astype(str)})
    blocks = delta.groupby("unit").delta.agg(["sum", "size"]).sort_index()
    sums, counts = blocks["sum"].to_numpy(float), blocks["size"].to_numpy(float)
    index = draws(len(blocks), seed=seed)
    return {"left": left, "right": right, "metric": metric, "unit": unit, "difference": float(delta.delta.mean()),
            "ci": _interval(sums, counts, index, level), "level": level, "units": int(len(blocks)),
            "episodes": int(len(delta))}


def wilson_upper(k: float, n: float, z: float = 1.959964) -> float:
    if n <= 0:
        return float("nan")
    p = k / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float(min(1.0, (centre + spread) / (1 + z * z / n)))


# ------------------------------------------------------------------------------ calibration
def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _expit(x: np.ndarray) -> np.ndarray:
    """Overflow-safe logistic transform.

    ``np.exp(-eta)`` overflows for the large intermediate values produced by a separated
    stratum.  Clipping only the argument to the exponential preserves the useful range while
    making the failure mode deterministic and warning-free.
    """
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    positive = x >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-np.minimum(x[positive], 709.0)))
    exp_x = np.exp(np.maximum(x[~positive], -709.0))
    out[~positive] = exp_x / (1.0 + exp_x)
    return out


def _newton(X: np.ndarray, y: np.ndarray, offset: np.ndarray, iterations: int = 50,
            *, penalty: float = 0.0, max_abs_beta: float = 40.0) -> np.ndarray | None:
    """Fit a small logistic recalibration model by damped IRLS.

    The unpenalised path intentionally remains the default for compatibility with the original
    large-sample numbers.  A positive ridge penalty is used only by the thin-stratum fallback.
    Returning ``None`` on separation lets the caller report the direct risk bound instead of a
    huge, meaningless calibration coefficient.
    """
    beta = np.zeros(X.shape[1], dtype=float)
    identity = np.eye(X.shape[1], dtype=float)
    for _ in range(iterations):
        eta = X @ beta + offset
        mu = _expit(eta)
        w = np.maximum(mu * (1.0 - mu), 1e-12)
        gradient = X.T @ (y - mu) - penalty * beta
        hessian = X.T @ (X * w[:, None]) + penalty * identity
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(step)):
            return None

        # A line search prevents a single Newton jump from crossing into a numerically flat
        # region.  It is a no-op for the ordinary, well-supported fit.
        current = float(np.sum(y * np.log(np.clip(mu, 1e-15, 1.0)) +
                              (1.0 - y) * np.log(np.clip(1.0 - mu, 1e-15, 1.0))) -
                        0.5 * penalty * np.sum(beta * beta))
        scale = 1.0
        accepted = False
        while scale >= 1e-4:
            candidate = beta + scale * step
            if np.max(np.abs(candidate)) > max_abs_beta:
                scale *= 0.5
                continue
            candidate_mu = _expit(X @ candidate + offset)
            candidate_score = float(np.sum(y * np.log(np.clip(candidate_mu, 1e-15, 1.0)) +
                                          (1.0 - y) * np.log(np.clip(1.0 - candidate_mu, 1e-15, 1.0))) -
                                    0.5 * penalty * np.sum(candidate * candidate))
            if candidate_score >= current - 1e-12:
                beta = candidate
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            return None
        if np.max(np.abs(scale * step)) < 1e-10:
            break
    return beta if np.all(np.isfinite(beta)) and np.max(np.abs(beta)) <= max_abs_beta else None


MIN_CALIBRATION_SUPPORT = 20


def _fit_calibration(x: np.ndarray, y: np.ndarray, *, varied: bool) -> tuple[float | None, float | None, str]:
    """Fit calibration, using bounded regularisation when support is thin or separated.

    The fallback is deliberately conservative: coefficients are marked as diagnostic only and
    the Wilson bound on the observed labels remains the direct risk estimate.  A half-unit
    Jeffreys/Beta-Binomial prior keeps the fallback finite without changing the established fit
    for strata with at least ``MIN_CALIBRATION_SUPPORT`` observations.
    """
    n = len(y)
    if n == 0:
        return None, None, "empty"
    design_intercept = np.ones((n, 1))
    design_slope = np.column_stack([np.ones(n), x])
    # Keep the historical ``None`` result for a large, single-class stratum: neither a
    # recalibration intercept nor a slope is identified there.  Thin strata use the bounded
    # prior below so the diagnostic remains finite and explicitly marked unstable.
    if n >= MIN_CALIBRATION_SUPPORT and not varied:
        return None, None, "unavailable_single_class"
    if n >= MIN_CALIBRATION_SUPPORT and varied:
        intercept = _newton(design_intercept, y, x)
        slope = _newton(design_slope, y, np.zeros(n)) if np.ptp(x) > 1e-9 else None
        # Separation can still occur in a nominally large stratum.  Fall through to the
        # bounded fit rather than returning a divergent coefficient.
        if intercept is not None and (np.ptp(x) <= 1e-9 or slope is not None):
            return float(intercept[0]), None if slope is None else float(slope[1]), "unpenalized"

    # Positive penalty gives a finite Beta-Binomial/Jeffreys-style shrinkage fallback for all-
    # one/all-zero labels and tiny strata.  Keep the slope absent when the forecast has no
    # variation: it is not identified even after regularisation.
    intercept = _newton(design_intercept, y, x, penalty=0.5)
    slope = _newton(design_slope, y, np.zeros(n), penalty=0.5) if np.ptp(x) > 1e-9 else None
    return (None if intercept is None else float(intercept[0]),
            None if slope is None else float(slope[1]), "beta_binomial_fallback")


def calibration_metrics(p, y, *, bins: int = 10) -> dict:
    """Calibration diagnostics with finite small-sample fits and direct observed-risk bounds."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(p)
    out = {"n": int(n), "support": int(n)}
    if n == 0:
        return out
    q = np.clip(p, 1e-6, 1 - 1e-6)
    out.update({"mean_forecast": float(p.mean()), "observed": float(y.mean()),
                "brier": float(np.mean((p - y) ** 2)),
                "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))})
    index = np.minimum((p * bins).astype(int), bins - 1)
    reliability, ece = [], 0.0
    for b in range(bins):
        mask = index == b
        if mask.any():
            gap = abs(p[mask].mean() - y[mask].mean())
            ece += mask.mean() * gap
            reliability.append({"bin": b, "n": int(mask.sum()), "forecast": float(p[mask].mean()),
                                "observed": float(y[mask].mean())})
    out["ece"] = float(ece)
    out["reliability"] = reliability
    x = _logit(p)
    varied = 0 < y.sum() < n
    intercept, slope, method = _fit_calibration(x, y, varied=varied)
    out["intercept"] = intercept
    out["slope"] = slope
    out["calibration_method"] = method
    out["calibration_stable"] = method == "unpenalized"
    # This is a direct bound on the realised label rate, rather than a bound inferred from the
    # forecast calibration.  It is conservative for tiny or completely separated strata.
    # The half-unit prior is also useful as a stable point estimate when a stratum is too thin
    # to support a recalibration coefficient.  Keep the observed Wilson bound alongside it: the
    # former is a smoothed descriptive rate, the latter is the conservative direct risk bound.
    out["beta_binomial_rate"] = float((y.sum() + 0.5) / (n + 1.0))
    out["beta_binomial_alpha"] = float(y.sum() + 0.5)
    out["beta_binomial_beta"] = float(n - y.sum() + 0.5)
    out["observed_wilson_upper95"] = wilson_upper(float(y.sum()), n)
    out["direct_rate_upper95"] = out["observed_wilson_upper95"]
    return out
