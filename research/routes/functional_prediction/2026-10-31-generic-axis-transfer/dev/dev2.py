import numpy as np, sys
sys.path.insert(0, ".")
from dev_abtt import load_pool, residualise_rows, rowcorr, loo_generic, knn_predict, boot_ci
rng = np.random.default_rng(1)
drugs, moa, Y, Ysec, X, opts = load_pool()
G = loo_generic(Y); Ysel = residualise_rows(Y, G)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
# noise ceiling: primary vs secondary selective r where secondary exists
Gs = loo_generic(Ysec)
rs = rowcorr(residualise_rows(Ysec, G), Ysel)
print("primary-vs-secondary selective r: actives", np.nanmean(rs[active]), "n", np.isfinite(rs[active]).sum(), " all", np.nanmean(rs), np.isfinite(rs).sum())

def feats(X, mode, D=0, K=50):
    n, O, Gn = X.shape
    out = []
    for o in range(O):
        have = np.isfinite(X[:, o, 0])
        A = X[have, o]; mu = A.mean(0); Ac = A - mu
        U, S, Vt = np.linalg.svd(Ac, full_matrices=False)
        if mode == "abtt":
            Z = Ac - (Ac @ Vt[:D].T) @ Vt[:D]
        elif mode == "whiten":
            lam = S[:K]**2/(have.sum()-1); Z = (Ac @ Vt[:K].T)/np.sqrt(lam + lam.mean())
        else:
            Z = A
        F = np.full((n, Z.shape[1]), np.nan); F[have] = Z
        out.append(F)
    return out

def mean_cos(blocks):
    n = len(blocks[0]); num = np.zeros((n, n)); cnt = np.zeros((n, n))
    for F in blocks:
        have = np.isfinite(F[:, 0]); V = np.nan_to_num(F); nr = np.linalg.norm(V, axis=1)
        V = V/np.maximum(nr, 1e-12)[:, None]; m = have[:, None] & have[None, :]
        num += np.where(m, V @ V.T, 0); cnt += m
    S = np.where(cnt > 0, num/np.maximum(cnt, 1), np.nan); np.fill_diagonal(S, np.nan); return S

def krr(S, Y, lam=1.0, power=1):
    """LOO kernel ridge with kernel K = max(S,0)^power (diag 1); targets NaN->row-mean imputed per column."""
    n = len(Y); K = np.nan_to_num(np.clip(S, 0, None))**power; np.fill_diagonal(K, 1.0)
    Yc = np.where(np.isfinite(Y), Y, np.nanmean(Y, 0)[None])
    mu = Yc.mean(0)
    H = np.linalg.solve(K + lam*np.eye(n), np.eye(n))  # (K+lam I)^-1
    A = H @ (Yc - mu)
    # LOO residual shortcut: y_i - yhat_-i = a_i / H_ii for kernel ridge with fixed K
    fit = K @ A
    loo = (Yc - mu) - A/np.diag(H)[:, None]
    return loo + mu

if __name__ != "__main__":
    raise SystemExit
res = {}
for name, (mode, D, K) in {"raw": ("raw", 0, 0), "abtt10": ("abtt", 10, 0), "whiten50": ("whiten", 0, 50), "whiten100": ("whiten", 0, 100)}.items():
    S = mean_cos(feats(X, mode, D, K))
    for k in (5, 20, 40):
        for wt in ("clip", "softmax"):
            P = knn_predict(S, Y, k=k, weighting=wt, temp=0.05)
            r = rowcorr(residualise_rows(P, G), Ysel); res[(name, f"knn{k}{wt}")] = r
            print(f"{name:9s} knn{k:2d} {wt:7s} actives {np.nanmean(r[active]):.4f} all {np.nanmean(r):.4f}", flush=True)
    for lam in (0.3, 1, 3):
        for pw in (1, 3):
            P = krr(S, Y, lam=lam, power=pw)
            r = rowcorr(residualise_rows(P, G), Ysel); res[(name, f"krr{lam}p{pw}")] = r
            print(f"{name:9s} krr lam={lam} p={pw} actives {np.nanmean(r[active]):.4f} all {np.nanmean(r):.4f}", flush=True)
base = res[("raw", "knn5clip")]
print("\npaired vs raw knn5clip (actives):")
for key, r in res.items():
    m, lo, hi, nn = boot_ci((r-base)[active]); print(f"  {key[0]:9s} {key[1]:14s} {m:+.4f} [{lo:+.4f},{hi:+.4f}]")
