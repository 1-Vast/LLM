"""Post hoc (not registered): does skipping missing reference values change the virtual cell's transfer?

The frozen kNN (predictors.World.knn) sums weighted reference profiles with nansum and divides by the
total weight, so a reference's missing line counts as 0 with full weight. The promotion candidate
skips missing values (per-line weight normalisation). This compares both on the confirmation killers
(known and novel class) and the 160-line own-screen combination. No model call; sealed tier is open.
Output: posthoc/missing_value_rule.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import evaluate as EV  # noqa: E402
import mining as MI  # noqa: E402
import predictors as PR  # noqa: E402

sys.path.insert(0, str(HERE.parents[0] / "mechanism_falsification_20261010"))
import intervals as IV  # noqa: E402


def knn_skip(world, sim, pool, k=PR.K):
    ok = np.isfinite(sim)
    if ok.sum() == 0:
        return None
    order = np.argsort(-np.where(ok, sim, -np.inf))[:k]
    w = np.clip(sim[order], 0, None)
    if w.sum() <= 0:
        w = np.ones(len(order))
    X = world.P[pool[order]]
    have = np.isfinite(X)
    den = (w[:, None] * have).sum(0)
    return np.where(den > 0, (w[:, None] * np.where(have, X, 0.0)).sum(0) / np.maximum(den, 1e-12), np.nan)


def main():
    P = EV.protocol()
    world, queries = EV.setup("sealed", None)
    killers = EV.killers_of(world, queries, P)
    fe = MI.Features(world)
    rows = []
    for i in killers:
        r = {"moa": world.moa[i]}
        for regime in ("known_class", "novel_class"):
            pool = world.pool(i, regime)
            s = world.l1000_sim(i, pool)
            for tag, pred in (("frozen", world.knn(s, pool)), ("skip", knn_skip(world, s, pool))):
                r[f"{regime}:{tag}"] = EV.fin(PR.selective_r(pred, world.P[i], world.G))
                if regime == "novel_class":
                    y = PR.residual(world.P[i], world.G)
                    t = fe.test[np.isfinite(y[fe.test])]
                    d = fe.discovery(160)
                    d = d[np.isfinite(y[d])]
                    ridge = fe.ridge_predict(y[d], d, t)
                    Ln = PR.residual(pred, world.G)[t]
                    r[f"own160:{tag}"] = EV.fin(PR.pearson(PR.combine([Ln, ridge]), y[t], 30))
        rows.append(r)
    cl = np.array([r["moa"] for r in rows])
    out = {"label": "post hoc, not registered", "n_killers": len(rows)}
    for key in ("known_class", "novel_class", "own160"):
        a = np.array([r[f"{key}:skip"] for r in rows])
        b = np.array([r[f"{key}:frozen"] for r in rows])
        d = IV.paired_difference(a, b, cl, n_boot=2000, seed=20261011)
        out[key] = {"skip_mean": float(a.mean()), "frozen_mean": float(b.mean()), "skip_minus_frozen": d["mean_difference"],
                    "ci95": d["ci95"], "max_abs_drug_difference": float(np.abs(a - b).max())}
    (HERE / "posthoc" / "missing_value_rule.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
