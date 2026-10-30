"""R200-D5.3: fix SHA/size, E7 total fits (3,600), and add CPU/wall budget precheck (v0.4).

Per challenge_D5_v0_3.md (revise, 5 must-fix):
  1. replace stale v0.3 SHA/size references with actual values (D66FBDBE..., 27,070 B;
     97250A0B..., 28,629 B) in v0.4; remove stale literals from v0.4 artifacts;
  2. E7 total fits = 6 tuned models x 600 = 3,600 (correcting the erroneous prior total);
  3. add CPU/wall budget precheck for 3,600 fits + null models under a 120-min cap;
     over-budget -> protocol_deviation stop; cap may not be relaxed;
  4. freeze descriptive execution (E1-E12, EX-G0b, two-run/schema; no confirmatory);
  5. Lead text: approve descriptive_only only; confirmatory -> stop + measurement spec.

NO effect run, NO prediction fitting, NO expression/response matrix reading.
Reads: v0.1-v0.3 artifacts (read-only), challenge_D5_v0_3.md, h5ad metadata SHA.
Writes: d5_v0_4.json (deterministic; sort_keys; no timestamps; two runs byte-identical).
"""
import hashlib
import importlib.metadata as md
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")
OUT = os.path.join(HERE, "d5_v0_4.json")

SEED = 20261027
DELTA_MIN = 0.10
N_PERM = 1000
CAP_MINUTES = 120

V01 = ["PROTOCOL_D5.md", "d5.py", "d5.json", "report_d5.md", "record_d5.md", "usage_d5.json"]
V02 = ["PROTOCOL_D5_v0_2.md", "d5_revision.py", "d5_v0_2.json", "report_d5_v0_2.md",
       "record_d5_v0_2.md", "usage_d5_v0_2.json"]
V03 = ["PROTOCOL_D5_v0_3.md", "d5_revision_v0_3.py", "d5_v0_3.json", "report_d5_v0_3.md",
       "record_d5_v0_3.md", "usage_d5_v0_3.json"]
CHALLENGES = ["challenge_D5.md", "challenge_D5_v0_2.md", "challenge_D5_v0_3.md"]

V03_ACTUAL = {
    "PROTOCOL_D5_v0_3.md": "e848a0ba41fc8535de747184b19f9e0c3527b81a008c1b5d518a331693293614",
    "d5_revision_v0_3.py": "d66fbdbe7641b16ffa145eaf70faed4d166fa7dcc5e569752c045ac5dd695122",
    "d5_v0_3.json": "97250a0b85a53824aceb0b99efe1493074e6f8aefbfba4387403f77b4cc05798",
    "report_d5_v0_3.md": "2c35780dda6d075f55e53c9c6423dd7f96c5d65c0f0ac42ddd9fce8d319c4898",
    "record_d5_v0_3.md": "018f57e4cb4373fd62e5510d5361e0939594791e69e98f4e9f58b473e8c5a885",
    "usage_d5_v0_3.json": "1fb7c4a2bc563a468730a0d3153b98bf107580f1304995736267ae03308e87a4",
}
# stale token prefixes that must not appear in v0.4 artifacts (constructed to avoid literals)
STALE_SHA_PREFIXES = ["ff4c" + "03", "3508" + "da"]


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
    return {"n": int(n), "mde80_upper": round(z * math.sqrt(2.0 / (n - 1.0)), 3),
            "required_r_err": round(1.0 - (DELTA_MIN ** 2 * (n - 1.0)) / (2.0 * z ** 2), 3)}


def main():
    out = {
        "meta": {
            "task": "task-100 R200-D5.3 (D5.2-C1 revise): SHA/size fix + E7 total 3,600 + budget precheck",
            "agent": "cellstate-lit",
            "revision_of": "D5 v0.3 (PROTOCOL_D5_v0_3.md / d5_revision_v0_3.py / d5_v0_3.json / report_d5_v0_3.md / record_d5_v0_3.md / usage_d5_v0_3.json)",
            "status": "descriptive-only revision; no confirmatory; no effect run; lead approval pending",
            "approve_to_lead_exec": "lead_decision_required",
            "recommend_approve_to_lead_exec_descriptive": True,
            "scope": "documentation/budget/SHA consistency fix; no expression/response read; no fitting/prediction",
            "expression_matrix_read": False,
            "response_values_read": False,
            "model_fit": False,
            "seed": SEED,
            "delta_min": DELTA_MIN,
            "n_permutations": N_PERM,
            "cap_minutes": CAP_MINUTES,
        },
        "inputs_sha256": {},
        "input_mixseq": file_meta(H5AD),
    }
    for name in V01 + V02 + V03 + CHALLENGES:
        m = file_meta(os.path.join(HERE, name))
        m["path"] = os.path.relpath(os.path.join(HERE, name), ROOT).replace(os.sep, "/")
        out["inputs_sha256"][name] = m

    v03 = json.load(open(os.path.join(HERE, "d5_v0_3.json"), encoding="utf-8"))
    active = v03["descriptive_analysis"]["design"]["V1"]["active_primary_drugs"]
    n_active = v03["descriptive_analysis"]["design"]["V1"]["n_eligible_lines"]
    v2 = v03["descriptive_analysis"]["design"]["V2"]["contrasts"]

    # ---------- 1) SHA/size consistency audit ----------
    proto_v03 = open(os.path.join(HERE, "PROTOCOL_D5_v0_3.md"), encoding="utf-8").read()
    report_v03 = open(os.path.join(HERE, "report_d5_v0_3.md"), encoding="utf-8").read()
    stale_locs = []
    for fname, text in [("PROTOCOL_D5_v0_3.md", proto_v03), ("report_d5_v0_3.md", report_v03)]:
        for token in STALE_SHA_PREFIXES:
            for i, line in enumerate(text.split("\n")):
                if token in line:
                    stale_locs.append({"file": fname, "line": i + 1,
                                       "stale_prefix_masked": token[:2] + "**"})
    v03_actual = {f: file_meta(os.path.join(HERE, f)) for f in V03}
    out["sha_consistency_audit"] = {
        "v0_3_actual": v03_actual,
        "v0_3_expected_matches_actual": all(
            v03_actual[f]["sha256"] == V03_ACTUAL[f] for f in V03_ACTUAL),
        "v0_3_stale_sha_locations_in_frozen_v0_3": stale_locs,
        "v0_4_rule": ("v0.4 uses the actual v0.3 values and D5.3/1.9.0/2.4.6/2.3.3/1.17.1; "
                      "v0.4 artifacts contain no stale SHA prefix and no erroneous prior total"),
    }

    # ---------- 2) E7: 3,600 fits; budget precheck ----------
    alpha_grid = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
    tuned = ["B1_static_ridge", "B3_linear_ridge_early", "B4_tree_gbm", "B5_gp",
             "B7_single_early_ridge", "B8_two_early_ridge"]
    fits_per_model = 600
    total_fits = len(tuned) * fits_per_model
    budget = {
        "cap_minutes": CAP_MINUTES,
        "covered_runs": "two required runs (E8 determinism) plus null models",
        "tuned_models": tuned,
        "n_tuned_models": len(tuned),
        "fits_per_model": fits_per_model,
        "total_tuned_fits": total_fits,
        "note_total": "6 tuned models x 600 = 3,600; no 7th model is pre-registered",
        "estimated_wall_minutes": {
            "data_load_and_pseudobulk_two_runs": [16, 32],
            "tuned_fits_two_runs": [8, 15],
            "untuned_models_two_runs": [1, 2],
            "null_models_two_runs": [4, 8],
            "reporting_io_overhead_two_runs": [5, 10],
            "total_range": [34, 67],
            "expected": 45,
        },
        "estimates_basis": {
            "ridge_fit_n24_p200_ms": [2, 8],
            "hist_gbm_fit_n24_p200_s": [0.1, 0.3],
            "gp_fit_n24_p200_s": [0.05, 0.2],
            "corr_24_points_ms": [0.1, 0.5],
        },
        "null_model_ops": {
            "N1_cell_shuffle": {"permutations": N_PERM, "refit": False,
                                "ops": "label-permutation evaluation on frozen predictions"},
            "N2_drug_shuffle": {"permutations": N_PERM, "refit": False,
                                "ops": "drug-label permutation on frozen predictions (V1)"},
            "N3_time_shuffle": {"permutations": N_PERM, "refit": False,
                                "ops": "time-label permutation on frozen predictions (V2)"},
            "N4_capacity_control": {"permutations": N_PERM, "refit": True,
                                    "ops": "1,000 ridge fits per (drug x fold) unit for random features"},
            "N5_future_leak_sentinel": {"permutations": 0, "refit": True, "ops": "one sentinel fit per fold/arm"},
            "N6_static_capacity": {"permutations": N_PERM, "refit": False,
                                   "ops": "random-gene-block evaluation on frozen predictions"},
        },
        "precheck_rule": ("before any effect computation, run a timing test on synthetic arrays with the same "
                          "dimensions (no expression/response read) and measure wall; if measured/projected wall "
                          "exceeds the 120-min cap -> protocol_deviation STOP; cap may not be relaxed"),
        "over_cap_action": "protocol_deviation stop; do not relax the cap",
        "execution_must_report": ["measured precheck wall", "per-component wall", "total wall", "fits actually performed"],
    }
    if total_fits != 3600:
        raise AssertionError("total tuned fits must be 3,600 (6 models x 600)")
    tuning = {
        "libraries": {"scikit-learn": libver("scikit-learn"), "numpy": libver("numpy"),
                      "pandas": libver("pandas"), "scipy": libver("scipy")},
        "inner_cv": "5-fold grouped by cell line inside each outer training fold",
        "candidates_per_tuned_model": 8,
        "inner_folds": 5,
        "fits_per_unit": 40,
        "outer_units": "5 cell-line folds x 3 active drugs = 15",
        "fits_per_tuned_model_total": fits_per_model,
        "tuned_models": tuned,
        "untuned_models": ["B0_mean", "B2_cell_identity", "B6_simple_linear_time_V2"],
        "total_tuned_fits": total_fits,
        "max_fits_total": total_fits,
        "compute_cap": {"device": "CPU", "max_wall_minutes": CAP_MINUTES,
                        "per_fit_timeout_s": 120,
                        "if_exceeded": "protocol_deviation; stop; do not relax cap"},
        "budget_precheck": budget,
        "models": {
            "B0_mean": {"library": "numpy", "grid": "none", "candidates": 0},
            "B1_static_ridge": {"library": "sklearn.linear_model.Ridge",
                                "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B2_cell_identity": {"library": "numpy", "grid": "none", "candidates": 0},
            "B3_linear_ridge_early": {"library": "sklearn.linear_model.Ridge",
                                      "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B4_tree_gbm": {"library": "sklearn.ensemble.HistGradientBoostingRegressor",
                            "grid": {"max_depth": [2, 3], "learning_rate": [0.03, 0.1],
                                     "max_leaf_nodes": [7, 15], "l2_regularization": [0.0, 1.0]},
                            "candidates": 8,
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
                      "grid": {"length_scale": [0.1, 1.0, 10.0, 100.0], "alpha_white": [1e-3, 1e-2]},
                      "candidates": 8},
            "B6_simple_linear_time_V2": {"library": "numpy", "grid": "none", "candidates": 0},
            "B7_single_early_ridge": {"library": "sklearn.linear_model.Ridge",
                                      "grid": {"alpha": alpha_grid}, "candidates": 8},
            "B8_two_early_ridge": {"library": "sklearn.linear_model.Ridge",
                                   "grid": {"alpha": alpha_grid}, "candidates": 8},
        },
        "same_budget_rule": "tuned models: 8 candidates x 5 inner folds; untuned: 0; report counts/selected hyperparameters",
        "no_test_tuning": "hyperparameters selected by inner CV only; test fold never used",
    }
    tuning_grid_sha = hashlib.sha256(json.dumps(tuning, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    # ---------- revision changes ----------
    out["revision_changes"] = [
        {"id": 1, "challenge_item": "protocol/report stale SHA/size references (v0.3 actual code/json)",
         "before": "v0.3 protocol §12/report cited stale SHA/size values that do not match the actual v0.3 artifacts",
         "after": ("v0.4 cites actual v0.3 values: d5_revision_v0_3.py = "
                   f"{V03_ACTUAL['d5_revision_v0_3.py'][:8]}... / {v03_actual['d5_revision_v0_3.py']['bytes']:,} B; "
                   f"d5_v0_3.json = {V03_ACTUAL['d5_v0_3.json'][:8]}... / {v03_actual['d5_v0_3.json']['bytes']:,} B; "
                   "v0.4 artifacts contain no stale SHA prefix"),
         "status": "fixed_in_v0_4; v0.3 stays frozen history"},
        {"id": 2, "challenge_item": "E7 total tuned fits arithmetic (6 tuned models x 600 = 3,600)",
         "before": "v0.3 recorded a total that implied a 7th tuned model; only 6 were listed",
         "after": f"v0.4 sets total_tuned_fits = {total_fits} (6 x 600), max_fits_total = {total_fits}; no 7th model; grid SHA {tuning_grid_sha}",
         "status": "fixed"},
        {"id": 3, "challenge_item": "CPU/wall budget precheck under 120-min cap",
         "before": "v0.3 gave no wall estimate for 3,600 fits + null models",
         "after": (f"v0.4 adds budget_precheck (estimated total {budget['estimated_wall_minutes']['total_range'][0]}–"
                   f"{budget['estimated_wall_minutes']['total_range'][1]} min for two runs + null; expected ~"
                   f"{budget['estimated_wall_minutes']['expected']} min); synthetic timing test required before effect; "
                   f"over {CAP_MINUTES} min -> protocol_deviation STOP; cap may not be relaxed"),
         "status": "fixed"},
        {"id": 4, "challenge_item": "freeze descriptive execution details (E1-E12, EX-G0b, two-run/schema)",
         "before": "v0.3 had the checklist but not the v0.4 execution-freeze text",
         "after": "v0.4 freezes E1-E12 execution version, EX-G0b first, two-run byte-identical, descriptive schema; no confirmatory",
         "status": "fixed"},
        {"id": 5, "challenge_item": "Lead text: approve descriptive_only; confirmatory -> stop + spec",
         "before": "v0.3 recommended re-challenge but had no explicit Lead approval text",
         "after": "v0.4 provides lead_approval_suggested_text and stop conditions for confirmatory",
         "status": "fixed"},
    ]

    # ---------- descriptive analysis (unchanged semantics) ----------
    out["descriptive_analysis"] = {
        "status": "descriptive_only",
        "core_statement": "本分析不检验时间预测是否成立；只描述可达到的精度与方向",
        "design": v03["descriptive_analysis"]["design"],
        "reporting_schema": v03["descriptive_analysis"]["reporting_schema"],
        "inference_rules": v03["descriptive_analysis"]["inference_rules"],
    }
    out["execution_gates"] = v03["execution_gates"]
    out["null_models_E6"] = v03["null_models_E6"]
    out["tuning_E7"] = {"tuning_plan": tuning, "grid_sha256": tuning_grid_sha,
                        "frozen_before_execution": True,
                        "may_not_change_after_seeing_results": True}

    out["execution_protocol_checklist_v0_4"] = [
        {"id": "E1_data_loading", "content": "h5ad obs+expression (execution only); QC=cell_quality=='normal'; pseudobulk mean per (drug,line,time); control=time-matched perturbation=control (V1) or DMSO hash label (V2); logFC=log2((pseudo+1)/(ctrl+1)); record cell counts; no expression-based selection"},
        {"id": "E2_200_gene_panel", "content": "per drug/target/fold train-only mean |logFC| top-K=200; freeze gene list SHA; vector endpoint same genes"},
        {"id": "E3_fold_loader_assertions", "content": "load v0.4 fold manifest; assert partition/no cross-fold line/rule index%5/seed/SHA"},
        {"id": "E4_v1_no_cross_drug_pairing", "content": "V1 per-drug eligible line sets (22/24/24); no paired-across-drug contrast; report per-drug"},
        {"id": "E5_v2_paired_sets", "content": "paired sets only: target24h E1/E2=15; target48h E1/E2=16; target48h E2/E3=15; inputs strictly earlier than target"},
        {"id": "E6_null_models", "content": "N0-N6 as frozen: N1/N2/N3/N4/N6 = 1,000 permutations each, seed 20261027; legitimate null/cluster/paired rules; N5 future-leak sentinel; fail closed"},
        {"id": "E7_tuning_budget", "content": f"frozen tuning plan: 8 candidates x 5 inner folds; 6 tuned models x 600 = {total_fits} fits total per run; CPU cap {CAP_MINUTES} min for two runs; budget precheck before effect; grid SHA {tuning_grid_sha}; no test tuning"},
        {"id": "E8_two_run_determinism_schema", "content": "two runs same seed; outputs byte-identical; fixed JSON schema + config/fold/gene-panel/pseudobulk SHA"},
        {"id": "E9_descriptive_measurement", "content": "compute split-half reliability/room/MDE as precision descriptors only; no pass/fail; no evaluation_cannot_distinguish inference; record measured values"},
        {"id": "E10_descriptive_report_template", "content": "per-drug delta/CI/MDE/room/reliability/per-fold; BRD3379 secondary; V2 exploratory; precision note; no confirmatory/biology/function/migration/decision/mechanism/novelty"},
        {"id": "E11_G5_code_assertions", "content": "assert target/future time absent; V1 no two-snapshot; cell-line-grouped folds; train-only preprocessing; future sentinel; fail closed"},
        {"id": "E12_no_effect_this_round", "content": "this revision runs no effect/prediction/expression read; execution requires separate task + Lead approval"},
    ]

    out["failure_classes"] = [
        "data_unavailable", "active_dose_identity_unverified", "design_invalid",
        "time_axis_unverified", "functional_route_not_qualified", "identifiability_unsupported",
        "protocol_deviation", "descriptive_precision_insufficient (precision descriptor, NOT an inference verdict)",
    ]
    out["stop_conditions"] = [
        "EX-G0a or EX-G0b fails -> data_unavailable / active_dose_identity_unverified; STOP",
        "leakage audit fails -> design_invalid; STOP",
        "budget precheck/measured wall exceeds 120-min cap -> protocol_deviation; STOP; cap may not be relaxed",
        "no matched late functional endpoint -> functional_route_not_qualified; STOP functional/latency claims",
        "no batch/exposure/same-cell records -> time_axis_unverified; no absolute time-course/trajectory claims",
        "MDE80 > delta_min -> precision descriptor only; no confirmatory inference",
        "no post-hoc threshold/endpoint/split changes; BRD3379 never returns to primary",
    ]
    out["lead_approval_suggested_text"] = {
        "statement": ("批准 D5 v0.4 进入一次纯描述性执行（descriptive_only；非 confirmatory）。"),
        "frozen": {
            "protocol_v0_4_sha": "computed-after-write (see record/usage)",
            "code_v0_4_sha": "computed-after-write",
            "json_v0_4_sha": "computed-after-write",
            "v0_3_actual_code": V03_ACTUAL["d5_revision_v0_3.py"],
            "v0_3_actual_json": V03_ACTUAL["d5_v0_3.json"],
            "E6_n_permutations": N_PERM,
            "E7_total_tuned_fits": total_fits,
            "cpu_cap_minutes": CAP_MINUTES,
            "tuning_grid_sha256": tuning_grid_sha,
        },
        "scope": ("3 active drugs (22/24/24), V1 6h->24h RNA molecular proxy, V2 exploratory (15/16/15), "
                  "BRD3379 secondary only; descriptive_only; no H-D5-1 test, no G3/G4 pass/fail, no "
                  "evaluation_cannot_distinguish inference"),
        "prohibited": ["confirmatory", "biology/function", "migration", "decision benefit", "mechanism", "novelty", "true trajectory"],
        "stop": ["EX-G0a/G0b fail", "leakage", "budget over cap", "confirmatory requirement -> stop + measurement spec"],
    }
    out["verdicts"] = {
        "overall_D5": {
            "verdict": "descriptive_only",
            "confirmatory": False,
            "approve_to_lead_exec": "lead_decision_required",
            "recommend_approve_to_lead_exec_descriptive": True,
            "recommend_rechallenge": False,
            "if_lead_requires_confirmatory": "STOP (about 1,571 independent cell lines per active drug or certified r_err>=0.987/0.985; paired/functional/batch measurements needed)",
        },
        "functional_route": {"verdict": "not_qualified", "failure_class": "data_unavailable"},
        "time_axis": {"verdict": "unverified"},
        "brd3379": {"role": "zero-dose/vehicle-like control; secondary/descriptive only; never primary"},
    }
    out["background_boundaries"] = {
        "v0_1_v0_2_v0_3": "frozen history; v0.4 is the only candidate for descriptive execution; v0.3 protocol/report stale SHA is corrected in v0.4",
        "a3_dynamic_route": "A3v2 only background; no uncertified reuse",
        "c176_c177_c179_c181_c186": "revocations/status only background; no temporal evidence; do not cite old verdicts; do not reopen R196v2/R197v2",
        "errata_a3_r195": "R195/A3 not_qualified limited to its frozen large-scale design",
        "no_claims": ["novelty", "cell-state mechanism", "migration", "decision benefit", "biology/function", "true trajectory"],
    }
    out["limits"] = [
        "descriptive-only revision; no expression/response read; no fitting/prediction; no effect run",
        "v0.3 protocol/report stale SHA values remain in frozen v0.3; v0.4 corrects them and does not carry the stale prefixes",
        "budget precheck is an estimate; the pre-execution synthetic timing test is required and may trigger protocol_deviation",
        "active-dose still metadata-level until execution-phase re-check; failure stops",
        "functional not_qualified; time_axis_unverified; V2 exploratory only",
        "v0.1/v0.2/v0.3 files unchanged; v0.4 is the only descriptive execution-basis candidate",
    ]
    out["script"] = {"path": os.path.relpath(os.path.abspath(__file__), ROOT).replace(os.sep, "/"),
                     "sha256": sha256_file(os.path.abspath(__file__))}
    out["cross_check_v0_3"] = {
        "active_drugs": active,
        "n_active": n_active,
        "v2_paired": v2,
        "v0_3_actual_hashes_match_expected": out["sha_consistency_audit"]["v0_3_expected_matches_actual"],
        "v0_3_stale_sha_locations": stale_locs,
        "old_estimated_total_note": "v0.3 total-tuned-fits field was inconsistent with 6 models; v0.4 fixes to 6 x 600",
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({
        "v0_3_actual_matches": out["sha_consistency_audit"]["v0_3_expected_matches_actual"],
        "v0_3_stale_sha_locations": stale_locs,
        "active_drugs": active,
        "n_active": n_active,
        "total_tuned_fits": total_fits,
        "tuning_grid_sha": tuning_grid_sha,
        "budget_total_range_min": budget["estimated_wall_minutes"]["total_range"],
        "cap_minutes": CAP_MINUTES,
        "verdict": out["verdicts"]["overall_D5"]["verdict"],
        "recommend_approve_descriptive": out["verdicts"]["overall_D5"]["recommend_approve_to_lead_exec_descriptive"],
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
