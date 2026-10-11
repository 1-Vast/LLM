"""Feasibility probe B1-B2 (development killers; no provider calls).

Task: from a drug's selective viability profile (PRISM primary minus its projection on the generic
profile) in *discovery* lines, find genomic features (CCLE 19Q4 expression, damaging/hotspot
mutations) that predict its selective profile in *test* lines. Lines are split once (seed 20261011)
into halves; discovery sets are nested subsamples of 40, 80, 160 and all discovery lines.

Predictors on test lines (Pearson r with the observed selective profile):
  top1 / top5   features with the largest |r| in discovery lines (sign-adjusted z mean)
  ridge         ridge regression on all expressed genes (alpha by discovery 5-fold CV)
  targets_top1  top-1 restricted to the drug's Hub targets (expression or mutation)
  random20_top1 top-1 within 20 random genes (knowledge-free restriction, 20 draws)
  L             virtual cell transfer profile (known-class regime), residualised the same way
Output: feasibility/probe_biomarker_mining.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))
import predictors as PR  # noqa: E402

sys.path.insert(0, str(PR.BLOCK_M))
import intervals as IV  # noqa: E402

SEED = 20261011
SIZES = (40, 80, 160, None)


def feature_matrix(world):
    expr, mutated = world.ccle()
    E = expr.to_numpy(float)  # (lines, genes)
    keep = np.nanstd(E, axis=0) > 0.5
    genes = np.array(expr.columns)[keep]
    E = E[:, keep]
    mg = [g for g, s in mutated.items() if 5 <= len(s) <= len(world.lines) - 5]
    M = np.array([[1.0 if l in mutated[g] else 0.0 for g in mg] for l in world.lines])
    names = [f"{g}:expr" for g in genes] + [f"{g}:mut" for g in mg]
    F = np.concatenate([E, M], axis=1)
    ok_lines = np.isfinite(F).all(axis=1)
    return F, names, ok_lines


def zcols(F, rows):
    mu, sd = np.nanmean(F[rows], axis=0), np.nanstd(F[rows], axis=0)
    sd[sd == 0] = np.inf
    return mu, sd


def corr_cols(F, y):
    Fc = F - F.mean(axis=0)
    yc = y - y.mean()
    den = np.sqrt((Fc ** 2).sum(axis=0) * (yc ** 2).sum())
    with np.errstate(invalid="ignore", divide="ignore"):
        return (Fc * yc[:, None]).sum(axis=0) / den


def predict_top(F, y_d, d_rows, t_rows, cand, k):
    r = corr_cols(F[d_rows][:, cand], y_d)
    r = np.where(np.isfinite(r), r, 0.0)
    order = np.argsort(-np.abs(r))[:k]
    mu, sd = zcols(F, d_rows)
    cols = cand[order]
    Z = (F[t_rows][:, cols] - mu[cols]) / sd[cols]
    return (Z * np.sign(r[order])).mean(axis=1)


def ridge_predict(F, y_d, d_rows, t_rows, n_expr):
    from sklearn.linear_model import RidgeCV
    X = F[:, :n_expr]
    mu, sd = zcols(X, d_rows)
    Xd, Xt = (X[d_rows] - mu) / sd, (X[t_rows] - mu) / sd
    m = RidgeCV(alphas=np.logspace(1, 5, 9), cv=5).fit(Xd, y_d)
    return m.predict(Xt)


def main() -> dict:
    world = PR.load_world("open")
    F, names, ok_lines = feature_matrix(world)
    n_expr = sum(n.endswith(":expr") for n in names)
    name_idx = {n: i for i, n in enumerate(names)}
    rng = np.random.default_rng(SEED)
    lines = np.where(ok_lines)[0]
    perm = rng.permutation(lines)
    disc_all, test = np.sort(perm[: len(perm) // 2]), np.sort(perm[len(perm) // 2:])
    disc_order = rng.permutation(disc_all)
    dev = [i for i in np.where(world.role == "development")[0] if np.nanmean(world.P[i] < -1) >= 0.05]
    rows = []
    for i in dev:
        y = PR.residual(world.P[i], world.G)
        L = world.baselines(i, "known_class")["L"]
        Lr = PR.residual(L, world.G) if L is not None else None
        for size in SIZES:
            d = np.sort(disc_order[:size]) if size else disc_all
            d = d[np.isfinite(y[d])]
            t = test[np.isfinite(y[test])]
            row = {"drug": world.drug[i], "moa": world.moa[i], "size": size or len(disc_all)}
            allc = np.arange(F.shape[1])
            row["top1"] = PR.pearson(predict_top(F, y[d], d, t, allc, 1), y[t], 30)
            row["top5"] = PR.pearson(predict_top(F, y[d], d, t, allc, 5), y[t], 30)
            row["ridge"] = PR.pearson(ridge_predict(F, y[d], d, t, n_expr), y[t], 30)
            tc = np.array([name_idx[n] for g in world.targets[i] for n in (f"{g}:expr", f"{g}:mut") if n in name_idx])
            row["targets_top1"] = PR.pearson(predict_top(F, y[d], d, t, tc, 1), y[t], 30) if len(tc) else 0.0
            rr = []
            for k in range(20):
                rc = np.random.default_rng(SEED + k).choice(n_expr, 20, replace=False)
                rr.append(PR.pearson(predict_top(F, y[d], d, t, rc, 1), y[t], 30))
            row["random20_top1"] = float(np.nanmean(rr))
            row["L"] = PR.pearson(Lr[t], y[t], 30) if Lr is not None else np.nan
            rows.append(row)
    import pandas as pd
    df = pd.DataFrame(rows)
    res = {"n_drugs": len(dev), "n_test_lines": int(len(test)), "n_features": int(F.shape[1]), "by_size": {}}
    for size, g in df.groupby("size"):
        e = {}
        for col in ("top1", "top5", "ridge", "targets_top1", "random20_top1", "L"):
            v = g[col].to_numpy(float)
            v = np.where(np.isfinite(v), v, 0.0)
            est, lo, hi = IV.cluster_bootstrap(v, g["moa"].to_numpy(), n_boot=500, seed=SEED)
            e[col] = [round(est, 4), round(lo, 4), round(hi, 4)]
        res["by_size"][int(size)] = e
    (HERE / "probe_biomarker_mining.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(HERE / "probe_biomarker_mining_rows.csv", index=False)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
