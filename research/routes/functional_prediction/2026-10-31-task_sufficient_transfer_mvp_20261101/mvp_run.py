"""Single-run exploratory task-sufficient transfer MVP.

Reads only the exposed GAT PRISM 19Q4 development pool. It does not import project src/tools
or any confirmation data. The freeze binds this file and the input before execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import time
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

STUDY = Path(__file__).resolve().parent
DATA = Path("D:/MAESTRO/data/processed/generic_axis_transfer_20261031/dev_pool.npz")
SEED = 20261101
N_FOLDS = 5
D = 5
KNN_K = 20
PCA_KS = (2, 5, 10, 20, 50, 100)
METHODS = ["raw_k5", "raw_k20", "chemistry_k20", "gat_d5_k20", "global_residual_diagnostic", "full_flat_residual_k20", "gat_permuted_null"] + [f"pca_residual_k{k}" for k in PCA_KS] + [f"random_residual_k{k}" for k in PCA_KS] + ["ridge_raw"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fold_groups(keys: np.ndarray) -> np.ndarray:
    out = []
    for i, key in enumerate(keys.astype(str)):
        group = key if key else f"missing-singleton-{i}"
        out.append(int(hashlib.sha256(group.encode()).hexdigest(), 16) % N_FOLDS)
    return np.asarray(out, dtype=int)


def generic_directions(X: np.ndarray, d: int) -> list[tuple[np.ndarray, np.ndarray]]:
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for o in range(X.shape[1]):
        have = np.isfinite(X[:, o, 0])
        A = X[have, o].astype(float)
        mu = A.mean(axis=0) if len(A) else np.zeros(X.shape[2], dtype=float)
        if d == 0 or len(A) < 2:
            out.append((mu, np.zeros((0, X.shape[2]), dtype=float)))
            continue
        C = A - mu
        vals, vecs = np.linalg.eigh(C.T @ C)
        top = np.argsort(vals)[::-1][: min(d, len(A) - 1)]
        out.append((mu, vecs[:, top].T))
    return out


def remove_generic(X: np.ndarray, dirs: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    out = np.full(X.shape, np.nan, dtype=float)
    for o, (mu, V) in enumerate(dirs):
        have = np.isfinite(X[:, o, 0])
        C = X[have, o].astype(float) - mu
        if len(V):
            C = C - (C @ V.T) @ V
        out[have, o] = C
    return out


def mean_cosine(Q: np.ndarray, R: np.ndarray) -> np.ndarray:
    num = np.zeros((len(Q), len(R)), dtype=float)
    cnt = np.zeros_like(num)
    for o in range(Q.shape[1]):
        hq = np.isfinite(Q[:, o, 0])
        hr = np.isfinite(R[:, o, 0])
        q = np.nan_to_num(Q[:, o].astype(float))
        r = np.nan_to_num(R[:, o].astype(float))
        nq = np.linalg.norm(q, axis=1)
        nr = np.linalg.norm(r, axis=1)
        q /= np.maximum(nq, 1e-12)[:, None]
        r /= np.maximum(nr, 1e-12)[:, None]
        ok = (hq & (nq > 0))[:, None] & (hr & (nr > 0))[None, :]
        num += np.where(ok, q @ r.T, 0.0)
        cnt += ok
    return np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)


def knn(sim: np.ndarray, Y: np.ndarray, k: int) -> tuple[np.ndarray, list[np.ndarray]]:
    pred = np.full((len(sim), Y.shape[1]), np.nan, dtype=float)
    neighbours: list[np.ndarray] = []
    for i, s in enumerate(sim):
        ok = np.isfinite(s)
        if not ok.any():
            neighbours.append(np.array([], dtype=int))
            continue
        order = np.argsort(-np.where(ok, s, -np.inf), kind="stable")[: min(k, int(ok.sum()))]
        neighbours.append(order)
        w = np.clip(s[order], 0.0, None)
        if w.sum() <= 0:
            w = np.ones(len(order))
        X = Y[order]
        have = np.isfinite(X)
        den = (w[:, None] * have).sum(axis=0)
        pred[i] = np.where(den > 0, (w[:, None] * np.where(have, X, 0.0)).sum(axis=0) / np.maximum(den, 1e-12), np.nan)
    return pred, neighbours


def flatten_centered(X: np.ndarray) -> np.ndarray:
    # Reference-centred residual tensors have zero as the reference mean; missing stays at zero.
    return np.nan_to_num(X, nan=0.0).reshape(len(X), -1).astype(np.float64, copy=False)


def fit_impute(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    A = X.reshape(len(X), -1).astype(np.float64, copy=False)
    mu = np.nanmean(A, axis=0)
    mu = np.nan_to_num(mu, nan=0.0)
    return np.where(np.isfinite(A), A, mu), mu


def residualise(y: np.ndarray, g: np.ndarray) -> np.ndarray:
    out = np.full(len(y), np.nan, dtype=float)
    ok = np.isfinite(y) & np.isfinite(g)
    if ok.sum() < 2:
        return out
    yc = y[ok] - y[ok].mean()
    gc = g[ok] - g[ok].mean()
    out[ok] = yc - float(np.dot(yc, gc) / max(np.dot(gc, gc), 1e-12)) * gc
    return out


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) < 1e-12 or np.std(b[ok]) < 1e-12:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def hit_precision(pred: np.ndarray, obs: np.ndarray, generic: np.ndarray) -> float:
    a, b = residualise(pred, generic), residualise(obs, generic)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 40 or np.std(a[ok]) < 1e-12 or np.std(b[ok]) < 1e-12:
        return float("nan")
    m = max(1, int(round(0.10 * ok.sum())))
    # PRISM LFC: lower residual means more sensitive.
    pa, pb = -a[ok], -b[ok]
    ia = set(np.argsort(-pa, kind="stable")[:m])
    ib = set(np.argsort(-pb, kind="stable")[:m])
    return float(len(ia & ib) / m)


def selection_regret(pred: np.ndarray, obs: np.ndarray, generic: np.ndarray) -> float:
    a, b = residualise(pred, generic), residualise(obs, generic)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 40 or np.std(a[ok]) < 1e-12 or np.std(b[ok]) < 1e-12:
        return float("nan")
    m = max(1, int(round(0.10 * ok.sum())))
    pa, true_sensitivity = -a[ok], -b[ok]
    chosen = np.argsort(-pa, kind="stable")[:m]
    oracle = np.argsort(-true_sensitivity, kind="stable")[:m]
    return float(true_sensitivity[oracle].mean() - true_sensitivity[chosen].mean())


def metrics(pred: np.ndarray, obs: np.ndarray, generic: np.ndarray) -> tuple[float, float, float, float]:
    sr = pearson(residualise(pred, generic), residualise(obs, generic))
    raw = pearson(pred, obs)
    hp = hit_precision(pred, obs, generic)
    ok = np.isfinite(pred) & np.isfinite(obs)
    mae = float(np.mean(np.abs(pred[ok] - obs[ok]))) if ok.any() else float("nan")
    return hp, sr, raw, mae


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    sa, sb = set(map(int, a)), set(map(int, b))
    return float(len(sa & sb) / len(sa | sb)) if sa or sb else float("nan")


def env_info() -> dict[str, str]:
    import scipy
    import sklearn
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
        "pid": str(os.getpid()),
    }


def main() -> None:
    started = time.perf_counter()
    freeze = json.loads((STUDY / "FREEZE.json").read_text(encoding="utf-8"))
    if (STUDY / "RUN").exists():
        raise RuntimeError("RUN exists; single launch only")
    if freeze["code_sha256"] != sha256(Path(__file__).resolve()):
        raise RuntimeError("code hash differs from freeze")
    if freeze["data_sha256"] != sha256(DATA):
        raise RuntimeError("input hash differs from freeze")
    d = np.load(DATA, allow_pickle=True)
    X = d["signature"].astype(np.float32)
    Y = d["profile"].astype(float)
    keys = d["ik14"].astype(str)
    lines = d["line"].astype(str)
    fp = d["fingerprint"].astype(float)
    folds = fold_groups(keys)
    active = np.nanmean(Y <= -1.0, axis=1) >= 0.05
    n = len(Y)
    predictions = {m: np.full_like(Y, np.nan, dtype=float) for m in METHODS}
    neighbor_overlap = {m: np.full(n, np.nan, dtype=float) for m in METHODS}
    rows: list[dict[str, object]] = []
    rng = np.random.default_rng(SEED)
    for f in range(N_FOLDS):
        q = folds == f
        r = ~q
        Xq, Xr, Yq, Yr = X[q], X[r], Y[q], Y[r]
        generic = np.nanmean(Yr, axis=0)
        raw_sim = mean_cosine(Xq, Xr)
        raw_pred, raw5_nb = knn(raw_sim, Yr, 5)
        predictions["raw_k5"][q] = raw_pred
        predictions["raw_k20"][q], raw20_nb = knn(raw_sim, Yr, 20)
        raw_sets = raw20_nb
        qfp, rfp = fp[q], fp[r]
        inter = qfp @ rfp.T
        union = qfp.sum(1)[:, None] + rfp.sum(1)[None, :] - inter
        chem_sim = inter / np.maximum(union, 1e-12)
        chem_sim[qfp.sum(1) == 0] = np.nan
        chem_sim[:, rfp.sum(1) == 0] = np.nan
        predictions["chemistry_k20"][q], chem_nb = knn(chem_sim, Yr, 20)
        for i, nbi in enumerate(raw5_nb):
            neighbor_overlap["raw_k5"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
        neighbor_overlap["raw_k20"][q] = 1.0
        for i, nbi in enumerate(chem_nb):
            neighbor_overlap["chemistry_k20"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
        dirs = generic_directions(Xr, D)
        Rr = remove_generic(Xr, dirs)
        Rq = remove_generic(Xq, dirs)
        gat_sim = mean_cosine(Rq, Rr)
        gat_pred, gat_nb = knn(gat_sim, Yr, KNN_K)
        predictions["gat_d5_k20"][q] = gat_pred
        # Exact target decomposition with line-wise missingness retained; reassembly is ordinary GAT.
        means = np.nanmean(Yr, axis=1)
        g = generic - np.nanmean(generic)
        denom = np.nansum(np.where(np.isfinite(Yr), g[None, :] ** 2, np.nan), axis=1)
        beta = np.nansum((Yr - means[:, None]) * g[None, :], axis=1) / np.maximum(denom, 1e-12)
        global_part = means[:, None] + beta[:, None] * g[None, :]
        global_part[~np.isfinite(Yr)] = np.nan
        residual_part = Yr - global_part
        gp, _ = knn(gat_sim, global_part, KNN_K)
        rp, _ = knn(gat_sim, residual_part, KNN_K)
        predictions["global_residual_diagnostic"][q] = gp + rp
        for i, nb in enumerate(gat_nb):
            neighbor_overlap["gat_d5_k20"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nb)

        Rrf = flatten_centered(Rr)
        Rqf = flatten_centered(Rq)
        flat_sim = (Rqf @ Rrf.T) / np.maximum(np.linalg.norm(Rqf, axis=1)[:, None] * np.linalg.norm(Rrf, axis=1)[None, :], 1e-12)
        predictions["full_flat_residual_k20"][q], flat_nb = knn(flat_sim, Yr, KNN_K)
        for i, nbi in enumerate(flat_nb):
            neighbor_overlap["full_flat_residual_k20"][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
        perm = np.random.default_rng(SEED + 1000 + f).permutation(len(Yr))
        predictions["gat_permuted_null"][q], _ = knn(gat_sim, Yr[perm], KNN_K)
        pca = PCA(n_components=max(PCA_KS), svd_solver="randomized", iterated_power=3, n_oversamples=10, power_iteration_normalizer="QR", random_state=SEED + f)
        pca.fit(Rrf)
        Pr = pca.transform(Rrf)
        Pq = pca.transform(Rqf)
        proj, _ = np.linalg.qr(rng.normal(size=(Rrf.shape[1], max(PCA_KS))).astype(np.float64), mode="reduced")
        Rrand, Qrand = Rrf @ proj, Rqf @ proj
        for k in PCA_KS:
            psim = (Qq := Pq[:, :k]) @ Pr[:, :k].T
            qn, rn = np.linalg.norm(Qq, axis=1), np.linalg.norm(Pr[:, :k], axis=1)
            psim = psim / np.maximum(qn[:, None] * rn[None, :], 1e-12)
            pp, nb = knn(psim, Yr, KNN_K)
            name = f"pca_residual_k{k}"
            predictions[name][q] = pp
            for i, nbi in enumerate(nb):
                neighbor_overlap[name][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)
            qv, rv = Qrand[:, :k], Rrand[:, :k]
            rsim = (qv @ rv.T) / np.maximum(np.linalg.norm(qv, axis=1)[:, None] * np.linalg.norm(rv, axis=1)[None, :], 1e-12)
            rp, nb = knn(rsim, Yr, KNN_K)
            name = f"random_residual_k{k}"
            predictions[name][q] = rp
            for i, nbi in enumerate(nb):
                neighbor_overlap[name][np.flatnonzero(q)[i]] = jaccard(raw_sets[i], nbi)

        Xri, xmu = fit_impute(Xr)
        Xqi = np.where(np.isfinite(Xq.reshape(len(Xq), -1)), Xq.reshape(len(Xq), -1), xmu)
        Yri, ymu = fit_impute(Yr)
        ridge = Ridge(alpha=100.0, fit_intercept=True, solver="cholesky")
        ridge.fit(Xri, Yri)
        predictions["ridge_raw"][q] = ridge.predict(Xqi)

        qidx = np.flatnonzero(q)
        for j, idx in enumerate(qidx):
            for name in METHODS:
                hp, sr, raw, mae = metrics(predictions[name][idx], Y[idx], generic)
                rows.append({"query_index": int(idx), "drug": str(d["drug"][idx]), "fold": int(f), "active": bool(active[idx]),
                             "method": name, "hit_precision": hp, "miss_rate": (1.0 - hp) if np.isfinite(hp) else np.nan,
                             "regret": selection_regret(predictions[name][idx], Y[idx], generic),
                             "selective_r": sr, "raw_r": raw, "raw_mae": mae,
                             "neighbor_overlap_vs_raw": neighbor_overlap[name][idx]})
        print(f"fold {f} queries {int(q.sum())} references {int(r.sum())}", flush=True)

    table = pd.DataFrame(rows)
    out = STUDY / "RUN"
    out.mkdir(exist_ok=True)
    table.to_csv(out / "per_query_metrics.csv", index=False, lineterminator="\n")
    np.savez_compressed(out / "predictions.npz", drug=d["drug"], line=lines, fold=folds, active=active, **predictions)
    summaries: dict[str, object] = {}
    for name in METHODS:
        sub = table[table.method == name]
        summaries[name] = {}
        for pop_name, pop in (("active", sub.active), ("all", np.ones(len(sub), dtype=bool))):
            ss = sub[np.asarray(pop)]
            summaries[name][pop_name] = {c: float(np.nanmean(ss[c])) if ss[c].notna().any() else None
                                         for c in ("hit_precision", "miss_rate", "regret", "selective_r", "raw_r", "raw_mae", "neighbor_overlap_vs_raw")}
    results = {
        "study": "task_sufficient_transfer_mvp_20261101",
        "status": "exploratory_non_confirmatory",
        "data_sha256": sha256(DATA),
        "code_sha256": sha256(Path(__file__).resolve()),
        "n_compounds": int(n), "n_lines": int(Y.shape[1]), "n_active": int(active.sum()),
        "n_folds": N_FOLDS, "fold_counts": {str(f): int((folds == f).sum()) for f in range(N_FOLDS)},
        "methods": METHODS, "summaries": summaries,
        "environment": env_info(), "elapsed_seconds": time.perf_counter() - started,
    }
    (out / "RESULTS.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (out / "environment.json").write_text(json.dumps(env_info(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"study": results["study"], "n": n, "active": int(active.sum()), "methods": len(METHODS)}, indent=2))


if __name__ == "__main__":
    main()



