"""POST HOC (after the confirmatory run; not a registered test).

verify.py found that the frozen evaluator compared r(B) on all lines with a 5-day outcome against
r(B + R_mag) on the subset that also had >= 10 treated cells (an unpaired estimand), and that the
M3 measurement policy could not select lines too depleted to measure. This script recomputes M1, M2
and M3 on the common line set per drug (paired), with the same predictions (PREDICTIONS.npz), the
same bootstrap seed and resample count. It also reports which lines were dropped and their outcome.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import gate as G  # noqa: E402

SEED, NB, K = 20261010, 2000, 10
with np.load(HERE.parent / "PREDICTIONS.npz", allow_pickle=False) as z:
    pr = {k: z[k].copy() for k in z.files}
with np.load(ROOT / "data/external/kinetic_horizon_20261010/prism_mix_sealed.npz", allow_pickle=False) as z:
    tab = pd.DataFrame(z["secondary_mean"], index=z["files"], columns=z["drugs"])
lines = list(pr["M_lines"])
drugs, sdrugs = G.MIX_DRUGS_LATE, G.STATE_DRUGS
Y = np.column_stack([tab.loc[lines, d].to_numpy() for d in drugs])
B, R, S = pr["M_B"], pr["M_Rmag"], pr["M_Smag"]


def zf(x):
    return (x - np.nanmean(x)) / np.nanstd(x)


def r(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def common(j, extra):
    return np.flatnonzero(np.isfinite(Y[:, j]) & np.isfinite(B[:, j]) & np.isfinite(extra[:, j]))


def inc(rows_by_drug, extra, js):
    vals = []
    for j in js:
        c = rows_by_drug[j]
        b, e, y = B[c, j], extra[c, j], Y[c, j]
        vals.append(r(zf(b) + zf(e), y) - r(b, y))
    return float(np.mean(vals))


def util(score, y):
    sel = np.argsort(score, kind="stable")[:K]
    return float(-np.mean(y[sel]))


def boot(stat, js, extra):
    rng = np.random.default_rng(SEED)
    n = len(lines)
    out = []
    for _ in range(NB):
        b = rng.integers(0, n, n)
        rows = {j: np.array([i for i in b if np.isfinite(Y[i, j]) and np.isfinite(B[i, j]) and np.isfinite(extra[i, j])]) for j in js}
        out.append(stat(rows))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


res = {}
for name, extra, js in (("M1_measurement", R, range(len(drugs))), ("M2_state", S, [drugs.index(d) for d in sdrugs])):
    rows = {j: common(j, extra) for j in js}
    per = {drugs[j]: {"n": int(len(rows[j])), "B": r(B[rows[j], j], Y[rows[j], j]),
                      "B_plus": r(zf(B[rows[j], j]) + zf(extra[rows[j], j]), Y[rows[j], j])} for j in js}
    m3 = {drugs[j]: util(B[rows[j], j], Y[rows[j], j]) for j in js}
    m3p = {drugs[j]: util(zf(B[rows[j], j]) + zf(extra[rows[j], j]), Y[rows[j], j]) for j in js}
    du = lambda rr: float(np.mean([util(zf(B[rr[j], j]) + zf(extra[rr[j], j]), Y[rr[j], j]) - util(B[rr[j], j], Y[rr[j], j]) for j in js]))  # noqa: E731
    res[name] = {"per_drug": per, "mean_increment": inc(rows, extra, js), "ci95": boot(lambda rr: inc(rr, extra, js), js, extra),
                 "drugs_improved": int(sum(v["B_plus"] > v["B"] for v in per.values())),
                 "top10_utility_prior": m3, "top10_utility_policy": m3p,
                 "top10_difference": du(rows), "top10_difference_ci95": boot(du, js, extra),
                 "top10_drugs_better": int(sum(m3p[d] > m3[d] for d in m3))}
dropped = {}
for j, d in enumerate(drugs):
    miss = [i for i in range(len(lines)) if np.isfinite(Y[i, j]) and not np.isfinite(R[i, j])]
    dropped[d] = {"n_dropped": len(miss), "dropped_mean_late": float(np.mean(Y[miss, j])) if miss else None,
                  "kept_mean_late": float(np.nanmean(Y[common(j, R), j]))}
res["lines_without_measurement"] = dropped
(HERE / "paired_reanalysis.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: {kk: v[kk] for kk in ("mean_increment", "ci95", "drugs_improved", "top10_difference", "top10_difference_ci95", "top10_drugs_better")} for k, v in res.items() if k.startswith("M")}, indent=1))
print(json.dumps(dropped, indent=1))
