import numpy as np, sys
sys.path.insert(0, ".")
from dev_abtt import load_pool, residualise_rows, rowcorr, loo_generic
drugs, moa, Y, Ysec, X, opts = load_pool()
G = loo_generic(Y); Ysel = residualise_rows(Y, G)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
n, O, Gn = X.shape
def blocks(D):
    out = []
    for o in range(O):
        have = np.isfinite(X[:, o, 0]); A = X[have, o]; Ac = A - A.mean(0)
        U, S, Vt = np.linalg.svd(Ac, full_matrices=False)
        Z = Ac - (Ac @ Vt[:D].T) @ Vt[:D] if D else A
        F = np.full((n, Gn), np.nan); F[have] = Z; out.append(F)
    return out
def mean_cos(bl):
    num = np.zeros((n, n)); cnt = np.zeros((n, n))
    for F in bl:
        have = np.isfinite(F[:, 0]); V = np.nan_to_num(F); nr = np.linalg.norm(V, axis=1)
        V = V/np.maximum(nr, 1e-12)[:, None]; m = have[:, None] & have[None, :]
        num += np.where(m, V @ V.T, 0); cnt += m
    S = np.where(cnt > 0, num/np.maximum(cnt, 1), np.nan); np.fill_diagonal(S, np.nan); return S
S = mean_cos(blocks(10))
K = np.nan_to_num(np.clip(S, 0, None))**3; np.fill_diagonal(K, 1.0)
Yc = np.where(np.isfinite(Y), Y, np.nanmean(Y, 0)[None]); mu = Yc.mean(0)
lam = 3.0
H = np.linalg.inv(K + lam*np.eye(n)); A = H @ (Yc - mu)
short = (Yc - mu) - A/np.diag(H)[:, None] + mu
ev = np.linalg.eigvalsh(K); print("K eig min/max", ev.min(), ev.max())
idx = np.where(active)[0][:40]
exp = np.zeros((len(idx), Y.shape[1]))
for t, i in enumerate(idx):
    keep = np.arange(n) != i
    Kk = K[np.ix_(keep, keep)]; mk = Yc[keep].mean(0)
    a = np.linalg.solve(Kk + lam*np.eye(n-1), Yc[keep] - mk)
    exp[t] = K[i, keep] @ a + mk
r_short = rowcorr(residualise_rows(short[idx], G[idx]), Ysel[idx])
r_exp = rowcorr(residualise_rows(exp, G[idx]), Ysel[idx])
print("shortcut sel r (40 actives): %.3f   explicit: %.3f" % (np.nanmean(r_short), np.nanmean(r_exp)))
print("max abs diff shortcut vs explicit:", np.abs(short[idx]-exp).max())
