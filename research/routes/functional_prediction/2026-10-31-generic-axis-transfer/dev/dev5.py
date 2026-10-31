"""10-fold CV development comparison on the exposed 1,403-compound pool (no LOO shortcuts)."""
import numpy as np, sys
sys.path.insert(0, ".")
from dev_abtt import load_pool, residualise_rows, rowcorr, boot_ci
drugs, moa, Y, Ysec, X, opts = load_pool()
n, O, Gn = X.shape
rng = np.random.default_rng(7)
fold = rng.permutation(np.arange(n) % 10)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05

def fit_dirs(Xfit, D):
    dirs = []
    for o in range(O):
        have = np.isfinite(Xfit[:, o, 0]); A = Xfit[have, o]; mu = A.mean(0)
        U, S, Vt = np.linalg.svd(A - mu, full_matrices=False)
        dirs.append((mu, Vt[:D]))
    return dirs

def apply_dirs(Xs, dirs, D):
    out = []
    for o, (mu, V) in enumerate(dirs):
        F = np.full((len(Xs), Gn), np.nan); have = np.isfinite(Xs[:, o, 0])
        A = Xs[have, o]
        if D == -1: Z = A
        else:
            Ac = A - mu; Z = Ac - (Ac @ V.T) @ V if D > 0 else Ac
        F[have] = Z; out.append(F)
    return out

def cos_blocks(Qb, Rb):
    nq, nr = len(Qb[0]), len(Rb[0]); num = np.zeros((nq, nr)); cnt = np.zeros((nq, nr))
    for Fq, Fr in zip(Qb, Rb):
        hq, hr = np.isfinite(Fq[:, 0]), np.isfinite(Fr[:, 0])
        Vq = np.nan_to_num(Fq); Vq /= np.maximum(np.linalg.norm(Vq, axis=1), 1e-12)[:, None]
        Vr = np.nan_to_num(Fr); Vr /= np.maximum(np.linalg.norm(Vr, axis=1), 1e-12)[:, None]
        m = hq[:, None] & hr[None, :]
        num += np.where(m, Vq @ Vr.T, 0); cnt += m
    return np.where(cnt > 0, num/np.maximum(cnt, 1), np.nan)

def knn(Sq, Yr, k):
    P = np.full((len(Sq), Yr.shape[1]), np.nan)
    for i, s in enumerate(Sq):
        ok = np.isfinite(s); order = np.argsort(-np.where(ok, s, -np.inf), kind="stable")[:min(k, ok.sum())]
        w = np.clip(s[order], 0, None); w = w if w.sum() > 0 else np.ones(len(order))
        Xn = Yr[order]; h = np.isfinite(Xn); den = (w[:, None]*h).sum(0)
        P[i] = np.where(den > 0, (w[:, None]*np.where(h, Xn, 0)).sum(0)/np.maximum(den, 1e-12), np.nan)
    return P

def krr(Sq, Srr, Yr, lam, pw):
    Kr = np.nan_to_num(np.clip(Srr, 0, None))**pw; np.fill_diagonal(Kr, 1.0)
    Kq = np.nan_to_num(np.clip(Sq, 0, None))**pw
    Yc = np.where(np.isfinite(Yr), Yr, np.nanmean(Yr, 0)[None]); mu = Yc.mean(0)
    A = np.linalg.solve(Kr + lam*np.eye(len(Kr)), Yc - mu)
    return Kq @ A + mu

methods = {}
for D in (-1, 0, 3, 5, 10, 20):
    for k in (5, 10, 20, 40): methods[(D, f"knn{k}")] = ("knn", k)
    for lam in (0.1, 0.3, 1.0): 
        for pw in (1, 2, 3): methods[(D, f"krr{lam}p{pw}")] = ("krr", (lam, pw))
P = {m: np.full_like(Y, np.nan) for m in methods}
Gcv = np.full_like(Y, np.nan)
for f in range(10):
    q, r = fold == f, fold != f
    Gr = np.nanmean(Y[r], 0); Gcv[q] = Gr
    for D in (-1, 0, 3, 5, 10, 20):
        dirs = fit_dirs(X[r], max(D, 0))   # directions fit on the reference fold only
        Rb, Qb = apply_dirs(X[r], dirs, D), apply_dirs(X[q], dirs, D)
        Sq, Srr = cos_blocks(Qb, Rb), cos_blocks(Rb, Rb)
        for (DD, name), (kind, par) in methods.items():
            if DD != D: continue
            P[(DD, name)][q] = knn(Sq, Y[r], par) if kind == "knn" else krr(Sq, Srr, Y[r], *par)
    print("fold", f, "done", flush=True)
Ysel = residualise_rows(Y, Gcv)
R = {m: rowcorr(residualise_rows(P[m], Gcv), Ysel) for m in methods}
base = R[(-1, "knn5")]
print("\nselective r, 10-fold CV (actives n=%d)" % active.sum())
for m in methods:
    d, lo, hi, nn = boot_ci((R[m]-base)[active])
    lab = {-1: "raw", 0: "center"}.get(m[0], f"abtt{m[0]}")
    print(f"  {lab:7s} {m[1]:10s} actives {np.nanmean(R[m][active]):.4f} all {np.nanmean(R[m]):.4f}  vs raw-knn5 {d:+.4f} [{lo:+.4f},{hi:+.4f}]")
np.savez_compressed("dev5_res.npz", fold=fold, active=active, **{f"{m[0]}_{m[1]}": R[m] for m in methods})
