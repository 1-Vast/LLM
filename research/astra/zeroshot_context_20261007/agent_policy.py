"""Gaussian belief over candidate deviation energies, common update and final rule, and policies.

Every policy sees the same prior (from one world), the same correlation structure and the same
purchased screen values. Policies differ only in which candidate's first well they buy next and
when they stop. The final flag rule is fixed: the m largest posterior means.

Scale: y = sign(z) * sqrt(|z|) ("root deviation energy"), on which the prior regression, the
correlation and the screen observation model are calibrated.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def root(z):
    z = np.asarray(z, dtype=np.float64)
    return np.sign(z) * np.sqrt(np.abs(z))


@dataclass
class Belief:
    mean: np.ndarray
    cov: np.ndarray
    obs_var: np.ndarray            # per-candidate screen observation variance on the y scale
    obs_slope: float = 1.0         # screen y_A = intercept + slope * y_B + e
    obs_intercept: float = 0.0
    screened: dict = field(default_factory=dict)

    def copy(self):
        return Belief(self.mean.copy(), self.cov.copy(), self.obs_var.copy(), self.obs_slope, self.obs_intercept, dict(self.screened))

    def update(self, i: int, value: float):
        """Condition on y_A,i = a + b * y_B,i + e_i (exact Gaussian update of all candidates)."""
        b, a = self.obs_slope, self.obs_intercept
        s = self.cov[:, i] * b
        denom = b * b * self.cov[i, i] + self.obs_var[i]
        gain = s / denom
        resid = value - (a + b * self.mean[i])
        self.mean = self.mean + gain * resid
        self.cov = self.cov - np.outer(gain, s)
        self.screened[i] = value

    def preposterior_sd(self, i: int) -> np.ndarray:
        """SD of the change in every posterior mean caused by screening i."""
        b = self.obs_slope
        denom = b * b * self.cov[i, i] + self.obs_var[i]
        return np.abs(self.cov[:, i] * b) / np.sqrt(denom)


def flags(belief: Belief, m: int) -> list[int]:
    return [int(i) for i in np.lexsort((np.arange(len(belief.mean)), -belief.mean))[:m]]


def kg_values(belief: Belief, m: int, available, samples: int = 64, seed: int = 0) -> dict[int, float]:
    """One-step knowledge gradient for the top-m sum of posterior means (common random numbers)."""
    rng = np.random.default_rng(seed)
    normals = rng.standard_normal(samples)
    current = np.sort(belief.mean)[-m:].sum()
    out = {}
    for i in available:
        direction = belief.cov[:, i] * belief.obs_slope / np.sqrt(belief.obs_slope ** 2 * belief.cov[i, i] + belief.obs_var[i])
        values = []
        for zeta in normals:
            values.append(np.sort(belief.mean + direction * zeta)[-m:].sum())
        out[int(i)] = float(np.mean(values) - current)
    return out


def choose_none(belief, m, available, budget_left, rng):
    return None


def choose_top_prior(belief, m, available, budget_left, rng, prior_order=None):
    for i in prior_order:
        if i in available:
            return int(i)
    return None


def choose_ucb(belief, m, available, budget_left, rng):
    sd = np.sqrt(np.maximum(np.diag(belief.cov), 0))
    score = belief.mean + sd
    return int(max(available, key=lambda i: (score[i], -i)))


def choose_kg(belief, m, available, budget_left, rng):
    values = kg_values(belief, m, available)
    best = max(values, key=lambda i: (values[i], -i))
    return best if values[best] > 0 else None


def choose_random(belief, m, available, budget_left, rng):
    return int(rng.choice(sorted(available)))


POLICIES = {"none": choose_none, "ucb": choose_ucb, "kg": choose_kg, "random": choose_random}


def run_episode(belief: Belief, screen_values: np.ndarray, budget: int, m: int, policy, rng=None, prior_order=None,
                on_purchase=None, log=None):
    """Sequentially buy up to `budget` first-well profiles, then flag m. Returns flags and the purchase order."""
    rng = rng or np.random.default_rng(0)
    order = []
    available = set(range(len(belief.mean)))
    for step in range(budget):
        if policy is choose_top_prior:
            choice = policy(belief, m, available, budget - step, rng, prior_order=prior_order)
        else:
            choice = policy(belief, m, available, budget - step, rng)
        if choice is None:
            break
        if choice not in available:
            raise ValueError("policy chose an unavailable candidate")
        value = screen_values[choice] if on_purchase is None else on_purchase(choice)
        belief.update(choice, value)
        available.discard(choice)
        order.append(choice)
        if log is not None:
            log.append({"step": step, "choice": int(choice), "observed_root_energy": float(value)})
    return flags(belief, m), order
