"""Episode runner and metrics shared by development and sealed evaluation.

One episode = one query drug, one design policy, budgets 1..B. At each budget the record keeps the
non-rejected set, whether the true class is in it, its p-value, and the uncalibrated comparator:
the smallest Gaussian-posterior credible set (uniform prior over hypotheses, likelihood
exp(-total_nll / 2) from the same compiled models) reaching 1 - alpha mass.
"""
from __future__ import annotations

import numpy as np

import falsify as F
import study as S


def credible_set(fz: F.Falsifier, z: np.ndarray, opts: list[int], hyp: np.ndarray, alpha: float) -> np.ndarray:
    Q, b, A = fz.stats(z, opts, hyp)
    s, _ = F.score_from_stats(Q, b, A, fz.noise.tau2, len(opts))
    nll = s * len(opts)
    nll = np.where(np.isnan(fz.P[hyp][:, opts, 0]).any(axis=1), np.inf, nll)
    ll = -0.5 * nll
    ll = ll - np.max(ll[np.isfinite(ll)]) if np.isfinite(ll).any() else ll
    w = np.where(np.isfinite(ll), np.exp(ll), 0.0)
    w = w / w.sum() if w.sum() > 0 else np.full(len(hyp), 1 / len(hyp))
    order = np.argsort(-w)
    cum = np.cumsum(w[order])
    k = int(np.searchsorted(cum, 1 - alpha) + 1)
    return hyp[order[:k]]


def run_queries(b: S.Built, data: dict, queries: np.ndarray, policies: list[str], budget: int,
                hyp_filter=None, z_override: np.ndarray | None = None) -> list[dict]:
    fz = S.falsifier(b)
    Z = b.Z_open if z_override is None else z_override
    names = fz.names
    step_cals = {}
    if b.cfg.calib == "episode":
        if hyp_filter is not None:
            raise ValueError("episode calibration is defined for the full hypothesis set only")
        step_cals = {pol: F.episode_calibration(fz, pol, budget, seed=b.cfg.seed) for pol in policies}
    rows = []
    for qi in queries:
        true = data["moa"][qi]
        avail = S.available(data, qi)
        hyp = np.arange(len(names)) if hyp_filter is None else hyp_filter(qi, true)
        for pol in policies:
            res = fz.run(Z[qi], avail, pol, budget, true, seed=int(b.cfg.seed + qi), hyp=hyp, step_cal=step_cals.get(pol))
            steps = []
            for k, (o, surv, pt) in enumerate(zip(res.observed, res.surviving, res.pvalues_true)):
                opts = res.observed[:k + 1]
                cs = credible_set(fz, Z[qi], opts, hyp, b.cfg.alpha)
                steps.append({"budget": k + 1, "option": data["options"][o], "set_size": len(surv),
                              "covered": bool(true in surv), "p_true": pt,
                              "cred_size": int(len(cs)), "cred_covered": bool(true in set(names[cs]))})
            rows.append({"drug": str(data["drug"][qi]), "moa": true, "policy": pol, "status": res.status,
                         "n_hyp": int(len(hyp)), "true_in_H": bool(true in set(names[hyp])), "steps": steps})
    return rows


def summarise(rows: list[dict], budget: int) -> dict:
    """Coverage and set size at each budget; an episode that stopped early keeps its last set."""
    out = {}
    pols = sorted({r["policy"] for r in rows})
    for pol in pols:
        rs = [r for r in rows if r["policy"] == pol]
        per_b = {}
        for k in range(1, budget + 1):
            cov, size, ccov, csize = [], [], [], []
            for r in rs:
                if not r["steps"]:
                    continue
                st = r["steps"][min(k, len(r["steps"])) - 1]
                cov.append(st["covered"])
                size.append(st["set_size"])
                ccov.append(st["cred_covered"])
                csize.append(st["cred_size"])
            per_b[k] = {"n": len(cov), "coverage": float(np.mean(cov)), "mean_set": float(np.mean(size)),
                        "median_set": float(np.median(size)), "cred_coverage": float(np.mean(ccov)),
                        "cred_mean_set": float(np.mean(csize))}
        out[pol] = per_b
    return out
