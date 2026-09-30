"""In-context state transitions: a compound's profile at an unmeasured condition from its measured prompts.

File summary
- Path: research/incontext_world/transition.py
- Purpose: the virtual-cell observation model of the in-context world model. Given a compound's
  measured shift at a prompt condition p, predict its shift at a target condition c, from
  references (other-fold compounds) measured at both.
- Core points:
  - Baselines follow Tahoe-x1's mean-delta family: `null`, `global_mean`, `context_mean`,
    `perturbation_mean` (the prompt itself, contexts treated as replicates). `additive` is Stack's
    PerturbMean: the prompt plus the context shift between p and c.
  - Learned transitions: `scaled` (one coefficient on the centred prompt) and `ridge_st`, a
    linear analogue of State's transition model. Ridge regression maps the top-k principal
    components of centred prompt shifts to centred target shifts. k and lambda come from fixed
    grids, chosen per (p, c) by closed-form leave-one-out error on the references.
  - `loo_predictions` gives each reference's own leave-one-out prediction. The world model uses it
    to fit its transfer kernel without letting a reference predict itself.
  - A prompt is a real, bought measurement of the same compound. The target's own shift never
    enters a prediction (Stack's prompt-availability rule).
- Interfaces: `Transition`, `fit`, `BASELINES`, `LEARNED`, `ARMS`
- Depends on: numpy
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

BASELINES = ("null", "global_mean", "context_mean", "perturbation_mean", "additive")
LEARNED = ("scaled", "ridge_st")
ARMS = BASELINES + LEARNED
K_GRID = (1, 2, 4, 8, 16, 32)
LAMBDA_GRID = (0.01, 0.1, 1.0, 10.0)
"""Ridge penalty as a multiple of the mean retained eigenvalue; fixed in spec.json before any score."""


@dataclass
class Transition:
    """Fitted transition from prompt condition p to target condition c."""

    prompt: tuple
    target: tuple
    names: tuple
    mean_prompt: np.ndarray
    mean_target: np.ndarray
    global_mean: np.ndarray
    beta: float
    basis: np.ndarray            # d x k right singular vectors of the centred prompts
    weights: np.ndarray          # k x d ridge coefficients from component scores to centred targets
    k: int
    lam: float
    loo_mse: float
    hat_diagonal: np.ndarray = field(default_factory=lambda: np.zeros(0))
    fitted: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    centred_targets: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))

    @property
    def references(self) -> int:
        return len(self.names)

    def predict(self, x: np.ndarray, arm: str = "ridge_st") -> np.ndarray:
        """Predicted shift at the target from one prompt shift `x` (or the mean of several prompts)."""
        x = np.asarray(x, dtype=np.float64)
        if arm == "null":
            return np.zeros_like(self.mean_target)
        if arm == "global_mean":
            return self.global_mean.copy()
        if arm == "context_mean":
            return self.mean_target.copy()
        if arm == "perturbation_mean":
            return x.copy()
        if arm == "additive":
            return x + self.mean_target - self.mean_prompt
        if arm == "scaled":
            return self.mean_target + self.beta * (x - self.mean_prompt)
        if arm == "ridge_st":
            if self.k == 0:
                return self.mean_target.copy()
            return self.mean_target + ((x - self.mean_prompt) @ self.basis) @ self.weights
        raise ValueError(arm)

    def loo_predictions(self) -> np.ndarray:
        """Each reference's `ridge_st` prediction with itself left out of the ridge fit (hat-matrix identity).

        The principal components and means still include the reference; this only matters for
        hyperparameter fitting and is not used to score held-out compounds.
        """
        if self.k == 0 or len(self.names) == 0:
            return np.broadcast_to(self.mean_target, (len(self.names), len(self.mean_target))).copy()
        residual = (self.centred_targets - self.fitted) / np.maximum(1.0 - self.hat_diagonal, 1e-6)[:, None]
        return self.mean_target + self.centred_targets - residual


def fit(prompt_key, target_key, names, X: np.ndarray, Y: np.ndarray, global_mean: np.ndarray) -> Transition:
    """Fit every arm on references measured at both conditions (rows of X and Y are the same compounds)."""
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    n, d = X.shape
    mp = X.mean(0) if n else np.zeros(d)
    mt = Y.mean(0) if n else np.zeros(Y.shape[1])
    Xc, Yc = X - mp, Y - mt
    denom = float((Xc * Xc).sum())
    beta = float((Xc * Yc).sum() / denom) if denom > 1e-12 else 0.0
    empty = Transition(tuple(prompt_key), tuple(target_key), tuple(names), mp, mt, np.asarray(global_mean, float), beta,
                       np.zeros((d, 0)), np.zeros((0, Y.shape[1])), 0, 0.0, float("nan"))
    if n < 3:
        return empty
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    keep = S > 1e-8 * max(S[0], 1e-12)
    U, S, Vt = U[:, keep], S[keep], Vt[keep]
    UtY = U.T @ Yc
    best = None
    for k in K_GRID:
        if k > min(len(S), n - 2):
            continue
        s2 = S[:k] ** 2
        for mult in LAMBDA_GRID:
            lam = mult * float(s2.mean())
            shrink = s2 / (s2 + lam)
            fitted = U[:, :k] @ (shrink[:, None] * UtY[:k])
            hat = (U[:, :k] ** 2) @ shrink
            residual = (Yc - fitted) / np.maximum(1.0 - hat, 1e-6)[:, None]
            mse = float((residual ** 2).mean())
            if best is None or mse < best[0] - 1e-15:
                best = (mse, k, lam, fitted, hat)
    if best is None:
        return empty
    mse, k, lam, fitted, hat = best
    s = S[:k]
    weights = (s / (s ** 2 + lam))[:, None] * UtY[:k]
    return Transition(tuple(prompt_key), tuple(target_key), tuple(names), mp, mt, np.asarray(global_mean, float), beta,
                      Vt[:k].T, weights, k, lam, mse, hat, fitted, Yc)
