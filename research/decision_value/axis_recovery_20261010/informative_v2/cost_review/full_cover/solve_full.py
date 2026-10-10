"""Canonical minimum full-hint multicover under a pre-read budget amendment."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
COST_REVIEW = HERE.parent
PLAN = COST_REVIEW.parent
BASE = PLAN.parent
sys.path.insert(0, str(COST_REVIEW))
from solve import optimize


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (HERE / "FREEZE.json").exists():
        raise FileExistsError("Full-cover planning already frozen")
    pool = sorted(read(PLAN / "CANDIDATE_POOL.json"), key=lambda c: (c["file"], c["label"]))
    prior = read(PLAN / "SELECTION.json")
    deficits = prior["initial_index_deficits_to_three"]
    requirements = [(f, g, d) for f, genes in deficits.items() for g, d in genes.items() if d > 0]
    pool = [c for c in pool if any(c["file"] == f and c["all39_named_deltas"][g] > 0 for f, g, d in requirements)]
    n = len(pool)
    costs = np.array([c["index_screen_bytes"] for c in pool], dtype=np.int64)
    cover = np.array([[int(c["file"] == f and c["all39_named_deltas"][g] > 0) for c in pool] for f, g, d in requirements])
    file_counts = np.array([[int(c["file"] == f) for c in pool] for f in deficits])
    matrix = np.concatenate([cover, file_counts])
    lower = np.array([d for f, g, d in requirements]+[0]*len(deficits))
    upper = np.array([np.inf]*len(requirements)+[8]*len(deficits))
    decision, primary = optimize(costs, matrix, lower, upper, np.zeros(n), np.ones(n))
    assert decision is not None
    minimum = int(costs @ decision)
    assert minimum == 10_652_056 <= 11_000_000
    canonical_matrix = np.concatenate([matrix, costs[None, :]])
    canonical_low, canonical_high = np.append(lower, minimum), np.append(upper, minimum)
    lows, highs = np.zeros(n), np.ones(n)
    receipts = [{"stage": "minimum_full_hint_cost", **primary}]
    for i in range(n):
        if decision[i] == 1:
            lows[i] = highs[i] = 1
            continue
        trial = lows.copy()
        trial[i] = 1
        alternate, receipt = optimize(np.zeros(n), canonical_matrix, canonical_low, canonical_high, trial, highs)
        receipts.append({"stage": "lexicographic_binary_tie", "candidate": i, **receipt})
        if alternate is None:
            lows[i] = highs[i] = 0
        else:
            lows[i] = highs[i] = 1
            decision = alternate
    assert np.array_equal(decision, lows.astype(int))
    selected = [dict(c, rank=i+1) for i, c in enumerate(c for c, bit in zip(pool, decision) if bit)]
    result = {"schema": "canonical_full_hint_supplementary_selection_v1", "status": "FULL_HINT_COVER_FEASIBLE",
        "source_repo": "arcinstitute/State-Tahoe-Filtered", "source_revision": "fdf87abece385feea6fa5e9944ab46e173b6af50",
        "summary_revision": "c7963cf334bec0683225d41c9586d900ca6303a2", "source_inputs": prior["source_inputs"],
        "planning_amendment": "Beforeanysupplementaryindices, combinedcalibrationcap28MB replaces25MB; global60MBunchanged. Onefinite supplementaryscreen; acceptance/endpointunchanged.",
        "requirements": [{"file": f, "gene": g, "new_positive_hint_conditions_required": d,
                          "selected_positive_hint_conditions": int(cover[i] @ decision)} for i, (f,g,d) in enumerate(requirements)],
        "selection_rule": "Binaryfullpositivehintmulticover, <=8newconditions/file. Minimizeexact32bitCSRindexbytes; thenfixminimumintegercost andpreferbit1 wheneverfeasibleinascending(file,exactlabel)order.",
        "solver": "scipy.optimize.milp/HiGHS", "scipy_version": scipy.__version__, "mip_rel_gap": 0.0,
        "solver_receipts": receipts, "eligible_positive_candidate_count": n, "selected": selected,
        "new_conditions_per_file": {f: sum(c["file"]==f for c in selected) for f in deficits},
        "new_full_qc_index_cells": sum(c["full_qc_available"] for c in selected),
        "exact_new_index_payload_bytes": minimum, "new_index_payload_cap": 11_000_000,
        "prior_calibration_body_bytes": 12_397_900, "raw_values_and_HVG_reserve": 4_000_000,
        "metadata_and_error_body_cap": 102_100, "projected_total_with_reserves": 12_397_900+minimum+4_000_000+102_100,
        "calibration_total_body_cap": 28_000_000, "global_body_cap_unchanged": 60_000_000,
        "new_network_calls": 0, "new_index_reads": False, "all_hint_deficits_covered": True,
        "parent_review_required_before_indices": True, "paired_cell_cap_unchanged": 256,
        "scientific_boundary": "Namedpositiveconditionsarenotactualnonzerorates. Indexpresenceisnecessaryonly; dataaxisneedsuniquepairedvalues/holdoutperfile. Noprediction/agent/decisiongainorcheckpointcertificate.",
        "exposure_rule": "Alreadyconsultedplate1summaryunits excludedacrosspooledsamples; futureindices calibration-onlyexpressionpresence. Noindependentterminalvalidation."}
    assert result["projected_total_with_reserves"] == 27_152_056 <= 28_000_000
    (HERE / "SELECTION.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    deps = [PLAN / "FREEZE.json", PLAN / "CANDIDATE_POOL.json", PLAN / "SELECTION.json",
            COST_REVIEW / "solve.py", COST_REVIEW / "FREEZE.json", COST_REVIEW / "SELECTION.json",
            HERE / "solve_full.py", HERE / "SELECTION.json"]
    frozen = {"schema": "canonical_full_hint_pre_index_freeze_v1", "new_indices_read": False,
              "sha256": {p.relative_to(BASE).as_posix(): sha(p) for p in deps}}
    (HERE / "FREEZE.json").write_text(json.dumps(frozen, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "new_conditions_per_file", "new_full_qc_index_cells",
        "exact_new_index_payload_bytes", "projected_total_with_reserves", "all_hint_deficits_covered")}))


if __name__ == "__main__":
    main()
