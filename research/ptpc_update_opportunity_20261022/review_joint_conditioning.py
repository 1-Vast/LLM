"""Independent synthetic covariance check; no biological inputs are read."""
import json
from pathlib import Path

import numpy as np


def check(seed):
    rng = np.random.default_rng(seed)
    ns, nt, q = 3, 2, 2
    n = ns + nt
    j = rng.normal(size=(n * q, 2))
    prior_precision = np.diag([0.7, 1.3])
    noise = np.diag(np.linspace(0.2, 0.6, n * q))
    cm = j @ np.linalg.solve(prior_precision, j.T) + noise
    # Chemical functional covariance differs from low-rank molecular covariance.
    chemical = rng.normal(size=(n, 3))
    distance = ((chemical[:, None] - chemical[None, :]) ** 2).sum(axis=2)
    kf = np.exp(-distance / 3.0) + np.eye(n) * 0.15
    h = np.zeros((n, n * q))
    for i in range(n):
        h[i, i * q:(i + 1) * q] = rng.normal(size=q)
    p = ns * q
    ms = rng.normal(size=p)
    ys = rng.normal(size=ns)
    js, jt = j[:p], j[p:]
    hs, ht = h[:ns, :p], h[ns:, p:]
    rs = noise[:p, :p]
    kss, kts = kf[:ns, :ns], kf[ns:, :ns]

    # The proposed two updates, computed in parameter coordinates.
    a = np.linalg.solve(
        prior_precision + js.T @ np.linalg.solve(rs, js),
        js.T @ np.linalg.solve(rs, ms),
    )
    proposed = ht @ jt @ a + kts @ np.linalg.solve(kss, ys - hs @ ms)

    # Ordinary joint Gaussian conditioning, computed without parameter updates
    # or residualizing observed labels. Observations are [m_S, y_S].
    cmss, cmts = cm[:p, :p], cm[p:, :p]
    observed_covariance = np.block([
        [cmss, cmss @ hs.T],
        [hs @ cmss, hs @ cmss @ hs.T + kss],
    ])
    target_observed_covariance = np.hstack([
        ht @ cmts,
        ht @ cmts @ hs.T + kts,
    ])
    direct = target_observed_covariance @ np.linalg.solve(
        observed_covariance, np.concatenate([ms, ys])
    )
    # Same generative model, conventional functional-only conditioning.
    functional_only = (ht @ cmts @ hs.T + kts) @ np.linalg.solve(
        hs @ cmss @ hs.T + kss, ys
    )
    return {
        "seed": seed,
        "proposed_vs_direct_maxabs": float(np.max(np.abs(proposed - direct))),
        "paired_vs_functional_only_maxabs": float(np.max(np.abs(proposed - functional_only))),
        "proposed": proposed.tolist(),
        "ordinary_joint": direct.tolist(),
    }


def main():
    checks = [check(seed) for seed in range(701, 706)]
    error = max(row["proposed_vs_direct_maxabs"] for row in checks)
    assert error <= 1e-10, error
    nodes, weights = np.polynomial.hermite.hermgauss(100)
    logistic = lambda x: 1 / (1 + np.exp(-x))
    conditional_mean, conditional_sd = 1.0, 1.0
    integrated = float(weights @ logistic(conditional_mean + np.sqrt(2) * conditional_sd * nodes) / np.sqrt(np.pi))
    plugin = float(logistic(conditional_mean))
    result = {
        "biological_inputs_read": False,
        "hypothesis": "paired anchored linear update equals ordinary full joint Gaussian conditioning",
        "tolerance": 1e-10,
        "max_error": error,
        "checks": checks,
        "nonlinear_plugin_example": {
            "distribution": "Normal(1,1), logistic head",
            "plugin": plugin,
            "conditional_expectation_100point_quadrature": integrated,
            "difference": plugin - integrated,
        },
    }
    out = Path("log/20261022/ptpc_update_opportunity/review/ALGEBRA_FALSIFIER_RESULT.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
