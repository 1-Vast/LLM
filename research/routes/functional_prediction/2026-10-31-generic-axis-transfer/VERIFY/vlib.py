"""Verifier's own implementations of the protocol's endpoint, arms and tests (written from PROTOCOL.md sections 5-7).

Nothing here is imported from the study's run code or from src/; the maintained module is used only as a
cross-check in a separate script.
"""
import numpy as np
from scipy import stats

ARMS = ["B0", "B1", "B2", "C1", "L"]


# ----------------------------------------------------------------------------------------------- endpoint
def resid(y, g):
    """y minus its least-squares fit on g, both centred over the lines where both are finite."""
    y = np.asarray(y, dtype=np.float64)
    g = np.asarray(g, dtype=np.float64)
    ok = np.isfinite(y) & np.isfinite(g)
    out = np.full(y.shape, np.nan)
    if ok.sum() == 0:
        return out
    yc = y[ok] - y[ok].mean()
    gc = g[ok] - g[ok].mean()
    gg = float(gc @ gc)
    beta = float(yc @ gc) / (gg if gg > 1e-12 else 1e-12)
    out[ok] = yc - beta * gc
    return out


def sel_r(pred, obs, g, min_lines):
    a, b = resid(pred, g), resid(obs, g)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < min_lines:
        return np.nan
    a, b = a[ok], b[ok]
    if a.std() < 1e-10 or b.std() < 1e-10:
        return np.nan
    a = a - a.mean()
    b = b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))


def n_top(n, rule):
    if rule == "floor":
        return int(np.floor(0.1 * n + 1e-9))
    if rule == "round":
        return int(round(0.1 * n))
    if rule == "round_half_up":
        return int(np.floor(0.1 * n + 0.5 + 1e-9))
    if rule == "ceil":
        return int(np.ceil(0.1 * n - 1e-9))
    raise ValueError(rule)


def hit_precision(pred, obs, g, sign, *, eval_rule="both", count_rule="round"):
    """Shared fraction of the top-10% lines by sensitivity residual (sign=+1: z; sign=-1: -LFC)."""
    a, b = resid(pred, g), resid(obs, g)
    if eval_rule == "both":
        ok = np.isfinite(a) & np.isfinite(b)
    elif eval_rule == "observed":
        ok = np.isfinite(b)
    else:
        raise ValueError(eval_rule)
    idx = np.flatnonzero(ok)
    n = n_top(len(idx), count_rule)
    if n < 1:
        return np.nan
    sa = sign * a[idx]
    sb = sign * b[idx]
    # predicted residual may be NaN under eval_rule="observed": rank NaN last
    sa = np.where(np.isfinite(sa), sa, -np.inf)
    top_pred = set(idx[np.argsort(-sa, kind="stable")[:n]].tolist())
    top_true = set(idx[np.argsort(-sb, kind="stable")[:n]].tolist())
    return len(top_pred & top_true) / n


# ----------------------------------------------------------------------------------------------- tests
def paired_one_sided(x, y):
    """One-sided paired t-test of mean(x - y) > 0."""
    d = np.asarray(x, float) - np.asarray(y, float)
    n = len(d)
    m = d.mean()
    s = d.std(ddof=1)
    t = m / (s / np.sqrt(n))
    p = float(stats.t.sf(t, n - 1))
    return {"mean_difference": float(m), "t": float(t), "p_one_sided": p, "n": int(n)}


def one_sample_two_sided(x):
    x = np.asarray(x, float)
    n = len(x)
    t = x.mean() / (x.std(ddof=1) / np.sqrt(n))
    return float(x.mean()), float(t), float(2 * stats.t.sf(abs(t), n - 1))


def holm(pvals, alpha=0.05):
    """Holm step-down decisions in the input order."""
    p = np.asarray(pvals, float)
    order = np.argsort(p, kind="stable")
    m = len(p)
    rej = np.zeros(m, bool)
    for i, j in enumerate(order):
        if p[j] <= alpha / (m - i):
            rej[j] = True
        else:
            break
    return rej.tolist()


def boot_ci(d, n_boot=10000, seed=12345, method="choice"):
    d = np.asarray(d, float)
    rng = np.random.default_rng(seed)
    n = len(d)
    if method == "choice":
        idx = rng.integers(0, n, size=(n_boot, n))
    else:
        idx = np.vstack([rng.choice(n, size=n, replace=True) for _ in range(n_boot)])
    means = d[idx].mean(axis=1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


# ----------------------------------------------------------------------------------------------- arms
def mean_cosine(qsig, Rsig):
    """Mean cosine over options measured for both. qsig: O x G; Rsig: N x O x G (NaN rows = unmeasured)."""
    q = np.asarray(qsig, np.float64)
    R = np.asarray(Rsig, np.float64)
    qh = np.isfinite(q[:, 0])
    rh = np.isfinite(R[:, :, 0])
    sims = np.zeros(R.shape[0])
    cnt = np.zeros(R.shape[0])
    for o in np.flatnonzero(qh):
        have = rh[:, o]
        if not have.any():
            continue
        qo = q[o]
        Ro = R[have, o, :]
        num = Ro @ qo
        den = np.linalg.norm(Ro, axis=1) * np.linalg.norm(qo)
        good = den > 0
        c = np.zeros(len(Ro))
        c[good] = num[good] / den[good]
        hidx = np.flatnonzero(have)
        sims[hidx[good]] += c[good]
        cnt[hidx[good]] += 1
    out = np.full(R.shape[0], np.nan)
    out[cnt > 0] = sims[cnt > 0] / cnt[cnt > 0]
    return out


class AxisRemoval:
    """Per option: centre on the reference mean, project out the top-D principal directions of the references."""

    def __init__(self, Rsig, D, centre_query=True):
        R = np.asarray(Rsig, np.float64)
        self.D = D
        self.centre_query = centre_query
        self.mu, self.V = {}, {}
        for o in range(R.shape[1]):
            have = np.isfinite(R[:, o, 0])
            X = R[have, o, :]
            mu = X.mean(axis=0)
            Xc = X - mu
            _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
            self.mu[o] = mu
            self.V[o] = Vt[:D]

    def transform(self, sig):
        """sig: N x O x G (NaN rows stay NaN)."""
        S = np.array(sig, dtype=np.float64, copy=True)
        for o in range(S.shape[1]):
            X = S[:, o, :]
            have = np.isfinite(X[:, 0])
            Xc = X[have] - self.mu[o] if self.centre_query else X[have]
            V = self.V[o]
            X[have] = Xc - (Xc @ V.T) @ V
            S[:, o, :] = X
        return S


def tanimoto(qfp, Rfp):
    q = np.asarray(qfp, bool)
    R = np.asarray(Rfp, bool)
    inter = (R & q).sum(axis=1)
    union = (R | q).sum(axis=1)
    out = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    return out.astype(np.float64)


def weighted_prediction(sim, Y, k):
    """Clipped-similarity-weighted mean of the k most similar references' profiles, skipping missing values."""
    sim = np.asarray(sim, float)
    usable = np.isfinite(sim)
    if not usable.any():
        return np.full(Y.shape[1], np.nan), None
    kk = min(k, int(usable.sum()))
    order = np.argsort(-np.where(usable, sim, -np.inf), kind="stable")[:kk]
    w = np.clip(sim[order], 0.0, None)
    if w.sum() <= 0:
        w = np.ones(len(order))
    X = Y[order]
    have = np.isfinite(X)
    den = (w[:, None] * have).sum(axis=0)
    num = (w[:, None] * np.where(have, X, 0.0)).sum(axis=0)
    out = np.full(Y.shape[1], np.nan)
    out[den > 0] = num[den > 0] / den[den > 0]
    return out, order
