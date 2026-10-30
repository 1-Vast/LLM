"""Recount saved artifacts and hashes only; no experiment imports or execution."""
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\MAESTRO")
HERE = Path(__file__).resolve().parent
M1 = ROOT / "research/2026-10-28-m1-stage2-rerun"
DIAG = ROOT / "research/2026-10-28-m1-stage2-fail-diag"
M3 = ROOT / "research/2026-10-28-m3-stage3-exec-prereg"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def check_chain(expected):
    mismatches = []
    for rel, want in expected.items():
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT / "research") or "sealed" in str(path).lower():
            raise ValueError("Out-of-scope chain path")
        actual = sha(path) if path.is_file() else None
        if actual != want.upper():
            mismatches.append({"path": rel, "expected": want, "actual": actual})
    return {"count": len(expected), "mismatches": mismatches, "all_match": not mismatches}


inventory = []
for folder in (M1, DIAG, M3):
    for path in sorted(folder.iterdir()):
        if path.is_file():
            st = path.stat()
            inventory.append({"path": path.relative_to(ROOT).as_posix(), "bytes": st.st_size,
                              "mtime_local": datetime.fromtimestamp(st.st_mtime).isoformat(), "sha256": sha(path)})
h = read(M1 / "m1_stage2_rerun.json")
d = read(DIAG / "diag_m1_s2.json")
p = read(M3 / "exec_plan_m3_s3_v0_2.json")
s = read(M3 / "schema_m3_s3_exec_v0_2.json")
u = read(DIAG / "usage_diag_m1_s2.json")
rows = d["rows"]
table = {(r["dimension"], r["N"]): r for r in h["H1"]}
with (M1 / "m1_stage2_rerun_checks.csv").open(encoding="utf-8", newline="") as f:
    checks = list(csv.DictReader(f))
csv_h1 = [r for r in checks if r["gate"] == "H1"]
arms = p["stage3"]["arms"]
prec = p["precision_headroom"]
result = {
    "audit_time_local": datetime.now().astimezone().isoformat(), "python": sys.executable,
    "effective_model": "unknown", "effective_effort": "unknown",
    "scope": "saved JSON/CSV counts, arithmetic and file hashes only; no training/simulation/network/server",
    "inventory": inventory,
    "M1": {"verdict": h["verdict"], "H1_cells": len(h["H1"]),
           "H1_recomputed_pass": sum(r["TV_256bin"] <= r["tolerance"] for r in h["H1"]),
           "H1_flags_consistent": all(r["pass"] == (r["TV_256bin"] <= r["tolerance"]) for r in h["H1"]),
           "H1_CSV_match": len(csv_h1) == 16 and all(abs(float(r["value"]) - table[(int(r["dimension_or_epsilon"]), int(r["N_or_blank"]))]["TV_256bin"]) < 1e-9 for r in csv_h1),
           "H2_converged": sum(r["converged"] for r in h["H2"]),
           "H2_max_error": max(r["max_marginal_error"] for r in h["H2"]), "H3": h["H3"],
           "chain": check_chain(h["chain"]["chain_files"])},
    "diagnostic": {
        "source_C216_sha_match": sha(M1 / "m1_stage2_rerun.json") == d["C216"]["sha256"],
        "usage_hashes_match": {name: sha(DIAG / name) == want for name, want in u["artifacts_sha256"].items() if (DIAG / name).is_file()},
        "category_counts": dict(Counter(r["category"] for r in rows)),
        "floor_MC_q95_ge_tol": sum(r["floor_MC_TV"]["q95"] >= r["tolerance"] for r in rows),
        "oracle_mean_gt_tol": sum(r["oracle_true_vs_true_TV"]["mean"] > r["tolerance"] for r in rows),
        "oracle_q95_ge_tol": sum(r["oracle_true_vs_true_TV"]["q95"] >= r["tolerance"] for r in rows),
        "oracle_q05_gt_tol": sum(r["oracle_true_vs_true_TV"]["q05"] > r["tolerance"] for r in rows),
        "cmdn_gt_oracle_q95": sum(r["C_MDN_TV_C216"] > r["oracle_true_vs_true_TV"]["q95"] for r in rows),
        "cmdn_gt_oracle_mean": sum(r["C_MDN_TV_C216"] > r["oracle_true_vs_true_TV"]["mean"] for r in rows),
        "max_C216_value_difference": max(abs(r["C_MDN_TV_C216"] - table[(r["dimension"], r["N"])]["TV_256bin"]) for r in rows),
        "distinct_dimension_oracle_summaries": len({(r["dimension"], r["oracle_mean_TV"]) for r in rows}),
        "capacity_improved": sum(r["delta_TV"] < 0 for r in d["capacity_sensitivity"]),
        "capacity_worsened": sum(r["delta_TV"] > 0 for r in d["capacity_sensitivity"]),
        "capacity_delta_median": statistics.median(r["delta_TV"] for r in d["capacity_sensitivity"]),
        "fidelity_caveats_gt_0_005": [r for r in d["fidelity_check"] if abs(r["delta_TV"]) > 0.005],
        "per_cell": [{"d": r["dimension"], "N": r["N"], "tol": r["tolerance"], "cmdn": r["C_MDN_TV_C216"], "oracle": r["oracle_true_vs_true_TV"], "floor_MC": r["floor_MC_TV"]} for r in rows]},
    "M3": {"status": p["status"], "stage3_status": p["stage3"]["status"], "arms": len(arms),
           "family": len(p["endpoints"]["family"]), "same_allocation_policy": len({a["allocation_policy"] for a in arms}) == 1,
           "optimal_allocation_arm_ids": [a["id"] for a in arms if "optimal_allocation" in a["id"]],
           "schema_missing_stream_fields": [f for f in ("feedback_stream_sha", "evaluation_stream_sha") if f not in s["arm_fields"]],
           "per_arm_stream_hash_fields_present": all(all(f in a for f in ("feedback_stream_sha", "evaluation_stream_sha")) for a in arms),
           "stale_optimal_allocation_boundary": [x for x in p["stop_boundaries"] if "optimal allocation" in x],
           "schema_file_in_plan": p["schema_file"], "actual_schema": "schema_m3_s3_exec_v0_2.json",
           "mde_saved": prec["MDE80_conservative"], "mde_arithmetic": 2.801585 * prec["conservative_SD_D"] / math.sqrt(prec["n_eff_conservative"]),
           "chain": check_chain(p["frozen_inputs"]), "no_training_or_comparison_executed": p["no_training_or_comparison_executed"]}}
out = HERE / "latest_other_agent_audit_counts.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
result.pop("inventory")
result["diagnostic"].pop("per_cell")
print(json.dumps(result, ensure_ascii=False, indent=2))
