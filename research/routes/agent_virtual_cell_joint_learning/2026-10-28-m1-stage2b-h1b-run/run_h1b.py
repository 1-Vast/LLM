#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-H1B-EXEC: measurable hash-bin TV measurement (new separate protocol).

Mechanism account only; compute-only; 0 wells. Old C216/C217 unchanged. No effect/
decision/pharmacology/transfer/mechanism/novelty claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from typing import Any, Dict, List

import numpy as np

ROOT = r"D:\MAESTRO"
HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(ROOT, "research", "2026-10-28-m1-stage2b-h1b-prereg")
RERUN = os.path.join(ROOT, "research", "2026-10-28-m1-stage2-rerun")
DEFAULT_OUT = HERE
SCHEMA = os.path.join(HERE, "schema_h1b_run.json")
CAPS = {"wall_s": 1800.0, "cpu_s": 7200.0, "memory_gb": 8.0, "new_wells": 0}
B = 16
N_EVAL = 32768
K_MEAS = 1
DIMS = [8, 16, 32, 64]
NS = [512, 1024, 2048, 4096]
TOL = {8: 0.049, 16: 0.050, 32: 0.049, 64: 0.048}
DATA_SEED = 20261811
EVAL_SEED = 20261812
CELL_SEEDS = [20261821 + i for i in range(16)]
PARAM_SEED = 20261301
FLOOR_Q95 = {8: 0.01642609, 16: 0.01642609, 32: 0.01642609, 64: 0.01642609}

sys.path.insert(0, RERUN)
import run_m1_stage2_rerun as base  # noqa: E402


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj: Any, p: str) -> None:
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def hash_cells(Y: np.ndarray) -> np.ndarray:
    q = np.floor((np.asarray(Y, dtype=float) + 2.0) / 4.0 * 256.0)
    q = np.clip(q, 0, 255).astype(np.int64)
    code = q[:, 0] + 256 * q[:, 1] + 65536 * q[:, 2] + 16777216 * q[:, 3]
    return code % B


def hash_tv(Ya: np.ndarray, Yb: np.ndarray) -> float:
    ca = np.bincount(hash_cells(Ya), minlength=B) / len(Ya)
    cb = np.bincount(hash_cells(Yb), minlength=B) / len(Yb)
    return float(0.5 * np.abs(ca - cb).sum())


def run_cell(d: int, n_train: int, cell_seed: int) -> Dict[str, Any]:
    theta = base.PTheta(PARAM_SEED)
    rng_data = np.random.default_rng(DATA_SEED)
    Xtr = rng_data.normal(size=(n_train, d))
    Atr = np.zeros(n_train, dtype=np.int64)
    Ytr = np.array([theta.sample_y(Xtr[i], 0, rng_data) for i in range(n_train)])
    model = base.fit_mdn(Xtr, Atr, Ytr, seed=cell_seed, epochs=200, n_actions=4, y_dim=4)
    rng_eval = np.random.default_rng(EVAL_SEED)
    Xev = rng_eval.normal(size=(N_EVAL, d))
    Aev = np.zeros(N_EVAL, dtype=np.int64)
    Ycand = base.sample_mdn(model, Xev, Aev, seed=cell_seed + 1)
    Yora = np.array([theta.sample_y(Xev[i], 0, rng_eval) for i in range(N_EVAL)])
    tv = hash_tv(Ycand, Yora)
    tol = TOL[d]
    return {"d": d, "N_train": n_train, "TV_h1b": tv, "tolerance": tol,
            "pass": bool(tv <= tol), "n_eval": N_EVAL, "K": K_MEAS, "B": B,
            "cell_seed": cell_seed, "floor_q95": FLOOR_Q95[d]}


def run_all() -> List[Dict[str, Any]]:
    rows = []
    idx = 0
    for d in DIMS:
        for n_train in NS:
            rows.append(run_cell(d, n_train, CELL_SEEDS[idx]))
            idx += 1
    return rows


def main() -> int:
    t0 = time.perf_counter()
    if not os.path.exists(SCHEMA):
        raise SystemExit("schema missing")
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    chain = {"files": {}, "mismatches": {}, "lead_decision": {}}
    for group in ("h1b", "c215_c216_c217"):
        for rel, exp in schema["chain"][group].items():
            p = os.path.join(ROOT, rel)
            actual = sha_file(p) if os.path.exists(p) else None
            chain["files"][rel] = {"expected": exp, "actual": actual, "match": actual == exp}
            if actual != exp:
                chain["mismatches"][rel] = {"expected": exp, "actual": actual}
    ld = schema["chain"]["lead_decision"]
    lp = os.path.join(ROOT, ld["path"])
    la = sha_file(lp) if os.path.exists(lp) else None
    chain["lead_decision"] = {"expected": ld["sha256"], "actual": la, "match": la == ld["sha256"]}
    chain["pass"] = len(chain["mismatches"]) == 0 and chain["lead_decision"]["match"]
    if not chain["pass"]:
        result = {"task": "R204-M1-H1B-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "chain": chain,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(HERE, "h1b_result.json"))
        print("CHAIN MISMATCH")
        return 2

    # final-implementation pilot: full 16 cells
    tp = time.perf_counter(); cp = time.process_time()
    pilot_rows = run_all()
    pilot_wall = time.perf_counter() - tp
    pilot_cpu = time.process_time() - cp
    try:
        import psutil
        pilot_mem = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        pilot_mem = 0.0
    pilot_ok = bool(pilot_wall <= CAPS["wall_s"] and pilot_cpu <= CAPS["cpu_s"] and pilot_mem <= CAPS["memory_gb"])
    if not pilot_ok:
        result = {"task": "R204-M1-H1B-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: compute_budget_exceeded",
                  "chain": chain, "pilot": {"wall_s": pilot_wall, "cpu_s": pilot_cpu, "memory_gb": pilot_mem},
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(HERE, "h1b_result.json"))
        return 3
    t = time.perf_counter()
    cells = run_all()
    main_wall = time.perf_counter() - t
    main_cpu = time.process_time() - cp
    try:
        import psutil
        main_mem = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        main_mem = 0.0
    all_pass = all(c["pass"] for c in cells)
    result = {
        "task": "R204-M1-H1B-EXEC",
        "status": "completed_h1b_measurement" if all_pass else "design_invalid",
        "scope": "mechanism account only; H1b measurable-TV measurement; compute-only; 0 wells; no effect/decision/pharmacology/transfer/mechanism/novelty",
        "old_protocol_unchanged": schema["old_protocol_unchanged"],
        "chain": {"pass": chain["pass"], "mismatches": chain["mismatches"],
                  "lead_decision": chain["lead_decision"]},
        "selected_measurement": schema["measurement"],
        "tolerance_table": schema["tolerance_table"],
        "H1b_grid": schema["H1b_grid"],
        "cells": cells,
        "H1b_all_pass": all_pass,
        "failure_category": None if all_pass else "design_invalid: projection",
        "verdict": "h1b_measurement_pass" if all_pass else "design_invalid: projection",
        "caps": CAPS,
        "no_effect_results": True,
        "no_decision_utility_or_regret": True,
        "no_method_comparison": True,
        "no_real_data": True,
        "old_C216_C217_modified": False,
        "new_wells": 0,
        "schema_sha256": sha_file(SCHEMA),
    }
    write_json(result, os.path.join(HERE, "h1b_result.json"))
    with open(os.path.join(HERE, "h1b_cells.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("d,N_train,TV_h1b,tolerance,pass,n_eval,K,B,cell_seed,floor_q95\n")
        for c in cells:
            fh.write(f"{c['d']},{c['N_train']},{c['TV_h1b']:.10f},{c['tolerance']},{c['pass']},"
                     f"{c['n_eval']},{c['K']},{c['B']},{c['cell_seed']},{c['floor_q95']}\n")
    diag = {"task": "R204-M1-H1B-EXEC", "chain": chain, "cells": cells,
            "H1b_all_pass": all_pass, "failure_category": result["failure_category"],
            "old_protocol_unchanged": schema["old_protocol_unchanged"],
            "no_effect_results": True}
    write_json(diag, os.path.join(HERE, "h1b_diagnostics.json"))
    timing = {"task": "R204-M1-H1B-EXEC", "pilot": {"cells": 16, "wall_s": pilot_wall, "cpu_s": pilot_cpu,
                                                     "memory_gb": pilot_mem, "ok": pilot_ok},
              "main": {"cells": 16, "wall_s": main_wall, "cpu_s": main_cpu, "memory_gb": main_mem},
              "caps": CAPS, "canonical": True, "wells": 0,
              "note": "final implementation pilot 16 cells (C-MDN training + N_eval 32768 + oracle); telemetry only",
              "result_sha256": sha_file(os.path.join(HERE, "h1b_result.json"))}
    write_json(timing, os.path.join(HERE, "timing_h1b_run.json"))
    print("chain", chain["pass"], "all_pass", all_pass, "failure", result["failure_category"])
    print("pilot", pilot_wall, pilot_cpu, pilot_mem, "main", main_wall, main_cpu, main_mem)
    print("cells", [(c["d"], c["N_train"], round(c["TV_h1b"], 6), c["pass"]) for c in cells])
    print("result_sha", sha_file(os.path.join(HERE, "h1b_result.json")))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
