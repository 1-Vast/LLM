"""MAESTRO-FAR deterministic core (phases 1-3): Virtual Cell base models, failure signatures, orthogonal L1000 assay actions, slice policies, repairs.

File summary
- Task (per eval fold F, per target line j): pool Q = compounds of fold F; nominate K=16; utility = mean over nominees of u = -S[q,j], where S is the
  selective residual (compound mean and reference line-mean profile removed) of PRISM 19Q4 primary log-fold-change. Higher = more selective killing.
- Base Virtual Cell = mean of Tanimoto-kernel ridge and Tanimoto kNN (ECFP4) trained on reference compounds of other folds (Tanimoto >= 0.5 purged).
- Orthogonal assay action = L1000 signature of every compound in one slice (slices = 16 average-linkage chemistry clusters of Q); at most 4 slices.
  Measured compounds get a repaired score; unmeasured compounds keep the base score. Costs are equal across policies (4 slices).
- Repairs (fixed, no tuning by an agent): none, fuse (mean of base and transcriptional-transfer), gate (transfer if trust >= tau), residual expert, abstain.
No LLM is used here.
"""
from __future__ import annotations
import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from scipy.stats import norm

K_NOM, K_NN, N_SLICE, N_ACT, LAM, TANI = 16, 10, 16, 4, 1.0, 0.5
REFS = {"search": {0: (1, 2), 1: (0, 2)}, "select": {2: (0, 1)}, "test": {3: (0, 1, 2, 4), 4: (0, 1, 2, 3)}}


def selective(Y, ref):
    Z = Y - np.nanmean(Y, axis=1, keepdims=True)
    return Z - np.nanmean(Z[ref], axis=0, keepdims=True)


def knn_w(Tq, k=K_NN):
    """Row weights: top-k positive similarities."""
    W = np.zeros_like(Tq)
    idx = np.argsort(-Tq, axis=1)[:, :k]
    r = np.arange(Tq.shape[0])[:, None]
    W[r, idx] = np.clip(Tq[r, idx], 0, None)
    return W


def wmean(W, S):
    fin = np.isfinite(S)
    num = W @ np.where(fin, S, 0.0)
    den = W @ fin.astype(float)
    return np.where(den > 1e-9, num / np.maximum(den, 1e-9), 0.0), den


def wsd(W, S, mu):
    fin = np.isfinite(S)
    d2 = np.where(fin, S, 0.0) ** 2
    m2, den = wmean(W, np.where(fin, S ** 2, np.nan))
    return np.sqrt(np.clip(m2 - mu ** 2, 0, None))


def krr(Tqr, Trr, S, lam=LAM):
    S0 = np.where(np.isfinite(S), S, 0.0)
    return Tqr @ np.linalg.solve(Trr + lam * np.eye(Trr.shape[0]), S0)


def l1000_sim(Xq, Xr):
    """Mean cosine over the cell lines measured for both compounds (missing never read as zero)."""
    def prep(X):
        m = np.isfinite(X).all(axis=2)                      # n x lines
        Z = np.where(np.isfinite(X), X, 0.0)
        nrm = np.linalg.norm(Z, axis=2, keepdims=True)
        return Z / np.maximum(nrm, 1e-9), m
    A, ma = prep(Xq); B, mb = prep(Xr)
    num = np.einsum("qlg,rlg->qr", A, B)  # sums over lines of cosine incl. only lines where both measured (zeros elsewhere)
    cnt = ma.astype(float) @ mb.astype(float).T
    return np.where(cnt >= 2, num / np.maximum(cnt, 1), np.nan)


class Campaign:
    """One eval fold: base predictions, signatures, transfer predictions, truth utility for all lines."""

    def __init__(self, D, fold, ref_folds, tau=None):
        f = D["fold"]
        self.q = np.where(f == fold)[0]
        r = np.where(np.isin(f, ref_folds))[0]
        r = r[(D["T"][np.ix_(r, self.q)].max(axis=1) < TANI)]
        self.r = r
        self.fold = fold
        Y = D["Y"]
        Sall = selective(Y, r)
        self.S_r, self.S_q = Sall[r], Sall[self.q]
        fin = np.isfinite(self.S_r).mean(axis=0) >= 0.9
        self.lines = np.where(fin & (np.isfinite(self.S_q).mean(axis=0) >= 0.9))[0]
        Tqr, Trr = D["T"][np.ix_(self.q, r)], D["T"][np.ix_(r, r)]
        self.Tqr = Tqr
        self.p_krr = krr(Tqr, Trr, self.S_r)
        W = knn_w(Tqr)
        self.p_knn, _ = wmean(W, self.S_r)
        self.disp = wsd(W, self.S_r, self.p_knn)
        self.base = 0.5 * (self.p_krr + self.p_knn)
        self.dis = np.abs(self.p_krr - self.p_knn)
        self.dom = 1.0 - Tqr.max(axis=1)
        Xq, Xr = D["X"][self.q], D["X"][r]
        sim = l1000_sim(Xq, Xr)
        self.has_sig = np.isfinite(sim).any(axis=1)
        simz = np.where(np.isfinite(sim), sim, -1.0)
        self.trust = np.where(self.has_sig, simz.max(axis=1), -1.0)
        Wt = knn_w(np.clip(simz, 0, None))
        self.p_tr, _ = wmean(Wt, self.S_r)
        # residual expert: leave-fold-out base on references, ridge from L1000 PCs to the residual
        self.p_re = self._residual_expert(D, Xq, Xr, Trr)
        # slices: average-linkage chemistry clusters of Q
        dist = 1.0 - D["T"][np.ix_(self.q, self.q)]
        np.fill_diagonal(dist, 0.0)
        Z = linkage(squareform(np.clip(dist, 0, None), checks=False), "average")
        order = leaves_list(Z)                                   # dendrogram order keeps similar compounds adjacent
        self.slice = np.zeros(len(self.q), int)
        for s_, blk in enumerate(np.array_split(order, N_SLICE)):  # equal-size slices => equal assay cost for every policy
            self.slice[blk] = s_
        self.u = -self.S_q  # utility of nominating compound q for line j (NaN if unmeasured)

    def _residual_expert(self, D, Xq, Xr, Trr):
        fr = D["fold"][self.r]
        base_r = np.zeros_like(self.S_r)
        for g in np.unique(fr):
            te, tr = fr == g, fr != g
            T_te_tr = Trr[np.ix_(te, tr)]
            base_r[te] = 0.5 * (krr(T_te_tr, Trr[np.ix_(tr, tr)], self.S_r[tr]) + wmean(knn_w(T_te_tr), self.S_r[tr])[0])
        E = np.where(np.isfinite(self.S_r), self.S_r - base_r, 0.0)
        F = lambda X: np.nan_to_num(X).reshape(X.shape[0], -1)
        Fr, Fq = F(Xr), F(Xq)
        mu = Fr.mean(axis=0)
        U, s, Vt = np.linalg.svd(Fr - mu, full_matrices=False)
        P = Vt[:30].T
        Zr, Zq = (Fr - mu) @ P, (Fq - mu) @ P
        beta = np.linalg.solve(Zr.T @ Zr + 10.0 * np.eye(30), Zr.T @ E)
        return self.base + Zq @ beta


def repaired(c, tau):
    """Score matrices (q x line) after each fixed repair, for measured compounds."""
    base, tr = c.base, c.p_tr
    rk = lambda A: (np.argsort(np.argsort(A, axis=0), axis=0) + 0.5) / A.shape[0]
    out = {"none": base,
           "fuse": 0.5 * (base + tr),
           "gate": np.where((c.trust >= tau)[:, None], tr, base),
           "resid": c.p_re}
    ab = out["fuse"].copy()
    bad = np.abs(rk(-base) - rk(-tr)) > 0.5
    ab = np.where(bad, 1e6, ab)  # killing is negative S: large positive S = never nominated
    out["abstain"] = ab
    return out


def nominate(score, mask_measured_scores, K=K_NOM):
    """score: predicted S (lower = better). returns boolean nominees matrix q x line."""
    nq, nl = score.shape
    N = np.zeros((nq, nl), bool)
    idx = np.argsort(score, axis=0)[:K]
    N[idx, np.arange(nl)[None, :]] = True
    return N


def slice_choice(c, policy, j, rng, model=None):
    """Return the set of slice ids (<= N_ACT) measured for line j."""
    S = np.unique(c.slice)
    base = c.base[:, j]
    if policy == "random":
        return rng.choice(S, N_ACT, replace=False)
    if policy == "coverage":
        cents = np.array([c.Tqr[c.slice == s].mean(axis=0) for s in S])
        d = np.linalg.norm(cents[:, None] - cents[None], axis=2)
        pick = [int(np.argmax(d.sum(1)))]
        while len(pick) < N_ACT:
            pick.append(int(np.argmax(np.min(d[:, pick], axis=1))))
        return S[pick]
    sc = {}
    thr = np.sort(base)[K_NOM - 1]
    for s in S:
        m = c.slice == s
        if policy == "exploit":
            sc[s] = -base[m].mean()
        elif policy == "poh":
            sd = np.maximum(c.disp[m, j] + c.dis[m, j], 1e-3)
            sc[s] = norm.cdf((thr - base[m]) / sd).sum()
        elif policy == "far":
            band = base <= np.sort(base)[int(0.4 * len(base))]
            sig = model(c, j)                                 # P(false progression) for every q
            sc[s] = (sig[m] * band[m]).sum()
        elif policy == "far2":
            sc[s] = model(c, j)[m].sum()                      # predicted expected utility benefit of measuring the slice
        elif policy == "all":
            sc[s] = 0.0
        elif policy == "oracle":
            sc[s] = 0.0
    if policy == "oracle":
        return None
    if policy == "all":
        return S
    return np.array(sorted(sc, key=lambda s: -sc[s])[:N_ACT])


def false_prog_features(c, j):
    """Pre-assay failure signatures for line j (rank-normalised within the campaign): domain distance, neighbour dispersion, model disagreement."""
    rk = lambda a: (np.argsort(np.argsort(a)) + 0.5) / len(a)
    return np.column_stack([rk(c.dom), rk(c.disp[:, j]), rk(c.dis[:, j])])


def value_features(c, j):
    """Pre-assay features for the expected-benefit model (all computable before any assay): signatures, base rank/score, line scale."""
    rk = lambda a: (np.argsort(np.argsort(a)) + 0.5) / len(a)
    b = c.base[:, j]
    ls = np.nanstd(c.S_r[:, j])
    return np.column_stack([rk(c.dom), rk(c.disp[:, j]), rk(c.dis[:, j]), rk(b), b / max(ls, 1e-6), c.disp[:, j] / max(ls, 1e-6), np.full(len(b), ls)])


def benefit(c, j, repair="fuse", tau=0.0):
    """Realised benefit of measuring each compound (all others at base): change in utility share of the nominee set when every compound is repaired."""
    rep = repaired(c, tau)[repair][:, j]
    Nb = nominate(c.base[:, j:j + 1], None)[:, 0]
    sc = np.where(c.has_sig, rep, c.base[:, j])
    Nf = nominate(sc[:, None], None)[:, 0]
    u = np.nan_to_num(c.u[:, j])
    return (Nf.astype(float) - Nb.astype(float)) * u


def run_policy(c, policy, repair, tau, model, seed):
    rng = np.random.default_rng(seed)
    nq, lines = len(c.q), c.lines
    rep = repaired(c, tau)
    final = c.base.copy()
    measured = np.zeros((nq, c.base.shape[1]), bool)
    if policy in ("oracle", "oracle_split"):
        G = np.zeros((len(lines), N_SLICE))       # realised utility of nominees when only slice s is measured, per line
        for a, j in enumerate(lines):
            for s in range(N_SLICE):
                m = (c.slice == s) & c.has_sig
                sc = c.base[:, j].copy(); sc[m] = rep[repair][m, j]
                Nn = nominate(sc[:, None], None)[:, 0]
                G[a, s] = np.nansum(c.u[Nn, j])
        half = rng.permutation(len(lines)) % 2
    if policy != "none":
        for a, j in enumerate(lines):
            if policy == "oracle":
                S = np.argsort(-G[a])[:N_ACT]
            elif policy == "oracle_split":
                S = np.argsort(-G[half != half[a]].sum(0))[:N_ACT]       # chosen on the other half of lines only: reproducible slice value
            else:
                S = slice_choice(c, policy, j, rng, model)
            m = np.isin(c.slice, S) & c.has_sig
            measured[m, j] = True
        final = np.where(measured, rep[repair], c.base)
    N = nominate(final[:, c.lines], None)
    u = c.u[:, c.lines]
    contrib = np.where(N & np.isfinite(u), u, 0.0).sum(axis=1) / (K_NOM * len(c.lines))   # per-compound share of campaign-mean utility
    hits = (np.where(N & np.isfinite(u), (u >= 1.0).astype(float), 0.0)).sum(axis=1) / (K_NOM * len(c.lines))
    return contrib, hits, measured[:, c.lines].mean()
