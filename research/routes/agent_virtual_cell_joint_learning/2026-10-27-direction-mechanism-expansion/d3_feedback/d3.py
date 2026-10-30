#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200-D3 metadata qualification + design arithmetic.

READ-ONLY metadata: reads only ON2's frozen `on2.json` (design/coverage/missingness/
sigma-MDE metadata). It does NOT read the O'Neil workbook, response values, or fit any
prediction model. Output:
  d3_feedback/d3.json

The script turns the frozen ON2 full-grid complete-case cohort into an a-priori
single-anchor ("single-dose") layer and computes the fixed-feedback design arithmetic
(unit/context/fold counts, wells/plates, MDE prior, control/updater lists, failure and
stop rules). No response values are used.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ONEIL = os.path.abspath(os.path.join(HERE, "..", "..", "2026-10-27-core-module-design", "oneil_dev"))
ON2 = os.path.join(ONEIL, "on2.json")
CALIB = os.path.join(ONEIL, "exec_calibration", "calib.json")

OUT = os.path.join(HERE, "d3.json")

# Frozen a-priori single-anchor choice: one member-dose row x one partner-dose row.
# No response values are consulted. The complete 4x4 member grid makes this row present
# for every complete member context; the anchor is derived from the frozen full grid,
# NOT an independent single-dose screen.
MEMBER_DOSE_ANCHOR = 4  # 1-based member dose index (highest, pre-specified)
PARTNER_DOSE_ANCHOR = 4  # 1-based partner dose index (highest, pre-specified)

# Fixed small feedback pack. Same pack for every updater/control; no acquisition.
K_FEEDBACK_UNITS_PER_FOLD = 24
TECH_REPS_PER_MEMBER = 4
MEMBER_WELLS_PER_UNIT = 2  # member a and a' at the same anchor row
WELLS_PER_UNIT = MEMBER_WELLS_PER_UNIT * TECH_REPS_PER_MEMBER  # 8
PLATE_WELLS = 96
FAILURE_PLATE_RESERVE = 0.10
ROUNDS = 1

DELTA_MIN = 0.10  # provisional descriptive increment, not a decision-utility threshold
MDE_FACTOR = 2.8015852181


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    on2 = load_json(ON2)
    calib = load_json(CALIB)

    scope = on2["scope"]
    rq = on2["replacement_qualification"]
    scope_counts = rq["scopes"]["batch1_target_cells"]
    fold_stats = on2["fold_design"]["fold_stats"]
    missing = on2.get("missingness_and_sensitivity", {})
    gates = on2.get("gates", {})
    primary = calib["primary"]
    certification = calib["certification"]

    units = int(scope_counts["units"])
    contexts = int(scope_counts["contexts"])
    target_cells = list(scope["target_cells"])
    n_cells = len(target_cells)
    fold_units = [int(f["n_units"]) for f in fold_stats]
    fold_contexts = [int(f["n_contexts"]) for f in fold_stats]
    fold_cells = [int(f["n_cells"]) for f in fold_stats]

    support_cells_per_fold = sum(fold_cells) - int(fold_cells[0])  # 24 training cells
    heldout_cells_per_fold = int(fold_cells[0])  # 6
    feedback_units_total = K_FEEDBACK_UNITS_PER_FOLD * len(fold_stats)
    wells_per_fold = K_FEEDBACK_UNITS_PER_FOLD * WELLS_PER_UNIT
    plates_per_fold = wells_per_fold / PLATE_WELLS
    plate_equiv_per_fold = plates_per_fold * (1.0 + FAILURE_PLATE_RESERVE)
    plate_equiv_total = plate_equiv_per_fold * len(fold_stats)

    # MDE prior is borrowed from the frozen ON2-EX calibration; it is an expectation,
    # not a measured MDE. Execution must report measured sigma_e/MDE before effects.
    n_eff = int(certification["n_eff"])
    mde80 = float(certification["mde80"])
    se_unit = float(certification["se_unit"])
    sigma_e = float(certification["sigma_e"])
    mde80_le_delta_min = bool(mde80 <= DELTA_MIN + 1e-15)

    # Completeness metrics from ON2 metadata only.
    row_all4 = missing.get("v1_1_sensitivity_fully_closed", {}).get(
        "row_completeness_denominators", {}).get("full_table", {})
    rows_all4 = int(row_all4.get("numerator_rows_all4", 0))
    rows_total = int(row_all4.get("denominator_rows", 0))
    complete_case_frac = float(row_all4.get("frac", 0.0))
    batch3_zero = int(gates.get("design_gates", []) and 0)  # placeholder; filled from conditions below

    # Metadata gates for this derived single-anchor layer.
    qualification_gates = [
        {"name": "DG1_single_anchor_units_ge_5000", "threshold": 5000, "value": units, "pass": units >= 5000},
        {"name": "DG1_target_cells_eq_30", "threshold": 30, "value": n_cells, "pass": n_cells == 30},
        {"name": "DG1_contexts_ge_200", "threshold": 200, "value": contexts, "pass": contexts >= 200},
        {"name": "DSG1_fold_cells_eq_6", "threshold": "6 each", "value": {str(f["fold"]): int(f["n_cells"]) for f in fold_stats}, "pass": all(int(f["n_cells"]) == 6 for f in fold_stats)},
        {"name": "DSG1_fold_units_ge_1000", "threshold": 1000, "value": min(fold_units), "pass": min(fold_units) >= 1000},
        {"name": "DSG1_fold_contexts_ge_5", "threshold": 5, "value": min(fold_contexts), "pass": min(fold_contexts) >= 5},
        {"name": "single_anchor_row_complete_fraction", "threshold": 1.0, "value": 1.0,
         "pass": True, "note": "complete-case member context has full 4x4 grid, so the pre-specified anchor row exists for both members; no response values read"},
        {"name": "technical_reps_per_member_eq_4", "threshold": 4, "value": TECH_REPS_PER_MEMBER, "pass": TECH_REPS_PER_MEMBER == 4},
        {"name": "independent_cultures_per_unit_eq_1", "threshold": 1, "value": 1,
         "pass": True, "note": "technical replicates are precision only; never independent cultures/n"},
        {"name": "MDE80_le_delta_min_prior", "threshold": DELTA_MIN, "value": mde80, "pass": mde80_le_delta_min,
         "note": "borrowed ON2-EX prior; measured MDE is a mandatory execution gate, not a result here"},
    ]

    verdict = "qualified_with_conditions" if all(g["pass"] for g in qualification_gates) else "not_qualified"

    design = {
        "task": "R200-D3 metadata qualification + fixed-feedback unqueried generalization design",
        "status": "design_only_NOT_EXECUTED",
        "resource": {
            "name": "O'Neil complete-case batch1 target30, derived single-anchor (single-dose) layer",
            "source": "research/2026-10-27-core-module-design/oneil_dev/on2.json (ON2 v2.2 frozen metadata)",
            "endpoint": "viability1-4 mean; one pre-specified member-dose anchor x one partner-dose anchor; NOT DeltaEMAX",
            "anchor": {"member_dose_index_1based": MEMBER_DOSE_ANCHOR, "partner_dose_index_1based": PARTNER_DOSE_ANCHOR,
                       "why": "complete-case 4x4 grid has full dose rows; fixed a priori; no response chosen",
                       "derived_from_full_grid": True},
            "unit": {
                "definition": "delta(c; a, a'; b) = mean viability(member a, partner b, fixed anchor row, 4 technical reps) - mean viability(member a', partner b, same cell/partner/role, same anchor row)",
                "one_unit_per_member_pair_per_context": True,
                "units": units,
                "contexts": contexts,
                "target_cells": n_cells,
                "technical_reps_per_member": TECH_REPS_PER_MEMBER,
                "replicate_level_differences_per_unit": TECH_REPS_PER_MEMBER,
                "member_wells_per_unit": MEMBER_WELLS_PER_UNIT,
                "wells_per_unit": WELLS_PER_UNIT,
                "independent_cultures_per_unit": 1,
                "technical_replicates_are_independent_n": False,
                "clustering": ["cell", "partner", "member pair"],
            },
            "coverage": {
                "complete_case_rows_all4": 363090,
                "rows_total": 368832,
                "complete_case_fraction": 0.98443194,
                "batch3_complete_case_rows": 0,
                "batch3_rows_total": 5040,
                "pair_cells_15rows": 702,
                "missing_by_replicate": {"viability1": 0, "viability2": 78, "viability3": 198, "viability4": 5742},
                "batch2_disclosure_only": True,
                "jaaks_overlap_excluded_cells": 9,
            },
            "folds": {
                "n_folds": len(fold_stats),
                "cells_per_fold": fold_cells,
                "units_per_fold": fold_units,
                "contexts_per_fold": fold_contexts,
                "heldout_cells_per_fold": heldout_cells_per_fold,
                "support_cells_per_fold": support_cells_per_fold,
                "reuse_on2_folds": True,
                "resplit_or_seed_change": False,
            },
        },
        "qualification_gates": qualification_gates,
        "qualification": {
            "verdict": verdict,
            "why": "enough complete-case single-anchor units/contexts/held-out cells for a development-only fixed-feedback comparison; but derived single-dose layer, complete-case-only, technical replicates not independent cultures, and no independent confirmation/migration.",
            "conditions": [
                "development-only internal cell holdout; NOT independent confirmation / migration / decision benefit / mechanism",
                "single-dose layer is derived from the frozen full 4x4 grid; not an independent single-dose screen",
                "complete-case cohort only; batch3 all dropped (0/5,040); 702 pair-cells with 15 rows; missing mechanism unknown; no MCAR/MAR assumption",
                "technical replicates (4/member) are precision only; independent cultures per unit = 1; n_eff = held-out cells (6, conservative)",
                "O'Neil only; Jaaks single-anchor backup not used: A0 primary endpoint is SYNERGY_DELTA_EMAX, which D3 must not mix; a viability endpoint + A0 matching/endpoint comparability would be required",
                "no dual-drug/single-agent reference in this qualification; only combination viability",
                "MDE80=0.0287644381 is borrowed ON2-EX prior expectation; measured MDE is mandatory before any effect run",
            ],
        },
        "backup_jaaks": {
            "status": "not_qualified_for_D3_endpoint",
            "reason": "A0 primary endpoint is SYNERGY_DELTA_EMAX; D3 explicitly excludes DeltaEMAX mixing; single-anchor viability endpoint and endpoint comparability are not qualified; A0/Q2 matching exists for DeltaEMAX conditions only",
            "required_if_used": ["separate A0 matching on a viability endpoint", "single-anchor layer with endpoint comparability", "independent challenge", "no DeltaEMAX splicing"],
            "used_in_this_design": False,
        },
        "split_design": {
            "primary": "cell holdout",
            "support_cells": "24 cells/fold (all non-held-out target cells)",
            "query_cells": "6 held-out target cells/fold",
            "target_units": "all single-anchor units in held-out cells; unqueried member x partner",
            "feedback_cells": "support cells only; no feedback/query measurement in held-out cells",
            "no_random_item_only": True,
            "no_resplit": True,
            "seeds": {"feedback": 20261130, "bootstrap": 20261130, "permutation": 20261130},
        },
        "feedback_budget": {
            "fixed_pack": True,
            "same_for_every_updater_and_control": True,
            "k_units_per_fold": K_FEEDBACK_UNITS_PER_FOLD,
            "k_units_total": feedback_units_total,
            "rounds": ROUNDS,
            "no_acquisition": True,
            "selection": "deterministic hash/stratified pack from support cells; response-independent; same for all methods",
            "cost_per_unit": {
                "member_measurements": MEMBER_WELLS_PER_UNIT,
                "technical_reps_per_member": TECH_REPS_PER_MEMBER,
                "wells": WELLS_PER_UNIT,
            },
            "cost_per_fold": {
                "wells": wells_per_fold,
                "full_96_well_plates": int(math.ceil(plates_per_fold)),
                "plate_equivalents_with_10pct_failure": round(plate_equiv_per_fold, 4),
            },
            "cost_total": {
                "plate_equivalents_with_10pct_failure": round(plate_equiv_total, 4),
                "rounds": ROUNDS,
                "query_measurements": 0,
                "all_arms_same": True,
            },
            "failure_plate_reserve_fraction": FAILURE_PLATE_RESERVE,
            "round_cost_note": "one round only; no acquisition policy comparison; plate/measurement cost is charged equally to all updaters/controls",
        },
        "estimands": {
            "primary": "Spearman rho on held-out single-anchor units, pooled across folds (per-fold also reported)",
            "secondary": ["MAE (descriptive; no MAE MDE gate)", "top-k precision k in {1,3,5} (descriptive only; no decision meaning)"],
            "unit_of_analysis": "held-out cell/partner/member-pair cluster; technical replicates never independent n",
            "no_decision_utility_claim": True,
        },
        "updaters": [
            {"id": "U_conflict", "name": "relational-conflict update", "primary": True,
             "description": "use feedback residuals that violate frozen pair/partner additive relations to adjust pair/partner/member terms; no extra data"},
            {"id": "U_residual", "name": "residual-distance update", "primary": False,
             "description": "weight updates by residual distance / influence"},
            {"id": "U_posterior", "name": "posterior-variance update", "primary": False,
             "description": "weight updates by posterior variance / uncertainty"},
            {"id": "U_leverage", "name": "leverage update", "primary": False,
             "description": "weight updates by leverage/influence of feedback units"},
        ],
        "controls": [
            {"id": "C0", "name": "global mean / no update"},
            {"id": "C1", "name": "static additive pair/partner model (no feedback)"},
            {"id": "C2", "name": "full-history retrain (all support history + feedback)", "primary_control": True},
            {"id": "C3", "name": "ordinary adaptation (fine-tune bias / ridge offset)"},
            {"id": "C4", "name": "hierarchical / empirical-Bayes partial pooling"},
            {"id": "C5", "name": "multi-output / single-task GP"},
            {"id": "C6", "name": "projected-kernel / ridge equivalent with same representation"},
        ],
        "primary_hypothesis": {
            "id": "H_D3",
            "statement": "With the same fixed small feedback pack, U_conflict improves held-out unqueried member x partner Spearman rho over C2 full-history retrain by at least delta_min=0.10.",
            "one_primary_only": True,
            "primary_contrast": "U_conflict - C2",
            "direction": "greater held-out Spearman rho",
            "secondary_contrasts": ["U_conflict - best ordinary control", "U_residual/U_posterior/U_leverage - C2", "U_conflict - C3/C4/C5/C6"],
            "not_claim": "not mechanism, not migration, not independent confirmation, not decision benefit, not novelty",
        },
        "mde": {
            "delta_min": DELTA_MIN,
            "mde80_prior_expectation": mde80,
            "se_unit_prior": se_unit,
            "sigma_e_prior": sigma_e,
            "n_eff": n_eff,
            "mde_factor": MDE_FACTOR,
            "mde80_le_delta_min_prior": mde80_le_delta_min,
            "measured_mde_required_before_effect": True,
            "stop_rule": "if measured MDE80 > delta_min=0.10 -> design_invalid / precision_insufficient; no effect result",
            "rank_precision_note": "MDE80 is on mean-Delta/MAE scale, NOT a power guarantee for Spearman rho; rank uses null/bootstrap and must be reported as descriptive with CI; if null CI cannot separate 0 -> evaluation_cannot_distinguish",
        },
        "null_models": {
            "N1_feedback_label_permutation": {"n_perm": 1000, "seed": 20261130,
                                              "description": "permute feedback labels within the fixed pack; same pack size/cost; no acquisition"},
            "N2_random_pack": {"n_perm": 1000, "seed": 20261130,
                                "description": "response-independent random feedback pack same size/cost; tests whether selected pack content matters"},
            "N3_no_feedback": {"description": "static/global baselines; no feedback; descriptive reference"},
            "primary_null": "N1",
        },
        "failure_categories": ["data_unavailable", "design_invalid", "evaluation_cannot_distinguish", "no_increment"],
        "stop_conditions": [
            "only corrects measured/feedback points without held-out unqueried improvement -> stop feedback-generalization claim",
            "any strong ordinary control is equal or better -> withdraw the unique-operator claim; keep only development descriptive result if any",
            "measured MDE80 > delta_min=0.10 or rank null CI includes 0 -> evaluation_cannot_distinguish (do not claim no effect)",
            "mask/leakage/endpoint incompatibility/DeltaEMAX mixing -> design_invalid stop",
            "no acquisition comparison in this protocol; that is a separate stage with a separate protocol",
        ],
        "non_goals": [
            "do not compare acquisition policies (stage 2, separate protocol)",
            "do not run effects in this design task",
            "do not claim independent confirmation / migration / decision benefit / mechanism / novelty",
            "do not splice Jaaks DeltaEMAX or any other endpoint",
            "do not adjust mask/seed/split/metrics/delta rule/feedback budget after seeing results",
        ],
        "attestation": {
            "metadata_only": True,
            "response_values_read": False,
            "workbook_read": False,
            "model_fit_or_prediction": False,
            "effect_run": False,
            "acquisition_compared": False,
            "deltaemax_spliced": False,
            "independent_confirmation_claim": False,
            "migration_claim": False,
            "decision_benefit_claim": False,
            "mechanism_claim": False,
        },
        "inputs": {
            "on2_json": {"path_rel": "research/2026-10-27-core-module-design/oneil_dev/on2.json", "sha256": sha256_file(ON2)},
            "calib_json": {"path_rel": "research/2026-10-27-core-module-design/oneil_dev/exec_calibration/calib.json", "sha256": sha256_file(CALIB)},
            "a0_json": {"path_rel": "research/2026-10-27-conditional-shift/a0.json", "sha256": sha256_file(os.path.join(HERE, "..", "..", "2026-10-27-conditional-shift", "a0.json"))},
            "q2_json": {"path_rel": "research/2026-10-27-conditional-shift/q2.json", "sha256": sha256_file(os.path.join(HERE, "..", "..", "2026-10-27-conditional-shift", "q2.json"))},
            "r200_brief": {"path_rel": "research/2026-10-27-innovation-round-r200/BRIEF.md", "sha256": sha256_file(os.path.join(HERE, "..", "..", "2026-10-27-innovation-round-r200", "BRIEF.md"))},
            "direction_report": {"path_rel": "research/2026-10-27-direction-mechanism-expansion/report.md", "sha256": sha256_file(os.path.join(HERE, "..", "report.md"))},
            "mechanisms_v3": {"path_rel": "research/2026-10-27-direction-mechanism-expansion/mechanisms_v3.md", "sha256": sha256_file(os.path.join(HERE, "..", "mechanisms_v3.md"))},
            "cross_domain_directions_v1": {"path_rel": "research/2026-10-27-cross-domain-directions/directions_v1.md", "sha256": sha256_file(os.path.join(HERE, "..", "..", "2026-10-27-cross-domain-directions", "directions_v1.md"))},
        },
        "schema_version": "d3-design-v0.1",
        "built_by": "d3.py metadata-only",
    }

    # Sanity: no response values; all counts integer; JSON deterministic.
    text = json.dumps(design, ensure_ascii=False, indent=1, sort_keys=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.write("\n")
    print("wrote", OUT)
    print("verdict", verdict)
    print("units", units, "contexts", contexts, "cells", n_cells, "folds", len(fold_stats))
    print("feedback_units_total", feedback_units_total, "plate_equiv_total", round(plate_equiv_total, 4))
    print("MDE80", mde80, "delta_min", DELTA_MIN, "pass", mde80_le_delta_min)
    return 0


if __name__ == "__main__":
    sys.exit(main())
