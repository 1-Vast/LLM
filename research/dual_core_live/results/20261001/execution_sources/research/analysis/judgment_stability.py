"""What irreproducibility costs a judgment source, and what can be measured without outcomes.

The live verification of 2026-09-25 found that the typed decision model returns different
answers to the same state: a choice question moved between two of five options across two
identical calls. The judgment ledger grades such a source by Brier score against measured
outcomes, which are the scarcest thing in the system. This file asks what can be established
before any outcome exists.

Claims checked here, all by exact computation plus Monte Carlo:

1. Brier decomposition. For a stochastic source returning probability P for a fixed state, and
   an outcome Y with P(Y=1) = q independent of the source's randomness:

       E[(P - Y)^2] = q(1-q) + (mu - q)^2 + sigma^2

   irreducible uncertainty, plus squared miscalibration of the mean, plus the source's own
   variance. The third term needs no outcome to measure.

2. Averaging law. Averaging n independent calls leaves the first two terms and divides the
   third: E[(P_bar_n - Y)^2] = q(1-q) + (mu - q)^2 + sigma^2 / n. So repetition buys a known
   Brier reduction of sigma^2 (1 - 1/n), computable before any outcome is seen.

3. Pre-outcome floor. E[Brier] >= sigma^2 for every q, so an estimated sigma^2 above the
   ledger's revocation threshold guarantees revocation whatever the outcomes turn out to be.
   This is checked to be *sufficient but weak*: it catches only extreme instability.

4. Decision-flip rate. For a ranking question the operative quantity is not Brier but whether
   the selected option changes between identical calls. The collision probability sum_v p_v^2
   has an exactly unbiased estimator from n repeats, sum_v c_v (c_v - 1) / (n (n-1)).

5. Sample size. How many repeats are needed before gating on either quantity is safe, measured
   as the false-revocation rate of a stable source and the detection rate of an unstable one.

No biology, no data, no provider. Run: python research/analysis/judgment_stability.py
"""
from __future__ import annotations

import numpy as np

rng = np.random.default_rng(20260925)
UNINFORMATIVE_BRIER = 0.25  # matches maestro.judgment


def decomposition(weights, values, q):
    """Exact E[(P-Y)^2], and the three terms it decomposes into, for a discrete source."""

    weights = np.asarray(weights, dtype=float)
    values = np.asarray(values, dtype=float)
    mu = float(weights @ values)
    sigma2 = float(weights @ (values - mu) ** 2)
    exact = float(weights @ ((values - 1.0) ** 2 * q + values**2 * (1.0 - q)))
    return exact, q * (1 - q), (mu - q) ** 2, sigma2


# 1. The decomposition is an identity, not an approximation ---------------------------
worst = 0.0
for _ in range(4000):
    k = rng.integers(2, 6)
    weights = rng.dirichlet(np.ones(k))
    values = rng.uniform(0, 1, size=k)
    q = float(rng.uniform(0, 1))
    exact, aleatoric, bias2, sigma2 = decomposition(weights, values, q)
    worst = max(worst, abs(exact - (aleatoric + bias2 + sigma2)))
assert worst < 1e-12, worst
print(f"1. decomposition is exact                      max |error| = {worst:.2e}")

# Monte Carlo confirmation that the analytic expectation is the sampled one.
weights, values, q = np.array([0.5, 0.3, 0.2]), np.array([0.9, 0.3, 0.55]), 0.7
exact, aleatoric, bias2, sigma2 = decomposition(weights, values, q)
draws = rng.choice(values, size=400_000, p=weights)
outcomes = (rng.uniform(size=400_000) < q).astype(float)
print(
    f"   analytic {exact:.5f} = irreducible {aleatoric:.5f}"
    f" + bias^2 {bias2:.5f} + variance {sigma2:.5f}"
    f" | sampled {np.mean((draws - outcomes) ** 2):.5f}"
)

# 2. Averaging divides the variance term and nothing else -----------------------------
print("2. averaging law: E[Brier_n] = irreducible + bias^2 + sigma^2/n")
for n in (1, 2, 3, 5, 10):
    predicted = aleatoric + bias2 + sigma2 / n
    sampled = rng.choice(values, size=(200_000, n), p=weights).mean(axis=1)
    outcomes = (rng.uniform(size=200_000) < q).astype(float)
    observed = float(np.mean((sampled - outcomes) ** 2))
    assert abs(observed - predicted) < 3e-3, (n, observed, predicted)
    print(f"   n={n:<3} predicted {predicted:.5f}  sampled {observed:.5f}"
          f"  saved {sigma2 * (1 - 1 / n):.5f}")

# 3. The pre-outcome floor holds for every q, and is weak ------------------------------
violations = 0
for _ in range(20_000):
    k = rng.integers(2, 6)
    weights = rng.dirichlet(np.ones(k))
    values = rng.uniform(0, 1, size=k)
    q = float(rng.uniform(0, 1))
    exact, _, _, sigma2 = decomposition(weights, values, q)
    violations += exact < sigma2 - 1e-12
assert violations == 0
# How unstable must a source be before the floor alone forces revocation?
print(f"3. floor E[Brier] >= sigma^2 held in 20000/20000 cases")
print(f"   sigma^2 >= {UNINFORMATIVE_BRIER} forces revocation with no outcome at all,")
print( "   but sigma^2 = 0.25 is the maximum for any [0,1] variable: the floor only")
print( "   catches a source alternating between near-certain yes and near-certain no.")
for sigma in (0.1, 0.2, 0.3, 0.5):
    print(f"   sigma = {sigma:.2f} (swings of +/-{sigma:.2f}) -> sigma^2 = {sigma**2:.4f}"
          f" -> forces revocation: {sigma**2 >= UNINFORMATIVE_BRIER}")

# 4. Collision probability has an exactly unbiased estimator --------------------------
def agreement_estimate(counts, n):
    """Unbiased estimator of sum_v p_v^2: the chance two independent calls agree."""

    if n < 2:
        return None
    return float(sum(c * (c - 1) for c in counts) / (n * (n - 1)))


biases = []
for _ in range(300):
    k = int(rng.integers(2, 6))
    p = rng.dirichlet(np.ones(k))
    truth = float(p @ p)
    n = int(rng.integers(3, 12))
    draws = rng.multinomial(n, p, size=4000)
    estimates = [agreement_estimate(row, n) for row in draws]
    biases.append(abs(float(np.mean(estimates)) - truth))
print(f"4. agreement estimator unbiased                max |bias| = {max(biases):.4f}")
observed = {"proximal_activity": 0.33, "orthogonal_rescue": 0.29, "engagement_shift": 0.27,
            "none_of_the_listed_options": 0.08, "rna_low": 0.03}
collision = sum(v * v for v in observed.values())
print(f"   if the reported distribution were the sampling distribution, two identical")
print(f"   calls would agree {collision:.2f} of the time, so {1 - collision:.2f} of decisions")
print( "   that consult this question would not reproduce. The measured run saw one")
print( "   disagreement in one pair, which is consistent with that and does not establish it.")

# 5. How many repeats before gating is safe -------------------------------------------
print("5. repeats needed to gate on modal agreement (revoke if modal fraction < 0.6)")
print("   n    false revocation (stable p=0.95)   detection (unstable, 3 options equally likely)")
for n in (3, 5, 8, 12, 20):
    stable = rng.multinomial(n, [0.95, 0.03, 0.02], size=20_000)
    unstable = rng.multinomial(n, [1 / 3, 1 / 3, 1 / 3], size=20_000)
    false_rate = float(np.mean(stable.max(axis=1) / n < 0.6))
    detect = float(np.mean(unstable.max(axis=1) / n < 0.6))
    print(f"   {n:<4} {false_rate:<35.3f} {detect:.3f}")
print("   Three repeats cannot separate the two. Eight gives a usable gate; the cost is")
print("   eight evaluations per review, and the measured call was 517 input tokens.")
