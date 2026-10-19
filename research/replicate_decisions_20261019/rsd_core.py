"""RSD core: replicate-identified Virtual Cell posterior, decision rules, escalation agent and sealed evaluator.

File summary
- Selective response of one read y (compound x lines): s = y - rowmean(y) - g, where g is the reference line-mean of
  row-centred reference profiles (generic line sensitivity). Higher killing = more negative s.
- Virtual Cell (VC), two parts, both fitted on the block's purged reference compounds only:
  1. chemistry prior mu(d): mean of a Tanimoto kNN (k = 10) and a Tanimoto-kernel ridge (lambda = 1) on reference
     profiles (mean of the three reads). Reference compounds get cross-fitted priors (leave-cluster-out with edge purge).
  2. response geometry: signal covariance S of the residual s - mu and noise covariance N of one read, identified
     from two replicate reads (B, T) of reference compounds: S = sym Cov(rB, rT), N = Cov(rB - rT) / 2 (the
     Noise2Noise identity: independent replicate noise cancels in the cross-covariance). S is low-rank (q) plus
     diagonal; N keeps within-pool structure (shrunk by rho) and is zero across pools. Per activity tier
     (read-A row-mean log2FC: <= -1, (-1, -0.3], > -0.3) both get a scalar scale.
- Posterior for a query after r averaged reads on observed lines o: m = mu + S[:, o] (S[o, o] + N[o, o] / r)^-1 (y_o - mu_o).
- Decisions: D1 context selection (top M lines per compound), D2 progression (top K compounds per line in a block),
  D3 escalation (agent buys read B for a fraction of the block's compounds, then D2).
- Evaluator: the only code path that reads T of query compounds. Utility = mean of -s_T over chosen pairs with known T.
No LLM, no paid call, no sealed tier.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

M_LINES, K_DRUGS, K_NN, LAM = 10, 16, 10, 1.0
TIER_EDGES = (-1.0, -0.3)


# ----------------------------------------------------------------------------- helpers
def selective(Y, g):
    Z = Y - np.nanmean(Y, axis=1, keepdims=True)
    return Z - g[None, :]


def line_mean(Yref):
    Z = Yref - np.nanmean(Yref, axis=1, keepdims=True)
    return np.nanmean(Z, axis=0)


def tier_of(Araw):
    mu = np.nanmean(Araw, axis=1)
    return np.where(mu <= TIER_EDGES[0], 0, np.where(mu <= TIER_EDGES[1], 1, 2))


def pair_cov(X, Y):
    """Pairwise-complete cross-covariance of columns (rows = compounds), each column centred on its observed mean."""
    mx, my = np.isfinite(X), np.isfinite(Y)
    m = mx & my
    Xc = np.where(m, X - np.nanmean(np.where(m, X, np.nan), 0), 0.0)
    Yc = np.where(m, Y - np.nanmean(np.where(m, Y, np.nan), 0), 0.0)
    cnt = m.astype(float).T @ m.astype(float)
    return (Xc.T @ Yc) / np.maximum(cnt - 1, 1.0)


# ----------------------------------------------------------------------------- VC: chemistry prior
def knn_ridge_prior(Tqr, Trr, Sref):
    """Mean of Tanimoto kNN and Tanimoto-kernel ridge predictions of selective profiles (NaN-safe)."""
    S0 = np.where(np.isfinite(Sref), Sref, 0.0)
    fin = np.isfinite(Sref).astype(float)
    W = np.zeros_like(Tqr)
    idx = np.argsort(-Tqr, axis=1)[:, :K_NN]
    r = np.arange(Tqr.shape[0])[:, None]
    W[r, idx] = np.clip(Tqr[r, idx], 0, None)
    den = W @ fin
    knn = np.where(den > 1e-9, (W @ S0) / np.maximum(den, 1e-9), 0.0)
    krr = Tqr @ np.linalg.solve(Trr + LAM * np.eye(Trr.shape[0]), S0)
    return 0.5 * (knn + krr)


class VirtualCell:
    """Chemistry prior plus replicate-identified response geometry for one query block."""

    def __init__(self, Tsim, ref, ref_cluster, edges, A, B, T, pools, q=20, rho=1.0, tiers=True, use_prior=True,
                 noise_model="pool", geometry="replicate"):
        self.q, self.rho, self.tiers, self.use_prior = q, rho, tiers, use_prior
        self.noise_model, self.geometry = noise_model, geometry
        self.ref = ref
        self.Tsim = Tsim
        Yref = (np.nanmean(np.stack([A[ref], B[ref], T[ref]]), 0))
        self.g = line_mean(Yref)
        self.Sref = selective(Yref, self.g)
        self.pools = pools
        # cross-fitted reference priors: leave-cluster-out, purging edge-connected references
        mu_ref = np.zeros_like(self.Sref)
        if use_prior:
            cl = np.asarray(ref_cluster)
            for c in np.unique(cl):
                qi = np.where(cl == c)[0]
                keep = np.where((cl != c) & ~edges[np.ix_(ref, ref)][qi].any(0))[0]
                mu_ref[qi] = knn_ridge_prior(Tsim[np.ix_(ref[qi], ref[keep])], Tsim[np.ix_(ref[keep], ref[keep])], self.Sref[keep])
        sA, sB, sT = (selective(X[ref], self.g) for X in (A, B, T))
        tier = tier_of(A[ref]) if tiers else np.zeros(len(ref), int)
        rB, rT = sB - mu_ref, sT - mu_ref
        rA = sA - mu_ref
        L = A.shape[1]
        # global shapes
        C = pair_cov(rB, rT)
        S0 = 0.5 * (C + C.T)
        D = (rB - rT) / np.sqrt(2.0)
        N0 = pair_cov(D, D)
        if geometry == "total":            # identification ablation: total covariance of one read, no replicate split
            S0 = pair_cov(rA, rA)
        self.S0 = self._lowrank_diag(S0, q)
        same_pool = pools[:, None] == pools[None, :]
        if noise_model == "pool":
            N = np.where(same_pool, N0, 0.0)
            off = ~np.eye(L, dtype=bool)
            N[off] *= rho
            # a pairwise-complete covariance block need not be PSD: clip each pool block's eigenvalues at a floor
            floor = 1e-3 * np.median(np.diag(N0))
            for p in np.unique(pools):
                ix = np.where(pools == p)[0]
                w, V = np.linalg.eigh(N[np.ix_(ix, ix)])
                N[np.ix_(ix, ix)] = (V * np.clip(w, floor, None)) @ V.T
        else:
            N = np.diag(np.diag(N0))
        self.N0 = N + 1e-6 * np.eye(L)
        # per-tier scalar scales (replicate identified within tier)
        self.alpha, self.beta = np.ones(3), np.ones(3)
        if tiers:
            for k in range(3):
                mk = tier == k
                if mk.sum() < 10:
                    continue
                Ck = pair_cov(rB[mk], rT[mk])
                Nk = pair_cov(D[mk], D[mk])
                self.alpha[k] = max(np.trace(0.5 * (Ck + Ck.T)) / np.trace(self.S0), 0.05)
                self.beta[k] = max(np.trace(Nk) / np.trace(self.N0), 0.05)
                if geometry == "total":
                    Ck = pair_cov(rA[mk], rA[mk])
                    self.alpha[k] = max(np.trace(Ck) / np.trace(self.S0), 0.05)
        self.tier_counts = np.bincount(tier, minlength=3)

    @staticmethod
    def _lowrank_diag(S, q):
        w, V = np.linalg.eigh(S)
        o = np.argsort(w)[::-1][:q]
        w, V = np.clip(w[o], 0, None), V[:, o]
        LR = (V * w) @ V.T
        d = np.clip(np.diag(S) - np.diag(LR), 1e-4, None)
        return LR + np.diag(d)

    def prior(self, qidx, keep_ref):
        if not self.use_prior:
            return np.zeros((len(qidx), len(self.g)))
        r = self.ref[keep_ref]
        return knn_ridge_prior(self.Tsim[np.ix_(qidx, r)], self.Tsim[np.ix_(r, r)], self.Sref[keep_ref])

    def posterior(self, mu, reads_raw, n_reads, tier):
        """reads_raw: raw log2FC (n x L) already averaged over n_reads replicates; returns mean, var (signal), predictive var of one new read."""
        y = selective(reads_raw, self.g)
        n, L = y.shape
        mean = mu.copy()
        var = np.zeros((n, L))
        for i in range(n):
            k = tier[i] if self.tiers else 0
            S = self.alpha[k] * self.S0
            Nn = self.beta[k] * self.N0 / n_reads[i]
            o = np.isfinite(y[i])
            if o.sum() == 0:
                var[i] = np.diag(S)
                continue
            Soo = S[np.ix_(o, o)] + Nn[np.ix_(o, o)]
            Sxo = S[:, o]
            Kt = np.linalg.solve(Soo, Sxo.T)                  # o x L
            mean[i] = mu[i] + Kt.T @ (y[i, o] - mu[i, o])
            var[i] = np.diag(S) - np.einsum("ol,ol->l", Sxo.T, Kt)
        noise1 = np.array([self.beta[t if self.tiers else 0] * np.diag(self.N0) for t in tier])
        return mean, np.clip(var, 1e-8, None), noise1


# ----------------------------------------------------------------------------- reference-internal replicate-split selection
def inner_select(Tsim, ref, ref_cluster, edges, A, B, T, pools, grid, pca_grid, n_inner=5, salt="rsd20261019|inner"):
    """Choose (q, rho, use_prior) for the VC and q for the PCA baseline using only reference compounds: input = read A of held-out
    reference clusters, target = their read T (independent replicate noise), objective = mean of D1 and D2 utility gains
    over the raw read. Folds are reference clusters (hash), held-out references are edge-purged from the inner fit."""
    import hashlib
    cl = np.asarray(ref_cluster)
    fold = np.array([int(hashlib.sha256((salt + "|" + c).encode()).hexdigest()[:8], 16) % n_inner for c in cl])
    rows = {("vc", g["q"], g["rho"], g["use_prior"]): [] for g in grid} | {("pca", qq, None, None): [] for qq in pca_grid}
    for f in range(n_inner):
        qi = ref[fold == f]
        conn = edges[np.ix_(ref, qi)].any(1)
        ri = ref[(fold != f) & ~conn]
        if len(qi) < 10 or len(ri) < 50:
            continue
        Ain = A[qi]
        tier = tier_of(Ain)
        base = None
        for g in grid:
            vc = VirtualCell(Tsim, ri, cl[np.isin(ref, ri)], edges, A, B, T, pools, q=g["q"], rho=g["rho"], use_prior=g["use_prior"])
            if base is None:
                sT = selective(T[qi], vc.g)
                raw = raw_score(Ain, vc.g)
                base = (_u1(raw, sT), _u2(raw, sT))
                sAr = selective(A[ri], vc.g)
            mu = vc.prior(qi, np.arange(len(ri)))
            m = vc.posterior(mu, Ain, np.ones(len(qi)), tier)[0]
            rows[("vc", g["q"], g["rho"], g["use_prior"])].append(0.5 * (_u1(m, sT) - base[0]) + 0.5 * (_u2(m, sT) - base[1]))
        for qq in pca_grid:
            m = pca_denoise(Ain, vc.g, sAr, qq)
            rows[("pca", qq, None, None)].append(0.5 * (_u1(m, sT) - base[0]) + 0.5 * (_u2(m, sT) - base[1]))
    score = {k: float(np.mean(v)) for k, v in rows.items() if v}
    vc_best = max((k for k in score if k[0] == "vc"), key=lambda k: (score[k], -k[1]))
    pca_best = max((k for k in score if k[0] == "pca"), key=lambda k: (score[k], -k[1]))
    return (dict(q=vc_best[1], rho=vc_best[2], use_prior=vc_best[3], q_pca=pca_best[1]),
            {f"{k[0]}|q={k[1]}|rho={k[2]}|prior={k[3]}": v for k, v in score.items()})


def _u1(score, sT):
    v = np.take_along_axis(sT, d1_choose(score), axis=1)
    return float(np.nanmean(-v))


def _u2(score, sT):
    ch = d2_choose(score)
    L = sT.shape[1]
    v = sT[ch, np.tile(np.arange(L), (ch.shape[0], 1))]
    return float(np.nanmean(-v))


# ----------------------------------------------------------------------------- baselines on the same read(s)
def raw_score(reads_raw, g):
    return selective(reads_raw, g)


def pca_denoise(reads_raw, g, Sref_single, q):
    """Established low-rank denoiser: project the read's selective profile on the top-q principal axes of single reference reads."""
    y = selective(reads_raw, g)
    C = pair_cov(Sref_single, Sref_single)
    w, V = np.linalg.eigh(0.5 * (C + C.T))
    V = V[:, np.argsort(w)[::-1][:q]]
    out = np.zeros_like(y)
    for i in range(len(y)):
        o = np.isfinite(y[i])
        if o.sum() < q + 2:
            out[i] = np.where(o, y[i], 0.0)
            continue
        coef, *_ = np.linalg.lstsq(V[o], y[i, o], rcond=None)
        out[i] = V @ coef
    return out


def scalar_shrink(reads_raw, g, rel_by_tier, tier):
    y = selective(reads_raw, g)
    return np.where(np.isfinite(y), y, 0.0) * rel_by_tier[tier][:, None]


def fusion(reads_raw, g, mu, w_by_tier, tier):
    y = selective(reads_raw, g)
    w = w_by_tier[tier][:, None]
    return np.where(np.isfinite(y), w * y + (1 - w) * mu, mu)


# ----------------------------------------------------------------------------- decisions (scores: more negative = more killing)
def d1_choose(score, m=M_LINES):
    s = np.where(np.isfinite(score), score, np.inf)
    return np.argsort(s, axis=1)[:, :m]


def d2_choose(score, k=K_DRUGS):
    s = np.where(np.isfinite(score), score, np.inf)
    return np.argsort(s, axis=0)[:k, :]                       # k x lines


# ----------------------------------------------------------------------------- escalation agent (D3)
def kg_scores(mean, var_now, var_after, k=K_DRUGS):
    """Knowledge-gradient value of buying one more read for each compound, summed over lines (progression decision D2)."""
    sd_red = np.sqrt(np.clip(var_now - var_after, 1e-12, None))
    srt = np.sort(mean, axis=0)
    b_in, b_out = srt[k - 1], srt[k]                          # k-th and (k+1)-th most killing per line
    inside = mean <= b_in[None, :]
    bnd = np.where(inside, b_out[None, :], b_in[None, :])
    z = -np.abs(mean - bnd) / sd_red
    return (sd_red * (z * norm.cdf(z) + norm.pdf(z))).sum(axis=1)


# ----------------------------------------------------------------------------- sealed evaluator
class Evaluator:
    """Holds truth reads T (and the independent primary-screen run) for query compounds; policies never see them."""

    def __init__(self, Ttruth_raw, Praw, g, cluster):
        self._sT = selective(Ttruth_raw, g)
        self._sP = selective(Praw, g) if Praw is not None else None
        self.cluster = np.asarray(cluster)

    def d1(self, chosen, truth="T"):
        S = self._sT if truth == "T" else self._sP
        v = np.take_along_axis(S, chosen, axis=1)               # n x m
        known = np.isfinite(v)
        u = np.where(known, -v, np.nan)
        return dict(util=np.nanmean(u, 1), hit=np.nanmean(np.where(known, (v <= -1.0).astype(float), np.nan), 1),
                    fp=np.nanmean(np.where(known, (v > 0).astype(float), np.nan), 1), unknown=(~known).sum())

    def d2_pairs(self, chosen, truth="T"):
        """Per chosen (compound, line) pair: compound index, -s_truth (NaN unknown)."""
        S = self._sT if truth == "T" else self._sP
        k, L = chosen.shape
        lines = np.tile(np.arange(L), (k, 1))
        v = S[chosen, lines]
        return chosen.ravel(), lines.ravel(), -v.ravel()
