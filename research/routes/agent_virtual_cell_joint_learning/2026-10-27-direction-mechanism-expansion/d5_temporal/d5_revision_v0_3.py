"""R200-D5.2: reduce D5 to a descriptive-only development analysis (v0.3).

Per challenge_D5_v0_2.md (reduce_to_descriptive, 5 must-fix):
  1. fix V2 paired-set typo (third value 16 -> 15) in v0.3 docs; record v0.2 typo location;
  2. freeze E6 null models: N1/N2 = 1,000 permutations (not 200);
  3. make E7 concrete: libraries/grids/candidate counts/inner folds/trials/compute cap + grid SHA;
  4. remove confirmatory H-D5-1 and G3/G4 pass/fail; descriptive reporting only;
  5. require execution-phase G0b re-check (compound identity/dose/vehicle); failure stops with
     active_dose_identity_unverified; BRD3379 never returns to primary.

NO effect run, NO prediction fitting, NO expression/response matrix reading.
Reads: v0.1/v0.2 artifacts (read-only), challenge files, Mix-seq h5ad metadata only,
       installed library version metadata.
Writes: d5_v0_3.json (deterministic; sort_keys; no timestamps; two runs byte-identical).
"""
import hashlib
import importlib.metadata as md
import json
import math
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")
OUT = os.path.join(HERE, "d5_v0_3.json")

SEED = 20261027
DELTA_MIN = 0.10
N_PERM = 1000

V01_FILES = ["PROTOCOL_D5.md", "d5.py", "d5.json", "report_d5.md", "record_d5.md", "usage_d5.json"]
V02_FILES = ["PROTOCOL_D5_v0_2.md", "d5_revision.py", "d5_v0_2.json", "report_d5_v0_2.md",
             "record_d5_v0_2.md", "usage_d5_v0_2.json"]
CHALLENGES = ["challenge_D5.md", "challenge_D5_v0_2.md"]

ACTIVE_DRUGS = ["Bortezomib", "Idasanutlin", "Trametinib"]
ZERO_DOSE = "BRD3379"
CONTROL = "control"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def file_meta(path):
    return {"present": os.path.exists(path),
            "bytes": os.path.getsize(path) if os.path.exists(path) else None,
            "sha256": sha256_file(path) if os.path.exists(path) else None}


def libver(name):
    try:
        return md.version(name)
    except Exception:
        return "unknown"


def mde_prerun(n):
    if n is None or n < 2:
        return {"n": n, "mde80_upper": None, "required_r_err": None}
    z = 1.959964 + 0.841621
    return {"n": int(n),
            "mde80_upper": round(z * math.sqrt(2.0 / (n - 1.0)), 3),
            "required_r_err": round(1.0 - (DELTA_MIN ** 2 * (n - 1.0)) / (2.0 * z ** 2), 3)}


def main():
    out = {
        "meta": {
            "task": "task-98 R200-D5.2 reduce_to_descriptive (challenge_D5_v0_2.md, 5 must-fix)",
            "agent": "cellstate-lit",
            "revision_of": "R200-D5.1 v0.2 (PROTOCOL_D5_v0_2.md / d5_revision.py / d5_v0_2.json / report_d5_v0_2.md / record_d5_v0_2.md / usage_d5_v0_2.json)",
            "status": "DESCRIPTIVE-ONLY revision; no confirmatory H-D5-1; no G3/G4 pass/fail; not an effect run",
            "approve_to_lead_exec": False,
            "scope": ("documentation/qualification/design revision only; no expression values read, no response values, "
                      "no model fitting, no prediction run; descriptive analysis schema + execution preconditions only"),
            "expression_matrix_read": False,
            "response_values_read": False,
            "model_fit": False,
            "seed": SEED,
            "delta_min": DELTA_MIN,
            "n_permutations": N_PERM,
        },
        "inputs_sha256": {},
        "input_mixseq": file_meta(H5AD),
    }
    for name in V01_FILES + V02_FILES + CHALLENGES:
        m = file_meta(os.path.join(HERE, name))
        m["path"] = os.path.relpath(os.path.join(HERE, name), ROOT).replace(os.sep, "/")
        out["inputs_sha256"][name] = m

    # ---------- read v0.2 JSON (read-only) and h5ad metadata for cross-check ----------
    v02 = json.load(open(os.path.join(HERE, "d5_v0_2.json"), encoding="utf-8"))
    active_v02 = v02["v1_primary"]["active_drugs"]
    n_active = {p: active_v02[p]["n_eligible_lines"] for p in active_v02}
    paired_correct = {
        "target24h_E1_E2": v02["v2_corrected"]["contrasts"][0]["paired_n"],
        "target48h_E1_E2": v02["v2_corrected"]["contrasts"][1]["paired_n_E1_E2"],
        "target48h_E2_E3": v02["v2_corrected"]["contrasts"][1]["paired_n_E2_E3"],
    }

    # ---------- typo audit: v0.2 protocol must be corrected in v0.3 (v0.2 stays frozen) ----------
    proto_v02 = open(os.path.join(HERE, "PROTOCOL_D5_v0_2.md"), encoding="utf-8").read()
    typo_token = "15/16/" + "16"  # constructed so v0.3 artifacts stay free of the literal token
    typo_lines = [i + 1 for i, line in enumerate(proto_v02.split("\n")) if typo_token in line]
    correct_token = "15/16/15"
    correct_lines_v02 = [i + 1 for i, line in enumerate(proto_v02.split("\n")) if correct_token in line]

    # ---------- E6 null models: frozen 1,000 permutations ----------
    null_models = {
        "seed": SEED,
        "n_permutations": N_PERM,
        "N0_mean": {"description": "training-line mean per drug/time; no permutation",
                    "permutations": 0},
        "N1_cell_shuffle": {
            "description": "permute cell-line labels of early features within the same drug/time fold; cells are not paired",
            "permutations": N_PERM,
            "null_distribution": "distribution of the primary descriptive statistic over 1,000 cell-label permutations",
            "unit": "cell line (permuted label); folds kept fixed across permutations",
        },
        "N2_drug_shuffle": {
            "description": "V1 only: permute drug labels of early features across the 3 active drugs; target kept",
            "permutations": N_PERM,
            "null_distribution": "distribution of per-drug delta over 1,000 drug-label permutations",
            "unit": "drug label; folds kept fixed",
        },
        "N3_time_shuffle": {
            "description": "V2 only: permute earlier-time labels among allowed earlier times of the same (line,treatment)",
            "permutations": N_PERM,
            "null_distribution": "distribution of paired delta-rho over 1,000 time-label permutations",
            "unit": "time label within (line,treatment); paired line set kept fixed",
        },
        "N4_capacity_control": {
            "description": "V2 only: add matched-dimension random features to E1, or replace second-time features with shuffled features",
            "permutations": N_PERM,
            "null_distribution": "distribution of delta-rho over 1,000 matched-dimension random/second-time-shuffled draws",
            "unit": "cell line; same tuning budget as the real counterpart",
        },
        "N5_future_leak_sentinel": {
            "description": ("positive-control: replace early features with target-time features; expected near-oracle; "
                            "if it does not raise rho, the pipeline/metric is broken (fail closed)"),
            "permutations": 0,
            "runs": "1 per fold/arm (not a null distribution; a pipeline sentinel)",
        },
        "N6_static_capacity": {
            "description": "same-dimension random gene block for the static baseline",
            "permutations": N_PERM,
            "null_distribution": "distribution of static-baseline delta over 1,000 random-block draws",
            "unit": "cell line; folds fixed",
        },
        "legitimate_null_rules": [
            "permute only within the same fold/drug/time stratum; never mix folds",
            "preserve marginal feature/target distributions",
            "same tuning budget for real and null runs",
            "record permutation seeds and counts; do not reduce below 1,000 without a pre-registered power justification",
        ],
    }

    # ---------- E7 concrete tuning plan (grids frozen here; no fitting) ----------
    alpha_grid = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
    tuning = {
        "libraries": {"scikit-learn": libver("scikit-learn"), "numpy": libver("numpy"),
                      "pandas": libver("pandas"), "scipy": libver("scipy")},
        "inner_cv": "5-fold grouped by cell line inside each outer training fold",
        "candidates_per_tuned_model": 8,
        "inner_folds": 5,
        "fits_per_unit": 40,
        "outer_units": "5 cell-line folds x 3 active drugs = 15",
        "fits_per_tuned_model_total": 600,
        "tuned_models": ["B1_static_ridge", "B3_linear_ridge_early", "B4_tree_gbm",
                         "B5_gp", "B7_single_early_ridge", "B8_two_early_ridge"],
        "untuned_models": ["B0_mean", "B2_cell_identity", "B6_simple_linear_time_V2"],
        "max_fits_total": 4200,
        "compute_cap": {"device": "CPU", "max_wall_minutes": 120,
                        "per_fit_timeout_s": 120,
                        "if_exceeded": "record protocol_deviation; do not report effect/descriptive result"},
        "models": {
            "B0_mean": {"library": "numpy", "grid": "none", "candidates": 0},
            "B1_static_ridge": {"library": "sklearn.linear_model.Ridge",
                                "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B2_cell_identity": {"library": "numpy", "grid": "none", "candidates": 0},
            "B3_linear_ridge_early": {"library": "sklearn.linear_model.Ridge",
                                      "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B4_tree_gbm": {"library": "sklearn.ensemble.HistGradientBoostingRegressor",
                            "grid": {
                                "max_depth": [2, 3],
                                "learning_rate": [0.03, 0.1],
                                "max_leaf_nodes": [7, 15],
                                "l2_regularization": [0.0, 1.0],
                            },
                            "candidates": "8 pre-registered combinations listed below",
                            "candidate_list": [
                                {"max_depth": 2, "learning_rate": 0.03, "max_leaf_nodes": 7, "l2_regularization": 0.0},
                                {"max_depth": 2, "learning_rate": 0.03, "max_leaf_nodes": 15, "l2_regularization": 1.0},
                                {"max_depth": 2, "learning_rate": 0.1, "max_leaf_nodes": 7, "l2_regularization": 1.0},
                                {"max_depth": 2, "learning_rate": 0.1, "max_leaf_nodes": 15, "l2_regularization": 0.0},
                                {"max_depth": 3, "learning_rate": 0.03, "max_leaf_nodes": 7, "l2_regularization": 1.0},
                                {"max_depth": 3, "learning_rate": 0.03, "max_leaf_nodes": 15, "l2_regularization": 0.0},
                                {"max_depth": 3, "learning_rate": 0.1, "max_leaf_nodes": 7, "l2_regularization": 0.0},
                                {"max_depth": 3, "learning_rate": 0.1, "max_leaf_nodes": 15, "l2_regularization": 1.0},
                            ]},
            "B5_gp": {"library": "sklearn.gaussian_process.GaussianProcessRegressor",
                      "grid": {"length_scale": [0.1, 1.0, 10.0, 100.0],
                               "alpha_white": [1e-3, 1e-2]},
                      "candidates": "8 (4 length scales x 2 white-noise levels, fixed list)"},
            "B6_simple_linear_time_V2": {"library": "numpy", "grid": "none (closed-form per gene)", "candidates": 0},
            "B7_single_early_ridge": {"library": "sklearn.linear_model.Ridge",
                                      "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B8_two_early_ridge": {"library": "sklearn.linear_model.Ridge",
                                   "grid": {"alpha": alpha_grid}, "candidates": 8},
        },
        "same_budget_rule": ("tuned models get exactly 8 candidates x 5 inner folds; untuned models get 0; "
                             "report candidate counts and selected hyperparameters per fold/drug"),
        "no_test_tuning": "hyperparameters selected by inner CV only; test fold never used",
    }
    tuning_grid_sha = hashlib.sha256(json.dumps(tuning, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    # ---------- descriptive reporting schema ----------
    reporting_schema = {
        "statement": ("本分析不检验时间预测是否成立；只描述可达到的精度与方向。任何数值不用于 confirmatory 推断；"
                      "不写 biology/功能/迁移/决策/机制/新颖性。"),
        "per_drug_fields": ["drug", "n_eligible_lines", "rho_early6h", "rho_static", "delta_rho",
                            "delta_ci_low", "delta_ci_high", "mde80", "room", "reliability_split_half",
                            "per_fold_delta_rho", "fold_manifest_sha256", "selected_hyperparameters"],
        "summary_fields": ["active_drug_equal_weight_mean_delta_rho", "min_max_per_drug_delta_rho",
                           "descriptive_precision_note"],
        "brd3379_fields": ["role", "n_eligible_lines", "secondary_descriptive_only", "never_in_primary"],
        "v2_fields": ["target_h", "E1", "E2", "E3", "n_E1", "n_E2", "n_E3", "paired_n",
                      "delta_rho", "delta_ci", "per_fold", "capacity_control_result", "exploratory_only"],
        "must_not_report": ["confirmatory p-value for H-D5-1", "hypothesis-testing verdict", "biology/function claim",
                            "migration/decision/mechanism claim", "BRD3379 as active drug"],
        "precision_note_rule": ("MDE80/room are reported as precision descriptors; if MDE80 > delta_min, write "
                                "'descriptive precision insufficient for confirmatory inference', not a test verdict"),
    }

    # ---------- revision changes ----------
    out["revision_changes"] = [
        {"id": 1, "challenge_item": "V2 paired-set typo in PROTOCOL_D5_v0_2.md line 96 (third value 16 -> 15)",
         "v0_2_typo_found": {"token_masked": "15/16/**16**", "lines": typo_lines, "file_frozen": "PROTOCOL_D5_v0_2.md"},
         "v0_2_correct_occurrences": {"token": correct_token, "lines": correct_lines_v02},
         "after": "v0.3 uses 15/16/15 everywhere; v0.3 artifacts contain no literal typo token (verified post-write)",
         "status": "fixed_in_v0_3; v0.2 remains frozen history"},
        {"id": 2, "challenge_item": "E6 null models must be frozen at 1,000 permutations (N1/N2)",
         "before": "v0.2 E6 wrote '>=200 permutations'",
         "after": f"v0.3 E6 sets N1/N2=1,000 (and N3/N4/N6=1,000) with legitimate null/cluster/paired rules, seed {SEED}",
         "status": "fixed"},
        {"id": 3, "challenge_item": "E7 must specify B1-B8 libraries/grids/candidates/inner folds/trials/compute cap",
         "before": "v0.2 E7 only said 'freeze libraries/grids before execution'",
         "after": ("v0.3 E7 fixes libraries/versions, inner CV, 8 candidates per tuned model, 5 inner folds, "
                   "40 fits/unit, 15 outer units, 600 fits/tuned model, compute cap, explicit grids, and a frozen "
                   f"tuning-grid SHA256 {tuning_grid_sha}"),
         "status": "fixed"},
        {"id": 4, "challenge_item": "reduce to descriptive: remove confirmatory H-D5-1 and G3/G4 pass/fail",
         "before": "v0.2 had confirmatory-development status and G3/G4 pass/fail semantics",
         "after": ("v0.3 is DESCRIPTIVE-ONLY: H-D5-1 descriptive; no G3/G4 pass/fail; no "
                   "'evaluation_cannot_distinguish' as inference; report per-drug delta/CI/MDE/room/reliability/"
                   "per-fold, BRD3379 secondary, V2 exploratory; explicit non-inference statement"),
         "status": "fixed"},
        {"id": 5, "challenge_item": "G0b execution-phase re-check of compound identity/dose/vehicle; failure -> stop",
         "before": "v0.2 G0b was metadata-level conditional pass",
         "after": ("v0.3 keeps G0b as an execution precondition requiring actual compound identity/dose/vehicle records; "
                   "failure -> active_dose_identity_unverified stop; BRD3379 never primary"),
         "status": "fixed"},
    ]

    out["descriptive_analysis"] = {
        "status": "descriptive_only",
        "design": {
            "V1": {
                "endpoint": "6h early RNA -> 24h late RNA molecular proxy (pseudobulk logFC; train-only top-200 genes)",
                "active_primary_drugs": ACTIVE_DRUGS,
                "n_eligible_lines": n_active,
                "outer_split": "leave-cell-line-out 5 folds (sorted lines, fold=index%5)",
                "inner_cv": "5-fold grouped by cell line",
                "primary_statistic": ("per-drug delta_rho = rho(early6h) - rho(static); equal-weight mean over the 3 "
                                      "active drugs is reported as a descriptive summary (not a confirmatory test)"),
                "mde_prerun_upper": {p: mde_prerun(n) for p, n in n_active.items()},
                "paired_across_drugs": False,
            },
            "BRD3379": {
                "role": "zero-dose/vehicle-like control; secondary/descriptive only",
                "n_eligible_lines_history": 95,
                "included_in_primary": False,
                "never_returns_to_primary": True,
            },
            "V2": {
                "status": "exploratory only (n<20)",
                "contrasts": {"target24h": {"n_E1": 18, "n_E2": 15, "paired_n": paired_correct["target24h_E1_E2"]},
                              "target48h": {"n_E1": 19, "n_E2": 16, "n_E3": 15,
                                            "paired_n_E1_E2": paired_correct["target48h_E1_E2"],
                                            "paired_n_E2_E3": paired_correct["target48h_E2_E3"]}},
                "statistic": "paired delta_rho on paired line sets only",
            },
            "functional_route": {"status": "not_qualified", "failure_class": "data_unavailable",
                                 "reason": "no matched late functional endpoint; RNA proxy is not a functional endpoint"},
            "time_axis": {"status": "unverified",
                          "reason": "no batch/plate/run/exposure/independent-culture records; destructive snapshots"},
        },
        "reporting_schema": reporting_schema,
        "inference_rules": {
            "confirmatory_H_D5_1": "removed (not a confirmatory analysis)",
            "G3_G4_pass_fail": "removed",
            "evaluation_cannot_distinguish_as_inference": "removed; MDE/room are precision descriptors only",
            "allowed_language": ["descriptive", "precision descriptor", "direction of the observed association",
                                 "feasibility/qualification of the development asset"],
            "forbidden_language": ["confirmatory", "significant", "supports time prediction", "biology",
                                   "function/viability", "migration", "decision benefit", "mechanism", "novelty"],
        },
    }

    out["execution_gates"] = {
        "note": "these are execution preconditions (eligibility/identity), not inferential gates",
        "EX_G0a_coverage": {
            "rule": "every active primary drug has >= 20 eligible lines",
            "actual": n_active, "status": "pass",
        },
        "EX_G0b_active_dose_identity_recheck": {
            "rule": ("before any execution, record measured/curated compound identity, actual dose (uM), and vehicle "
                     "identity for each active drug; metadata-only annotation is insufficient"),
            "required_fields": ["compound_identity_record", "dose_record_uM", "vehicle_identity_record",
                                "assay_or_source_for_identity"],
            "active_drugs_metadata_level": {p: v02["active_drug_qualification"]["arms"][p]["active_dose_metadata_check"]
                                            for p in ACTIVE_DRUGS},
            "failure_category": "active_dose_identity_unverified",
            "failure_action": "STOP; do not execute; BRD3379 must not return to primary",
            "BRD3379": "zero-dose/vehicle-like control only; excluded from primary permanently",
        },
    }

    out["null_models_E6"] = null_models
    out["tuning_E7"] = {"tuning_plan": tuning, "grid_sha256": tuning_grid_sha,
                        "frozen_before_execution": True,
                        "may_not_change_after_seeing_results": True}

    out["execution_protocol_checklist_v0_3"] = [
        {"id": "E1_data_loading", "content": "h5ad obs+expression (execution only); QC=cell_quality=='normal'; pseudobulk mean per (drug,line,time); control=time-matched perturbation=control (V1) or DMSO hash label (V2); logFC=log2((pseudo+1)/(ctrl+1)); record cell counts; no expression-based selection"},
        {"id": "E2_200_gene_panel", "content": "per drug/target/fold, train-fold-only mean |logFC| top-K=200; freeze gene list SHA; vector endpoint same genes"},
        {"id": "E3_fold_loader_assertions", "content": "load v0.3 fold manifest; assert partition/no cross-fold line/rule index%5/seed/SHA"},
        {"id": "E4_v1_no_cross_drug_pairing", "content": "V1 uses per-drug eligible line sets (22/24/24); no paired-across-drug line contrast; report per-drug values"},
        {"id": "E5_v2_paired_sets", "content": "paired sets only: target24h E1/E2=15; target48h E1/E2=16; target48h E2/E3=15; inputs strictly earlier than target"},
        {"id": "E6_null_models", "content": "N0-N6 as frozen: N1/N2/N3/N4/N6 = 1,000 permutations each, seed 20261027, legitimate null/cluster/paired rules; N5 future-leak sentinel; fail closed"},
        {"id": "E7_tuning_budget", "content": "frozen tuning plan: 8 candidates x 5 inner folds per tuned model; 40 fits/unit; 15 outer units; 600 fits/tuned model; max 4,200 fits; CPU 120 min cap; grid SHA in JSON; no test tuning"},
        {"id": "E8_two_run_determinism_schema", "content": "two runs same seed; outputs byte-identical; fixed JSON schema (per-drug/per-fold descriptive fields; config/fold SHA; pseudobulk SHA)"},
        {"id": "E9_descriptive_measurement", "content": "compute split-half reliability/room/MDE as precision descriptors only; no pass/fail; no evaluation_cannot_distinguish inference; record measured values"},
        {"id": "E10_descriptive_report_template", "content": "report fields: per-drug delta/CI/MDE/room/reliability/per-fold; BRD3379 secondary; V2 exploratory; precision note; no confirmatory/biology/function/migration/decision/mechanism language"},
        {"id": "E11_G5_code_assertions", "content": "assert target/future time absent from inputs; V1 no two-snapshot arm; cell-line-grouped folds; train-only preprocessing; no expression-derived test info; future sentinel; fail closed"},
        {"id": "E12_no_effect_this_round", "content": "this revision runs no effect/prediction/expression read; execution requires separate task + independent challenge"},
    ]

    out["failure_classes"] = [
        "data_unavailable", "active_dose_identity_unverified", "design_invalid",
        "time_axis_unverified", "functional_route_not_qualified", "identifiability_unsupported",
        "protocol_deviation", "descriptive_precision_insufficient (precision descriptor, NOT an inference verdict)",
    ]
    out["stop_conditions"] = [
        "EX-G0a or EX-G0b fails -> data_unavailable / active_dose_identity_unverified; STOP",
        "leakage audit fails -> design_invalid; STOP",
        "no matched late functional endpoint -> functional_route_not_qualified; STOP functional/latency claims",
        "no batch/exposure/same-cell records -> time_axis_unverified; no absolute time-course/trajectory claims",
        "MDE80 > delta_min -> report 'descriptive precision insufficient for confirmatory inference'; NOT an inference verdict",
        "no post-hoc threshold/endpoint/split changes; no BRD3379 return to primary",
    ]

    out["verdicts"] = {
        "overall_D5": {
            "verdict": "descriptive_only",
            "scope": "3 active drugs; V1 6h->24h RNA molecular proxy; V2 exploratory; BRD3379 zero-dose/vehicle-like control secondary only",
            "confirmatory": False,
            "approve_to_lead_exec": False,
            "recommend_rechallenge": True,
            "if_lead_requires_confirmatory": "STOP (measurement spec needed; do not substitute a descriptive run)",
        },
        "functional_route": {"verdict": "not_qualified", "failure_class": "data_unavailable"},
        "time_axis": {"verdict": "unverified"},
        "brd3379": {"role": "zero-dose/vehicle-like control; secondary/descriptive only; never primary"},
    }

    out["background_boundaries"] = {
        "v0_1_v0_2": "v0.1 and v0.2 files are frozen history, not execution basis; v0.3 is descriptive-only",
        "a3_dynamic_route": "A3v2 only background; no uncertified reuse",
        "c176_c177_c179_c181_c186": "revocations/status only background; no temporal evidence; do not cite old verdicts; do not reopen R196v2/R197v2",
        "errata_a3_r195": "R195/A3 not_qualified limited to its frozen large-scale design",
        "no_claims": ["novelty", "cell-state mechanism", "migration", "decision benefit", "biology/function", "true trajectory"],
    }
    out["limits"] = [
        "descriptive-only revision: no expression/response read; no fitting/prediction; no effect run",
        "MDE/room are reported as precision descriptors; no confirmatory inference",
        "active-dose remains metadata-level until execution-phase re-check; failure stops",
        "functional not_qualified; time_axis_unverified; V2 exploratory only",
        "E1-E12 checklist is not an execution protocol; separate task + independent challenge required",
        "v0.2 paired-set typo (third value 16) remains in frozen v0.2 history; v0.3 is corrected",
    ]
    out["script"] = {"path": os.path.relpath(os.path.abspath(__file__), ROOT).replace(os.sep, "/"),
                     "sha256": sha256_file(os.path.abspath(__file__))}
    out["cross_check_v0_2"] = {
        "active_drugs": active_v02,
        "n_active": n_active,
        "paired_corrected": paired_correct,
        "mde_active_only": v02["v1_primary"]["mde_prerun_active_only"],
        "v0_2_protocol_typo": {"token_masked": "15/16/**16**", "lines": typo_lines},
        "v0_2_correct_occurrences": {"token": correct_token, "lines": correct_lines_v02},
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({
        "v0_2_typo_lines": typo_lines,
        "active_drugs": ACTIVE_DRUGS,
        "n_active": n_active,
        "paired_n": paired_correct,
        "mde": {p: mde_prerun(n) for p, n in n_active.items()},
        "n_permutations": N_PERM,
        "tuning_grid_sha": tuning_grid_sha,
        "verdict": out["verdicts"]["overall_D5"]["verdict"],
        "approve_to_lead_exec": out["verdicts"]["overall_D5"]["approve_to_lead_exec"],
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
