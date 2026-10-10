"""Pre-index binary multicover planning; named positivity is only a hint."""
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
BASE = PARENT.parent
INDEX_CAP = 8_500_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def optimize(objective, matrix, lower, upper, bounds_low, bounds_high):
    result = milp(np.asarray(objective, dtype=float), integrality=np.ones(len(objective)),
        bounds=Bounds(bounds_low, bounds_high),
        constraints=LinearConstraint(matrix, lower, upper),
        options={"mip_rel_gap": 0.0, "time_limit": 60.0})
    if result.status not in (0, 2):
        raise RuntimeError(f"MILP did not settle: {result.status}: {result.message}")
    if result.status == 2:
        return None, {"status": 2, "message": result.message}
    decision = np.rint(result.x).astype(int)
    assert np.max(np.abs(result.x-decision)) < 1e-6
    total = matrix @ decision
    assert np.all(total >= lower-1e-6) and np.all(total <= upper+1e-6)
    assert np.all(decision >= bounds_low) and np.all(decision <= bounds_high)
    return decision, {"status": 0, "message": result.message, "mip_gap": float(result.mip_gap),
                      "objective": float(result.fun), "nodes": int(result.mip_node_count)}


def main():
    if (HERE / "FREEZE.json").exists():
        raise FileExistsError("Cost review already frozen")
    pool = sorted(read(PARENT / "CANDIDATE_POOL.json"), key=lambda c: (c["file"], c["label"]))
    earlier = read(PARENT / "SELECTION.json")
    deficits = earlier["initial_index_deficits_to_three"]
    requirements = [(file, gene, count) for file, genes in deficits.items() for gene, count in genes.items() if count > 0]
    pool = [c for c in pool if any(c["file"] == f and c["all39_named_deltas"][g] > 0 for f, g, d in requirements)]
    n = len(pool)
    cost = np.array([c["index_screen_bytes"] for c in pool], dtype=np.int64)
    cover = np.array([[int(c["file"] == file and c["all39_named_deltas"][gene] > 0)
                       for c in pool] for file, gene, count in requirements], dtype=np.int64)
    need = np.array([count for file, gene, count in requirements], dtype=np.int64)
    file_rows = np.array([[int(c["file"] == file) for c in pool] for file in deficits], dtype=np.int64)
    matrix = np.concatenate([cover, file_rows], axis=0)
    lower = np.concatenate([need, np.zeros(len(deficits))])
    upper = np.concatenate([np.full(len(need), np.inf), np.full(len(deficits), 8)])
    decision, primary = optimize(cost, matrix, lower, upper, np.zeros(n), np.ones(n))
    minimal_full_cost = int(cost @ decision) if decision is not None else None
    feasible = minimal_full_cost is not None and minimal_full_cost <= INDEX_CAP
    solve_receipts = [{"stage": "unbudgeted_minimum_full_hint_cover", **primary}]
    remaining = None
    if feasible:
        # Exact integer minimum cost, then a unique bit-vector in ascending file/label
        # order: prefer 1 whenever it can still complete a minimum-cost solution.
        canonical_matrix = np.concatenate([matrix, cost[None, :]], axis=0)
        canonical_lower = np.append(lower, minimal_full_cost)
        canonical_upper = np.append(upper, minimal_full_cost)
        bounds_low, bounds_high = np.zeros(n), np.ones(n)
        for i in range(n):
            if decision[i] == 1:
                bounds_low[i] = bounds_high[i] = 1
                continue
            trial_low = bounds_low.copy()
            trial_low[i] = 1
            alternate, receipt = optimize(np.zeros(n), canonical_matrix, canonical_lower,
                                          canonical_upper, trial_low, bounds_high)
            solve_receipts.append({"stage": "canonical_tie", "candidate": i, **receipt})
            if alternate is not None:
                bounds_low[i] = bounds_high[i] = 1
                decision = alternate
            else:
                bounds_low[i] = bounds_high[i] = 0
        assert np.array_equal(decision, bounds_low.astype(int))
        assert int(cost @ decision) == minimal_full_cost
    else:
        # If full coverage is unavailable, first minimize integer hint shortfall,
        # then minimize bytes at that shortfall. This still cannot certify rates.
        m = len(requirements)
        extended = np.concatenate([np.concatenate([cover, np.eye(m, dtype=int)], axis=1),
            np.concatenate([file_rows, np.zeros((len(deficits), m), dtype=int)], axis=1),
            np.concatenate([cost, np.zeros(m, dtype=int)])[None, :]], axis=0)
        extended_low = np.concatenate([need, np.zeros(len(deficits)), [0]])
        extended_high = np.concatenate([np.full(m, np.inf), np.full(len(deficits), 8), [INDEX_CAP]])
        bound_low = np.zeros(n+m)
        bound_high = np.concatenate([np.ones(n), need])
        objective = np.concatenate([np.zeros(n), np.ones(m)])
        partial, receipt = optimize(objective, extended, extended_low, extended_high, bound_low, bound_high)
        solve_receipts.append({"stage": "minimum_budgeted_hint_shortfall", **receipt})
        assert partial is not None
        shortage = int(partial[n:].sum())
        short_row = np.concatenate([np.zeros(n), np.ones(m)])[None, :]
        extended = np.concatenate([extended, short_row], axis=0)
        extended_low = np.append(extended_low, shortage)
        extended_high = np.append(extended_high, shortage)
        partial, receipt = optimize(np.concatenate([cost, np.zeros(m)]), extended,
            extended_low, extended_high, bound_low, bound_high)
        solve_receipts.append({"stage": "min_bytes_at_minimum_shortfall", **receipt})
        decision = partial[:n]
        remaining = {file: {gene: max(count-int(cover[i] @ decision), 0)
                    for i, (f, gene, count) in enumerate(requirements) if f == file} for file in deficits}
    selected = [dict(candidate, rank=i+1) for i, candidate in enumerate(c for c, bit in zip(pool, decision) if bit)]
    actual_cost = int(cost @ decision)
    actual_cover = cover @ decision
    if remaining is None:
        remaining = {file: {gene: max(count-int(actual_cover[i]), 0)
                    for i, (f, gene, count) in enumerate(requirements) if f == file} for file in deficits}
    result = {"schema": "pre_index_cost_minimum_hint_multicover_v1",
        "status": "FULL_HINT_COVER_FEASIBLE" if feasible else "BOUNDED_HINT_SHORTFALL_PANEL",
        "planning_amendment": "Before any supplementary indices: preserve original greedyfreeze and replace acquisitionproposal with costminimum binarynamedhintmulticover.",
        "source_repo": "arcinstitute/State-Tahoe-Filtered", "source_revision": "fdf87abece385feea6fa5e9944ab46e173b6af50",
        "summary_revision": "c7963cf334bec0683225d41c9586d900ca6303a2",
        "source_inputs": earlier["source_inputs"], "requirements": [{"file":f,"gene":g,"new_positive_hint_conditions_required":d} for f,g,d in requirements],
        "solver": "scipy.optimize.milp/HiGHS", "scipy_version": scipy.__version__, "mip_rel_gap": 0.0,
        "primary_objective": "Minimize exact32bitCSRindexpayloadbytes subjecttoallhintmulticoverand<=8conditions/file; compareminimumwith8.5MBcap.",
        "tie_rule": "Forfullcover, fixminimumintegerbytecost thenlexicographically preferbinary1 inascending(file,exactlabel)whenfeasible; unique bit-vector. Shortfallfallbackminimizestotalintegerdeficit thenbytecost andusesdeterministicHiGHSoutput; notcanonicalunderalternativeoptima.",
        "eligible_positive_candidate_count": n, "minimal_full_hint_cover_bytes": minimal_full_cost,
        "full_hint_cover_within_index_budget": feasible, "index_budget_bytes": INDEX_CAP,
        "selected": selected, "exact_new_index_payload_bytes": actual_cost,
        "new_conditions_per_file": {f:sum(c['file']==f for c in selected) for f in deficits},
        "new_full_qc_index_cells": sum(c["full_qc_available"] for c in selected),
        "remaining_hint_deficits": remaining,
        "prior_calibration_body_bytes": 12_397_900, "raw_values_and_HVG_reserve": 4_000_000,
        "metadata_and_error_body_cap": 102_100,
        "projected_total_with_reserves": 12_397_900+actual_cost+4_000_000+102_100,
        "calibration_body_cap": 25_000_000, "solver_receipts": solve_receipts,
        "new_network_calls": 0, "new_index_reads": False,
        "scientific_boundary": "Positive summaryhints arenotactualindex/valuenonzero guarantees. This planningoptimumdoesnotproveaxisidentity, biologicalresponse, decisiongain orinformationinfeasibility.",
        "exposure_rule": "All selectedunits alreadyplate1expressionexposed andexcludedacrosssharedpooledsamplelines; anyfreshindicesfurthercalibration-onlypresenceexposure.",
        "parent_review_required_before_indices": True}
    HERE.mkdir(exist_ok=True)
    (HERE / "SELECTION.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    freeze = {"schema": "pre_index_cost_review_freeze_v1", "new_indices_read": False,
        "sha256": {p.relative_to(BASE).as_posix(): digest(p) for p in
            (PARENT / "SELECTION.json", PARENT / "CANDIDATE_POOL.json", PARENT / "FREEZE.json", HERE / "solve.py", HERE / "SELECTION.json")}}
    (HERE / "FREEZE.json").write_text(json.dumps(freeze, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status", "minimal_full_hint_cover_bytes", "exact_new_index_payload_bytes",
        "new_conditions_per_file", "new_full_qc_index_cells", "remaining_hint_deficits", "projected_total_with_reserves")}))


if __name__ == "__main__":
    main()
