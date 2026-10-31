"""Development check (exposed data only): does removing dominant generic L1000 directions
improve kNN transfer of PRISM selective-killing profiles to held-out compounds?

Pool = Block N open+sealed PRISM tiers (1,403 compounds, all exposed) joined to the Block M
landmark arrays (9 lines x 6/24 h x 978 genes, 10 uM). Leave-one-compound-out.
"""
import sys
import numpy as np

ROOT = "D:/MAESTRO/data/external"
rng = np.random.default_rng(0)


def load_pool():
    o = np.load(f"{ROOT}/prism_19q4/derived/block_n_prism_open.npz", allow_pickle=True)
    s = np.load(f"{ROOT}/prism_19q4/derived/block_n_prism_sealed.npz", allow_pickle=True)
    lo = np.load(f"{ROOT}/lincs_l1000_gse92742/derived/block_m_landmark_open.npz", allow_pickle=True)
    ls = np.load(f"{ROOT}/lincs_l1000_gse92742/derived/block_m_landmark_sealed.npz", allow_pickle=True)
    drugs = np.concatenate([o["drug"], s["drug"]])
    Y = np.concatenate([o["primary"], s["primary"]]).astype(float)
    Ysec = np.concatenate([o["secondary"], s["secondary"]]).astype(float)
    moa = np.concatenate([o["moa"], s["moa"]])
    ldr = np.concatenate([lo["drug"], ls["drug"]])
    lx = np.concatenate([lo["x"], ls["x"]]).astype(float)
    idx = {d: i for i, d in enumerate(ldr)}
    X = np.stack([lx[idx[d]] for d in drugs])
    return drugs, moa, Y, Ysec, X, lo["option"]


def residualise_rows(P, G):
    """Row-wise: remove centred least-squares projection on G (NaN-aware, per row)."""
    out = np.full_like(P, np.nan)
    for i in range(len(P)):
        y, g = P[i], G[i] if G.ndim == 2 else G
        ok = np.isfinite(y) & np.isfinite(g)
        if ok.sum() < 3:
            continue
        yc, gc = y[ok] - y[ok].mean(), g[ok] - g[ok].mean()
        out[i, ok] = yc - (yc @ gc) / max(gc @ gc, 1e-12) * gc
    return out


def rowcorr(A, B, min_n=50):
    r = np.full(len(A), np.nan)
    for i in range(len(A)):
        ok = np.isfinite(A[i]) & np.isfinite(B[i])
        if ok.sum() < min_n:
            continue
        a, b = A[i, ok], B[i, ok]
        if a.std() < 1e-10 or b.std() < 1e-10:
            continue
        r[i] = np.corrcoef(a, b)[0, 1]
    return r


def transform(X, mode, D=0, K=0, fit_rows=None):
    """Per option (line x time) transform of signatures. X: n x O x G (NaN = unmeasured)."""
    n, O, Gn = X.shape
    Z = np.full_like(X, np.nan)
    for o in range(O):
        have = np.isfinite(X[:, o, 0])
        fit = have if fit_rows is None else (have & fit_rows)
        if fit.sum() < 20:
            continue
        A = X[have, o]
        if mode == "raw":
            Z[have, o] = A
            continue
        mu = X[fit, o].mean(axis=0)
        Ac = A - mu
        F = X[fit, o] - mu
        U, S, Vt = np.linalg.svd(F, full_matrices=False)
        if mode == "abtt":
            V = Vt[:D]
            Z[have, o] = Ac - (Ac @ V.T) @ V if D > 0 else Ac
        elif mode == "whiten":
            lam = S[:K] ** 2 / max(fit.sum() - 1, 1)
            shrink = lam.mean()  # shrink toward isotropy
            Z[have, o] = (Ac @ Vt[:K].T) / np.sqrt(lam + shrink)
        elif mode == "pcatrunc":
            Z[have, o] = Ac @ Vt[D:K].T * 1.0
    return Z


def mean_cosine(Z):
    n, O, _ = Z.shape
    num = np.zeros((n, n))
    cnt = np.zeros((n, n))
    for o in range(O):
        have = np.isfinite(Z[:, o, 0])
        V = np.nan_to_num(Z[:, o])
        nrm = np.linalg.norm(V, axis=1)
        V = V / np.maximum(nrm, 1e-12)[:, None]
        C = V @ V.T
        m = (have[:, None] & have[None, :]) & (nrm[:, None] > 0) & (nrm[None, :] > 0)
        num += np.where(m, C, 0.0)
        cnt += m
    S = np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)
    np.fill_diagonal(S, np.nan)
    return S


def knn_predict(S, Y, k=5, weighting="clip", temp=0.1):
    n = len(Y)
    P = np.full_like(Y, np.nan)
    for i in range(n):
        s = S[i].copy()
        s[i] = np.nan
        ok = np.isfinite(s)
        order = np.argsort(-np.where(ok, s, -np.inf), kind="stable")[: min(k, ok.sum())]
        if weighting == "clip":
            w = np.clip(s[order], 0, None)
            if w.sum() <= 0:
                w = np.ones(len(order))
        elif weighting == "softmax":
            w = np.exp((s[order] - s[order].max()) / temp)
        else:
            w = np.ones(len(order))
        Xn = Y[order]
        have = np.isfinite(Xn)
        den = (w[:, None] * have).sum(0)
        P[i] = np.where(den > 0, (w[:, None] * np.where(have, Xn, 0)).sum(0) / np.maximum(den, 1e-12), np.nan)
    return P


def loo_generic(Y):
    have = np.isfinite(Y)
    tot = np.where(have, Y, 0).sum(0)
    cnt = have.sum(0)
    G = (tot[None] - np.where(have, Y, 0)) / np.maximum(cnt[None] - have, 1)
    return G


def boot_ci(d, B=4000):
    d = d[np.isfinite(d)]
    bs = rng.choice(d, size=(B, len(d))).mean(1)
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(d)


if __name__ == "__main__":
    drugs, moa, Y, Ysec, X, opts = load_pool()
    n = len(Y)
    G = loo_generic(Y)
    Ysel = residualise_rows(Y, G)
    frac_kill = np.nanmean(Y <= -1.0, axis=1)
    active = frac_kill >= 0.05
    print(f"pool {n}, actives (>=5% lines LFC<=-1): {active.sum()}")
    variants = {"raw": ("raw", 0, 0), "center": ("abtt", 0, 0)}
    for D in (1, 2, 3, 5, 10, 20):
        variants[f"abtt{D}"] = ("abtt", D, 0)
    for K in (20, 50, 100):
        variants[f"whiten{K}"] = ("whiten", 0, K)
    res = {}
    for name, (mode, D, K) in variants.items():
        Z = transform(X, mode, D=D, K=K)
        S = mean_cosine(Z)
        for k in (5, 10, 20):
            P = knn_predict(S, Y, k=k)
            r = rowcorr(residualise_rows(P, G), Ysel)
            res[(name, k)] = r
            print(f"{name:10s} k={k:2d}  sel r actives {np.nanmean(r[active]):.4f}  all {np.nanmean(r):.4f}", flush=True)
    base = res[("raw", 5)]
    print("\npaired vs raw k=5 (actives):")
    for key, r in res.items():
        m, lo, hi, nn = boot_ci((r - base)[active])
        print(f"  {key[0]:10s} k={key[1]:2d}  {m:+.4f} [{lo:+.4f},{hi:+.4f}] n={nn}")
    np.savez_compressed(sys.argv[1] if len(sys.argv) > 1 else "dev_abtt_res.npz",
                        **{f"{a}_k{b}": v for (a, b), v in res.items()}, active=active, drugs=drugs)
