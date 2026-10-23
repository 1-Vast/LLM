"""Empirical-Bayes world fit: Student-t read noise, an NPMLE effect prior and the Jaaks primary-read model."""
import numpy as np
from scipy import optimize, special

from common import GRID
from evalues import t_logpdf


def residuals(X):
    """Within-unit residuals scaled by sqrt(n/(n-1)) so each has the variance of one read's noise."""
    X = np.asarray(X, dtype=float)
    n = (~np.isnan(X)).sum(axis=1)
    keep = n >= 2
    Xk, nk = X[keep], n[keep]
    mean = np.nanmean(Xk, axis=1)
    r = (Xk - mean[:, None]) * np.sqrt(nk / (nk - 1.0))[:, None]
    return r[~np.isnan(r)]


def fit_t(r):
    """Location-0 Student-t maximum likelihood over sigma > 0 and nu in [2.1, 100] (L-BFGS-B, three starts)."""
    r = np.asarray(r, dtype=float)
    s0 = 1.4826 * np.median(np.abs(r))
    if not s0 > 0:
        s0 = float(np.std(r))

    def nll(theta):
        return -float(np.sum(t_logpdf(r, np.exp(theta[0]), theta[1])))

    bounds = [(np.log(s0) - 6.0, np.log(s0) + 6.0), (2.1, 100.0)]
    best = None
    for nu0 in (3.0, 8.0, 40.0):
        res = optimize.minimize(nll, x0=[np.log(s0), nu0], method="L-BFGS-B", bounds=bounds)
        if best is None or res.fun < best.fun:
            best = res
    return {"sigma": float(np.exp(best.x[0])), "nu": float(best.x[1]), "neg_loglik": float(best.fun),
            "n_residuals": int(r.size), "converged": bool(best.success), "nu_at_bound": bool(best.x[1] >= 99.999)}


THETA_FIT = np.linspace(-np.pi / 2, np.pi / 2, 2003)[1:-1]


def invariant_loglik(X, sigma, nu, scale, theta=THETA_FIT, chunk=400):
    """Sum over units of log of the integral over m of prod_j f_t(x_uj - m): the density of each unit's
    within-unit contrasts, which depends on the single-read noise law but not on the effect prior.
    Integrated on m = mean_u + scale * tan(theta) by the trapezoid rule (the integrand vanishes at the ends)."""
    X = np.asarray(X, dtype=float)
    xbar = np.nanmean(X, axis=1)
    t = np.tan(theta)
    logjac = np.log(scale) - 2.0 * np.log(np.cos(theta)) + np.log(theta[1] - theta[0])
    total = 0.0
    for lo in range(0, X.shape[0], chunk):
        Xc = X[lo:lo + chunk]
        m = xbar[lo:lo + chunk, None] + scale * t[None, :]
        ll = np.broadcast_to(logjac, m.shape).copy()
        for j in range(Xc.shape[1]):
            ok = ~np.isnan(Xc[:, j])
            if ok.any():
                ll[ok] += t_logpdf(Xc[ok, j, None] - m[ok], sigma, nu)
        total += float(np.sum(special.logsumexp(ll, axis=1)))
    return total


def fit_t_invariant(X):
    """Single-read Student-t noise by maximum location-invariant likelihood over units with >= 2 reads.

    Residual-based fits see averages of noise draws and so understate tail weight; this likelihood is exact for
    iid t noise around any unit effect. Starts from the residual fit, whose sigma also fixes the quadrature scale."""
    X = np.asarray(X, dtype=float)
    X = X[(~np.isnan(X)).sum(axis=1) >= 2]
    start = fit_t(residuals(X))
    scale = start["sigma"]

    def nll(theta):
        return -invariant_loglik(X, np.exp(theta[0]), theta[1], scale)

    bounds = [(np.log(scale) - 3.0, np.log(scale) + 3.0), (2.1, 100.0)]
    best = None
    for nu0 in (min(max(start["nu"], 2.5), 60.0), 4.0):
        res = optimize.minimize(nll, x0=[np.log(scale), nu0], method="L-BFGS-B", bounds=bounds)
        if best is None or res.fun < best.fun:
            best = res
    return {"sigma": float(np.exp(best.x[0])), "nu": float(best.x[1]), "neg_loglik": float(best.fun),
            "units": int(X.shape[0]), "reads": int((~np.isnan(X)).sum()), "converged": bool(best.success),
            "nu_at_bound": bool(best.x[1] >= 99.999), "method": "location-invariant likelihood",
            "residual_fit": start}


def read_loglik(X, sigma, nu, grid=GRID):
    """LL[u, g] = sum over unit u's finite reads of log f_t(x - grid[g])."""
    X = np.asarray(X, dtype=float)
    LL = np.zeros((X.shape[0], grid.size))
    for j in range(X.shape[1]):
        col = X[:, j]
        ok = ~np.isnan(col)
        LL[ok] += t_logpdf(col[ok, None] - grid[None, :], sigma, nu)
    return LL


def npmle(LL, tol=1e-10, max_iter=5000):
    """Nonparametric ML prior on the grid by EM; stops when the relative log-likelihood change is below tol."""
    top = LL.max(axis=1, keepdims=True)
    L = np.exp(LL - top)
    K, G = L.shape
    w = np.full(G, 1.0 / G)
    previous = -np.inf
    loglik = -np.inf
    iterations = 0
    for iterations in range(1, max_iter + 1):
        mix = L @ w
        loglik = float(np.sum(np.log(mix)) + np.sum(top))
        if np.isfinite(previous) and abs(loglik - previous) <= tol * abs(previous):
            break
        previous = loglik
        w = w * (L.T @ (1.0 / mix)) / K
        w /= w.sum()
    return {"weights": w, "loglik": loglik, "iterations": iterations, "converged": iterations < max_iter}


def prior_summary(w, grid=GRID):
    mean = float(w @ grid)
    sd = float(np.sqrt(w @ (grid - mean) ** 2))
    cdf = np.cumsum(w)
    quant = {str(q): float(grid[np.searchsorted(cdf, q)]) for q in (0.05, 0.25, 0.5, 0.75, 0.95)}
    return {"mean": mean, "sd": sd, "p_positive": float(w[grid > 0].sum()), "p_zero_atom": float(w[grid == 0].sum()),
            "quantiles": quant, "support_points_over_1e-4": int((w > 1e-4).sum())}


def fit_primary(p, n_o, LL, w, nu, grid=GRID):
    """Marginal ML for p = a + b mu + eta, eta ~ t(nu, sigma_p / sqrt(n_o)), with the prior and noise model fixed."""
    finite = np.isfinite(p)
    pf, nf, LLf = p[finite], n_o[finite].astype(float), LL[finite]
    logw = np.log(np.maximum(w, 1e-300))

    def nll(theta):
        a, b, lsp = theta
        scale = np.exp(lsp) / np.sqrt(nf)
        lp = t_logpdf((pf[:, None] - a - b * grid[None, :]) / scale[:, None], 1.0, nu) - np.log(scale)[:, None]
        return -float(np.sum(special.logsumexp(lp + LLf + logw[None, :], axis=1)))

    s0 = float(np.std(pf))
    best = None
    for b0 in (0.5, 1.0, 2.0):
        res = optimize.minimize(nll, x0=[0.0, b0, np.log(s0)], method="L-BFGS-B",
                                bounds=[(-1.0, 1.0), (-5.0, 10.0), (np.log(s0) - 8.0, np.log(s0) + 3.0)])
        if best is None or res.fun < best.fun:
            best = res
    a, b, lsp = best.x
    return {"a": float(a), "b": float(b), "sigma_p": float(np.exp(lsp)), "neg_loglik": float(best.fun),
            "n_units": int(finite.sum()), "converged": bool(best.success)}


def draw_effects(rng, w, size, grid=GRID):
    return rng.choice(grid, size=size, p=w)


def draw_noise(rng, sigma, nu, shape):
    return sigma * rng.standard_t(nu, size=shape)
