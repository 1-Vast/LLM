"""Student-t likelihood ratios, finite-grid diagnostics and terminal e-BH.

At known noise parameters the LR has boundary-null expectation one. The finite composite-null grid is a numerical
diagnostic, not a proof over all null means. Sequential e-process claims additionally require conditional validity
in the allocator's global filtration. Fitting noise on reused evidence or checking a capped mean does not establish
that contract. Terminal e-BH requires valid e-values; arbitrary cross-unit dependence does not repair invalid inputs.
"""
import numpy as np
from scipy import integrate, special

from common import ALPHA, CHECK_M, CHECK_MU, PF_MULTIPLES


def t_logpdf(x, sigma, nu):
    z = np.asarray(x, dtype=float) / sigma
    return (special.gammaln((nu + 1) / 2) - special.gammaln(nu / 2) - 0.5 * np.log(nu * np.pi) - np.log(sigma)
            - (nu + 1) / 2 * np.log1p(z * z / nu))


def log_lr(x, m, sigma, nu):
    """log f_t(x - m) - log f_t(x); the normalising constants cancel."""
    x = np.asarray(x, dtype=float)
    return -(nu + 1) / 2 * (np.log1p(((x - m) / sigma) ** 2 / nu) - np.log1p((x / sigma) ** 2 / nu))


def null_expectation(m_std, mu_std, nu):
    """E[LR(x; m)] for x ~ t_nu centred at mu, in units of sigma."""
    def integrand(x):
        return float(np.exp(t_logpdf(x - mu_std, 1.0, nu) + log_lr(x, m_std, 1.0, nu)))
    cuts = sorted({float(mu_std), 0.0, float(m_std) / 2, float(m_std)})
    edges = [-np.inf, *cuts, np.inf]
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        if lo < hi:
            total += integrate.quad(integrand, lo, hi, epsabs=1e-13, epsrel=1e-12, limit=400)[0]
    return total


THETA = np.linspace(-np.pi / 2, np.pi / 2, 100001)[1:-1]


def null_expectation_grid(ms, mu_std, nu, scale=4.0, chunk=16):
    """Vectorised E_mu[LR(.; m)] for many bets: trapezoid rule after x = scale * tan(theta).

    The integrand vanishes at theta = +-pi/2 for nu > 1; test_synthetic.py checks it against adaptive quadrature."""
    x = scale * np.tan(THETA)
    base = t_logpdf(x - mu_std, 1.0, nu) + np.log(scale) - 2.0 * np.log(np.cos(THETA))
    ms = np.asarray(ms, dtype=float)
    out = np.empty(ms.size)
    step = THETA[1] - THETA[0]
    for lo in range(0, ms.size, chunk):
        v = np.exp(base[None, :] + log_lr(x[None, :], ms[lo:lo + chunk, None], 1.0, nu))
        out[lo:lo + chunk] = step * (v.sum(axis=1) - 0.5 * (v[:, 0] + v[:, -1]))
    return out


def composite_null_check(nu, check_m=CHECK_M, check_mu=CHECK_MU, tolerance=1e-6):
    """Maximum on the supplied finite null grid; `valid` denotes grid compliance only."""
    table = np.array([null_expectation_grid(check_m, mu, nu) for mu in check_mu])
    worst = table.max(axis=0)
    at_zero = table[int(np.argmin(np.abs(check_mu)))]
    valid = worst <= 1.0 + tolerance
    return {"nu": float(nu), "m_over_sigma": check_m, "max_expectation": worst, "expectation_at_mu0": at_zero,
            "valid": valid, "all_valid": bool(valid.all()), "max_over_grid": float(worst.max())}


def clip_bets(m, sigma, check_m, valid):
    """Clip each bet down to the largest valid checked bet at or below it (up to the smallest valid bet)."""
    grid = np.asarray(check_m)[np.asarray(valid)] * sigma
    if grid.size == 0:
        raise ValueError("No grid-compliant bets are available")
    m = np.asarray(m, dtype=float)
    idx = np.searchsorted(grid, m * (1 + 1e-12), side="right") - 1
    return grid[np.clip(idx, 0, len(grid) - 1)]


def cumulative_table(X, bets, sigma, nu):
    """C[u, j, k] = sum of log LR over unit u's first j reads with bet k; bets are per unit (K, M) or shared (M,)."""
    X = np.asarray(X, dtype=float)
    bets = np.asarray(bets, dtype=float)
    if bets.ndim == 1:
        bets = np.broadcast_to(bets, (X.shape[0], bets.size))
    L = log_lr(X[:, :, None], bets[:, None, :], sigma, nu)
    L = np.where(np.isnan(X)[:, :, None], 0.0, L)
    C = np.zeros((X.shape[0], X.shape[1] + 1, bets.shape[1]))
    np.cumsum(L, axis=1, out=C[:, 1:, :])
    return C


def pf_table(X, sigma, nu, multiples=PF_MULTIPLES):
    return cumulative_table(X, np.asarray(multiples) * sigma, sigma, nu)


def mixture_log_e(C, n):
    """log of the uniform Bayes mixture over the table's bets after n[u] reads of each unit."""
    rows = C[np.arange(C.shape[0]), np.asarray(n, dtype=int), :]
    return special.logsumexp(rows, axis=1) - np.log(C.shape[2])


def ebh(log_e, alpha=ALPHA):
    """e-BH: reject the k* largest e-values, k* = max{k : e_(k) >= K / (alpha k)}. Returns (mask, k*)."""
    log_e = np.asarray(log_e, dtype=float)
    K = log_e.size
    srt = np.sort(log_e)[::-1]
    ok = srt >= np.log(K) - np.log(alpha) - np.log(np.arange(1, K + 1))
    if not ok.any():
        return np.zeros(K, dtype=bool), 0
    k = int(np.nonzero(ok)[0].max()) + 1
    return log_e >= np.log(K) - np.log(alpha) - np.log(k), k


def stop_threshold(K, k1, alpha=ALPHA):
    """log T, T = K / (alpha max(k1, 1)): units at or above it are round-1 discoveries and stop."""
    return np.log(K) - np.log(alpha) - np.log(max(k1, 1))
