"""Workstream C, task 1 residual diagnostic.

The verifier's float64 recomputation differs from the study by ~1e-10 on M2 (relative <5e-7).
Hypothesis: the study's Panel stores training-context STATE forecasts as float16 and averages
them in float32 before forming devS. This script repeats the verifier computation with that
storage emulated (the rest unchanged) for the lines given, to see whether the residual vanishes.
Writes task1_residual_diagnostic.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import task1_recompute as t1  # the verifier's own module

S = t1.S
C = t1.C


def main():
    lines = sys.argv[1:] or ["c31.h5ad", "c20.h5ad"]
    with open(os.path.join(S, "SPLIT.json"), encoding="utf-8") as fh:
        split = json.load(fh)
    heldout = set(split["files"].values())
    train = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in heldout]
    panel, pd_sum, pd_cnt, _ = t1.build_panel(train)
    # float16 storage emulation: sum of float16-rounded values in float32, divided in float32
    acc = {}
    for f in train:
        sf = np.load(os.path.join(C, "state_forecasts", f + ".npz"))
        for lab, pl, pdv in zip(sf["label"].tolist(), sf["plate"].tolist(), sf["paired_delta"]):
            k = (lab, pl)
            acc.setdefault(k, np.zeros(2000, np.float32))
            acc[k] += pdv.astype(np.float16).astype(np.float32)
    pd16 = {k: (acc[k] / np.float32(pd_cnt[k])).astype(np.float64) for k in acc}
    ones = {k: 1 for k in acc}
    with open(os.path.join(S, "world_eval", "EVAL_RESULTS.json"), encoding="utf-8") as fh:
        ev = json.load(fh)
    with open(os.path.join(S, "world_dev", "DEV_RESULTS.json"), encoding="utf-8") as fh:
        dv = json.load(fh)
    inv = {v: k for k, v in split["files"].items()}
    out = {}
    for f in lines:
        r64 = t1.evaluate_line(f, panel, pd_sum, pd_cnt)
        r16 = t1.evaluate_line(f, panel, pd16, ones)
        name = inv[f]
        if name in split["evaluation"]:
            study_m2 = ev["mean_corrected_se"]["M2"][name]
        else:
            study_m2 = dv["per_line"][name]["mean_corrected_se"]["M2_g0.5"]
        out[name] = {"study_M2": study_m2,
                     "verifier_float64_M2": r64["mean_se_M2"],
                     "verifier_float16_panel_state_M2": r16["mean_se_M2"],
                     "abs_diff_float64": r64["mean_se_M2"] - study_m2,
                     "abs_diff_float16_emulated": r16["mean_se_M2"] - study_m2}
    with open(os.path.join(HERE, "task1_residual_diagnostic.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
