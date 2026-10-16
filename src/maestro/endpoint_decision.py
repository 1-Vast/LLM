"""Choose a follow-up measurement by its probability of meeting the experimental success criterion.

File summary
- Path: src/maestro/endpoint_decision.py
- Purpose: turn a response forecast into a follow-up decision ranked by what the experiment counts as
  success. The criterion is an observed mean beyond a raw effect threshold in the predicted direction,
  with every replicate agreeing. The rule replaces ranking by the largest standardised prediction.
- Core points:
  - Ranking by standardised prediction is misaligned with a raw-threshold, replicate-agreement hit.
    Features with a small reference spread look large in standard units while their predicted raw
    effect stays below the threshold. Replicate noise then decides whether the replicates agree.
  - `fit_endpoint_model` estimates three things from reference leave-one-out forecasts only:
    - a shrinkage slope that removes regression to the mean from selected actions;
    - the spread of the true mean around the shrunk forecast, net of replicate noise;
    - a two-parameter logistic recalibration of the chosen action's probability.
  - `EndpointModel.hit_probability` integrates over that spread and over replicate noise by Monte
    Carlo. Common random numbers keep the ranking stable across actions, and a fixed seed keeps it
    reproducible.
  - `choose` returns one decision per target line or per query. A decision whose calibrated
    probability is below `abstain_below` carries the refusal `HIT_PROBABILITY_BELOW_THRESHOLD`; the
    caller may then measure an anchor or wait instead.
  - `choose_validated` is the guarded entry point: it refuses (`ScopeRefused`) a declared scope other
    than `VALIDATED_SCOPE` (`SCOPE_NOT_VALIDATED`) and a missing abstention threshold
    (`ABSTENTION_THRESHOLD_REQUIRED`). `choose` itself stays permissive for development use and is
    unchanged, so a caller outside the validated scope must not use it to report a decision.
- Interfaces: `EndpointModel`, `EndpointDecision`, `ScopeRefused`, `signed_hits`, `pooled_replicate_sd`,
  `fit_endpoint_model`, `choose`, `choose_validated`.
- Depends on: numpy.

Evidence (2026-10-13, `research/collaboration_limits_20261013`): GCP histone peptides, 24 h, A375 anchor,
three target lines (A549, NPC, Astrocyte) never opened before the freeze, 47 compounds.
- With the same frozen forecast, hits per target-line decision rose from 55/141 to 77/141:
  +15.6 points [+9.2, +22.7], cluster sign-flip p = 5e-5.
- Calibrated probability at least 0.5 hit 81% of the time, against 38% below 0.5.
  Calibration-in-the-large was -0.03 per decision [-0.11, +0.05].
- Nearly all of the decision gain comes from ranking on the raw scale; the uncertainty model adds +2
  hits (p 0.68) and supplies the calibrated abstention.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

VALIDATED_SCOPE = "gcp_histone_peptides_24h_lvl3_minus_plate_dmso_a375_anchor_three_target_lines"
HIT_PROBABILITY_BELOW_THRESHOLD = "HIT_PROBABILITY_BELOW_THRESHOLD"
SCOPE_NOT_VALIDATED = "SCOPE_NOT_VALIDATED"
ABSTENTION_THRESHOLD_REQUIRED = "ABSTENTION_THRESHOLD_REQUIRED"
_CLIP = 1e-4


def signed_hits(replicates: np.ndarray, threshold: float) -> np.ndarray:
    """+1 / -1 where that direction is a hit for each feature, 0 otherwise.

    ``replicates`` is replicates x features. A hit needs at least two finite replicates, a mean beyond
    ``threshold`` and every finite replicate on the same side of zero.
    """
    replicates = np.asarray(replicates, dtype=float)
    finite = np.isfinite(replicates)
    count = finite.sum(0)
    mean = np.where(count > 0, np.nansum(replicates, 0) / np.maximum(count, 1), np.nan)
    up = np.where(finite, replicates > 0, True).all(0)
    down = np.where(finite, replicates < 0, True).all(0)
    out = np.zeros(replicates.shape[1], dtype=int)
    ok = (count >= 2) & np.isfinite(mean)
    out[ok & up & (mean > threshold)] = 1
    out[ok & down & (mean < -threshold)] = -1
    return out


def pooled_replicate_sd(cells: Sequence[np.ndarray]) -> np.ndarray:
    """Pooled within-cell replicate SD per feature from replicates x features arrays."""
    if not len(cells):
        raise ValueError("NO_REPLICATED_CELLS")
    width = np.asarray(cells[0]).shape[1]
    ss, df = np.zeros(width), np.zeros(width)
    for cell in cells:
        r = np.asarray(cell, dtype=float)
        fin = np.isfinite(r)
        cnt = fin.sum(0)
        mean = np.where(cnt > 0, np.nansum(r, 0) / np.maximum(cnt, 1), 0)
        ss += np.nansum(np.where(fin, (r - mean) ** 2, 0), 0)
        df += np.maximum(cnt - 1, 0)
    return np.sqrt(ss / np.maximum(df, 1))


@dataclass(frozen=True)
class EndpointModel:
    shrink: float                 # slope of observed on forecast (reference leave-one-out)
    sigma: np.ndarray             # targets x features: SD of the true mean around shrink x forecast
    tau: np.ndarray               # targets x features: replicate SD
    platt: tuple[float, float]    # logistic recalibration of a chosen action's probability
    threshold: float = 0.5
    draws: int = 4000
    seed: int = 0

    def hit_probability(self, forecast: np.ndarray, replicates: np.ndarray,
                        *, max_replicates: int | None = None) -> np.ndarray:
        """P(hit) for the forecast's sign, queries x targets x features.

        ``replicates`` (queries x targets) is the planned replicate count; fewer than two means no
        hit is possible. Draws are shared across the batch: ``max_replicates`` fixes their width so a
        query's probabilities do not depend on what else is in the batch.
        """
        forecast = np.asarray(forecast, dtype=float) * self.shrink
        replicates = np.asarray(replicates, dtype=int)
        if forecast.ndim != 3 or forecast.shape[1:] != self.sigma.shape or replicates.shape != forecast.shape[:2]:
            raise ValueError("AXIS_MISMATCH: forecast is queries x targets x features, replicates queries x targets")
        rng = np.random.default_rng(self.seed)
        width = int(max_replicates if max_replicates is not None else replicates.max(initial=0))
        if width < replicates.max(initial=0):
            raise ValueError("max_replicates is below a planned replicate count")
        z = rng.standard_normal((self.draws, 1, 1, 1))
        eps = rng.standard_normal((self.draws, max(width, 1), 1, 1))
        sign = np.where(forecast >= 0, 1.0, -1.0)
        out = np.zeros(forecast.shape)
        for i in range(len(forecast)):
            for t in range(forecast.shape[1]):
                n = int(replicates[i, t])
                if n < 2:
                    continue
                mu = (sign[i, t] * forecast[i, t])[None] + self.sigma[t][None] * z[:, 0, 0]
                reps = mu[:, None, :] + self.tau[t][None, None, :] * eps[:, :n, 0, :]
                out[i, t] = ((reps.mean(1) > self.threshold) & (reps > 0).all(1)).mean(0)
        return out

    def calibrated(self, probability: np.ndarray) -> np.ndarray:
        p = np.clip(np.asarray(probability, dtype=float), _CLIP, 1 - _CLIP)
        return 1 / (1 + np.exp(-(self.platt[0] + self.platt[1] * np.log(p / (1 - p)))))


@dataclass(frozen=True)
class EndpointDecision:
    query: int
    target: int
    feature: int
    sign: int
    p_hit: float
    calibrated: float
    refusal: str = ""


def _logistic_fit(p: np.ndarray, y: np.ndarray, iterations: int = 100) -> tuple[float, float]:
    """Maximum-likelihood a, b in logit(q) = a + b logit(p), by Newton's method."""
    p = np.clip(p, _CLIP, 1 - _CLIP)
    x = np.log(p / (1 - p))
    X = np.column_stack([np.ones_like(x), x])
    w = np.array([0.0, 1.0])
    for _ in range(iterations):
        q = 1 / (1 + np.exp(-(X @ w)))
        grad = X.T @ (y - q)
        hess = X.T @ (X * (q * (1 - q))[:, None]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(hess, grad)
        w = w + step
        if np.abs(step).max() < 1e-10:
            break
    return float(w[0]), float(w[1])


def fit_endpoint_model(loo_forecast: np.ndarray, truth: np.ndarray, hits: np.ndarray, tau: np.ndarray,
                       replicates: np.ndarray, *, threshold: float = 0.5, draws: int = 4000,
                       seed: int = 0) -> EndpointModel:
    """Fit from references: each reference forecast without itself.

    loo_forecast, truth, hits: references x targets x features. ``hits`` holds `signed_hits` of each
    reference cell. tau: targets x features. replicates: references x targets.
    """
    lp, lt = np.asarray(loo_forecast, dtype=float), np.asarray(truth, dtype=float)
    if lp.shape != lt.shape or lp.shape != np.shape(hits) or lp.shape[1:] != np.shape(tau):
        raise ValueError("AXIS_MISMATCH: forecasts, truth and hits are references x targets x features")
    ok = np.isfinite(lp) & np.isfinite(lt)
    shrink = float(np.sum(lp[ok] * lt[ok]) / np.sum(lp[ok] ** 2))
    tau = np.asarray(tau, dtype=float)
    replicates = np.asarray(replicates, dtype=int)
    rep_var = tau ** 2 / np.maximum(np.median(replicates, axis=0), 1)[:, None]

    def spread(exclude: int | None = None) -> np.ndarray:
        r = shrink * lp - lt
        if exclude is not None:
            r = np.delete(r, exclude, axis=0)
        var = np.nanmean(r ** 2, axis=0)
        return np.sqrt(np.maximum(var - rep_var, .25 * var))

    chosen_p, chosen_hit = [], []
    for i in range(len(lp)):
        held = EndpointModel(shrink, spread(i), tau, (0.0, 1.0), threshold, draws, seed)
        P = held.hit_probability(lp[i:i + 1], replicates[i:i + 1])[0]
        for t in range(lp.shape[1]):
            j = int(np.argmax(P[t]))
            chosen_p.append(P[t, j])
            chosen_hit.append(float(hits[i, t, j] == (1 if lp[i, t, j] >= 0 else -1)))
    platt = _logistic_fit(np.array(chosen_p), np.array(chosen_hit))
    return EndpointModel(shrink, spread(), tau, platt, threshold, draws, seed)


def choose(model: EndpointModel, forecast: np.ndarray, replicates: np.ndarray, *, per: str = "line",
           abstain_below: float | None = None, max_replicates: int | None = None) -> list[EndpointDecision]:
    """One decision per (query, target line) with ``per="line"``, or per query with ``per="query"``."""
    if per not in ("line", "query"):
        raise ValueError("per must be 'line' or 'query'")
    forecast = np.asarray(forecast, dtype=float)
    P = model.hit_probability(forecast, replicates, max_replicates=max_replicates)
    out = []
    for i in range(len(forecast)):
        options = [(t, int(np.argmax(P[i, t]))) for t in range(forecast.shape[1])]
        if per == "query":
            options = [max(options, key=lambda tj: P[i, tj[0], tj[1]])]
        for t, j in options:
            p = float(P[i, t, j])
            q = float(model.calibrated(p))
            refusal = HIT_PROBABILITY_BELOW_THRESHOLD if abstain_below is not None and q < abstain_below else ""
            out.append(EndpointDecision(i, t, j, 1 if forecast[i, t, j] >= 0 else -1, p, q, refusal))
    return out


class ScopeRefused(ValueError):
    """A decision was requested outside the scope the model was validated on, or without an abstention rule."""


def choose_validated(model: EndpointModel, forecast: np.ndarray, replicates: np.ndarray, *, scope: str,
                     abstain_below: float, per: str = "line", max_replicates: int | None = None) -> list[EndpointDecision]:
    """`choose` for a reported decision: the declared scope must be `VALIDATED_SCOPE` and abstention is mandatory."""
    if scope != VALIDATED_SCOPE:
        raise ScopeRefused(f"{SCOPE_NOT_VALIDATED}: {scope!r} is not {VALIDATED_SCOPE!r}")
    if isinstance(abstain_below, bool) or not isinstance(abstain_below, (int, float)) or not 0.0 < abstain_below < 1.0:
        raise ScopeRefused(f"{ABSTENTION_THRESHOLD_REQUIRED}: abstain_below must be a probability in (0, 1)")
    return choose(model, forecast, replicates, per=per, abstain_below=float(abstain_below), max_replicates=max_replicates)
