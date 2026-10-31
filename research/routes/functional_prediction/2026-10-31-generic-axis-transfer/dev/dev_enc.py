"""Development: contrastive-encoder similarity vs raw/ABTT on the exposed PRISM pool, 10-fold CV (same folds as dev5)."""
import sys
import numpy as np
import torch
sys.path.insert(0, ".")
from dev_abtt import load_pool, residualise_rows, rowcorr, boot_ci
from contrastive import Encoder, embed

drugs, moa, Y, Ysec, X, opts = load_pool()
n, O, Gn = X.shape
fold = np.random.default_rng(7).permutation(np.arange(n) % 10)
active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
ck = torch.load(sys.argv[1], map_location="cuda")
model = Encoder().cuda()
model.load_state_dict(ck["state"])

# E1: per-option embeddings of the same 10 uM per-option mean signatures the baseline uses
flat = X.reshape(n * O, Gn)
have = np.isfinite(flat[:, 0])
E = np.full((n * O, 256), np.nan, dtype=np.float32)
E[have] = embed(model, flat[have])
E = E.reshape(n, O, 256)


def mean_cos(A, B):
    num = np.zeros((len(A), len(B)))
    cnt = np.zeros((len(A), len(B)))
    for o in range(A.shape[1]):
        ha, hb = np.isfinite(A[:, o, 0]), np.isfinite(B[:, o, 0])
        Va = np.nan_to_num(A[:, o]); Va /= np.maximum(np.linalg.norm(Va, axis=1), 1e-12)[:, None]
        Vb = np.nan_to_num(B[:, o]); Vb /= np.maximum(np.linalg.norm(Vb, axis=1), 1e-12)[:, None]
        m = ha[:, None] & hb[None, :]
        num += np.where(m, Va @ Vb.T, 0)
        cnt += m
    return np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)


def knn(Sq, Yr, k):
    P = np.full((len(Sq), Yr.shape[1]), np.nan)
    for i, s in enumerate(Sq):
        ok = np.isfinite(s)
        order = np.argsort(-np.where(ok, s, -np.inf), kind="stable")[:min(k, ok.sum())]
        w = np.clip(s[order], 0, None)
        w = w if w.sum() > 0 else np.ones(len(order))
        Xn = Yr[order]; h = np.isfinite(Xn); den = (w[:, None] * h).sum(0)
        P[i] = np.where(den > 0, (w[:, None] * np.where(h, Xn, 0)).sum(0) / np.maximum(den, 1e-12), np.nan)
    return P


def abtt(Xr, Xq, D):
    out_r, out_q = np.full_like(Xr, np.nan), np.full_like(Xq, np.nan)
    for o in range(O):
        hr, hq = np.isfinite(Xr[:, o, 0]), np.isfinite(Xq[:, o, 0])
        A = Xr[hr, o]; mu = A.mean(0)
        _, _, Vt = np.linalg.svd(A - mu, full_matrices=False)
        V = Vt[:D]
        for src, h, dst in ((Xr, hr, out_r), (Xq, hq, out_q)):
            C = src[h, o] - mu
            dst[h, o] = C - (C @ V.T) @ V
    return out_r, out_q


arms = {}
for name in ("raw", "abtt10", "enc_e1", "enc_e1_center"):
    for k in (5, 10, 20, 40):
        arms[(name, k)] = np.full_like(Y, np.nan)
G = np.full_like(Y, np.nan)
for f in range(10):
    q, r = fold == f, fold != f
    G[q] = np.nanmean(Y[r], 0)
    sims = {"raw": mean_cos(X[q], X[r]), "enc_e1": mean_cos(E[q], E[r])}
    Ar, Aq = abtt(X[r], X[q], 10)
    sims["abtt10"] = mean_cos(Aq, Ar)
    mu = np.nanmean(E[r], axis=0, keepdims=True)  # centre embeddings per option on references
    sims["enc_e1_center"] = mean_cos(E[q] - mu, E[r] - mu)
    for (name, k), P in arms.items():
        P[q] = knn(sims[name], Y[r], k)
    print("fold", f, flush=True)
Ysel = residualise_rows(Y, G)
R = {a: rowcorr(residualise_rows(P, G), Ysel) for a, P in arms.items()}
base = R[("raw", 5)]
for a in arms:
    d, lo, hi, _ = boot_ci((R[a] - base)[active])
    print(f"{a[0]:14s} k={a[1]:2d} actives {np.nanmean(R[a][active]):.4f} all {np.nanmean(R[a]):.4f}  vs raw5 {d:+.4f} [{lo:+.4f},{hi:+.4f}]")
d, lo, hi, _ = boot_ci((R[("enc_e1", 20)] - R[("abtt10", 20)])[active])
print(f"enc_e1 k20 - abtt10 k20 (actives): {d:+.4f} [{lo:+.4f},{hi:+.4f}]")
