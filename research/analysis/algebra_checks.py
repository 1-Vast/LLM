"""Exact algebra checks for the ASRG report (no data, no biology).

1. Dual-residual non-identifiability: shifting ideal_hat moves mass between r_goal and
   r_realization without changing their sum, and flips a norm-based branch rule.
2. Gain identity: with a *predicted* anchor, argmax analytic gain == nearest predicted
   candidate (any positive-definite W). With a *measured* anchor they differ exactly by
   the anchor residual e0 = y_obs(a0) - y_hat(a0).
3. Action-supported reachability bound: min_a ||r - d_a||_W^2 >=
   max(0, ||P_perp r||_W - max_a ||P_perp d_a||_W)^2 for the W-orthogonal complement of
   any subspace S (tight form when S contains every d_a).
4. Uncertainty-adjusted gain: E[Gain] = Gain_hat - tr(W Sigma) for Gaussian delta with a
   measured anchor, verified by Monte Carlo.
"""
from __future__ import annotations

import numpy as np

rng = np.random.default_rng(20260925)


def wnorm2(v, W):
    return float(v @ W @ v)


# 1. Non-identifiability --------------------------------------------------------------
d = 6
g, actual = rng.normal(size=d), rng.normal(size=d)
ideal = rng.normal(size=d)
for _ in range(1000):
    v = rng.normal(size=d) * rng.uniform(0.1, 10)
    ideal2 = ideal + v
    r_goal, r_real = g - ideal2, ideal2 - actual
    assert np.allclose(r_goal + r_real, g - actual)
flips = []
for t in np.linspace(0, 1, 11):
    ideal_t = actual + t * (g - actual)  # ideal_hat anywhere on the segment
    r_goal, r_real = g - ideal_t, ideal_t - actual
    branch = "repair_realization" if np.linalg.norm(r_real) >= np.linalg.norm(r_goal) else "repair_hypothesis"
    flips.append((round(t, 1), branch))
print("1. sum invariant under 1000 random ideal_hat shifts: OK")
print("   branch along ideal_hat = actual + t(g - actual):", flips)

# 2. Gain identity ------------------------------------------------------------------------
n, d = 40, 12
A = rng.normal(size=(d, d)); W = A @ A.T + 0.1 * np.eye(d)  # arbitrary positive definite W
g = rng.normal(size=d)
y_hat = rng.normal(size=(n, d))
a0 = 7
r = g - y_hat[a0]
gain = np.array([2 * r @ W @ (y_hat[a] - y_hat[a0]) - wnorm2(y_hat[a] - y_hat[a0], W) for a in range(n)])
nearest = int(np.argmin([wnorm2(g - y_hat[a], W) for a in range(n)]))
assert int(np.argmax(gain)) == nearest
assert np.allclose(gain, wnorm2(g - y_hat[a0], W) - np.array([wnorm2(g - y_hat[a], W) for a in range(n)]))
print("2. predicted anchor: argmax gain == nearest predicted candidate (W positive definite): OK")
y_obs_a0 = y_hat[a0] + rng.normal(size=d) * 1.5  # measured anchor differs from its prediction
e0 = y_obs_a0 - y_hat[a0]
r_meas = g - y_obs_a0
gain_meas = np.array([2 * r_meas @ W @ (y_hat[a] - y_hat[a0]) - wnorm2(y_hat[a] - y_hat[a0], W) for a in range(n)])
anchored = int(np.argmin([wnorm2(g - (y_hat[a] + e0), W) for a in range(n)]))
assert int(np.argmax(gain_meas)) == anchored
print(f"   measured anchor: argmax gain == argmin ||g - (y_hat + e0)|| (offset-corrected): OK;"
      f" differs from nearest here: {anchored != nearest} (nearest={nearest}, anchored={anchored})")
differs = 0
for trial in range(2000):
    y_hat = rng.normal(size=(n, d)); g = rng.normal(size=d); e0 = rng.normal(size=d)
    near = np.argmin(((g - y_hat) ** 2).sum(1)); anch = np.argmin(((g - y_hat - e0) ** 2).sum(1))
    differs += int(near != anch)
print(f"   random instances where the two rules pick different candidates: {differs}/2000")

# 3. Reachability lower bound -----------------------------------------------------------
worst_gap = np.inf
for trial in range(3000):
    d, n, k = 10, 25, int(rng.integers(1, 6))
    A = rng.normal(size=(d, d)); W = A @ A.T + 0.1 * np.eye(d)
    B = rng.normal(size=(d, k))
    deltas = rng.normal(size=(n, k)) @ B.T + rng.normal(size=(n, d)) * rng.choice([0.0, 0.05])
    r = rng.normal(size=d) * 2
    # W-orthogonal projector onto S = span(B): P = B (B^T W B)^-1 B^T W
    P = B @ np.linalg.solve(B.T @ W @ B, B.T @ W)
    perp = lambda v: v - P @ v
    lhs = min(wnorm2(r - dl, W) for dl in deltas)
    bound = max(0.0, np.sqrt(wnorm2(perp(r), W)) - max(np.sqrt(wnorm2(perp(dl), W)) for dl in deltas)) ** 2
    assert lhs >= bound - 1e-9
    worst_gap = min(worst_gap, lhs - bound)
print("3. reachability lower bound held in 3000 random instances (min slack %.3g)" % worst_gap)

# 4. Uncertainty-adjusted gain ---------------------------------------------------------
d = 8
A = rng.normal(size=(d, d)); W = A @ A.T + 0.1 * np.eye(d)
r = rng.normal(size=d); mu = rng.normal(size=d)
L = rng.normal(size=(d, d)) * 0.4; Sigma = L @ L.T
samples = rng.multivariate_normal(mu, Sigma, size=400_000)
mc = np.mean(2 * samples @ W @ r - np.einsum("ij,jk,ik->i", samples, W, samples))
closed = 2 * r @ W @ mu - mu @ W @ mu - np.trace(W @ Sigma)
print(f"4. E[Gain]: Monte Carlo {mc:.4f} vs closed form {closed:.4f} (Gain_hat - tr(W Sigma))")
assert abs(mc - closed) < 0.05 * max(1.0, abs(closed))
