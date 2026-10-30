#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-STAGE1 one-step DR / allocation / planning diagnostics only.

Support research; mechanism account; no effect comparison, no gain, no real data.
Imports the frozen M3 v0.2 formalism arithmetic and runs Stage1 checks + S1 diagnostics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
from typing import Any, Dict, List

ROOT = r"D:\MAESTRO"
PREREG = os.path.join(ROOT, "research", "2026-10-28-m3-decision-credit-prereg")
DEFAULT_OUT = os.path.join(ROOT, "research", "2026-10-28-m3-stage1")
SCHEMA_NAME = "schema_m3_stage1.json"
CAPS = {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8, "new_wells": 0}

sys.path.insert(0, PREREG)
import formalism_M3_v0_2 as v3  # noqa: E402


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    args = ap.parse_args()
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)
    t0 = time.perf_counter()

    schema_path = os.path.join(outdir, SCHEMA_NAME)
    if os.path.abspath(schema_path) != os.path.abspath(os.path.join(DEFAULT_OUT, SCHEMA_NAME)):
        if not os.path.isfile(schema_path):
            import shutil
            shutil.copyfile(os.path.join(DEFAULT_OUT, SCHEMA_NAME), schema_path)
    if not os.path.isfile(schema_path):
        raise SystemExit("missing schema")
    schema = json.load(open(schema_path, encoding="utf-8"))

    # chain verification
    chain = {}
    for name, expected in schema["frozen_chain"].items():
        p = os.path.join(PREREG, name)
        actual = sha256_file(p) if os.path.isfile(p) else None
        chain[name] = {"expected": expected, "actual": actual, "match": actual == expected}
    chain_ok = all(v["match"] for v in chain.values())
    if not chain_ok:
        result = {"task": "R204-M3-STAGE1", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "chain": chain,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage1.json"))
        print("CHAIN MISMATCH", chain)
        return 2

    core, core_elapsed = v3.run_core()
    checks = dict(core["checks"])
    expected = dict(schema["expected_checks"])
    # verify 19 checks and expected values; never alter thresholds
    check_rows = []
    for cid in schema["check_ids"]:
        actual = bool(checks.get(cid, False))
        exp = bool(expected.get(cid, True))
        check_rows.append({"check_id": cid, "actual": actual, "expected": exp,
                           "pass": bool(actual == exp)})
    all_checks_pass = all(r["pass"] for r in check_rows) and bool(core["all_checks_pass"])

    # S1-class diagnostics
    dr = core["one_step_DR"]
    sup = core["support_positivity"]
    clip = core["clipping_bias"]
    tilt = core["score_tilt_update"]
    alloc = core["allocation_second_order"]
    plan = core["planning_arithmetic"]
    base = core["standard_baselines"]
    fail = core["three_stage_plan"]
    rows_alloc = alloc["rows_frozen_m"]
    ratios = [rows_alloc[k]["ratio_full_over_noise"] for k in sorted(rows_alloc)]
    s1 = {
        "S1_a_dr_identity": {"max_abs_gap": dr["max_abs_gap"], "expected": 0.0,
                             "pass": approx(dr["max_abs_gap"], 0.0)},
        "S1_b_clipping": {"bias": clip["bias"], "expected": -0.026407185629,
                          "cap": clip["cap"], "max_raw_weight": clip["max_raw_weight"],
                          "n_weights_clipped": clip["n_weights_clipped"],
                          "pass": approx(clip["bias"], -0.026407185629, 1e-9)},
        "S1_c_score_root": {"epsilon_root": tilt["epsilon_root"], "expected": -0.562633036711,
                            "score_at_root": tilt["score_at_root"],
                            "pass": approx(tilt["epsilon_root"], -0.562633036711, 1e-9)
                            and abs(tilt["score_at_root"]) <= 1e-10},
        "S1_d_identifiability": {"collinear_scores_rank": tilt["collinear_scores_rank"],
                                 "expected_rank": 1, "nonunique": tilt["collinearity_nonunique"],
                                 "zero_support_identified": sup["identified"],
                                 "pass": bool(tilt["collinear_scores_rank"] == 1
                                              and tilt["collinearity_nonunique"]
                                              and not sup["identified"])},
        "S1_e_allocation": {"ratios_full_over_noise": ratios,
                            "expected": [1.217228464419, 1.166867632081],
                            "pass": all(approx(r, e, 1e-9) for r, e in zip(ratios, [1.217228464419, 1.166867632081]))},
        "S1_f_pi_equals_b": {"max_abs_H_minus_1": base["max_abs_H_minus_1"], "expected": 0.0,
                             "pass": approx(base["max_abs_H_minus_1"], 0.0)},
        "S1_g_planning": {"MDE80": plan["MDE80"], "expected_MDE": 0.047982684954,
                          "n_req_cluster": plan["n_req_cluster"], "expected_n_req": 278,
                          "n_eff": plan["n_eff"], "expected_n_eff": 136.363636363636,
                          "pass": approx(plan["MDE80"], 0.047982684954, 1e-9)
                          and int(plan["n_req_cluster"]) == 278},
        "S1_h_fisher_z_only": {"delta_0.05": plan["fisher_z_only"]["delta_0.05"],
                               "delta_0.10": plan["fisher_z_only"]["delta_0.10"],
                               "non_integer": plan["fisher_z_only"]["non_integer"],
                               "not_a_gate": plan["fisher_z_only"]["not_a_gate"],
                               "not_paired_DR": plan["fisher_z_only"]["not_paired_DR_formula"],
                               "pass": bool(plan["fisher_z_only"]["non_integer"]
                                            and plan["fisher_z_only"]["not_a_gate"]
                                            and plan["fisher_z_only"]["not_paired_DR_formula"])},
        "S1_i_baseline_arms": {"baselines_required": base["baselines_required"],
                               "stage2_arms": fail["stage_2"]["arms"],
                               "stage3_arms": fail["stage_3"]["arms"],
                               "stage2_n": len(fail["stage_2"]["arms"]),
                               "stage3_n": len(fail["stage_3"]["arms"]),
                               "pass": bool(len(fail["stage_2"]["arms"]) == 6
                                            and len(fail["stage_3"]["arms"]) == 7
                                            and "optimal_experimental_design" in fail["stage_2"]["arms"]
                                            and "decision_AL" in fail["stage_2"]["arms"]
                                            and "optimal_experimental_design" in fail["stage_3"]["arms"]
                                            and "decision_AL" in fail["stage_3"]["arms"])},
    }
    s1_all_pass = all(v["pass"] for v in s1.values())
    failed_checks = [r["check_id"] for r in check_rows if not r["pass"]]
    failure = None
    if not all_checks_pass or not s1_all_pass:
        if any("collinear" in c or "support" in c for c in failed_checks):
            failure = "design_invalid: nonidentifiable"
        else:
            failure = "design_invalid"
    if failure is None and not s1["S1_d_identifiability"]["pass"]:
        failure = "design_invalid: nonidentifiable"
    if failure is None and not s1["S1_b_clipping"]["pass"]:
        failure = "design_invalid: calibration"

    # pilot with final implementation
    tp = time.perf_counter()
    for _ in range(10):
        v3.run_core()
    per_rep = (time.perf_counter() - tp) / 10.0
    timing = {"task": "R204-M3-STAGE1", "pilot_reps": 10,
              "per_rep_seconds": [round(per_rep, 9)],
              "mean_per_rep_seconds": round(per_rep, 9),
              "projected_seconds": round(per_rep * 10.0, 6),
              "full_stage1_wall_seconds": round(time.perf_counter() - t0, 6),
              "caps": CAPS, "wells": 0, "compute_only": True,
              "canonical": True, "note": "final implementation pilot; no effect comparison"}

    # rows/checks CSV
    checks_path = os.path.join(outdir, "m3_stage1_checks.csv")
    with open(checks_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "id", "actual", "expected", "pass"])
        for r in check_rows:
            w.writerow(["check19", r["check_id"], r["actual"], r["expected"], r["pass"]])
        for k, v in s1.items():
            w.writerow(["S1", k, json.dumps(v, ensure_ascii=False, sort_keys=True), "", v["pass"]])

    # result (no telemetry)
    result = {
        "task": "R204-M3-STAGE1",
        "status": "completed_synthetic_checks" if failure is None else "design_invalid",
        "scope": "support research / mechanism account only; Stage1 one-step DR synthetic diagnostics; no effect/gain/method comparison; 0 wells",
        "chain": chain,
        "chain_ok": chain_ok,
        "formalism_core": core,
        "check19": check_rows,
        "check19_pass": all_checks_pass,
        "S1_diagnostics": s1,
        "S1_all_pass": s1_all_pass,
        "all_checks_pass": all_checks_pass and s1_all_pass,
        "failed_checks": failed_checks,
        "failure_category": failure,
        "baseline_spec": {
            "baselines_required": base["baselines_required"],
            "stage2_arms": fail["stage_2"]["arms"],
            "stage3_arms": fail["stage_3"]["arms"],
            "same_budget_note": base["same_budget_note"],
            "equal_budget_stop": base["equal_budget_stop"],
            "baseline_audit": schema["baseline_audit"],
            "not_executed": True,
        },
        "fisher_z_note": {
            "delta_0.05": plan["fisher_z_only"]["delta_0.05"],
            "delta_0.10": plan["fisher_z_only"]["delta_0.10"],
            "non_integer": True, "not_a_gate": True,
            "not_universal_decision_gate": True, "not_paired_DR_formula": True,
            "decision_use": "MDE80=.047982685 / n_req_cluster=278 / headroom / cluster",
        },
        "no_effect_results": True,
        "no_gain_or_method_comparison": True,
        "no_decision_utility_or_regret": True,
        "no_topk": True,
        "no_real_data": True,
        "new_wells": 0,
        "schema_sha256": sha256_file(schema_path),
        "timing_file": "timing_m3_stage1.json",
        "two_run_note": "external two-run byte-identical check recorded in usage/report; result JSON has no telemetry",
    }
    write_json(result, os.path.join(outdir, "m3_stage1.json"))

    diagnostics = {
        "task": "R204-M3-STAGE1",
        "chain": chain,
        "core": core,
        "S1": s1,
        "checks": check_rows,
        "failed_checks": failed_checks,
        "failure_category": failure,
        "no_effect_results": True,
    }
    write_json(diagnostics, os.path.join(outdir, "m3_stage1_diagnostics.json"))

    timing["result_json_sha256"] = sha256_file(os.path.join(outdir, "m3_stage1.json"))
    write_json(timing, os.path.join(outdir, "timing_m3_stage1.json"))

    print("chain_ok", chain_ok)
    print("19 checks", sum(1 for r in check_rows if r["pass"]), "/", len(check_rows))
    print("S1", {k: v["pass"] for k, v in s1.items()})
    print("clip_bias", s1["S1_b_clipping"]["bias"], "root", s1["S1_c_score_root"]["epsilon_root"],
          "rank", s1["S1_d_identifiability"]["collinear_scores_rank"], "ratios", s1["S1_e_allocation"]["ratios_full_over_noise"])
    print("MDE", s1["S1_g_planning"]["MDE80"], "n_req", s1["S1_g_planning"]["n_req_cluster"])
    print("failure", failure, "all", all_checks_pass and s1_all_pass)
    print("timing", timing)
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
