"""10-fold dev grid with the study's gat_core functions (eigh directions): D x k for kNN, plus kernel ridge."""
import sys, time
import numpy as np
sys.path.insert(0, "D:/MAESTRO/src")
sys.path.insert(0, "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer")
sys.path.insert(0, ".")
from gat_core import generic_directions, remove_generic, mean_cosine, knn_transfer
from dev_abtt import load_pool, residualise_rows, rowcorr, boot_ci
drugs, moa, Y, Ysec, X, opts = load_pool()
n = len(Y)
fold = np.random.default_rng(7).permutation(np.arange(n) % 10)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
Ds = [-1, 0, 3, 5, 10, 15, 20, 30]
arms = {}
G = np.full_like(Y, np.nan)
t0 = time.time()
def krr(Sq, Srr, Yr, lam, pw):
    Kr = np.nan_to_num(np.clip(Srr, 0, None)) ** pw; np.fill_diagonal(Kr, 1.0)
    Kq = np.nan_to_num(np.clip(Sq, 0, None)) ** pw
    Yc = np.where(np.isfinite(Yr), Yr, np.nanmean(Yr, 0)[None]); mu = Yc.mean(0)   # reference-only centring
    return Kq @ np.linalg.solve(Kr + lam * np.eye(len(Kr)), Yc - mu) + mu
for f in range(10):
    q, r = fold == f, fold != f
    G[q] = np.nanmean(Y[r], 0)
    for D in Ds:
        if D == -1:
            Rq, Rr = X[q], X[r]
        else:
            dirs = generic_directions(X[r], D); Rq, Rr = remove_generic(X[q], dirs), remove_generic(X[r], dirs)
        Sq = mean_cosine(Rq, Rr)
        for k in (5, 10, 20, 40):
            arms.setdefault((D, f"knn{k}"), np.full_like(Y, np.nan))[q] = knn_transfer(Sq, Y[r], k)
        if D in (-1, 10):
            Srr = mean_cosine(Rr, Rr); np.fill_diagonal(Srr, np.nan)
            for lam in (1.0, 3.0, 10.0):
                for pw in (2, 3):
                    arms.setdefault((D, f"krr{lam:g}p{pw}"), np.full_like(Y, np.nan))[q] = krr(Sq, Srr, Y[r], lam, pw)
    print(f"fold {f} {time.time()-t0:.0f}s", flush=True)
Ysel = residualise_rows(Y, G)
R = {a: rowcorr(residualise_rows(P, G), Ysel) for a, P in arms.items()}
base = R[(-1, "knn5")]
for a in sorted(arms, key=lambda t: (t[0], t[1])):
    d, lo, hi, _ = boot_ci((R[a] - base)[active])
    lab = {-1: "raw", 0: "center"}.get(a[0], f"D{a[0]}")
    print(f"{lab:7s} {a[1]:10s} actives {np.nanmean(R[a][active]):.4f} all {np.nanmean(R[a]):.4f}  vs raw5 {d:+.4f} [{lo:+.4f},{hi:+.4f}]")
np.savez_compressed("dev6_res.npz", fold=fold, active=active, **{f"{a[0]}_{a[1]}": v for a, v in R.items()})
