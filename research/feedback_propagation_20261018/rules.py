"""Feedback-update rules: observed history -> scores for every (compound, line) pair.

File summary
- Path: research/feedback_propagation_20261018/rules.py
- Purpose: every update program the study compares, as a function of the same inputs: the fold (world,
  prior, generic profile), the compound index and its history `(P, y)` of probed lines and noisy values.
  A rule returns a score per line (higher = more likely a registered selective event). Rules never read
  `Fold.hidden`; the loop passes only what the oracle returned.
- Rules (all share the base predictor: structure prior + low-rank-plus-diagonal line covariance):
  - `prior`: no feedback (zero arm).
  - `ridge`: Gaussian conditional mean with the probed values plugged in, single unit scale. This is the
    registered ridge-plus-feedback comparator (`World.point_mean`).
  - `mixture_mean`: the same update with an empirical-Bayes scale (posterior mean over the world's scale grid).
  - `mixture_event`: the world's posterior probability of the registered event (the existing MAESTRO update).
  - `knn`: analogue regression on the probed lines (conventional adaptive/conditional comparator).
  - `empcov`: Gaussian conditional with the full-rank empirical covariance of the training residuals.
  - `repair`: the registered feedback-update repair (see `repair_*` and PROTOCOL.md).
- Also: `lopo` (closed-form leave-one-probe-out standardised residuals of the Gaussian update), used for
  the propagation-failure diagnosis.
- Interfaces: `RULES`, `score(rule, fold, i, P, y, **params)`, `lopo`, `emp_cov`.
"""
from __future__ import annotations

import warnings

import numpy as np

from bench import call_score, tc


def _clean(P, y):
    P = np.asarray(P, dtype=int)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(y)
    return P[ok], y[ok]


# ---------------------------------------------------------------- base Gaussian update
def gaussian_blocks(fold, P: np.ndarray, Sigma: tuple | None = None):
    """(Spp, SLP) of the base covariance (low-rank plus diagonal) or of a supplied dense covariance."""

    if Sigma is not None:
        S = Sigma
        return S[np.ix_(P, P)], S[:, P]
    return fold.world._blocks(P)


def conditional_mean(fold, m: np.ndarray, P, y, *, Sigma=None, noise_var: np.ndarray | float | None = None,
                     scale: float = 1.0) -> np.ndarray:
    """Gaussian conditional mean of the full profile; the probed values are plugged in at their lines.

    `noise_var` may be per probe (robust reweighting) and `scale` multiplies the signal covariance.
    """

    P, y = _clean(P, y)
    if len(P) == 0:
        return m.copy()
    Spp, SLP = gaussian_blocks(fold, P, Sigma)
    s2 = fold.world.s2 if noise_var is None else noise_var
    A = scale * scale * Spp + np.diag(np.broadcast_to(np.asarray(s2, float), (len(P),)).copy())
    d = y - m[P]
    out = m + (scale * scale) * SLP @ np.linalg.solve(A, d)
    out[P] = m[P] + d
    return out


def lopo(fold, m: np.ndarray, P, y, *, scale: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Leave-one-probe-out standardised residuals and predictive SDs of the Gaussian update.

    For the Gaussian model with covariance A over the probes, the leave-one-out residual is
    (A^-1 d)_p / (A^-1)_pp and its variance is 1 / (A^-1)_pp, so r_p = (A^-1 d)_p / sqrt((A^-1)_pp) is
    N(0, 1) when the propagation is right. Returns (r, predictive SD of y_p given the others).
    """

    P, y = _clean(P, y)
    if len(P) < 2:
        return np.zeros(len(P)), np.full(len(P), np.nan)
    Spp, _ = gaussian_blocks(fold, P)
    A = scale * scale * Spp + fold.world.s2 * np.eye(len(P))
    Ainv = np.linalg.inv(A)
    d = y - m[P]
    diag = np.diag(Ainv)
    return (Ainv @ d) / np.sqrt(diag), 1.0 / np.sqrt(diag)


# ---------------------------------------------------------------- comparator rules
def _score_prior(fold, i, P, y, **_):
    return call_score(fold.prior[i], fold.G)


def _score_ridge(fold, i, P, y, **_):
    return call_score(conditional_mean(fold, fold.prior[i], P, y), fold.G)


def mixture_profile(fold, i, P, y) -> np.ndarray:
    """Posterior-mean profile under the world's scale grid; vector solves only (same weights as World.posterior)."""

    P, y = _clean(P, y)
    m = fold.prior[i]
    w = fold.world
    if len(P) == 0:
        return m.copy()
    Spp, SLP = w._blocks(P)
    d = y - m[P]
    eye = np.eye(len(P))
    logs, means = [], []
    for t in w.scales:
        c = np.linalg.cholesky(t * t * Spp + w.s2 * eye)
        alpha = np.linalg.solve(c.T, np.linalg.solve(c, d))
        logs.append(-0.5 * (d @ alpha) - np.log(np.diag(c)).sum())
        means.append((t * t) * (SLP @ alpha))
    logs = np.array(logs) + np.log(w.scale_prior)
    wt = np.exp(logs - logs.max())
    wt /= wt.sum()
    out = m + np.tensordot(wt, np.stack(means), axes=1)
    out[P] = m[P] + d
    return out


def _score_mixture_mean(fold, i, P, y, **_):
    return call_score(mixture_profile(fold, i, P, y), fold.G)


def _score_mixture_event(fold, i, P, y, **_):
    P, y = _clean(P, y)
    post = fold.world.posterior(fold.prior[i], P, y, mixture=True)
    return fold.world.event_probability(post, str(fold.cores[i]))[0]


def knn_profile(fold, i, P, y, K: int = 20) -> np.ndarray:
    P, y = _clean(P, y)
    w = fold.world
    if len(P) == 0:
        return fold.prior[i].copy()
    ref = w.Ytrain[:, P]
    diff = ref - y[None, :]
    both = np.isfinite(diff)
    dist = np.where(both, diff ** 2, 0.0).sum(1) / np.maximum(both.sum(1), 1)
    dist[both.sum(1) < max(1, len(P) // 2)] = np.inf
    nn = np.argsort(dist, kind="stable")[:K]
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pred = np.nanmean(w.Ytrain[nn], axis=0)
    pred = np.where(np.isfinite(pred), pred, w.mu)
    pred[P] = y
    return pred


def _score_knn(fold, i, P, y, K: int = 20, **_):
    return call_score(knn_profile(fold, i, P, y, K), fold.G)


def emp_cov(fold, alpha: float) -> np.ndarray:
    """Dense empirical covariance of the training residuals (same normalisation as the world), shrunk to its diagonal."""

    key = ("empcov", float(alpha))
    if key not in fold.cache:
        w = fold.world
        finite = np.isfinite(w.Ytrain)
        K = tc.tanimoto(w.fp, w.fp)
        np.fill_diagonal(K, -1.0)
        R = np.where(finite, w.C - w._prior_offsets(K), 0.0)
        Rn = R / np.maximum(w.tau_train, 1e-6)[:, None]
        count = finite.astype(np.float64).T @ finite.astype(np.float64)
        S = (Rn.T @ Rn) / np.maximum(count, 1.0)
        fold.cache[key] = (1.0 - alpha) * S + alpha * np.diag(np.diag(S))
    return fold.cache[key]


def _score_empcov(fold, i, P, y, alpha: float = 0.1, **_):
    return call_score(conditional_mean(fold, fold.prior[i], P, y, Sigma=emp_cov(fold, alpha)), fold.G)


def _score_anchored(fold, i, P, y, K: int = 10, lam: float = 1.0, **_):
    import repair
    return call_score(repair.anchored_profile(fold, i, P, y, K, lam), fold.G)


def _score_repair(fold, i, P, y, **params):
    import repair
    return repair.score_repair(fold, i, P, y, **params)


class ForestModel:
    """Multi-output random forest from the values at a fixed set of lines to the training residual profile.

    Conventional nonlinear conditional regression. It needs the same lines for every compound (fixed designs only).
    Training inputs are the training compounds' own values at those lines plus the study's probe-noise model, so it
    sees the same measurement process as the arms do; targets are the top `rank` principal scores of the centred
    training profiles (missing cells filled with the line mean), reconstructed to a full profile at prediction time.
    """

    def __init__(self, fold, lines: np.ndarray, n_trees: int = 100, rank: int = 48, seed: int = 20261018):
        from sklearn.ensemble import RandomForestRegressor
        from bench import probe_sd

        w = fold.world
        self.lines = np.asarray(lines, dtype=int)
        Y = w.Ytrain
        filled = np.where(np.isfinite(Y), Y, w.mu[None, :])
        rng = np.random.default_rng(seed)
        sd = probe_sd(np.where(np.isfinite(Y[:, self.lines]), Y[:, self.lines], 0.0),
                      {"noise_bins": fold.noise_bins, "noise_factor": fold.noise_factor})
        X = filled[:, self.lines] + sd * rng.standard_normal(sd.shape)
        C = filled - w.mu[None, :]
        _, _, Vt = np.linalg.svd(C, full_matrices=False)
        self.Vt = Vt[:rank]
        self.mu = w.mu
        self.model = RandomForestRegressor(n_estimators=n_trees, min_samples_leaf=5, max_features=0.33, n_jobs=-1,
                                           random_state=seed).fit(X, C @ self.Vt.T)

    def profile(self, P, y) -> np.ndarray:
        x = np.full(len(self.lines), np.nan)
        pos = {int(l): k for k, l in enumerate(self.lines)}
        for l, v in zip(P, y):
            if int(l) in pos:
                x[pos[int(l)]] = v
        x = np.where(np.isfinite(x), x, self.mu[self.lines])
        return self.mu + self.model.predict(x[None, :])[0] @ self.Vt


def _score_forest(fold, i, P, y, **_):
    P = np.asarray(P, dtype=int)
    key = ("forest", tuple(sorted(int(l) for l in P)))
    if key not in fold.cache:
        fold.cache[key] = ForestModel(fold, np.array(sorted(int(l) for l in P)))
    prof = fold.cache[key].profile(P, y)
    ok = np.isfinite(y)
    prof = prof.copy()
    prof[np.asarray(P)[ok]] = np.asarray(y)[ok]
    return call_score(prof, fold.G)


RULES = {"prior": _score_prior, "ridge": _score_ridge, "mixture_mean": _score_mixture_mean,
         "mixture_event": _score_mixture_event, "knn": _score_knn, "empcov": _score_empcov,
         "anchored": _score_anchored, "repair": _score_repair, "forest": _score_forest}


def score(rule: str, fold, i: int, P, y, **params) -> np.ndarray:
    return RULES[rule](fold, i, P, y, **params)
