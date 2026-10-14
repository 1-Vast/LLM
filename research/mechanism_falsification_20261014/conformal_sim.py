"""Synthetic check of what conformal selection does and does not guarantee (asset-free, deterministic).

Setting: covariates X in R^5, outcome Y = f(X) + noise, a unit is a hit when Y > c. A predictor is fitted
on one split, conformal p-values (Jin and Candes 2023) are computed against a calibration split, and
Benjamini-Hochberg selects at level q. Scenarios:

  exchangeable          calibration and test drawn from one distribution (the setting of the theorem)
  covariate_shift       P(X) differs, P(Y|X) unchanged; plain p-values, then weighted p-values (true ratio)
  conditional_shift     P(Y|X) differs in the test set (a new mechanism family): no weighting can repair it
  marginal_coverage     selecting units whose 90% split-conformal interval lies above c: coverage is not FDR
                        (also with noise that depends on a covariate, exchangeable throughout)
  clustered             test units arrive in correlated clusters (shared latent effect), calibration iid

    python research/mechanism_falsification_20261014/conformal_sim.py   # writes CONFORMAL_SIM.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parent
Q, C, D = 0.1, 1.0, 5
N_TRAIN, N_CAL, M_TEST, REPS = 500, 500, 300, 300
BETA = np.array([1.0, 0.8, 0.5, 0.0, 0.0])


def draw(rng, n, shift_mean=0.0, shift_y=0.0, cluster_sd=0.0, clusters=1, hetero=False):
    x = rng.normal(size=(n, D))
    x[:, 0] += shift_mean
    latent = rng.normal(scale=cluster_sd, size=clusters)[rng.integers(0, clusters, size=n)] if cluster_sd else 0.0
    sd = (0.4 + 1.6 * (x[:, 1] > 0.3)) if hetero else 1.0              # noise depends on a covariate, in every split alike
    y = x @ BETA + shift_y + latent + sd * rng.normal(size=n)
    return x, y


def fit(x, y):
    a = np.column_stack([np.ones(len(x)), x])
    w = np.linalg.lstsq(a, y, rcond=None)[0]
    return lambda z: np.column_stack([np.ones(len(z)), z]) @ w


def conformal_p(mu_cal, y_cal, mu_test, weights_cal=None, weights_test=None):
    """p_j = (w_test_j + sum_i w_i 1{V_i < V_j}) / (sum_i w_i + w_test_j), with V_i = c - mu_i for nulls and +inf for hits."""
    null = y_cal <= C
    wc = np.ones(len(y_cal)) if weights_cal is None else weights_cal
    wt = np.ones(len(mu_test)) if weights_test is None else weights_test
    order = np.argsort(-mu_cal[null])                               # null calibration points by decreasing mu
    mu_sorted, w_sorted = mu_cal[null][order], wc[null][order]
    cum = np.concatenate([[0.0], np.cumsum(w_sorted)])
    k = np.searchsorted(-mu_sorted, -mu_test, side="left")           # nulls with mu_i > mu_j
    return (wt + cum[k]) / (wc.sum() + wt)


def bh(p, q):
    m = len(p)
    order = np.argsort(p)
    ok = np.flatnonzero(p[order] <= q * (np.arange(1, m + 1) / m))
    sel = np.zeros(m, bool)
    if ok.size:
        sel[order[: ok.max() + 1]] = True
    return sel


def score(sel, hit):
    n = int(sel.sum())
    return n, (int((sel & ~hit).sum()) / n if n else 0.0), (int((sel & hit).sum()) / max(1, int(hit.sum())))


def run(name, test_kwargs, weighted=False, interval=False):
    rng = np.random.default_rng(abs(hash(name)) % 2 ** 32 if False else sum(map(ord, name)))
    fdp, power, nsel = [], [], []
    for _ in range(REPS):
        base = {"hetero": test_kwargs["hetero"]} if test_kwargs.get("hetero") else {}
        xt, yt = draw(rng, N_TRAIN, **base)
        xc, yc = draw(rng, N_CAL, **base)
        xs, ys = draw(rng, M_TEST, **test_kwargs)
        f = fit(xt, yt)
        hit = ys > C
        if interval:                                                 # split-conformal 90% interval, select on lower bound > c
            half = np.quantile(np.abs(yc - f(xc)), np.ceil(0.9 * (N_CAL + 1)) / N_CAL)
            sel = (f(xs) - half) > C
        else:
            w_c = w_t = None
            if weighted:                                             # true density ratio of the shift in X[:, 0]
                s = test_kwargs["shift_mean"]
                ratio = lambda z: np.exp(s * z[:, 0] - s * s / 2)
                w_c, w_t = ratio(xc), ratio(xs)
            sel = bh(conformal_p(f(xc), yc, f(xs), w_c, w_t), Q)
        n, p_fdp, pw = score(sel, hit)
        fdp.append(p_fdp), power.append(pw), nsel.append(n)
    fdp = np.array(fdp)
    return {"nominal_q": Q, "mean_FDP_estimated_FDR": round(float(fdp.mean()), 4), "se": round(float(fdp.std(ddof=1) / np.sqrt(REPS)), 4),
            "fraction_of_runs_with_FDP_above_q": round(float((fdp > Q).mean()), 3),
            "mean_selected": round(float(np.mean(nsel)), 1), "mean_power": round(float(np.mean(power)), 3),
            "base_rate_test": None}


def main() -> None:
    res = {"settings": {"q": Q, "c": C, "n_train": N_TRAIN, "n_cal": N_CAL, "m_test": M_TEST, "reps": REPS, "beta": BETA.tolist()},
           "exchangeable": run("exchangeable", {}),
           "covariate_shift_unweighted": run("cov_plain", {"shift_mean": 1.0}),
           "covariate_shift_weighted_true_ratio": run("cov_weighted", {"shift_mean": 1.0}, weighted=True),
           "conditional_shift_weaker_signal_unweighted": run("cond", {"shift_y": -0.6}),
           "conditional_shift_after_covariate_weighting": run("cond_w", {"shift_mean": 1.0, "shift_y": -0.6}, weighted=True),
           "clustered_test_units": run("clustered", {"cluster_sd": 1.0, "clusters": 10}),
           "marginal_coverage_interval_selection_exchangeable": run("interval", {}, interval=True),
           "marginal_coverage_interval_selection_conditional_shift": run("interval_shift", {"shift_y": -0.6}, interval=True),
           "heteroscedastic_exchangeable_conformal_p_values": run("hetero_p", {"hetero": True}),
           "heteroscedastic_exchangeable_interval_selection": run("hetero_int", {"hetero": True}, interval=True)}
    notes = {
        "exchangeable": "BH on conformal p-values controls FDR at about q (theorem: finite-sample, calibration and test exchangeable)",
        "covariate_shift_weighted_true_ratio": "weights are the TRUE likelihood ratio; this is plain weighted p-values with BH, not the pruned WCS procedure; real ratios must be estimated",
        "conditional_shift": "any change in P(Y|X) between calibration and test breaks the guarantee, and weights on X cannot restore it",
        "marginal_coverage": "per-unit 90% coverage bounds the expected number of false selections by about 0.05 n0, not the ratio V/R; no FDR theorem applies. In these settings the rule was conservative (FDP 0.02-0.07) with low power, so the simulation does NOT show a failure; it shows the absence of a guarantee has not been tested to breaking here",
    }
    res["notes"] = notes
    (STUDY / "CONFORMAL_SIM.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    for k, v in res.items():
        if isinstance(v, dict) and "mean_FDP_estimated_FDR" in v:
            print(f"{k:58s} FDP {v['mean_FDP_estimated_FDR']:.3f} (se {v['se']:.3f})  >q in {v['fraction_of_runs_with_FDP_above_q']:.2f} of runs  selected {v['mean_selected']:.0f}  power {v['mean_power']:.2f}")


if __name__ == "__main__":
    main()
