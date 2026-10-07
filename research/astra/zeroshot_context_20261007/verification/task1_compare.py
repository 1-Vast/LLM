"""Workstream C, task 1 comparison: verifier recomputation vs the study's reported numbers.

Reads task1_recompute_result.json (written by task1_recompute.py) and the study's
EVAL_RESULTS.json / DEV_RESULTS.json; writes task1_comparison.json.
"""
import json
import os

import numpy as np

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
V = os.path.join(S, "verification")

with open(os.path.join(S, "SPLIT.json"), encoding="utf-8") as fh:
    split = json.load(fh)
with open(os.path.join(S, "world_eval", "EVAL_RESULTS.json"), encoding="utf-8") as fh:
    ev = json.load(fh)
with open(os.path.join(S, "world_dev", "DEV_RESULTS.json"), encoding="utf-8") as fh:
    dv = json.load(fh)
with open(os.path.join(V, "task1_recompute_result.json"), encoding="utf-8") as fh:
    mine = json.load(fh)

files = split["files"]


def cmp(a, b):
    """a = verifier, b = study."""
    d = a - b
    return {"verifier": a, "study": b, "abs_diff": d, "rel_diff": (d / abs(b)) if b else None}


out = {"evaluation": {}, "development": {}, "pooled_evaluation": {}, "tolerance_rel": 1e-4}
worst_rel = 0.0
for name in split["evaluation"]:
    r = mine["lines"][files[name]]
    e = {
        "eligible_groups": {"verifier": r["eligible_groups"], "study": ev["eligible_groups"][name],
                            "equal": r["eligible_groups"] == ev["eligible_groups"][name]},
        "M0": cmp(r["mean_se_M0"], ev["mean_corrected_se"]["M0"][name]),
        "M2": cmp(r["mean_se_M2"], ev["mean_corrected_se"]["M2"][name]),
        "M2_minus_M0": cmp(r["mean_M2_minus_M0"], ev["contrasts"]["M2_minus_M0"]["per_line"][name]),
    }
    for k in ("M0", "M2", "M2_minus_M0"):
        worst_rel = max(worst_rel, abs(e[k]["rel_diff"]))
    out["evaluation"][name] = e

diffs = []
for name in split["evaluation"]:
    for g in mine["lines"][files[name]]["groups"]:
        diffs.append(g["se_M2"] - g["se_M0"])
diffs = np.array(diffs)
pooled = cmp(float(diffs.mean()), ev["contrasts"]["M2_minus_M0"]["mean"])
pooled["groups"] = {"verifier": int(len(diffs)), "study": ev["contrasts"]["M2_minus_M0"]["groups"]}
pooled["drugs_verifier"] = len({g["label"].split("'")[1] for name in split["evaluation"]
                                for g in mine["lines"][files[name]]["groups"]})
pooled["drugs_study"] = ev["contrasts"]["M2_minus_M0"]["drugs"]
pooled["groups_with_M2_better"] = int((diffs < 0).sum())
worst_rel = max(worst_rel, abs(pooled["rel_diff"]))
out["pooled_evaluation"]["M2_minus_M0"] = pooled

for name in split["development"]:
    f = files[name]
    if f not in mine["lines"]:
        continue
    r = mine["lines"][f]
    pl = dv["per_line"][name]["mean_corrected_se"]
    d = {
        "eligible_groups": {"verifier": r["eligible_groups"], "study": dv["eligible_groups"][name],
                            "equal": r["eligible_groups"] == dv["eligible_groups"][name]},
        "M0": cmp(r["mean_se_M0"], pl["M0"]),
        "M2_g0.5": cmp(r["mean_se_M2"], pl["M2_g0.5"]),
        "M2_minus_M0": cmp(r["mean_M2_minus_M0"], dv["development_contrasts"]["M2g_minus_M0"]["per_line"][name]),
    }
    for k in ("M0", "M2_g0.5", "M2_minus_M0"):
        worst_rel = max(worst_rel, abs(d[k]["rel_diff"]))
    out["development"][name] = d

all_eq = all(v["eligible_groups"]["equal"] for v in out["evaluation"].values()) and \
    all(v["eligible_groups"]["equal"] for v in out["development"].values())
out["worst_abs_rel_diff"] = worst_rel
out["eligible_counts_all_equal"] = all_eq
out["pass"] = bool(all_eq and worst_rel < out["tolerance_rel"])
out["verifier_audit"] = mine["audit"]
with open(os.path.join(V, "task1_comparison.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(out, indent=1))
