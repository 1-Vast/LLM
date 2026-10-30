# -*- coding: utf-8 -*-
"""Corrected scientific contracts for R204 comparisons/estimators.

Scope: deterministic contract checks and finite-environment algebra only.
No model execution, no training on old config, no real data.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy import stats


# ---------------------------------------------------------------- comparisons
def paired_deltas(R_candidate: np.ndarray, baselines: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """D_j = R_candidate - R_baseline_j, elementwise over independent repeats."""
    Rc = np.asarray(R_candidate, dtype=float)
    out: Dict[str, np.ndarray] = {}
    for name, R in baselines.items():
        Rb = np.asarray(R, dtype=float)
        if Rb.shape != Rc.shape:
            raise ValueError(f"shape mismatch for {name}: {Rb.shape} vs {Rc.shape}")
        out[name] = Rc - Rb
    return out


def t_stats(d: np.ndarray) -> Tuple[float, float, float, int]:
    d = np.asarray(d, dtype=float)
    n = int(d.size)
    if n == 0:
        raise ValueError("empty sample")
    mean = float(d.mean())
    if n == 1:
        return mean, 0.0, float("nan"), 0
    se = float(d.std(ddof=1) / math.sqrt(n))
    return mean, se, float(n - 1), n


def one_sided_lower_p(d: np.ndarray) -> float:
    """Pre-registered improvement direction: D < 0.  Test H0: D >= 0, p = P(T <= t_obs)."""
    mean, se, df, n = t_stats(d)
    if n == 1:
        return 0.0 if mean < 0 else 1.0
    if se == 0.0:
        # degenerate sample: exact sign determines the limiting lower tail
        return 0.0 if mean < 0 else 1.0
    p = float(stats.t.cdf(mean / se, df=df))
    return min(1.0, max(0.0, p))


def ci95_t(d: np.ndarray) -> Tuple[float, float]:
    mean, se, df, n = t_stats(d)
    if n == 1 or se == 0.0:
        return mean, mean
    crit = float(stats.t.ppf(0.975, df=df))
    return mean - crit * se, mean + crit * se


def holm(pvals: Dict[str, float]) -> Dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out: Dict[str, float] = {}
    prev = 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, max(prev, (m - i) * float(p)))
        out[name] = adj
        prev = adj
    return out


def success_gate(d: np.ndarray, delta: float = 0.05, alpha: float = 0.05) -> Dict[str, object]:
    mean, se, df, n = t_stats(d)
    lo, hi = ci95_t(d)
    p = one_sided_lower_p(d)
    passed = bool(mean <= -delta and hi < 0.0 and p < alpha)
    return {
        "n": n,
        "mean": mean,
        "se": se,
        "ci95_t": [lo, hi],
        "p_one_sided_lower": p,
        "delta": delta,
        "alpha": alpha,
        "mean_le_minus_delta": bool(mean <= -delta),
        "ci_upper_lt_0": bool(hi < 0.0),
        "gate_pass": passed,
    }


def six_comparison_family(R_candidate: np.ndarray, baselines: Dict[str, np.ndarray],
                          delta: float = 0.05, alpha: float = 0.05) -> Dict[str, object]:
    """All six D_j = R_candidate - R_baseline_j (incl. standard); one unified Holm family."""
    if len(baselines) != 6:
        raise ValueError(f"expected 6 baselines, got {len(baselines)}")
    D = paired_deltas(R_candidate, baselines)
    raw = {name: one_sided_lower_p(d) for name, d in D.items()}
    adj = holm(raw)
    rows = {}
    for name, d in D.items():
        rows[name] = {
            "mean_DeltaR": float(np.mean(d)),
            "ci95_t": list(ci95_t(d)),
            "p_one_sided_lower": raw[name],
            "p_holm": adj[name],
            "pass": bool(np.mean(d) <= -delta and ci95_t(d)[1] < 0.0 and adj[name] < alpha),
        }
    return {"family_size": 6, "rows": rows}


# ---------------------------------------------------------------- headroom
def batch_max_improvement(baseline_regret: np.ndarray) -> float:
    """Regret lower bound is 0; maximum possible mean improvement is mean baseline regret."""
    return float(np.mean(np.asarray(baseline_regret, dtype=float)))


def headroom_gate(baseline_regret: np.ndarray, delta: float = 0.05) -> Dict[str, object]:
    cap = batch_max_improvement(baseline_regret)
    return {
        "baseline_regret_mean": cap,
        "delta": delta,
        "max_possible_mean_improvement": cap,
        "delta_feasible": bool(cap >= delta),
        "headroom_ratio": cap / delta if delta > 0 else float("inf"),
    }


# ---------------------------------------------------------------- propensity / DR
def dr_estimator(pi2: np.ndarray, behavior: np.ndarray, m: np.ndarray,
                 y: np.ndarray, a_obs: np.ndarray) -> float:
    """Finite-env DR value: E_h[ sum_a pi(a|h)m(h,a) + pi(a_obs|h)/behavior(a_obs|h) (y - m(h,a_obs)) ].

    Uses the ACTUAL sampling behaviour probability in the denominator.
    """
    pi2 = np.asarray(pi2, dtype=float)
    behavior = np.asarray(behavior, dtype=float)
    m = np.asarray(m, dtype=float)
    y = np.asarray(y, dtype=float)
    a_obs = np.asarray(a_obs, dtype=int)
    h_idx = np.arange(pi2.shape[0])
    base = (pi2 * m).sum(axis=1)
    correction = pi2[h_idx, a_obs] / behavior[h_idx, a_obs] * (y - m[h_idx, a_obs])
    return float(np.mean(base + correction))


def dr_identity_gap(pi2: np.ndarray, behavior: np.ndarray, m0: np.ndarray,
                    y: np.ndarray, a_obs: np.ndarray) -> float:
    """Exact target value under the same records: sum p(h) sum_a pi(a|h) E[Y|h,a]."""
    pi2 = np.asarray(pi2, dtype=float)
    y = np.asarray(y, dtype=float)
    a_obs = np.asarray(a_obs, dtype=int)
    h_idx = np.arange(pi2.shape[0])
    target = float(np.mean((pi2 * m0).sum(axis=1) + pi2[h_idx, a_obs] / np.asarray(behavior)[h_idx, a_obs]
                           * (y - m0[h_idx, a_obs])))
    return target - dr_estimator(pi2, behavior, m0, y, a_obs)


# ---------------------------------------------------------------- equivalence audit
def argmax_actions(scores: np.ndarray) -> np.ndarray:
    return np.argmax(np.asarray(scores, dtype=float), axis=1)


def decisions_equivalent(score_a: np.ndarray, score_b: np.ndarray) -> bool:
    return bool(np.array_equal(argmax_actions(score_a), argmax_actions(score_b)))


def affine_equivalent(score_a: np.ndarray, score_b: np.ndarray, rtol: float = 1e-9) -> bool:
    """score_b = alpha*score_a + beta (per-row common affine map) with alpha>0."""
    a = np.asarray(score_a, dtype=float)
    b = np.asarray(score_b, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] < 2:
        return False
    out = []
    for i in range(a.shape[0]):
        x, y = a[i], b[i]
        if np.ptp(x) == 0:
            out.append(bool(np.ptp(y) == 0))
            continue
        xc = x - x.mean()
        yc = y - y.mean()
        denom = float(np.dot(xc, xc))
        if denom == 0.0:
            out.append(False)
            continue
        alpha = float(np.dot(xc, yc) / denom)
        beta = y.mean() - alpha * x.mean()
        out.append(bool(alpha > 0 and np.allclose(y, alpha * x + beta, rtol=rtol, atol=1e-12)))
    return all(out)


# ---------------------------------------------------------------- learner contract
def softmax_rows(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def logit_fluctuation_fit(logits: np.ndarray, H: np.ndarray, a_obs: np.ndarray,
                          max_iter: int = 500, tol: float = 1e-10) -> Dict[str, object]:
    """Fit epsilon in p_eps(a|h) = softmax(logits + eps*H) by exact NLL and L-BFGS.

    Requirement: real loss, real update, optimizer, and a convergence criterion.
    """
    logits = np.asarray(logits, dtype=float)
    H = np.asarray(H, dtype=float)
    a_obs = np.asarray(a_obs, dtype=int)

    def nll_grad(eps_vec: np.ndarray) -> Tuple[float, np.ndarray]:
        eps = float(eps_vec[0])
        p = softmax_rows(logits + eps * H)
        n = logits.shape[0]
        nll = -float(np.mean(np.log(np.clip(p[np.arange(n), a_obs], 1e-12, None))))
        onehot = np.zeros_like(p)
        onehot[np.arange(n), a_obs] = 1.0
        grad = float(np.mean(np.sum((p - onehot) * H, axis=1)))
        return nll, np.array([grad])

    res = __import__("scipy").optimize.minimize(nll_grad, x0=np.array([0.0]), jac=True,
                                                method="L-BFGS-B",
                                                options={"maxiter": max_iter, "ftol": tol, "gtol": tol})
    eps = float(res.x[0])
    grad = float(res.jac[0])
    p = softmax_rows(logits + eps * H)
    onehot = np.zeros_like(p)
    onehot[np.arange(p.shape[0]), a_obs] = 1.0
    score_eq = float(np.mean(np.sum((p - onehot) * H, axis=1)))
    return {
        "epsilon": eps,
        "nll": float(res.fun),
        "grad_norm": abs(grad),
        "score_equation_residual": abs(score_eq),
        "converged": bool(res.success or abs(grad) < 1e-7),
        "iterations": int(res.nit),
        "optimizer": "L-BFGS-B",
        "loss": "mean NLL of p_eps at observed actions",
    }
