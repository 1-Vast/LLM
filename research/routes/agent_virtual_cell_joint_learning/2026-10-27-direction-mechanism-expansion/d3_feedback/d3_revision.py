#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200-D3.1 metadata-only revision / feasibility arithmetic.

Reads ONLY frozen ON2 metadata + ON2-EX calibration + ON3 peek disclosure metadata.
It does NOT read the O'Neil workbook, expression values, or viability responses, and
does NOT fit/predict/run any effect. It computes:
  - correct single-anchor mean-Delta MDE (8 wells/unit; SE=sigma/sqrt(2)),
  - rank-level MDE for the registered Spearman Delta-rho (Fisher-z conservative),
  - candidate aggregation/wells options and their simulated procurement costs,
  - the explicit feasibility ruling and failure tree.

Output: d3_v0_2.json
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ONEIL = os.path.abspath(os.path.join(HERE, "..", "..", "2026-10-27-core-module-design", "oneil_dev"))
ON2 = os.path.join(ONEIL, "on2.json")
CALIB = os.path.join(ONEIL, "exec_calibration", "calib.json")
PEEK = os.path.join(ONEIL, "PEEK_DISCLOSURE_ON3.md")
QUICK = os.path.join("tmp", "on3_exec_quick_debug.invalid.json")
OUT = os.path.join(HERE, "d3_v0_2.json")

Z80 = 2.8015852181
DELTA_MIN = 0.10
N_EFF_PER_FOLD = 6       # conservative: held-out cells/fold
N_EFF_POOLED = 30        # 5 folds x 6 held-out cells, pooled descriptive
K_FEEDBACK_UNITS_PER_FOLD = 24
PLATE_WELLS = 96
FAILURE_RESERVE = 0.10
N_FOLDS = 5
SIGMA_BATCH1_TARGET = 0.1384458171  # task-91 frozen ON2-EX batch1 target30 scope
SIGMA_ALL_BATCHES = 0.1422665081    # ON2-EX all-batches complete-case
SIGMA_FULL_GRID_FULL = 0.1422665081

# Candidate aggregation designs. wells_per_member counts technical wells per member
# used in the unit mean; wells_per_unit = 2 members * wells_per_member.
CANDIDATES = [
    {"id": "A_single_anchor_4rep", "label": "single anchor, 4 technical reps/member",
     "wells_per_member": 4, "wells_per_unit": 8, "n_eff": N_EFF_PER_FOLD,
     "question": "preserves D3 single-anchor question", "target_data_status": "existing 4 reps"},
    {"id": "B_single_anchor_4rep_pooled30", "label": "single anchor, 4 reps/member, pooled 30 cells",
     "wells_per_member": 4, "wells_per_unit": 8, "n_eff": N_EFF_POOLED,
     "question": "preserves D3 question; pooled 30 held-out cells", "target_data_status": "existing 4 reps"},
    {"id": "C_partner_average_16wells", "label": "anchor member dose, average 4 partner doses x 4 reps (16 wells/member)",
     "wells_per_member": 16, "wells_per_unit": 32, "n_eff": N_EFF_PER_FOLD,
     "question": "changes unit to partner-dose-averaged; not single anchor", "target_data_status": "existing 4 partner doses x 4 reps"},
    {"id": "D_full_grid_64wells", "label": "full 4x4 grid mean, 64 wells/member",
     "wells_per_member": 64, "wells_per_unit": 128, "n_eff": N_EFF_PER_FOLD,
     "question": "abandons single-anchor question", "target_data_status": "existing full grid"},
    {"id": "E_single_anchor_6rep", "label": "single anchor, 6 technical reps/member",
     "wells_per_member": 6, "wells_per_unit": 12, "n_eff": N_EFF_PER_FOLD,
     "question": "preserves D3 question; requires 2 new reps/member", "target_data_status": "new target/feedback wells required"},
    {"id": "F_full_grid_pooled30", "label": "full grid mean, pooled 30 cells",
     "wells_per_member": 64, "wells_per_unit": 128, "n_eff": N_EFF_POOLED,
     "question": "abandons single-anchor question; pooled", "target_data_status": "existing full grid"},
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def mean_mde(sigma: float, wells_per_member: int, n_eff: int) -> float:
    # delta unit variance = 2*sigma^2/wells_per_member; SE = sigma*sqrt(2/wells_per_member)
    se = sigma * math.sqrt(2.0 / float(wells_per_member))
    return Z80 * se / math.sqrt(float(n_eff))


def rank_mde_independent(n_eff: int) -> float:
    # Fisher-z conservative (independent model errors), difference of two correlations.
    if n_eff <= 4:
        return float("inf")
    return Z80 * math.sqrt(2.0 / float(n_eff - 3))


def rank_mde_paired(n_eff: int, r_err: float) -> float:
    if n_eff <= 4:
        return float("inf")
    return Z80 * math.sqrt(2.0 * (1.0 - r_err) / float(n_eff - 3))


def required_n_for_rank(delta: float) -> int:
    return int(math.ceil(3.0 + 2.0 * (Z80 / delta) ** 2))


def required_r_err_for_rank(n_eff: int, delta: float) -> float:
    return 1.0 - (delta ** 2 * (n_eff - 3)) / (2.0 * Z80 ** 2)


def procurement(wells_per_unit: int, k: int = K_FEEDBACK_UNITS_PER_FOLD) -> Dict[str, Any]:
    wells = wells_per_unit * k
    plates = wells / float(PLATE_WELLS)
    plate_eq = plates * (1.0 + FAILURE_RESERVE)
    return {
        "k_units_per_fold": k,
        "wells_per_fold": wells,
        "full_96_well_plates_per_fold": int(math.ceil(plates)),
        "plate_equivalents_per_fold_with_10pct_failure": round(plate_eq, 4),
        "plate_equivalents_total_5fold": round(plate_eq * N_FOLDS, 4),
        "rounds": 1,
        "query_measurements": 0,
        "note": "simulated procurement cost only; existing target data have k target units fixed; not a wet-lab quote",
    }


def main() -> int:
    on2 = json.load(open(ON2, "r", encoding="utf-8"))
    calib = json.load(open(CALIB, "r", encoding="utf-8"))
    scope = on2["replacement_qualification"]["scopes"]["batch1_target_cells"]
    folds = on2["fold_design"]["fold_stats"]
    units = int(scope["units"])
    contexts = int(scope["contexts"])
    target_cells = len(on2["scope"]["target_cells"])
    fold_units = [int(f["n_units"]) for f in folds]

    base_mde_batch1 = mean_mde(SIGMA_BATCH1_TARGET, 4, N_EFF_PER_FOLD)
    base_mde_all = mean_mde(SIGMA_ALL_BATCHES, 4, N_EFF_PER_FOLD)
    rank6 = rank_mde_independent(N_EFF_PER_FOLD)
    rank30 = rank_mde_independent(N_EFF_POOLED)
    req_n = required_n_for_rank(DELTA_MIN)
    req_r_err30 = required_r_err_for_rank(N_EFF_POOLED, DELTA_MIN)
    req_r_err6 = required_r_err_for_rank(N_EFF_PER_FOLD, DELTA_MIN)

    candidates: List[Dict[str, Any]] = []
    for c in CANDIDATES:
        mm = mean_mde(SIGMA_BATCH1_TARGET, int(c["wells_per_member"]), int(c["n_eff"]))
        rm = rank_mde_independent(int(c["n_eff"]))
        cost = procurement(int(c["wells_per_unit"]))
        candidates.append({
            "id": c["id"],
            "label": c["label"],
            "question": c["question"],
            "target_data_status": c["target_data_status"],
            "wells_per_member": c["wells_per_member"],
            "wells_per_unit": c["wells_per_unit"],
            "n_eff": c["n_eff"],
            "mean_mde80_batch1_target": round(mm, 10),
            "mean_mde_pass_delta": bool(mm <= DELTA_MIN),
            "rank_mde80_independent": round(rm, 10),
            "rank_mde_pass_delta": bool(rm <= DELTA_MIN),
            "procurement": cost,
            "overall_pass": bool(mm <= DELTA_MIN and rm <= DELTA_MIN),
        })

    # No candidate passes the rank gate; the mean gate can pass only by changing the
    # aggregation/adding wells, but rank precision is cell-line-limited.
    feasible_candidates = [c for c in candidates if c["overall_pass"]]
    stop_decision = len(feasible_candidates) == 0

    result: Dict[str, Any] = {
        "task": "R200-D3.1 revision / feasibility arithmetic",
        "status": "design_invalid_precision_insufficient" if stop_decision else "revised_feasible",
        "verdict": "design_invalid: precision_insufficient" if stop_decision else "revised_feasible",
        "stop_d3_execution": stop_decision,
        "approve_to_lead_exec": False if stop_decision else None,
        "base_v0_1": {
            "unit": "single anchor row, 2 members x 4 technical reps = 8 wells/unit",
            "sigma_batch1_target30": SIGMA_BATCH1_TARGET,
            "sigma_all_batches": SIGMA_ALL_BATCHES,
            "se_unit_batch1_single_anchor": round(SIGMA_BATCH1_TARGET / math.sqrt(2.0), 10),
            "mde80_mean_batch1_n6": round(base_mde_batch1, 10),
            "mde80_mean_all_batches_n6": round(base_mde_all, 10),
            "delta_min": DELTA_MIN,
            "mean_gate_pass": bool(base_mde_batch1 <= DELTA_MIN),
            "rank_mde80_n6_independent": round(rank6, 10),
            "rank_mde80_n30_independent": round(rank30, 10),
            "rank_gate_pass": False,
            "v0_1_prior_0_0287644381_used": False,
            "why_invalid": "MDE80=0.1119678 (batch1 target, n_eff=6) > delta_min=0.10; rank-level MDE is 2.287 (n=6) / 0.762 (pooled 30), both >0.10; v0.1's 0.02876 was the full-grid SE (sigma/sqrt(32)) misapplied to the 8-well single-anchor unit.",
        },
        "rank_level_gate": {
            "primary": "Spearman Delta-rho = rho(U_conflict)-rho(C2)",
            "formula_conservative_independent": "MDE_rank80 = 2.801585*sqrt(2/(n_eff-3)); Fisher-z approximation",
            "n_eff_per_fold": N_EFF_PER_FOLD,
            "n_eff_pooled": N_EFF_POOLED,
            "mde_rank_n6": round(rank6, 10),
            "mde_rank_n30": round(rank30, 10),
            "delta_min": DELTA_MIN,
            "required_independent_cell_lines_for_mde_rank_le_0_10": req_n,
            "required_paired_error_correlation_n30": round(req_r_err30, 10),
            "required_paired_error_correlation_n6": round(req_r_err6, 10),
            "claim": "with only 30 target cell lines, no technical-well increase can make the rank-level MDE <=0.10 without assuming error correlation >=0.9828 (n=30) or >=0.9981 (n=6); that assumption is not credentialed. Null/bootstrap only answers 'CI excludes 0', not 'resolves 0.10'.",
            "verdict": "design_invalid: precision_insufficient (rank gate)",
        },
        "resource": {
            "name": "O'Neil complete-case batch1 target30 single-anchor layer",
            "units": units,
            "contexts": contexts,
            "target_cells": target_cells,
            "folds": N_FOLDS,
            "fold_units": fold_units,
            "technical_reps_per_member": 4,
            "independent_cultures_per_unit": 1,
            "complete_case_rows": 363090,
            "rows_total": 368832,
            "complete_case_fraction": 0.98443194,
            "batch3_complete_case_rows": 0,
            "batch3_rows_total": 5040,
            "pair_cells_15rows": 702,
        },
        "candidate_designs": candidates,
        "feasible_candidates": feasible_candidates,
        "required_measurements_and_cost": {
            "if_fix_only_mean_delta": {
                "option": "single anchor, 6 technical reps/member (12 wells/unit), n_eff=6",
                "mean_mde80": round(mean_mde(SIGMA_BATCH1_TARGET, 6, N_EFF_PER_FOLD), 10),
                "mean_gate": bool(mean_mde(SIGMA_BATCH1_TARGET, 6, N_EFF_PER_FOLD) <= DELTA_MIN),
                "procurement": procurement(12),
                "caveat": "mean gate can pass, but primary is rank; rank MDE remains 2.287 (n=6) / 0.762 (pooled 30) -> design_invalid. Target data would also need 6 reps/member, not just feedback.",
            },
            "if_fix_rank": {
                "option": "independent cell lines to n≈1573 (or error correlation >=0.9828 at n=30)",
                "required_independent_cell_lines": req_n,
                "available_target_cells": target_cells,
                "required_paired_error_correlation_n30": round(req_r_err30, 10),
                "resource_cost": "requires an external resource with ~1,573 independent cell lines; O'Neil target30 cannot supply it; technical/feedback wells alone cannot fix rank MDE",
                "not_pursued": True,
            },
            "if_change_question": {
                "option": "full 4x4 grid mean / partner-dose average (changes D3 question; mean MDE may pass)",
                "note": "full-grid mean MDE=.02799 (n=6) or .0125 (pooled30), but rank MDE remains 2.287/.762; changing aggregation does not rescue the registered rank primary; not a redesign of H_D3.",
            },
        },
        "on3_non_blind_peek": {
            "inherited_non_blind_peek": True,
            "on3_quick_artifact_path": "tmp/on3_exec_quick_debug.invalid.json",
            "on3_quick_sha256": "39868CE400EBB3BAC4EDE765CDDEA889FC83EFD9B67064CE8A5A965CE5EDAFD5",
            "on3_quick_primary": "delta_rho_mean=0.0277068; CI=[0.01828,0.03572]; positive_folds=4; delta_rho_min_rank=0.10; per-fold B0-B5; verdict=design_invalid",
            "on3_peek_disclosure_sha": sha256_file(PEEK),
            "d3_is_non_blind": True,
            "cannot_claim_blind_or_independent_confirmation": True,
            "on3_quick_used_for_d3_direction": False,
            "on3_quick_used_for_d3_threshold": False,
            "on3_quick_used_for_d3_split": False,
            "on3_quick_used_for_d3_feedback_budget": False,
            "on3_quick_used_for_d3_controls": False,
            "statement": "D3 design was written after ON3 quick artifact; the artifact values were not used to choose D3 direction/threshold/split/feedback/controls. D3 is nevertheless non-blind/inherited-peek; no blind/pre-registered-confirmation/independent-confirmation claim is allowed.",
        },
        "strong_baselines": {
            "primary_control": "C2 full-history retrain (fixed, no result-dependent 'best ordinary control')",
            "controls": ["C0 global mean/no update", "C1 static additive (no feedback)", "C2 full-history retrain (primary)",
                         "C3 ordinary adaptation (fine-tune/bias)", "C4 hierarchical/EB", "C5 GP",
                         "C6 projected-kernel/ridge equivalent", "C7 fully-tuned tree/GBM (depth 2/3/5, leaf 20/50/100, lr 0.05/0.1, iter 200/500; nested CV)",
                         "C8 matrix completion/low-rank (rank 1-5, regularization grid)", "C9 direct response prediction (pre-registered mapping/feature contract; not a post-hoc best branch)",
                         "C10 exact closure where applicable (pre-registered; else report not applicable)"],
            "selection_rule": "no result-dependent 'best ordinary control'; C2 is fixed primary; all others secondary/descriptive with pre-specified multiplicity.",
            "equal_budget": "all arms same data/features/feedback pack; pre-registered tuning trials/seed/compute cap; full-history retrain not given extra data.",
        },
        "feedback_pack_contract": {
            "k_units_per_fold": K_FEEDBACK_UNITS_PER_FOLD,
            "k_total": K_FEEDBACK_UNITS_PER_FOLD * N_FOLDS,
            "rounds": 1,
            "selection": "one unit per support cell (24 support cells/fold), stratified by partner/member; deterministic hash rank with seed 20261130; no response used; deduplicate unit keys; no held-out cell unit in pack",
            "strata": ["cell line", "partner", "member pair", "anchor row"],
            "quotas": "1 unit per support cell/fold; balance partner/member across the 24 units as far as the hash permits; overflow/fallback to next hash-ranked unit in the same stratum",
            "failure_replacement": "pre-register 10% reserve units in the same stratum; replace failed/QC units by next hash-ranked reserve, never by response; replacement cost included",
            "query_measurements": 0,
            "all_arms_same": True,
            "cost_assumption": "8 wells/unit is a simulated procurement assumption; existing target data are not newly measured; not a wet-lab quote",
        },
        "compute_budget": {
            "per_arm": {"tuning_trials_le": 20, "inner_cv_folds": 5, "seeds": 3, "wall_cpu_hours_le": 2.0},
            "n1_n2_permutations": {"n1": 1000, "n2": 1000, "folds": N_FOLDS, "note": "1000 permutations x 5 folds x all arms is high; must be budgeted or the rank gate already stops execution"},
            "budget_exceeded_class": "design_invalid: compute_budget_exceeded (do not substitute a cheaper analysis after seeing results)",
            "status": "not executed; rank gate already stops before compute",
        },
        "failure_tree": {
            "design_invalid: precision_insufficient": "mean MDE80 > 0.10 OR rank MDE80 > 0.10 (prior or measured) -> stop; current v0.1",
            "design_invalid: leakage_or_endpoint": "target/future time in input; mask/fold violation; DeltaEMAX/endpoint mixing; held-out cell in feedback -> stop/re-register",
            "evaluation_cannot_distinguish": "rank CI includes 0 or cannot resolve delta_min=0.10; do not write 'no effect'",
            "no_increment": "all gates pass, rank delta point >=0? and <delta_min, CI excludes 0/equivalence declared; stop dynamic-necessity claim; keep descriptive",
            "development_increment_present": "all gates pass, rank delta >= delta_min and CI lower>0; development-only, no migration/mechanism/decision claim",
            "no_generalization": "only feedback/measured points improve -> stop feedback-generalization claim",
            "data_unavailable": "resource/qualification fails (not the current case; data exist)",
            "uniqueness": "one primary failure mapping; no dual mapping of the same condition",
        },
        "inputs": {
            "on2_json": {"path_rel": "research/2026-10-27-core-module-design/oneil_dev/on2.json", "sha256": sha256_file(ON2)},
            "calib_json": {"path_rel": "research/2026-10-27-core-module-design/oneil_dev/exec_calibration/calib.json", "sha256": sha256_file(CALIB)},
            "peek_disclosure": {"path_rel": "research/2026-10-27-core-module-design/oneil_dev/PEEK_DISCLOSURE_ON3.md", "sha256": sha256_file(PEEK) if os.path.exists(PEEK) else None},
            "on3_quick": {"path_rel": "tmp/on3_exec_quick_debug.invalid.json", "sha256": sha256_file(QUICK) if os.path.exists(QUICK) else None},
        },
        "attestation": {
            "metadata_only": True,
            "response_values_read": False,
            "workbook_read": False,
            "model_fit_or_prediction": False,
            "effect_run": False,
            "acquisition_compared": False,
            "non_blind_peek_disclosed": True,
            "independent_confirmation_claim": False,
            "migration_claim": False,
            "decision_benefit_claim": False,
            "mechanism_claim": False,
        },
    }

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True))
        fh.write("\n")
    print("wrote", OUT)
    print("verdict", result["verdict"])
    print("mean MDE base", round(base_mde_batch1, 6), "all", round(base_mde_all, 6))
    print("rank MDE n6/n30", round(rank6, 6), round(rank30, 6), "required_n", req_n)
    print("feasible_candidates", len(feasible_candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
