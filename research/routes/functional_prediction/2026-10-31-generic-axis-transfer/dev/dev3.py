import numpy as np, sys
sys.path.insert(0, ".")
from dev_abtt import load_pool, residualise_rows, rowcorr, loo_generic
drugs, moa, Y, Ysec, X, opts = load_pool()
G = loo_generic(Y); Ysel = residualise_rows(Y, G)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
rs = rowcorr(residualise_rows(Ysec, G), Ysel)
print("primary-vs-secondary selective r: actives %.3f (n=%d) all %.3f (n=%d)" % (np.nanmean(rs[active]), np.isfinite(rs[active]).sum(), np.nanmean(rs), np.isfinite(rs).sum()))
n, O, Gn = X.shape
def abtt_blocks(D):
    out = []
    for o in range(O):
        have = np.isfinite(X[:, o, 0]); A = X[have, o]; Ac = A - A.mean(0)
        U, S, Vt = np.linalg.svd(Ac, full_matrices=False)
        Z = Ac - (Ac @ Vt[:D].T) @ Vt[:D]
        F = np.full((n, Gn), np.nan); F[have] = Z; out.append(F)
    return out
def mean_cos(blocks):
    num = np.zeros((n, n)); cnt = np.zeros((n, n))
    for F in blocks:
        have = np.isfinite(F[:, 0]); V = np.nan_to_num(F); nr = np.linalg.norm(V, axis=1)
        V = V/np.maximum(nr, 1e-12)[:, None]; m = have[:, None] & have[None, :]
        num += np.where(m, V @ V.T, 0); cnt += m
    S = np.where(cnt > 0, num/np.maximum(cnt, 1), np.nan); np.fill_diagonal(S, np.nan); return S, cnt
for D in (0, 10):
    S, cnt = mean_cos(abtt_blocks(D)) if D else mean_cos([X[:, o] for o in range(O)])
    mx = np.nanmax(S, axis=1)
    print(f"D={D}: max-sim quantiles", np.nanpercentile(mx, [5, 25, 50, 75, 95, 99]).round(3), " pairs S>0.8:", int(np.nansum(np.triu(S > 0.8))), " S>0.6:", int(np.nansum(np.triu(S > 0.6))))
    i, j = np.where(np.triu(np.nan_to_num(S) > 0.7))
    rr = []
    for a, b in zip(i, j):
        ok = np.isfinite(Ysel[a]) & np.isfinite(Ysel[b])
        rr.append(np.corrcoef(Ysel[a, ok], Ysel[b, ok])[0, 1])
    print("   pairs >0.7:", len(i), "mean selective-profile r of those pairs:", np.nanmean(rr) if rr else None)
    for a, b in list(zip(i, j))[:15]:
        print("     ", drugs[a], "|", drugs[b], "| S=%.3f shared=%d" % (S[a, b], cnt[a, b]))
