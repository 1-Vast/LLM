"""Development pilot (exploratory): are the agent's post-observation biomarker hypotheses worth cell lines?

Population: development drugs killing at least 5% of lines. For discovery sizes 40, 80 and 160 the
agent (``explain.py``) sees the 20 most and 20 least selectively killed discovery lines; its
features are scored on the held-out test half. Comparators on the same split: unrestricted mining
(top1, top5, ridge), target-restricted mining, random 20-gene restriction, the virtual cell's
transfer profile L, and combinations with L (equal-weight z-sum).

Usage: python dev_explain.py
Output: development/explain_pilot.json and development/explain_pilot_rows.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import explain as EX  # noqa: E402
import mining as MI  # noqa: E402
import predictors as PR  # noqa: E402
import scientist as SC  # noqa: E402

sys.path.insert(0, str(PR.BLOCK_M))
import intervals as IV  # noqa: E402

SIZES = (40, 80, 160)
SEED = 20261011


def zt(v):
    return None if v is None else PR.z(v)


def main() -> dict:
    world = PR.load_world("open")
    fe = MI.Features(world)
    base = SC.Agent(world)  # provides the client and the spend ledger
    ex = EX.Explainer(world, base.ledger, base.client)
    dev = [i for i in np.where(world.role == "development")[0] if np.nanmean(world.P[i] < -1) >= 0.05]
    Y = {i: PR.residual(world.P[i], world.G) for i in dev}
    tasks = []
    for i in dev:
        tasks.append(("explain_prior", int(i), "prior", None, Y[i]))
        for s in SIZES:
            tasks.append(("explain_full", int(i), f"n{s}", fe.discovery(s), Y[i]))
            if s in (40, 160):
                tasks.append(("explain_novc", int(i), f"n{s}", fe.discovery(s), Y[i]))
    recs = ex.run(tasks)
    R = {(r["arm"], r["size"], r["drug"]): r for r in recs}
    rows = []
    for i in dev:
        y = Y[i]
        L = world.baselines(i, "known_class")["L"]
        Lr = PR.residual(L, world.G) if L is not None else None
        tc = np.array([fe.index[n] for g in world.targets[i] for n in (f"{g}:expr", f"{g}:mut") if n in fe.index], int)
        for s in SIZES:
            d = fe.discovery(s)
            d = d[np.isfinite(y[d])]
            t = fe.test[np.isfinite(y[fe.test])]
            row = {"drug": world.drug[i], "moa": world.moa[i], "size": s}
            pred = {"top1": fe.predict_top(np.arange(len(fe.names)), y[d], d, t, 1),
                    "top5": fe.predict_top(np.arange(len(fe.names)), y[d], d, t, 5),
                    "ridge": fe.ridge_predict(y[d], d, t),
                    "targets_top1": fe.predict_top(tc, y[d], d, t, 1),
                    "L": Lr[t] if Lr is not None else None}
            for arm, tag in (("explain_full", f"n{s}"), ("explain_novc", f"n{s}"), ("explain_prior", "prior")):
                rec = R.get((arm, tag, str(world.drug[i])))
                if rec is None:
                    continue
                cols, signs = fe.columns(rec["claims"]["features"])
                row[f"{arm}:n_claims"] = len(rec["claims"]["features"])
                row[f"{arm}:n_mappable"] = int(len(cols))
                pred[f"{arm}:direct3"] = fe.predict_claims(cols, signs, d, t, 3)
                pred[f"{arm}:direct_all"] = fe.predict_claims(cols, signs, d, t)
                pred[f"{arm}:mine1"] = fe.predict_top(cols, y[d], d, t, 1)
                pred[f"{arm}:mine3"] = fe.predict_top(cols, y[d], d, t, 3)
            for k in ("ridge", "top5", "explain_full:direct_all", "explain_full:mine3", "explain_prior:direct_all"):
                if k in pred:
                    parts = [zt(pred["L"]), zt(pred[k])]
                    pred[f"L+{k}"] = np.mean([p for p in parts if p is not None], axis=0) if any(p is not None for p in parts) else None
            for k, p in pred.items():
                r = PR.pearson(p, y[t], 30) if p is not None else np.nan
                row[k] = r if np.isfinite(r) else 0.0
            rows.append(row)
    df = pd.DataFrame(rows)
    res = {"n_drugs": len(dev), "ledger_total_usd": round(base.ledger.total_usd, 4),
           "status": {a: sum(1 for r in recs if r["arm"] == a and r["status"] == "ok") for a in ("explain_full", "explain_novc", "explain_prior")},
           "by_size": {}}
    pairs = [("explain_full:direct_all", "top5"), ("explain_full:direct_all", "ridge"), ("explain_full:mine3", "top5"),
             ("explain_full:mine1", "top1"), ("explain_full:direct_all", "explain_novc:direct_all"),
             ("explain_full:direct_all", "explain_prior:direct_all"), ("explain_full:direct_all", "targets_top1"),
             ("L+explain_full:direct_all", "L"), ("L+explain_full:direct_all", "L+ridge"), ("L+ridge", "L"), ("L+top5", "L"),
             ("L+explain_prior:direct_all", "L"), ("L+explain_full:mine3", "L")]
    for s, g in df.groupby("size"):
        cl = g["moa"].to_numpy()
        e = {"mean": {}, "paired": {}}
        for col in g.columns:
            if col in ("drug", "moa", "size") or ":n_" in col:
                continue
            v = g[col].to_numpy(float)
            est, lo, hi = IV.cluster_bootstrap(v, cl, n_boot=500, seed=SEED)
            e["mean"][col] = [round(est, 4), round(lo, 4), round(hi, 4)]
        for a, b in pairs:
            if a in g and b in g:
                r = IV.paired_difference(g[a].to_numpy(float), g[b].to_numpy(float), cl, n_boot=500, seed=SEED)
                e["paired"][f"{a} - {b}"] = [round(r["mean_difference"], 4), round(r["ci95"][0], 4), round(r["ci95"][1], 4)]
        e["mappable_share"] = {a: round(float((g[f"{a}:n_mappable"] / g[f"{a}:n_claims"].clip(lower=1)).mean()), 3)
                               for a in ("explain_full", "explain_novc", "explain_prior") if f"{a}:n_mappable" in g}
        res["by_size"][int(s)] = e
    out = HERE / "development"
    out.mkdir(exist_ok=True)
    (out / "explain_pilot.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(out / "explain_pilot_rows.csv", index=False)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
