"""Frozen decision-focused selection MVP on the exposed development pool."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

os.environ.update({"OMP_NUM_THREADS": "3", "MKL_NUM_THREADS": "3", "OPENBLAS_NUM_THREADS": "3", "NUMEXPR_NUM_THREADS": "3"})

ROOT = Path(__file__).resolve().parent
DATA = Path(r"D:/MAESTRO/data/processed/generic_axis_transfer_20261031/dev_pool.npz")
SEED = 20261101
ALPHA = 100.0
METHODS = ["raw_k20", "ridge_raw", "decision_top10_ridge"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def folds_from_ik(ik: np.ndarray) -> np.ndarray:
    out = []
    for i, value in enumerate(ik.astype(str)):
        label = value if value else f"missing-singleton-{i}"
        out.append(int(hashlib.sha256(label.encode()).hexdigest(), 16) % 5)
    return np.asarray(out, dtype=int)


def residualize(y: np.ndarray, g: np.ndarray) -> np.ndarray:
    out = np.full_like(y, np.nan, dtype=float)
    ok = np.isfinite(y) & np.isfinite(g)
    if ok.sum() < 2:
        return out
    yc = y[ok] - y[ok].mean()
    gc = g[ok] - g[ok].mean()
    out[ok] = yc - float(np.dot(yc, gc) / max(np.dot(gc, gc), 1e-12)) * gc
    return out


def mean_cosine(q: np.ndarray, r: np.ndarray) -> np.ndarray:
    num = np.zeros((len(q), len(r)), dtype=float)
    cnt = np.zeros_like(num)
    for option in range(q.shape[1]):
        hq = np.isfinite(q[:, option, 0])
        hr = np.isfinite(r[:, option, 0])
        qq = np.nan_to_num(q[:, option].astype(float))
        rr = np.nan_to_num(r[:, option].astype(float))
        nq = np.linalg.norm(qq, axis=1)
        nr = np.linalg.norm(rr, axis=1)
        qq /= np.maximum(nq, 1e-12)[:, None]
        rr /= np.maximum(nr, 1e-12)[:, None]
        ok = (hq & (nq > 0))[:, None] & (hr & (nr > 0))[None, :]
        num += np.where(ok, qq @ rr.T, 0.0)
        cnt += ok
    return np.where(cnt > 0, num / np.maximum(cnt, 1), np.nan)


def knn(sim: np.ndarray, y: np.ndarray, k: int) -> np.ndarray:
    pred = np.full((len(sim), y.shape[1]), np.nan, dtype=float)
    for i, row in enumerate(sim):
        ok = np.isfinite(row)
        if not ok.any():
            continue
        order = np.argsort(-np.where(ok, row, -np.inf), kind="stable")[: min(k, int(ok.sum()))]
        weights = np.clip(row[order], 0.0, None)
        if weights.sum() <= 0:
            weights = np.ones(len(order))
        yy = y[order]
        have = np.isfinite(yy)
        den = (weights[:, None] * have).sum(axis=0)
        pred[i] = np.where(den > 0, (weights[:, None] * np.where(have, yy, 0.0)).sum(axis=0) / np.maximum(den, 1e-12), np.nan)
    return pred


def impute_features(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    flat = x.reshape(len(x), -1).astype(float)
    mean = np.nanmean(flat, axis=0)
    mean = np.nan_to_num(mean, nan=0.0)
    return np.where(np.isfinite(flat), flat, mean), mean


def impute_targets(y: np.ndarray) -> np.ndarray:
    mean = np.nanmean(y, axis=0)
    mean = np.nan_to_num(mean, nan=0.0)
    return np.where(np.isfinite(y), y, mean)


def decision_labels(y: np.ndarray, generic: np.ndarray) -> np.ndarray:
    labels = np.full_like(y, np.nan, dtype=float)
    for i in range(len(y)):
        residual = residualize(y[i], generic)
        finite = np.where(np.isfinite(residual))[0]
        if len(finite) < 40:
            continue
        m = max(1, int(round(0.10 * len(finite))))
        order = finite[np.argsort(-(-residual[finite]), kind="stable")[:m]]
        labels[i, finite] = 0.0
        labels[i, order] = 1.0
    return labels


def decision_metrics(scores: np.ndarray, observed: np.ndarray, generic: np.ndarray) -> tuple[float, float, float]:
    residual = residualize(observed, generic)
    ok = np.isfinite(residual) & np.isfinite(scores)
    if ok.sum() < 40 or np.std(residual[ok]) < 1e-12:
        return (float("nan"), float("nan"), float("nan"))
    ids = np.where(ok)[0]
    m = max(1, int(round(0.10 * len(ids))))
    predicted = ids[np.argsort(-scores[ids], kind="stable")[:m]]
    oracle = ids[np.argsort(-(-residual[ids]), kind="stable")[:m]]
    overlap = len(set(predicted.tolist()) & set(oracle.tolist())) / m
    sensitivity = -residual
    regret = float(sensitivity[oracle].mean() - sensitivity[predicted].mean())
    threshold_hit = float(np.mean(observed[predicted] <= -1.0))
    return overlap, regret, threshold_hit


def profile_metrics(pred: np.ndarray, observed: np.ndarray) -> tuple[float, float]:
    ok = np.isfinite(pred) & np.isfinite(observed)
    if not ok.any():
        return float("nan"), float("nan")
    a, b = pred[ok], observed[ok]
    raw_r = float(np.corrcoef(a, b)[0, 1]) if a.std() > 1e-12 and b.std() > 1e-12 else float("nan")
    return raw_r, float(np.mean(np.abs(a - b)))


def main() -> None:
    start = time.time()
    data = np.load(DATA)
    x = data["signature"].astype(np.float64)
    y = data["profile"].astype(float)
    drug = data["drug"].astype(str)
    lines = data["line"].astype(str)
    folds = folds_from_ik(data["ik14"])
    active = np.nanmean(y <= -1.0, axis=1) >= 0.05
    predictions = {name: np.full_like(y, np.nan, dtype=float) for name in METHODS}
    rows: list[dict[str, object]] = []

    for fold in range(5):
        query = folds == fold
        reference = ~query
        xq, xr, yq, yr = x[query], x[reference], y[query], y[reference]
        generic = np.nanmean(yr, axis=0)

        raw_similarity = mean_cosine(xq, xr)
        predictions["raw_k20"][query] = knn(raw_similarity, yr, 20)

        xr_imp, xmean = impute_features(xr)
        xq_imp = np.where(np.isfinite(xq.reshape(len(xq), -1)), xq.reshape(len(xq), -1), xmean)
        yr_imp = impute_targets(yr)
        ridge = Ridge(alpha=ALPHA, fit_intercept=True, solver="cholesky").fit(xr_imp, yr_imp)
        predictions["ridge_raw"][query] = ridge.predict(xq_imp)

        labels = decision_labels(yr, generic)
        label_fit = impute_targets(labels)
        decision = Ridge(alpha=ALPHA, fit_intercept=True, solver="cholesky").fit(xr_imp, label_fit)
        predictions["decision_top10_ridge"][query] = decision.predict(xq_imp)

    for i in range(len(y)):
        generic = np.nanmean(y[folds != folds[i]], axis=0)
        for method in METHODS:
            scores = predictions[method][i]
            if method == "decision_top10_ridge":
                ranking = scores
            else:
                ranking = -residualize(scores, generic)
            overlap, regret, threshold_hit = decision_metrics(ranking, y[i], generic)
            raw_r, raw_mae = profile_metrics(scores, y[i])
            rows.append({"query_index": i, "drug": drug[i], "fold": int(folds[i]), "active": bool(active[i]), "method": method, "top10_overlap": overlap, "selection_regret": regret, "raw_threshold_hit": threshold_hit, "raw_r": raw_r, "raw_mae": raw_mae})

    table = pd.DataFrame(rows)
    out = ROOT / "RUN"
    out.mkdir(exist_ok=True)
    table.to_csv(out / "per_query_metrics.csv", index=False)
    np.savez_compressed(out / "predictions.npz", drug=drug, line=lines, fold=folds, active=active, **predictions)
    summaries = {}
    for method in METHODS:
        summaries[method] = {}
        for population, mask in (("active", table.active), ("all", np.ones(len(table), dtype=bool))):
            part = table[(table.method == method) & mask]
            summaries[method][population] = {col: (None if part[col].dropna().empty else float(part[col].mean())) for col in ["top10_overlap", "selection_regret", "raw_threshold_hit", "raw_r", "raw_mae"]}
    result = {"study": "decision_focused_selection_mvp", "status": "exploratory_non_confirmatory", "data_sha256": sha256(DATA), "code_sha256": sha256(Path(__file__).resolve()), "n_compounds": len(y), "n_lines": y.shape[1], "n_active": int(active.sum()), "fold_counts": [int((folds == i).sum()) for i in range(5)], "methods": METHODS, "summaries": summaries, "elapsed_seconds": time.time() - start, "science_gate": "NON_CONFIRMATORY"}
    (out / "RESULTS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    env = {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "sklearn": __import__("sklearn").__version__, "pid": os.getpid(), "threads": "3"}
    (out / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
