"""Workstream C, task 1 extra: independent drug-clustered bootstrap of the pooled M2 - M0 contrast.

Uses the verifier's per-group values (task1_recompute_result.json), the verifier's own drug parser
and its own seed, so the interval is an independent check of the reported one (not a bit-exact
reproduction). Writes task1_bootstrap.json.
"""
import ast
import json
import os

import numpy as np

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
V = os.path.join(S, "verification")
SEED = 314159
REPS = 4000


def main():
    with open(os.path.join(S, "SPLIT.json"), encoding="utf-8") as fh:
        split = json.load(fh)
    with open(os.path.join(V, "task1_recompute_result.json"), encoding="utf-8") as fh:
        mine = json.load(fh)
    with open(os.path.join(S, "world_eval", "EVAL_RESULTS.json"), encoding="utf-8") as fh:
        ev = json.load(fh)
    vals, drugs = [], []
    for name in split["evaluation"]:
        for g in mine["lines"][split["files"][name]]["groups"]:
            (drug, dose, unit), = ast.literal_eval(g["label"])
            vals.append(g["se_M2"] - g["se_M0"])
            drugs.append(drug)
    vals = np.asarray(vals)
    drugs = np.asarray(drugs)
    ids, inv = np.unique(drugs, return_inverse=True)
    sums = np.bincount(inv, weights=vals)
    counts = np.bincount(inv)
    rng = np.random.default_rng(SEED)
    stats = np.empty(REPS)
    for i in range(REPS):
        pick = rng.integers(0, len(ids), len(ids))
        stats[i] = sums[pick].sum() / counts[pick].sum()
    lo, hi = np.percentile(stats, [2.5, 97.5])
    out = {"groups": int(len(vals)), "drugs": int(len(ids)), "reps": REPS, "seed": SEED,
           "mean": float(vals.mean()), "ci95_verifier": [float(lo), float(hi)],
           "ci95_study": ev["contrasts"]["M2_minus_M0"]["ci95_drug_clustered"],
           "verifier_ci_excludes_zero": bool(hi < 0),
           "delta_min": 5.619872137814432e-05,
           "improvement_at_least_delta_min": bool(-vals.mean() >= 5.619872137814432e-05)}
    with open(os.path.join(V, "task1_bootstrap.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
