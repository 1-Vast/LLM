"""Heavy-tailed pair-noise posterior on the frozen RSD Virtual Cell (Student-t scale mixture, VB-EM per compound).

File summary
- Signal model: unchanged from the frozen RSD Virtual Cell (`replicate_decisions_20261019/rsd_core.VirtualCell`): for a
  query compound i in activity tier k, selective response x_i = mu_i + U f_i + g_i, f_i ~ N(0, alpha_k diag(w)),
  g_i ~ N(0, alpha_k diag(d)), where U diag(w) U' + diag(d) is the frozen rank-q + diagonal signal covariance S0.
  `FactorVC` is the frozen class with one recording hook that keeps (U, w, d); every other number is the frozen one.
- Noise model (the revision): one read y_ij = x_ij + e_ij with e_ij | lam_ij ~ N(0, s^2 beta_k n0_j / lam_ij) and
  lam_ij ~ Gamma(nu/2, rate nu/2), i.e. Student-t_nu pair noise with scale s * sqrt(beta_k n0_j). n0_j is the frozen
  replicate noise variance of line j (rho = 0, diagonal), beta_k the frozen tier scale.
- Tail fit: z = (s_B - s_T) / sqrt(2) / sqrt(beta_k n0_j) on reference compounds; under the model z = s (t1 - t2) / sqrt(2)
  with t1, t2 iid t_nu. The density is a two-dimensional Gamma scale mixture of normals (trapezoid quadrature on a
  log-lam grid, products merged on log variance), evaluated on a fine histogram of |z|. For each nu the scale s is
  fitted by maximum likelihood; nu_ML is the profile-likelihood maximiser on a fixed grid.
- Posterior: mean-field VB-EM per compound (vectorised over compounds): given E[lam], the posterior of x is Gaussian and
  computed in factor form (q x q systems); given q(x), E[lam_ij] = (nu + 1) / (nu + ((y_ij - m_ij)^2 + v_ij) / sigma_ij^2).
  nu = inf reproduces the frozen Gaussian posterior exactly (tested).
- Predictive for a new read: x ~ N(m, v) plus fresh t_nu noise; its CDF is a Gamma scale mixture of normal CDFs.
- `ht_inner_select`: chooses nu only inside the block's reference set, with the frozen replicate-split decision utility
  (input A, target T, the frozen five cluster folds and salt, held-out references edge-purged; objective = mean of the
  D1 and D2 gains over the raw read), geometry (q, prior) inherited from the frozen Gaussian inner choice.
No outcome of a query compound is read here; no LLM or paid call.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import gamma as gamma_dist
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
RSD = HERE.parent / "replicate_decisions_20261019"
if str(RSD) not in sys.path:
    sys.path.insert(0, str(RSD))
import rsd_core as C  # noqa: E402  (frozen; imported, never modified)

NU_GRID = (2.0, 3.0, 4.0, 6.0, 10.0, 20.0)                     # inner-selection grid (heavy-tailed only)
NU_ML_GRID = tuple(float(x) for x in np.round(np.geomspace(1.5, 100.0, 41), 4))
K_QUAD, K_DIFF = 160, 400
N_ITER, TOL = 200, 1e-6
INNER_SALT = "rsd20261019|inner"                                # the frozen fold salt of rsd_core.inner_select


# ----------------------------------------------------------------------------- geometry
class FactorVC(C.VirtualCell):
    """The frozen VirtualCell; `_lowrank_diag` additionally records the factors (U, w, d) of the matrix it returns."""

    def _lowrank_diag(self, S, q):
        out = C.VirtualCell._lowrank_diag(S, q)
        w, V = np.linalg.eigh(S)
        o = np.argsort(w)[::-1][:q]
        w, V = np.clip(w[o], 0, None), V[:, o]
        LR = (V * w) @ V.T
        self.U, self.w = V, w
        self.d = np.clip(np.diag(S) - np.diag(LR), 1e-4, None)
        return out

    def noise_diag(self):
        if self.rho != 0 or self.noise_model != "pool":
            raise ValueError("the heavy-tailed posterior is defined for diagonal pair noise (rho = 0) only")
        return np.diag(self.N0).copy()


def build_factor_vc(S, q, use_prior):
    """FactorVC with the frozen constructor arguments of rsd_run.build_vc, rho = 0 (diagonal pair noise)."""
    return FactorVC(S["Tsim"], S["ref"], S["t"].cluster.to_numpy()[S["ref"]], S["E"], S["A"], S["B"], S["T"], S["pools"],
                    q=q, rho=0.0, tiers=True, use_prior=use_prior, noise_model="pool", geometry="replicate")


# ----------------------------------------------------------------------------- Student-t quadrature
_NODES = {}


def gamma_nodes(nu, k=K_QUAD):
    """Nodes lam_k and weights of lam ~ Gamma(nu/2, rate nu/2): trapezoid rule on a log-lam grid between the 1e-10 and
    1 - 1e-12 quantiles (resolves the small-lam region that carries the t tails)."""
    key = (float(nu), k)
    if key not in _NODES:
        a = nu / 2.0
        lo, hi = gamma_dist.ppf(1e-10, a, scale=1 / a), gamma_dist.ppf(1 - 1e-12, a, scale=1 / a)
        u = np.linspace(np.log(lo), np.log(hi), k)
        lam = np.exp(u)
        w = np.exp(gamma_dist.logpdf(lam, a, scale=1 / a) + u)
        w[[0, -1]] *= 0.5
        _NODES[key] = (lam, w / w.sum())
    return _NODES[key]


def diff_mixture(nu, k=K_QUAD, n_bins=K_DIFF):
    """(t1 - t2) / sqrt(2), t1, t2 iid t_nu, as a scale mixture of normals: variance factors c and weights, the k x k
    products (1/lam1 + 1/lam2) / 2 merged into n_bins bins on log c (weight-averaged c per bin)."""
    key = ("diff", float(nu), k, n_bins)
    if key in _NODES:
        return _NODES[key]
    lam, w = gamma_nodes(nu, k)
    c = (0.5 * (1.0 / lam[:, None] + 1.0 / lam[None, :])).ravel()
    wc = (w[:, None] * w[None, :]).ravel()
    lc = np.log(c)
    b = np.minimum(((lc - lc.min()) / (np.ptp(lc) + 1e-12) * n_bins).astype(int), n_bins - 1)
    W = np.bincount(b, wc, n_bins)
    Cm = np.bincount(b, wc * c, n_bins)
    ok = W > 0
    _NODES[key] = (Cm[ok] / W[ok], W[ok] / W[ok].sum())
    return _NODES[key]


def t_scale_pdf_diff(z, s, nu):
    """Density of s (t1 - t2) / sqrt(2), t1, t2 iid t_nu (unit scale)."""
    c, wc = diff_mixture(nu)
    var = (s * s) * c
    z = np.asarray(z, float)[:, None]
    return (wc[None, :] * np.exp(-0.5 * z * z / var[None, :]) / np.sqrt(2 * np.pi * var[None, :])).sum(1)


def _hist(z, n_bins=4000):
    a = np.abs(z[np.isfinite(z)])
    edges = np.linspace(0.0, a.max() * (1 + 1e-9), n_bins + 1)
    cnt, _ = np.histogram(a, edges)
    mid = 0.5 * (edges[1:] + edges[:-1])
    keep = cnt > 0
    return mid[keep], cnt[keep].astype(float)


def fit_scale(z, nu, hist=None):
    """ML scale s of the difference model at fixed nu; returns (s, log-likelihood per observation)."""
    mid, cnt = hist if hist is not None else _hist(z)
    n = cnt.sum()

    def nll(ls):
        return -(cnt * np.log(np.maximum(t_scale_pdf_diff(mid, np.exp(ls), nu), 1e-300))).sum() / n

    r = minimize_scalar(nll, bounds=(np.log(0.05), np.log(3.0)), method="bounded", options=dict(xatol=1e-5))
    return float(np.exp(r.x)), float(-r.fun)


def gauss_scale_ll(z, hist=None):
    """Gaussian reference: ML scale and log-likelihood per observation of the same histogram (symmetric, zero mean)."""
    mid, cnt = hist if hist is not None else _hist(z)
    s2 = float((cnt * mid ** 2).sum() / cnt.sum())
    ll = float((cnt * norm.logpdf(mid, 0, np.sqrt(s2))).sum() / cnt.sum())
    return float(np.sqrt(s2)), ll


def standardized_differences(vc, A, B, T, idx, matrix=False):
    """z = (s_B - s_T) / sqrt(2) / sqrt(beta_k n0_j) over reference compounds idx (tier from read A, frozen edges)."""
    sB, sT = C.selective(B[idx], vc.g), C.selective(T[idx], vc.g)
    tier = C.tier_of(A[idx])
    sd = np.sqrt(vc.beta[tier][:, None] * vc.noise_diag()[None, :])
    Z = (sB - sT) / np.sqrt(2.0) / sd
    return Z if matrix else Z.ravel()


def compound_ll(ss, n, s, nu):
    """Mean log-likelihood per observation of rows z_i ~ N(0, s^2 / lam_i I), lam_i ~ Gamma(nu/2, rate nu/2) (a
    compound-level noise scale shared by the compound's lines and replicate reads), from row sums of squares ss and counts n."""
    lam, w = gamma_nodes(nu)
    lp = np.log(w)[None, :] + 0.5 * n[:, None] * np.log(lam[None, :] / (2 * np.pi * s * s)) - 0.5 * lam[None, :] * ss[:, None] / (s * s)
    m = lp.max(1, keepdims=True)
    return float((m[:, 0] + np.log(np.exp(lp - m).sum(1))).sum() / n.sum())


def fit_tail_compound(Z, nu_grid=NU_ML_GRID, extra=NU_GRID):
    """Profile likelihood over nu of the compound-level scale mixture (ML scale s at every nu)."""
    ok = np.isfinite(Z)
    n = ok.sum(1).astype(float)
    ss = np.where(ok, Z * Z, 0.0).sum(1)
    keep = n > 0
    n, ss = n[keep], ss[keep]
    prof = {}
    for nu in sorted(set(nu_grid) | set(extra)):
        r = minimize_scalar(lambda ls: -compound_ll(ss, n, np.exp(ls), nu), bounds=(np.log(0.05), np.log(3.0)),
                            method="bounded", options=dict(xatol=1e-5))
        prof[float(nu)] = dict(s=float(np.exp(r.x)), ll=float(-r.fun))
    best = max((nu for nu in prof if nu in set(nu_grid)), key=lambda nu: prof[nu]["ll"])
    ms = ss / n
    return dict(nu_ml=float(best), s_ml=prof[best]["s"], profile=prof, n_compounds=int(keep.sum()), n=int(n.sum()),
                compound_mean_z2_sd=float(np.std(ms[n >= 100])) if (n >= 100).any() else None,
                homogeneous_sd=float(np.sqrt(np.mean(2.0 / n[n >= 100]))) if (n >= 100).any() else None)


def fit_tail(z, nu_grid=NU_ML_GRID, extra=NU_GRID):
    """Profile likelihood over nu (and the scale s at every grid nu, including the inner-selection grid)."""
    h = _hist(z)
    prof = {}
    for nu in sorted(set(nu_grid) | set(extra)):
        s, ll = fit_scale(z, nu, h)
        prof[float(nu)] = dict(s=s, ll=ll)
    best = max((nu for nu in prof if nu in set(nu_grid)), key=lambda nu: prof[nu]["ll"])
    sg, llg = gauss_scale_ll(z, h)
    zz = z[np.isfinite(z)]
    zs = (zz - zz.mean()) / zz.std()
    return dict(nu_ml=float(best), s_ml=prof[best]["s"], profile=prof, gauss=dict(s=sg, ll=llg),
                n=int(zz.size), excess_kurtosis=float(np.mean(zs ** 4) - 3.0), share_abs_z_gt3=float(np.mean(np.abs(zs) > 3)))


# ----------------------------------------------------------------------------- posterior
def ht_posterior(vc, mu, reads_raw, tier, nu, s, n_iter=N_ITER, tol=TOL, nu_s=np.inf, level="pair"):
    """VB-EM posterior under Student-t_nu noise (nu = np.inf: frozen Gaussian posterior).

    level = "pair": one precision weight lam_ij per (compound, line) pair (independent pair outliers).
    level = "compound": one weight lam_i per compound, shared by its lines and by its replicate reads (multivariate-t
    noise; a noisy compound is noisy in every read). Its predictive for a new read uses the compound's posterior scale.
    nu_s < inf (development option) also gives the diagonal (line-specific) signal component Student-t_nu_s tails:
    g_ij | eta_ij ~ N(0, alpha_k d_j / eta_ij), eta_ij ~ Gamma(nu_s/2, rate nu_s/2).
    Returns dict(mean, var, sig2, nu, lam, iters, pred_sig2, pred_nu): posterior mean and variance of the selective
    signal, per-pair noise scale^2 of one read, E[lam], and the noise scale^2 and tail of a new read's predictive."""
    y = C.selective(reads_raw, vc.g)
    n, L = y.shape
    obs = np.isfinite(y)
    yc = np.where(obs, y - mu, 0.0)
    k = tier if vc.tiers else np.zeros(n, int)
    a = vc.alpha[k][:, None]
    d0 = a * vc.d[None, :]
    d = d0
    sig2 = (s * s) * vc.beta[k][:, None] * vc.noise_diag()[None, :]
    keep = vc.w > 1e-12
    U, w = vc.U[:, keep], vc.w[keep]
    q = U.shape[1]
    lam = np.ones((n, L))
    eta = np.ones((n, L))
    it = 0
    for it in range(1, n_iter + 1):
        if np.isfinite(nu_s):
            d = d0 / eta
        nn = sig2 / lam
        r = np.where(obs, d / (d + nn), 0.0)
        if q:
            P = np.where(obs, 1.0 / (d + nn), 0.0)
            Pf = np.einsum("lq,nl,lr->nqr", U, P, U)
            Pf[:, np.arange(q), np.arange(q)] += 1.0 / (a * w[None, :])
            Sf = np.linalg.inv(Pf)
            fh = np.einsum("nqr,nr->nq", Sf, np.einsum("lq,nl->nq", U, P * yc))
            pred = fh @ U.T
            uSu = np.einsum("lq,nqr,lr->nl", U, Sf, U)
        else:
            pred = np.zeros((n, L))
            uSu = np.zeros((n, L))
        mc = pred + r * (yc - pred)
        v = (1.0 - r) ** 2 * uSu + np.where(obs, d * nn / (d + nn), d)
        if not np.isfinite(nu) and not np.isfinite(nu_s):
            break
        delta = 0.0
        if np.isfinite(nu):
            e2 = (yc - mc) ** 2 + v
            if level == "compound":
                a_post = 0.5 * (nu + obs.sum(1))
                b_post = 0.5 * (nu + np.where(obs, e2 / sig2, 0.0).sum(1))
                lam_new = np.broadcast_to((a_post / b_post)[:, None], (n, L)).copy()
            else:
                lam_new = np.where(obs, (nu + 1.0) / (nu + e2 / sig2), 1.0)
            delta = float(np.max(np.abs(lam_new - lam))) if lam.size else 0.0
            lam = lam_new
        if np.isfinite(nu_s):
            g2 = (r * (yc - pred)) ** 2 + r * r * uSu + np.where(obs, d * nn / (d + nn), d)
            eta_new = np.where(obs, (nu_s + 1.0) / (nu_s + g2 / d0), 1.0)
            delta = max(delta, float(np.max(np.abs(eta_new - eta))) if eta.size else 0.0)
            eta = eta_new
        if delta < tol:
            break
    if level == "compound" and np.isfinite(nu):
        # new read of the same compound: noise variance sig2 * E[1/lam_i] under q(lam_i) = Gamma(a_post, b_post)
        pred_sig2, pred_nu = sig2 * (b_post / np.maximum(a_post - 1.0, 1e-6))[:, None], np.inf
    else:
        pred_sig2, pred_nu = sig2, float(nu)
    return dict(mean=mu + mc, var=np.clip(v, 1e-8, None), sig2=sig2, nu=float(nu), lam=lam, iters=it,
                pred_sig2=pred_sig2, pred_nu=pred_nu)


def predictive_cdf(e, var, sig2, nu):
    """P(new read - posterior mean <= e) for x ~ N(m, var) plus t_nu noise of scale^2 sig2 (Gaussian if nu = inf)."""
    if not np.isfinite(nu):
        return norm.cdf(e / np.sqrt(var + sig2))
    lam, w = gamma_nodes(nu)
    out = np.zeros_like(e, dtype=float)
    for lk, wk in zip(lam, w):
        out += wk * norm.cdf(e / np.sqrt(var + sig2 / lk))
    return out


def covered(e, var, sig2, nu, level=0.8):
    """Central predictive interval coverage indicator (symmetric unimodal predictive): |F(e) - 1/2| <= level/2."""
    return np.abs(predictive_cdf(e, var, sig2, nu) - 0.5) <= level / 2.0


# ----------------------------------------------------------------------------- reference-internal selection of nu
def fit_scale_compound(Z, nu):
    ok = np.isfinite(Z)
    n = ok.sum(1).astype(float)
    ss = np.where(ok, Z * Z, 0.0).sum(1)
    k = n > 0
    r = minimize_scalar(lambda ls: -compound_ll(ss[k], n[k], np.exp(ls), nu), bounds=(np.log(0.05), np.log(3.0)),
                        method="bounded", options=dict(xatol=1e-5))
    return float(np.exp(r.x))


def candidates(levels=("pair",), nu_grid=NU_GRID, nu_s_grid=(np.inf,)):
    """(level, nu, nu_s) noise-model candidates; nu_s < inf adds Student-t tails to the line-specific signal."""
    return [(lv, float(nu), float(ns)) for lv in levels for nu in nu_grid for ns in nu_s_grid]


def ht_inner_select(S, q, use_prior, cands=None, n_inner=5, salt=INNER_SALT):
    """Choose the noise model (level, nu, nu_s) using reference compounds only (frozen folds, utility and edge purge;
    geometry (q, prior) fixed); the noise scale s is the ML fit of the training references at that (level, nu). The
    Gaussian score is reported for comparison and is not a candidate. Ties go to the larger nu, then the larger nu_s."""
    cands = list(cands) if cands is not None else candidates()
    ref = S["ref"]
    cl = S["t"].cluster.to_numpy()[ref]
    E, A, B, T = S["E"], S["A"], S["B"], S["T"]
    fold = np.array([int(hashlib.sha256((salt + "|" + c).encode()).hexdigest()[:8], 16) % n_inner for c in cl])
    gauss = ("gauss", np.inf, np.inf)
    rows = {c: [] for c in cands} | {gauss: []}
    folds = []
    for f in range(n_inner):
        qi = ref[fold == f]
        conn = E[np.ix_(ref, qi)].any(1)
        ri = ref[(fold != f) & ~conn]
        if len(qi) < 10 or len(ri) < 50:
            continue
        vc = build_factor_vc(dict(S, ref=ri), q, use_prior)
        Z = standardized_differences(vc, A, B, T, ri, matrix=True)
        h = _hist(Z.ravel())
        Ain = A[qi]
        tier = C.tier_of(Ain)
        sT = C.selective(T[qi], vc.g)
        raw = C.raw_score(Ain, vc.g)
        base = (C._u1(raw, sT), C._u2(raw, sT))
        mu = vc.prior(qi, np.arange(len(ri)))
        rec = dict(fold=f, n_query=int(len(qi)), n_fit=int(len(ri)), scores={})
        scale = {}
        for c in cands + [gauss]:
            lv, nu, ns = c
            if lv == "gauss":
                s = 1.0
            else:
                if (lv, nu) not in scale:
                    scale[(lv, nu)] = fit_scale(None, nu, h)[0] if lv == "pair" else fit_scale_compound(Z, nu)
                s = scale[(lv, nu)]
            m = ht_posterior(vc, mu, Ain, tier, nu, s, level=("pair" if lv == "gauss" else lv), nu_s=ns)["mean"]
            sc = 0.5 * (C._u1(m, sT) - base[0]) + 0.5 * (C._u2(m, sT) - base[1])
            rows[c].append(sc)
            rec["scores"][cand_key(c)] = dict(s=s, score=float(sc), D1=float(C._u1(m, sT) - base[0]), D2=float(C._u2(m, sT) - base[1]))
        folds.append(rec)
    score = {c: float(np.mean(v)) for c, v in rows.items() if v}
    best = max((c for c in score if c in cands), key=lambda c: (score[c], c[1], c[2]))
    return dict(level=best[0], nu=float(best[1]), nu_s=float(best[2])), dict(score={cand_key(k): v for k, v in score.items()}, folds=folds)


def cand_key(c):
    return f"{c[0]}|nu={c[1]}|nu_s={c[2]}"
