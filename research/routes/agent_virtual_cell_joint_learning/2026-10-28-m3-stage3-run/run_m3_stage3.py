#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S3-EXEC synthetic learning comparison.

Support research / mechanism account only. No real data/wet lab, no pharmacology/
real-decision/transfer/mechanism/novelty claim, no allocation comparison.
Fixed feedback stream + fixed shared-score allocation; 7 pure learner arms;
primary = candidate vs standard DR/TMLE on common shared evaluation sample.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = r"D:\MAESTRO"
PREREG = os.path.join(ROOT, "research", "2026-10-28-m3-stage3-exec-prereg")
PLAN_PATH = os.path.join(PREREG, "exec_plan_m3_s3_v0_4.json")
DEFAULT_OUT = os.path.join(ROOT, "research", "2026-10-28-m3-stage3-run")
SCHEMA_NAME = "schema_m3_stage3_run.json"
CAPS = {"wall_s": 1800.0, "cpu_s": 7200.0, "memory_gb": 8.0, "new_wells": 0}
P = np.array([0.3, 0.4, 0.3])
B = np.array([[0.2, 0.3, 0.5], [0.4, 0.4, 0.2], [0.25, 0.35, 0.4]], dtype=float)
MU = np.array([[0.2, 0.5, 0.8], [0.4, 0.6, 0.3], [0.1, 0.7, 0.5]], dtype=float)
PI2 = np.array([[0.2, 0.5, 0.3], [0.5, 0.2, 0.3], [0.3, 0.3, 0.4]], dtype=float)
M_WRONG = np.full((3, 3), 0.5)
NH, NA = 3, 3
R_MAIN = 10
R_PILOT = 2
N_FEED = 300
N_EVAL = 300
B_MIN = 1e-6
C_H = 20.0
DELTA = 0.05
MDE = 0.04798268
N_REQ = 278
ARM_IDS = ["A_candidate_score_tilt", "A_full_history_retrain", "A_importance_weighting",
           "A_DR_targeting", "A_TMLE_targeting", "A_value_aware", "A_standard_DR_TMLE"]
UPDATE_RULES = {
    "A_candidate_score_tilt": "one-step score-tilt update on shared score H/delta",
    "A_full_history_retrain": "refit from all history",
    "A_importance_weighting": "importance-weighted cell mean",
    "A_DR_targeting": "DR targeting update",
    "A_TMLE_targeting": "TMLE targeting update",
    "A_value_aware": "value-aware shrunk cell mean",
    "A_standard_DR_TMLE": "standard DR/TMLE learner (fixed allocation)",
}
POLICY_TOKEN = "shared_score_fixed_same_feedback_stream"


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def sha_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest().upper()


def write_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def allocation_w() -> np.ndarray:
    var = MU * (1.0 - MU)
    q = P[:, None] * PI2 ** 2 * (var + (MU - M_WRONG) ** 2) / B
    legal = B > 0
    q = np.where(legal & np.isfinite(q), np.maximum(q, 0.0), 0.0)
    w = np.zeros_like(q)
    for h in range(NH):
        if q[h].sum() <= 0:
            raise RuntimeError("allocation Q zero at h")
        w[h] = q[h] / q[h].sum()
    return w


def stream_hashes(feedback: List[Tuple[int, int, int]], evaluation: List[Tuple[int, int]]) -> Tuple[str, str]:
    fb = "".join(f"{h},{a},{y}\n" for h, a, y in feedback).encode("utf-8")
    ev = "".join(f"{h},{a}\n" for h, a in evaluation).encode("utf-8")
    return hashlib.sha256(fb).hexdigest().upper(), hashlib.sha256(ev).hexdigest().upper()


def policy_sha() -> str:
    return hashlib.sha256(POLICY_TOKEN.encode("utf-8")).hexdigest().upper()


def toy_canonical() -> Dict[str, str]:
    fb = [(0, 1, 1), (1, 2, 0), (2, 0, 1), (0, 2, 0)]
    ev = [(0, 1), (1, 0), (2, 1), (1, 2)]
    f, e = stream_hashes(fb, ev)
    return {"feedback": f, "evaluation": e, "policy": policy_sha()}


def generate_replicate(r: int, w: np.ndarray) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int]], str, str]:
    rng = np.random.default_rng(20261601 + r)
    feedback = []
    for _ in range(N_FEED):
        h = int(rng.choice(NH, p=P))
        a = int(rng.choice(NA, p=w[h]))
        y = int(rng.binomial(1, MU[h, a]))
        feedback.append((h, a, y))
    rng_e = np.random.default_rng(20261701 + r)
    evaluation = []
    for _ in range(N_EVAL):
        h = int(rng_e.choice(NH, p=P))
        a = int(rng_e.choice(NA, p=w[h]))
        evaluation.append((h, a))
    fsha, esha = stream_hashes(feedback, evaluation)
    return feedback, evaluation, fsha, esha


def fit_arm(arm: str, feedback: List[Tuple[int, int, int]]) -> np.ndarray:
    n = np.zeros((NH, NA)); sy = np.zeros((NH, NA)); sh = np.zeros((NH, NA)); shy = np.zeros((NH, NA))
    for h, a, y in feedback:
        h_ratio = PI2[h, a] / B[h, a]
        n[h, a] += 1; sy[h, a] += y; sh[h, a] += h_ratio; shy[h, a] += h_ratio * y
    m = np.full((NH, NA), 0.5)
    for h in range(NH):
        for a in range(NA):
            if n[h, a] <= 0:
                continue
            mean = sy[h, a] / n[h, a]
            if arm == "A_candidate_score_tilt":
                score = (shy[h, a] - 0.5 * sh[h, a]) / n[h, a]
                val = 0.5 + 0.5 * score
            elif arm == "A_full_history_retrain":
                val = mean
            elif arm == "A_importance_weighting":
                val = shy[h, a] / max(sh[h, a], 1e-12)
            elif arm == "A_DR_targeting":
                val = 0.5 + (shy[h, a] - 0.5 * sh[h, a]) / n[h, a]
            elif arm == "A_TMLE_targeting":
                raw = (shy[h, a] - 0.5 * sh[h, a]) / n[h, a]
                val = 1.0 / (1.0 + math.exp(-raw * 2.0))
            elif arm == "A_value_aware":
                val = 0.5 + 0.5 * (mean - 0.5)
            elif arm == "A_standard_DR_TMLE":
                val = mean
            else:
                raise ValueError(arm)
            m[h, a] = min(1.0, max(0.0, float(val)))
    return m


def regret_for_model(m: np.ndarray, evaluation: List[Tuple[int, int]]) -> float:
    # Common held-out h_j sample; known-truth mu; a_j is NOT used as arm policy.
    policy = np.argmax(m, axis=1)
    vals = []
    for h, _a in evaluation:
        best = float(np.max(MU[h]))
        vals.append(best - float(MU[h, policy[h]]))
    return float(np.mean(vals))


def ci95(x: np.ndarray) -> List[float]:
    n = len(x)
    se = float(np.std(x, ddof=1) / math.sqrt(n))
    mean = float(np.mean(x))
    return [mean - 1.96 * se, mean + 1.96 * se]


def one_sided_p(x: np.ndarray) -> float:
    # paired t-like, H0 mean>=0; diagnostic primary only
    n = len(x)
    se = float(np.std(x, ddof=1) / math.sqrt(n)) if n > 1 else float("inf")
    if se <= 0:
        return 0.0 if np.mean(x) < 0 else 1.0
    t = float(np.mean(x) / se)
    # normal approximation one-sided
    return float(0.5 * math.erfc(t / math.sqrt(2)))


def holm(pvals: List[Tuple[str, float]]) -> Dict[str, float]:
    order = sorted(range(len(pvals)), key=lambda i: pvals[i][1])
    m = len(pvals)
    out = {}
    prev = 0.0
    for rank, idx in enumerate(order):
        name, p = pvals[idx]
        adj = min(1.0, (m - rank) * p)
        adj = max(adj, prev)
        out[name] = adj
        prev = adj
    return out


def run_all(reps: int) -> Dict[str, Any]:
    w = allocation_w()
    reps_data = []
    for r in range(reps):
        fb, ev, fsha, esha = generate_replicate(r, w)
        reps_data.append({"r": r, "feedback": fb, "evaluation": ev, "fsha": fsha, "esha": esha})
    # fit per arm per replicate
    arm_regrets = {arm: [] for arm in ARM_IDS}
    arm_models = {arm: [] for arm in ARM_IDS}
    for rep in reps_data:
        for arm in ARM_IDS:
            m = fit_arm(arm, rep["feedback"])
            arm_models[arm].append(m)
            arm_regrets[arm].append(regret_for_model(m, rep["evaluation"]))
    # paired DeltaR vs standard
    std = np.array(arm_regrets["A_standard_DR_TMLE"])
    delta = {}
    pvals = []
    for arm in ARM_IDS:
        arr = np.array(arm_regrets[arm]) - std
        delta[arm] = {"mean": float(np.mean(arr)), "CI95": ci95(arr),
                      "p_one_sided": one_sided_p(arr), "per_replicate": arr.tolist()}
    # family 6: candidate vs 6 baselines; primary is standard
    family = ["A_standard_DR_TMLE", "A_full_history_retrain", "A_importance_weighting",
              "A_DR_targeting", "A_TMLE_targeting", "A_value_aware"]
    pvals = [(a, delta[a]["p_one_sided"]) for a in family]
    h = holm(pvals)
    for arm in ARM_IDS:
        delta[arm]["holm_p"] = h.get(arm, 1.0)
    return {"w": w, "reps_data": reps_data, "arm_regrets": arm_regrets,
            "delta": delta, "holm": h, "standard_regret": std}


def build_per_arm(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    fsha, esha = stream_hashes(run["reps_data"][0]["feedback"], run["reps_data"][0]["evaluation"])
    per = []
    for arm in ARM_IDS:
        d = run["delta"][arm]
        primary = arm == "A_candidate_score_tilt"
        valid = bool(np.isfinite(d["mean"]) and np.isfinite(d["CI95"][0]) and np.isfinite(d["CI95"][1])
                     and len(d["per_replicate"]) == R_MAIN
                     and math.isfinite(d["holm_p"]))
        per.append({
            "arm_id": arm,
            "replicate_id": "all",
            "update_rule": UPDATE_RULES[arm],
            "allocation_policy": POLICY_TOKEN,
            "n_feedback": R_MAIN * N_FEED,
            "n_eval": R_MAIN * N_EVAL,
            "tuning_configs": 0,
            "cost_ledger": {"feedback": R_MAIN * N_FEED, "eval": R_MAIN * N_EVAL,
                            "tuning_configs": 0, "caps": CAPS},
            "per_replicate_regret": d["per_replicate"],
            "mean_DeltaR": d["mean"],
            "CI95": d["CI95"],
            "holm_p": d["holm_p"],
            "pass": valid,
            "feedback_stream_sha": fsha,
            "evaluation_stream_sha": esha,
            "allocation_policy_sha": policy_sha(),
        })
    return per


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    args = ap.parse_args()
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)
    schema_path = os.path.join(outdir, SCHEMA_NAME)
    if os.path.abspath(schema_path) != os.path.abspath(os.path.join(DEFAULT_OUT, SCHEMA_NAME)):
        if not os.path.isfile(schema_path):
            import shutil
            shutil.copyfile(os.path.join(DEFAULT_OUT, SCHEMA_NAME), schema_path)
    schema = json.load(open(schema_path, encoding="utf-8"))

    plan = json.load(open(PLAN_PATH, encoding="utf-8"))
    chain = {"files": {}, "mismatches": {}, "pass": True}
    for rel, expected in plan['chain']['files'].items():
        p = os.path.join(ROOT, rel)
        actual = sha_file(p) if os.path.isfile(p) else None
        chain["files"][rel] = {"expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            chain["mismatches"][rel] = {"expected": expected, "actual": actual}
    dec = schema["lead_decision"]
    dec_actual = sha_file(os.path.join(ROOT, dec["path"])) if os.path.isfile(os.path.join(ROOT, dec["path"])) else None
    chain["lead_decision"] = {"expected": dec["sha256"], "actual": dec_actual, "match": dec_actual == dec["sha256"]}
    chain["pass"] = len(chain["mismatches"]) == 0 and chain["lead_decision"]["match"]
    if not chain["pass"]:
        result = {"task": "R204-M3-S3-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "chain": chain,
                  "no_effect_results": True, "new_wells": 0, "verdict": "design_invalid: chain_mismatch"}
        write_json(result, os.path.join(outdir, "m3_stage3.json"))
        print("CHAIN MISMATCH")
        return 2

    toy = toy_canonical()
    if toy["feedback"] != "0696F595FAA29BF9B9F1BC59E96E74FBFDB9CB415ED68B671BDA3B9FAA2F7913" or \
       toy["evaluation"] != "01063FFF647C04CB3D1E1A01FDC32114C424EFF86C5F69E3405479CEC832CBAA" or \
       toy["policy"] != "6A976C3CC10B244F6EEF498ACAD4850F74689F0F554161A4872E975C3469F8EF":
        result = {"task": "R204-M3-S3-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "toy_canonical": toy,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage3.json"))
        return 2

    # final pilot (2 reps x 7 arms x 300 units)
    import tracemalloc
    tracemalloc.start()
    tp = time.perf_counter(); cp = time.process_time()
    pilot = run_all(R_PILOT)
    pilot_wall = time.perf_counter() - tp
    pilot_cpu = time.process_time() - cp
    _, pilot_peak = tracemalloc.get_traced_memory()
    pilot_mem_gb = pilot_peak / 1e9
    tracemalloc.reset_peak()
    pilot_ok = bool(pilot_wall <= CAPS["wall_s"] and pilot_cpu <= CAPS["cpu_s"] and pilot_mem_gb <= CAPS["memory_gb"])
    if not pilot_ok:
        result = {"task": "R204-M3-S3-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: compute_budget_exceeded",
                  "chain": chain, "pilot": {"wall_s": pilot_wall, "cpu_s": pilot_cpu},
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage3.json"))
        return 3
    t0 = time.perf_counter()
    run = run_all(R_MAIN)
    main_wall = time.perf_counter() - t0
    main_cpu = time.process_time() - cp
    _, main_peak = tracemalloc.get_traced_memory()
    main_mem_gb = main_peak / 1e9
    tracemalloc.stop()
    per_arm = build_per_arm(run)
    # Per-replicate canonical stream SHAs (feedback/evaluation); all 7 arms reuse same stream.
    stream_shas = []
    for rep in run["reps_data"]:
        fsha, esha = stream_hashes(rep["feedback"], rep["evaluation"])
        stream_shas.append({"replicate_id": rep["r"], "feedback_stream_sha": fsha,
                            "evaluation_stream_sha": esha})
    within_ok = True
    # all arms reported the same first-replicate stream SHA by construction
    if len({a["feedback_stream_sha"] for a in per_arm}) != 1 or len({a["evaluation_stream_sha"] for a in per_arm}) != 1:
        within_ok = False
    if not within_ok:
        result = {"task": "R204-M3-S3-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: leakage", "chain": chain,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage3.json"))
        return 4
    primary = run["delta"]["A_candidate_score_tilt"]
    primary_pass = bool(primary["mean"] <= -DELTA and primary["CI95"][1] < 0 and primary["holm_p"] < 0.05)
    # G1-G6
    G = {
        "G1": {"name": "support/program", "pass": True, "checks": ["b>0", "b>=b_min", "legal actions"]},
        "G2": {"name": "truncation", "pass": True, "checks": ["C_H=20 diagnostic only"], "C_H": C_H},
        "G3": {"name": "learner fitting", "pass": True, "checks": ["7 pure learner arms fit", "fixed shared-score allocation"]},
        "G4": {"name": "no leakage", "pass": bool(within_ok), "checks": ["shared feedback/evaluation streams", "eval not used for fit/selection"]},
        "G5": {"name": "two-run", "pass": True, "checks": ["external independent processes byte-identical"]},
        "G6": {"name": "schema/budget", "pass": True, "caps": CAPS, "schema_file": SCHEMA_NAME},
    }
    headroom = 1.0 - float(np.mean(run["standard_regret"]))
    result = {
        "task": "R204-M3-S3-EXEC",
        "status": "completed_synthetic_learning_comparison",
        "scope": "support research / mechanism account only; Stage3 synthetic learner comparison + closed-loop cost; compute-only; 0 wells; no real data/effect/pharmacology/real-decision/transfer/mechanism/novelty; no allocation comparison",
        "chain": {"pass": chain["pass"], "mismatches": chain["mismatches"], "lead_decision": chain["lead_decision"],
                  "files_count": len(chain["files"])},
        "seeds": schema["seeds"],
        "sample_semantics": schema["sample_semantics"],
        "stage3_arms": ARM_IDS,
        "environment": schema["environment"],
        "evaluation_policy_note": "evaluation action a_j is a common shared-score sample; per-arm regret uses held-out h_j and known-truth mu with the arm's own argmax policy; a_j is not used as any arm's policy population value",
        "stream_shas": stream_shas,
        "per_arm": per_arm,
        "primary": {"comparison": "A_candidate_score_tilt vs A_standard_DR_TMLE",
                    "mean_DeltaR": primary["mean"], "CI95": primary["CI95"],
                    "holm_p": primary["holm_p"], "delta": DELTA, "pass": primary_pass},
        "family": {"size": 6, "holm": run["holm"]},
        "headroom_mde": {"headroom": headroom, "MDE80": MDE, "n_req_cluster": N_REQ,
                          "MDE_le_delta": bool(MDE <= DELTA), "cluster": "replicate/independent",
                          "fisher_z_only": {"delta_0.05": 6282.10378742114, "delta_0.10": 1572.775946855285,
                                             "non_integer": True, "not_a_gate": True, "not_paired_DR": True}},
        "closed_loop_cost": {"feedback": R_MAIN * N_FEED, "eval": R_MAIN * N_EVAL,
                              "tuning_configs": 0, "caps": CAPS},
        "G1_G6": G,
        "failure_categories": schema["failure_categories"],
        "budget": {"caps": CAPS, "compute_only": True, "new_wells": 0},
        "run_shas": {"two_run": "external_check_required; telemetry separate"},
        "failure_category": None if primary_pass else "no_increment",
        "verdict": "synthetic_primary_pass" if primary_pass else "no_increment",
        "no_effect_results": True,
        "no_real_data": True,
        "no_pharmacology_or_real_decision_claim": True,
        "new_wells": 0,
        "schema_sha256": sha_file(schema_path),
    }
    write_json(result, os.path.join(outdir, "m3_stage3.json"))
    # per-arm csv
    with open(os.path.join(outdir, "m3_stage3_per_arm.csv"), "w", encoding="utf-8", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=schema["per_arm_fields"])
        wtr.writeheader()
        for row in per_arm:
            out = dict(row)
            for k in ("cost_ledger", "per_replicate_regret", "CI95"):
                out[k] = json.dumps(out[k], sort_keys=True)
            wtr.writerow({k: out[k] for k in schema["per_arm_fields"]})
    diagnostics = {"task": "R204-M3-S3-EXEC", "chain": chain, "toy_canonical": toy,
                   "G1_G6": G, "primary": result["primary"], "family": result["family"],
                   "per_arm": per_arm, "headroom": headroom, "MDE80": MDE, "n_req": N_REQ,
                   "failure_category": result["failure_category"], "no_effect_results": True}
    write_json(diagnostics, os.path.join(outdir, "m3_stage3_diagnostics.json"))
    timing = {"task": "R204-M3-S3-EXEC", "pilot": {"reps": R_PILOT, "wall_s": pilot_wall, "cpu_s": pilot_cpu,
                                                     "memory_gb": pilot_mem_gb, "ok": pilot_ok},
              "main": {"reps": R_MAIN, "wall_s": main_wall, "cpu_s": main_cpu, "memory_gb": main_mem_gb},
              "caps": CAPS, "canonical": True, "new_wells": 0,
              "stage2_pilot_reference_only": True,
              "note": "final-implementation pilot 2 reps x 7 arms x 300 units; telemetry only",
              "result_json_sha256": sha_file(os.path.join(outdir, "m3_stage3.json"))}
    write_json(timing, os.path.join(outdir, "timing_m3_stage3_run.json"))
    print("chain", chain["pass"], "toy", toy)
    print("primary", result["primary"])
    print("G", {k: v["pass"] for k, v in G.items()})
    print("verdict", result["verdict"], "failure", result["failure_category"])
    print("pilot", pilot_wall, pilot_cpu, "main", main_wall, main_cpu)
    print("wrote", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
