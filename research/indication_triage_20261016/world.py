"""World model of a new compound's response profile across the panel, conditioned on probes.

File summary
- Path: research/indication_triage_20261016/world.py
- Purpose: a numerical model every probing arm can share: a structure prior, a low-rank residual
  covariance across lines, a per-compound activity scale, Gaussian conditioning on probe wells,
  and event probabilities computed with the registered endpoint rule itself.
- Core points:
  - Prior mean: line means of the training compounds plus a similarity-weighted average of the
    k most Tanimoto-similar training profiles, shrunk toward the line means. Training priors are
    leave-one-out, so the residual covariance is not fitted on self-similarity.
  - Residuals are divided by a per-compound RMS scale (normalised to the median compound). The
    covariance of the normalised residuals is a rank-q factor plus a diagonal.
  - A compound's scale is unknown: a discrete prior over scale quantiles of the training set is
    updated by the probes' marginal likelihood (a Gaussian scale mixture). Inactive compounds
    keep small scales, active ones move to large scales.
  - Probes are noisy: the frozen `sigma_probe` from BUILD.json enters the likelihood and the
    conditioning.
  - Event probabilities come from posterior samples (pathwise conditioning with fixed per-compound
    random numbers). Each sample is residualised on the training generic profile, robust-z scored
    and called with the endpoint thresholds, so P(event) is the probability of the registered
    event, not a proxy score.
  - `point_mean` is the conventional single-scale Gaussian (ridge) completion used by the
    non-MAESTRO arms.
- Interfaces: `World`, `World.prior`, `World.posterior`, `World.event_probability`,
  `World.point_mean`, `World.sparse_design`, `call_score`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common import LFC_EVENT, MIN_EVENTS_ACTIVE, Z_EVENT, h, residualise, robust_z, tanimoto


@dataclass
class Posterior:
    mean_offset: np.ndarray        # (L,) prior mean m, kept for sampling
    probes: np.ndarray             # probed line indices with a finite observation
    residual: np.ndarray           # observation minus prior mean at those lines
    weights: np.ndarray            # posterior weight of each scale
    gains: list                    # per scale, (L, p) conditioning gain, or None without probes


class World:
    def __init__(self, Y: np.ndarray, fp: np.ndarray, G: np.ndarray, sigma_probe: float, *, rank: int = 48,
                 knn: int = 10, shrink: float = 1.0, n_scales: int = 10, samples: int = 64):
        Y = Y.astype(np.float64)
        finite = np.isfinite(Y)
        self.L = Y.shape[1]
        self.G = G.astype(np.float64)
        self.s2 = float(sigma_probe) ** 2
        self.knn, self.shrink, self.T = knn, shrink, samples
        self.mu = np.nanmean(Y, axis=0)
        self.C = np.where(finite, Y - self.mu, 0.0)
        self.fp = fp
        self.Ytrain = Y
        K = tanimoto(fp, fp)
        np.fill_diagonal(K, -1.0)
        M = self._prior_offsets(K)
        R = np.where(finite, self.C - M, 0.0)
        tau = np.sqrt((R ** 2).sum(1) / np.maximum(finite.sum(1), 1))
        tau = tau / np.median(tau)
        Rn = R / np.maximum(tau, 1e-6)[:, None]
        _, s, Vt = np.linalg.svd(Rn / np.sqrt(len(Rn)), full_matrices=False)
        self.V = (Vt[:rank].T * s[:rank])
        var_line = (Rn ** 2).sum(0) / np.maximum(finite.sum(0), 1)
        self.D = np.maximum(var_line - (self.V ** 2).sum(1), 0.05 * var_line.mean())
        levels = (np.arange(n_scales) + 0.5) / n_scales
        self.scales = np.quantile(tau, levels)
        self.scale_prior = np.full(n_scales, 1.0 / n_scales)
        X = np.column_stack([np.ones(self.L), self.G])
        self._X, self._pinv = X, np.linalg.pinv(X)
        self.tau_train = tau

    # ---- prior -------------------------------------------------------------------------------
    def _prior_offsets(self, K: np.ndarray) -> np.ndarray:
        k = min(self.knn, K.shape[1] - 1)
        top = np.argpartition(-K, k, axis=1)[:, :k]
        w = np.clip(np.take_along_axis(K, top, axis=1), 0.0, None)
        num = np.einsum("ik,ikl->il", w, self.C[top])
        return num / (w.sum(1, keepdims=True) + self.shrink)

    def prior(self, fp_query: np.ndarray) -> np.ndarray:
        """Prior mean profiles (n_query, L) from structure alone."""

        return self.mu + self._prior_offsets(tanimoto(fp_query, self.fp))

    # ---- conditioning ------------------------------------------------------------------------
    def _blocks(self, P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        VP = self.V[P]
        Spp = VP @ VP.T + np.diag(self.D[P])
        SLP = self.V @ VP.T
        SLP[P, np.arange(len(P))] += self.D[P]
        return Spp, SLP

    def posterior(self, m: np.ndarray, P, y, *, mixture: bool = True) -> Posterior:
        P = np.asarray(P, dtype=int)
        y = np.asarray(y, dtype=float)
        ok = np.isfinite(y)
        P, y = P[ok], y[ok]
        scales = self.scales if mixture else np.array([1.0])
        prior = self.scale_prior if mixture else np.array([1.0])
        if len(P) == 0:
            return Posterior(m, P, y, prior.copy(), [None] * len(scales))
        Spp, SLP = self._blocks(P)
        d = y - m[P]
        logs, gains = [], []
        eye = np.eye(len(P))
        for t in scales:
            A = t * t * Spp + self.s2 * eye
            c = np.linalg.cholesky(A)
            sol = np.linalg.solve(c.T, np.linalg.solve(c, d))
            logs.append(-0.5 * (d @ sol) - np.log(np.diag(c)).sum())
            gains.append((t * t * SLP) @ np.linalg.solve(c.T, np.linalg.solve(c, eye)))
        logs = np.array(logs) + np.log(prior)
        w = np.exp(logs - logs.max())
        return Posterior(m, P, d, w / w.sum(), gains)

    def point_mean(self, m: np.ndarray, P, y) -> np.ndarray:
        """Conventional completion: single-scale Gaussian conditional mean, probes plugged in."""

        post = self.posterior(m, P, y, mixture=False)
        out = m.copy() if post.gains[0] is None else m + post.gains[0] @ post.residual
        out[post.probes] = m[post.probes] + post.residual
        return out

    # ---- events ------------------------------------------------------------------------------
    def samples(self, post: Posterior, key: str) -> np.ndarray:
        rng = np.random.default_rng(h(key, "mc") % (2 ** 32))
        q = self.V.shape[1]
        Z = rng.standard_normal((self.T, q))
        E = rng.standard_normal((self.T, self.L))
        N = rng.standard_normal((self.T, self.L))
        counts = _allocate(post.weights, self.T)
        scales = self.scales if len(post.weights) == len(self.scales) else np.array([1.0])
        out = np.empty((self.T, self.L))
        start = 0
        sqrtD = np.sqrt(self.D)
        for t, n, gain in zip(scales, counts, post.gains):
            if n == 0:
                continue
            sl = slice(start, start + n)
            r = t * (Z[sl] @ self.V.T + E[sl] * sqrtD)
            if gain is not None and len(post.probes):
                innov = post.residual[None, :] - r[:, post.probes] - np.sqrt(self.s2) * N[sl][:, post.probes]
                r = r + innov @ gain.T
            out[sl] = post.mean_offset[None, :] + r
            start += n
        return out

    def event_probability(self, post: Posterior, key: str) -> tuple[np.ndarray, float]:
        """P(registered event) per line and P(active) for one compound."""

        Ys = self.samples(post, key)
        S = Ys - (Ys @ self._pinv.T) @ self._X.T
        Z = robust_z(S)
        ev = (Z <= Z_EVENT) & (Ys <= LFC_EVENT)
        return ev.mean(0), float((ev.sum(1) >= MIN_EVENTS_ACTIVE).mean())

    # ---- design ------------------------------------------------------------------------------
    def sparse_design(self, k: int) -> np.ndarray:
        """Greedy A-optimal lines: each pick maximises the total variance it removes, given probe noise."""

        S = self.V @ self.V.T + np.diag(self.D)
        chosen: list[int] = []
        for _ in range(min(k, self.L)):
            score = (S ** 2).sum(0) / (np.diag(S) + self.s2)
            score[chosen] = -np.inf
            j = int(np.argmax(score))
            chosen.append(j)
            g = S[:, j] / (S[j, j] + self.s2)
            S = S - np.outer(g, S[j])
        return np.array(chosen, dtype=int)


def _allocate(weights: np.ndarray, total: int) -> np.ndarray:
    """Largest-remainder split of `total` samples by weight (deterministic)."""

    raw = weights * total
    base = np.floor(raw).astype(int)
    rest = total - base.sum()
    if rest > 0:
        base[np.argsort(-(raw - base), kind="stable")[:rest]] += 1
    return base


def call_score(profile: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Conventional ranking of a point profile: pairs meeting the event rule first, then by robust z."""

    P = np.atleast_2d(profile)
    with np.errstate(invalid="ignore"):
        Z = robust_z(residualise(P, G))
        rule = (Z <= Z_EVENT) & (P <= LFC_EVENT)
    score = -Z + 1000.0 * rule
    return score if profile.ndim == 2 else score[0]
