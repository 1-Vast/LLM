"""Risk control for abstaining decision policies: a corrected Learn-then-Test with explicit abstention.

File summary
- Path: research/dual_core_v2/risk_control.py
- Purpose: replace block 7's P3 (`research/dual_core/e2.policies`), whose fixed-sequence loop started
  at the threshold 0. With no decisions, the transformed loss sits exactly on the null boundary, so the
  first test can never reject; the loop broke there and the policy fell back to the threshold 0. That
  fallback was then reported as "wrong among decided 0" at coverage 0.
- Core points:
  - What is controlled. For a policy lambda, per independent unit u: `wrong_u` and `decided_u` are
    the means over the unit's episodes of "the final decision eliminated the true hypothesis" and "a
    decision was made". The target is the unit-level conditional risk
        R(lambda) = E[wrong_u] / E[decided_u] <= alpha,
    together with a coverage requirement, relative to the unconstrained policy P0,
        E[decided_u(lambda)] >= rho * E[decided_u(P0)].
    Both are linear in unit means, so each is a test of a bounded mean:
    - risk: Z_u = (wrong_u - alpha decided_u + alpha) / (1 + alpha) in [0, 1];
      H0: E[Z] >= alpha / (1 + alpha).
    - coverage: V_u = (rho - (decided_u - rho decided_u(P0))) / (1 + rho) in [0, 1];
      H0: E[V] >= rho / (1 + rho).
    The candidate's p-value is max(p_risk, p_cov), which is valid for the union of the two nulls.
  - Abstention is explicit. `ABSTAIN_ALL` is a policy, not a number: a threshold of 0 still buys any
    step whose recorded risk is exactly 0. Abstain-all is never a candidate and is never "certified";
    it is the named fallback.
  - Conditional risk is undefined (NaN) when a policy makes no decision. It is never reported as 0.
  - Multiple testing. Holm's step-down over the candidate set controls the family-wise error rate at
    delta under any dependence between candidates, so no candidate ordering has to be guessed. Among
    certified candidates the one with the largest calibration coverage is used (ties: the larger
    threshold). The procedure never picks "the smallest p-value".
  - Two valid p-values for a bounded mean:
    - `hb_pvalue`: Hoeffding-Bentkus (Bates et al. 2021), identical to block 7's;
    - `betting_pvalue`: the Waudby-Smith and Ramdas (2024) betting supermartingale with a
      predictable plug-in bet. It is valid for any predictable bet and adapts to the variance, which
      HB ignores. Units are processed in a fixed, outcome-blind order (SHA-256 of the unit name).
  - Outcome of a certification, by name:
    - `structural_abstain`: P0 makes no decision on the calibration units, so no candidate can;
    - `no_candidate_certified`: abstain-all is used and the certificate says nothing about risk;
    - `certified`: a candidate passed. `abstains` says whether it differs from P0 (a threshold below
      the unconstrained policy) or is P0 itself, certified without abstention.
  - Guarantee. If calibration and test units are exchangeable given a frozen model-policy process,
    then with probability at least 1 - delta over the calibration draw, every certified candidate,
    hence the selected one, has population conditional risk <= alpha and coverage retention >= rho.
    It is a statement about the population of units, not the realised rate of one test fold, and it
    says nothing when the calibration and test processes differ (see `nested.py`).
- Interfaces: `ABSTAIN_ALL`, `UnitLosses`, `unit_losses`, `hb_pvalue`, `betting_pvalue`, `holm`,
  `certify`, `Certificate`, `apply_policy`, `conditional_risk`, `plugin_select`
- Depends on: numpy, scipy
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

import numpy as np

ABSTAIN_ALL = "abstain_all"
"""The explicit abstain-all policy: no measurement is bought and no decision is made."""


# ------------------------------------------------------------------------------------ p-values
def hb_pvalue(mean: float, n: int, t: float) -> float:
    """Hoeffding-Bentkus p-value for H0: E[X] >= t, X in [0, 1] (Bates et al. 2021); block 7's formula."""
    from scipy.stats import binom
    if n <= 0 or mean >= t:
        return 1.0
    if 0 < mean < 1:
        h1 = mean * math.log(mean / t) + (1 - mean) * math.log((1 - mean) / (1 - t))
    else:
        h1 = math.log(1 / (1 - t)) if mean == 0 else math.inf
    hoeffding = math.exp(-n * h1)
    bentkus = math.e * float(binom.cdf(math.ceil(n * mean), n, t))
    return min(hoeffding, bentkus, 1.0)


def betting_pvalue(x, t: float, *, delta: float = 0.1) -> float:
    """Anytime-valid p-value for H0: E[X] >= t, X in [0, 1], by betting (Waudby-Smith and Ramdas 2024).

    Capital K_i = prod_j (1 + lam_j (t - x_j)) is a nonnegative supermartingale under H0 for any
    predictable lam_j in [0, 1 / (1 - t)): each factor has conditional mean 1 + lam_j (t - E[X]) <= 1
    and stays >= 0 even at x_j = 1. By Ville's inequality P(sup K >= 1/a) <= a, so 1 / max K is a
    valid p-value. The bet is the predictable plug-in of their Theorem 3 tuned to `delta`,
    lam_i = sqrt(2 log(1/delta) / (sigma2_{i-1} i log(i + 1))), truncated at 0.75 / (1 - t). Tuning
    affects power only, never validity. The order of `x` must not depend on outcomes; callers pass
    units in hash order.
    """
    x = np.clip(np.asarray(x, dtype=np.float64), 0.0, 1.0)
    if len(x) == 0 or not 0 < t < 1:
        return 1.0
    cap = 0.75 / (1.0 - t)
    log_k, best = 0.0, 0.0
    total, squares = 0.0, 0.0                   # WSR's priors: mean 1/2 and variance 1/4, each counted once
    var = 0.25
    for i, xi in enumerate(x, start=1):
        lam = min(math.sqrt(2 * math.log(1 / delta) / (var * i * math.log(i + 1))), cap)
        log_k += math.log1p(lam * (t - xi))
        best = max(best, log_k)
        total += xi
        mu = (0.5 + total) / (i + 1)
        squares += (xi - mu) ** 2
        var = max((0.25 + squares) / (i + 1), 1e-8)
    return float(min(1.0, math.exp(-best)))


def unit_order(units) -> np.ndarray:
    """A fixed, outcome-blind processing order for the betting test: SHA-256 of the unit name."""
    keys = [hashlib.sha256(f"dual-core-v2|{u}".encode()).hexdigest() for u in units]
    return np.argsort(keys, kind="stable")


# ------------------------------------------------------------------------------------ unit losses
@dataclass(frozen=True)
class UnitLosses:
    """Per-unit mean outcomes of one policy on one set of units (units in a fixed order)."""

    units: tuple
    wrong: np.ndarray
    decided: np.ndarray

    def coverage(self) -> float:
        return float(self.decided.mean()) if len(self.units) else float("nan")

    def risk(self) -> float:
        return conditional_risk(self.wrong, self.decided)


def conditional_risk(wrong, decided) -> float:
    """E[wrong_u] / E[decided_u]; undefined (NaN) when no decision was made."""
    wrong, decided = np.asarray(wrong, float), np.asarray(decided, float)
    d = float(decided.mean()) if len(decided) else 0.0
    return float(wrong.mean() / d) if d > 0 else float("nan")


def unit_losses(frame, units=None) -> UnitLosses:
    """Collapse an episode table (columns unit, wrong, decided) to unit means, in `units` order if given."""
    g = frame.groupby(frame["unit"].astype(str))[["wrong", "decided"]].mean()
    if units is not None:
        g = g.reindex([str(u) for u in units])
        if g.isna().any().any():
            missing = list(g.index[g.isna().any(axis=1)])[:3]
            raise ValueError(f"units without episodes under this policy: {missing}")
    return UnitLosses(tuple(g.index), g.wrong.to_numpy(float), g.decided.to_numpy(float))


# ------------------------------------------------------------------------------------ certification
def _pvalue(values, t, method, delta, order):
    if method == "hb":
        return hb_pvalue(float(np.mean(values)), len(values), t)
    if method == "betting":
        return betting_pvalue(np.asarray(values)[order], t, delta=delta)
    raise ValueError(method)


def risk_pvalue(losses: UnitLosses, alpha: float, *, method: str = "betting", delta: float = 0.1) -> float:
    z = (losses.wrong - alpha * losses.decided + alpha) / (1 + alpha)
    return _pvalue(z, alpha / (1 + alpha), method, delta, unit_order(losses.units))


def coverage_pvalue(losses: UnitLosses, reference: UnitLosses, rho: float, *, method: str = "betting",
                    delta: float = 0.1) -> float:
    if losses.units != reference.units:
        raise ValueError("coverage is compared on identical units")
    v = (rho - (losses.decided - rho * reference.decided)) / (1 + rho)
    return _pvalue(v, rho / (1 + rho), method, delta, unit_order(losses.units))


def holm(pvalues: dict, delta: float) -> set:
    """Holm's step-down: the candidates rejected (certified) at family-wise error rate delta."""
    order = sorted(pvalues, key=lambda k: (pvalues[k], str(k)))
    m = len(order)
    rejected = set()
    for i, k in enumerate(order):
        if pvalues[k] <= delta / (m - i):
            rejected.add(k)
        else:
            break
    return rejected


@dataclass
class Certificate:
    status: str
    policy: object                      # a candidate threshold, or ABSTAIN_ALL
    alpha: float
    delta: float
    rho: float
    method: str
    units: int
    reference_coverage: float
    candidates: dict = field(default_factory=dict)   # threshold -> {p_risk, p_cov, p, risk, coverage}
    certified: tuple = ()
    abstains: bool = False

    def payload(self) -> dict:
        return {"status": self.status, "policy": self.policy, "abstains": self.abstains,
                "alpha": self.alpha, "delta": self.delta,
                "rho": self.rho, "method": self.method, "units": self.units,
                "reference_coverage": self.reference_coverage, "certified": list(self.certified),
                "candidates": {str(k): v for k, v in self.candidates.items()}}


def certify(losses_by_candidate: dict, reference: UnitLosses, *, alpha: float, delta: float, rho: float,
            method: str = "betting", reference_key=None) -> Certificate:
    """Learn-then-Test over explicit candidates with a tested coverage requirement and Holm's FWER control.

    `losses_by_candidate` maps each candidate (a threshold) to its calibration `UnitLosses`, on the
    same units as `reference` (P0). ABSTAIN_ALL must not be a candidate.
    """
    if ABSTAIN_ALL in losses_by_candidate:
        raise ValueError("abstain-all is the fallback, never a candidate")
    n = len(reference.units)
    ref_cov = reference.coverage()
    if n == 0 or not ref_cov > 0:
        return Certificate("structural_abstain", ABSTAIN_ALL, alpha, delta, rho, method, n, float(ref_cov or 0.0))
    table = {}
    for k, losses in losses_by_candidate.items():
        pr = risk_pvalue(losses, alpha, method=method, delta=delta)
        pc = coverage_pvalue(losses, reference, rho, method=method, delta=delta)
        table[k] = {"p_risk": pr, "p_cov": pc, "p": max(pr, pc), "risk": losses.risk(), "coverage": losses.coverage()}
    rejected = holm({k: v["p"] for k, v in table.items()}, delta)
    if not rejected:
        return Certificate("no_candidate_certified", ABSTAIN_ALL, alpha, delta, rho, method, n, ref_cov, table)
    best = max(rejected, key=lambda k: (table[k]["coverage"], float(k)))
    return Certificate("certified", best, alpha, delta, rho, method, n, ref_cov, table,
                       tuple(sorted(rejected, key=float)), abstains=reference_key is None or best != reference_key)


def plugin_select(losses_by_candidate: dict, reference: UnitLosses, *, alpha: float, rho: float):
    """P2 repaired: the plug-in choice with the same coverage requirement and an explicit fallback.

    The candidate with the largest calibration coverage among those whose empirical conditional
    risk is at most alpha and whose coverage is at least rho x P0's; otherwise ABSTAIN_ALL. No
    guarantee is attached.
    """
    ref_cov = reference.coverage()
    if not ref_cov > 0:
        return ABSTAIN_ALL, "structural_abstain"
    ok = [k for k, l in losses_by_candidate.items()
          if np.isfinite(l.risk()) and l.risk() <= alpha and l.coverage() >= rho * ref_cov]
    if not ok:
        return ABSTAIN_ALL, "no_candidate_meets_target"
    return max(ok, key=lambda k: (losses_by_candidate[k].coverage(), float(k))), "selected"


def apply_policy(outcomes_by_candidate: dict, policy):
    """The episode table of `policy` on test episodes; ABSTAIN_ALL decides nothing and buys nothing."""
    if policy == ABSTAIN_ALL:
        base = next(iter(outcomes_by_candidate.values()))
        return base.assign(decided=False, wrong=False, correct=False, abstained=True, measurements=0)
    return outcomes_by_candidate[policy]
