"""Workstream C: assemble verification_complete.json from the per-task outputs."""
import json
import os
from datetime import datetime, timezone

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
V = os.path.join(S, "verification")


def j(name):
    with open(os.path.join(V, name), encoding="utf-8") as fh:
        return json.load(fh)


t1 = j("task1_comparison.json")
t1r = j("task1_residual_diagnostic.json")
t1b = j("task1_bootstrap.json")
t2 = j("task2_raw_bytes.json")
t2b = j("task2b_membership.json")
t3 = j("task3_leakage_timeorder.json")
t4 = j("task4_agent_records.json")
t5 = j("task5_accounting.json")
with open(os.path.join(S, "SPLIT.json"), encoding="utf-8") as fh:
    split = json.load(fh)


def line_table(block, keys):
    return {name: {k: {"verifier": v[k]["verifier"], "study": v[k]["study"], "abs_diff": v[k]["abs_diff"],
                       "rel_diff": v[k]["rel_diff"]} for k in keys} |
            {"eligible_groups": v["eligible_groups"]} for name, v in block.items()}


summary = {
    "workstream": "C (independent verifier)",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "scope_note": "All quantities recomputed with the verifier's own scripts in this folder; no study helper module "
                  "was imported. No LLM/API call. Network: HTTPS range GETs to the pinned Hugging Face revision only.",
    "tasks": {
        "1_primary_contrast_recomputation": {
            "pass": t1["pass"],
            "lines_recomputed": ["HOP62", "Hs 766T", "C32", "PANC-1", "HepG2/C3A"],
            "evaluation": line_table(t1["evaluation"], ("M0", "M2", "M2_minus_M0")),
            "development": line_table(t1["development"], ("M0", "M2_g0.5", "M2_minus_M0")),
            "pooled_M2_minus_M0": t1["pooled_evaluation"]["M2_minus_M0"],
            "worst_abs_relative_difference": t1["worst_abs_rel_diff"],
            "eligible_group_counts_identical": t1["eligible_counts_all_equal"],
            "residual_explanation": {
                "finding": "M0 agrees to <=1.5e-11 absolute; M2 to <=1.5e-10 absolute (relative <=4.8e-7).",
                "cause": "world_models.Panel stores training-context STATE paired deltas as float16 before averaging "
                         "(devS panel mean); the verifier works in float64. Emulating float16 storage reduces the M2 "
                         "residual from ~1.4e-10 to ~3e-12 (HOP62, PANC-1).",
                "diagnostic": t1r,
                "material": False,
            },
            "independent_drug_clustered_bootstrap": t1b,
            "notes": [
                "The depth-correction terms (panel noise and observation noise) are identical for M0 and M2, so they "
                "cancel in M2 - M0; the primary contrast does not depend on the noise model.",
                "Training panel: treated_summaries n equals the plan's full-QC count for every training group "
                "(0 mismatches); %d of 630 training (file, plate) DMSO groups have fewer than 50 full-QC reference "
                "cells, all in c36 (NCI-H2122) and c39 (NCI-H596) plus two plates of c44; minimum 4." % 30,
            ],
        },
        "2_raw_byte_integrity": {
            "pass": bool(t2["pass"] and t2b["pass"]),
            "records_refetched": t2["records_checked"],
            "files_covered": t2["files_covered"],
            "sha256_matches": "%d/%d" % (t2["sha256_matches"], t2["records_checked"]),
            "heldout_spans_equal_rows_npy": "%d/%d" % (t2["heldout_rows_npy_equal"], t2["heldout_records_compared_with_rows_npy"]),
            "training_control_spans_equal_rows_npy": "%d/%d" % (t2["training_control_rows_npy_equal"], t2["training_control_records_compared_with_rows_npy"]),
            "training_treated_summaries_reproduced_from_raw_bytes": "%d/%d" % (
                sum(x["match"] for x in t2["treated_summary_checks"]), len(t2["treated_summary_checks"])),
            "treated_summary_max_abs_mean_diff": max(x["max_abs_mean_diff"] for x in t2["treated_summary_checks"]),
            "treated_summary_max_rel_var_diff": max(x["max_rel_var_diff"] for x in t2["treated_summary_checks"]),
            "c39_local_copy": t2["c39_local_copy_check"],
            "membership_supplement": {
                "plan_rows_checked_all_heldout": sum(v["rows"] for v in t2b["local_all_rows"].values()),
                "label_plate_qc_mismatches": sum(v["label_mismatch"] + v["plate_mismatch"] + v["full_flag_mismatch"]
                                                 for v in t2b["local_all_rows"].values()),
                "c31_code_arrays_complete_remote_refetch_identical": all(
                    x["equals_cache"] and x["sha256_equals_census"] for x in t2b["remote_complete"]["c31.h5ad"].values()),
                "sampled_code_windows_other_heldout_files": sum(len(v) for v in t2b["remote_sampled"].values()),
                "pass": t2b["pass"],
            },
            "network": {"range_gets": t5["verifier_network_use"]["requests"] + 1,
                        "bytes": t5["verifier_network_use"]["bytes"] + 1, "cap_bytes": 60_000_000,
                        "failed": t5["verifier_network_use"]["failed"]},
        },
        "3_leakage_and_time_order": {
            "pass": all(t3["pass"].values()),
            "subchecks": t3["pass"],
            "a_state_inputs": {
                "static": "state_infer.basal_sets iterates control groups only and keeps rows with control_role == "
                          "'basal' and full == True; treated groups contribute only (label, plate); state_infer.py "
                          "SHA-256 equals the frozen protocol entry: %s" % t3["a_static_state_infer"]["code_matches_frozen_protocol"],
                "plates_checked": t3["a_state_data"]["plates"],
                "files_checked": t3["a_state_data"]["files"],
                "problems": t3["a_state_data"]["problems"],
                "basal_tensor_sha256_recomputed_mismatches": t3["a_state_data"]["basal_tensor_sha_mismatch"],
                "basal_mean_by_plate_max_abs_diff": t3["a_state_data"]["max_abs_basal_mean_diff"],
                "paired_delta_identity_max_abs_diff": t3["a_state_data"]["paired_delta_max_abs_diff"],
                "plates_sampled_with_replacement": len(t3["a_state_data"]["with_replacement_plates"]),
            },
            "b_denominator_and_disjointness": {
                "files_checked": list(t3["b_denominator"]["files"].keys()),
                "ctrl_n_equals_reference_n_all_plates": all(v["ctrl_n_equals_reference_n"] == v["plates"]
                                                            for v in t3["b_denominator"]["files"].values()),
                "max_abs_diff_study_ctrl_mean_vs_reference_mean": max(v["max_abs_mean_diff_vs_reference"]
                                                                      for v in t3["b_denominator"]["files"].values()),
                "min_diff_vs_basal_mean": min(v["min_max_abs_mean_diff_vs_basal"] for v in t3["b_denominator"]["files"].values()),
                "min_diff_vs_all_full_mean": min(v["min_max_abs_mean_diff_vs_all_full"] for v in t3["b_denominator"]["files"].values()),
                "plans_checked_for_disjointness": t3["b_disjointness"]["plans"],
                "control_groups_checked": t3["b_disjointness"]["control_groups"],
                "overlaps_found": len(t3["b_disjointness"]["problems"]),
            },
            "c_times": {"order": t3["c_times"]["order"], "internal": t3["c_times"]["internal_timestamps"],
                        "freezes": {k: v["mtime_utc"] for k, v in t3["c_times"]["freezes"].items()},
                        "pre_freeze_evaluation_line_artifacts": t3["c_times"]["pre_freeze_evaluation_line_artifacts"]},
            "d_hashes": {k: v for k, v in t3["d_hashes"].items() if k != "code_hashes"} |
                        {"code_hash_mismatches_now": t3["d_hashes"]["code_hashes"]},
            "e_split": {"recomputed_order": t3["e_split"]["recomputed_order"], "digests": t3["e_split"]["digests"],
                        "matches": t3["e_split"]["pass"],
                        "split_created_utc": split["created_utc"],
                        "first_x_hvg_row_fetch_utc": t5["stages"]["extract"]["first_utc"],
                        "split_precedes_first_expression_fetch": split["created_utc"] < t5["stages"]["extract"]["first_utc"]},
        },
        "4_agent_evaluation_records": {
            "pass": t4["pass"],
            "arms_required": ["A", "B"],
            "cases": {a: t4["arms"][a]["cases_in_jsonl"] for a in t4["arms"]},
            "mismatches": t4["mismatches"],
            "screens_per_case_A_B": sorted({c["screens_sqlite_purchased"] for a in ("A", "B") for c in t4["arms"][a]["per_case"]}),
            "validates_per_case_A_B": sorted({c["validates"] for a in ("A", "B") for c in t4["arms"][a]["per_case"]}),
            "budget_and_use_A_B": sorted({(c["budget_sqlite"], c["spent_sqlite"]) for a in ("A", "B") for c in t4["arms"][a]["per_case"]}),
            "max_V_abs_diff": max(c["V_abs_diff"] for a in t4["arms"] for c in t4["arms"][a]["per_case"]),
            "mean_V_recomputed": {a: t4["arms"][a]["mean_V_recomputed"] for a in t4["arms"]},
            "summary_json_consistency": t4["summary_json_consistency"],
            "extra_arms_noneA_noneB_pass": t4["pass_all_arms"],
            "note": "Arms A and B used all 8 screening units in every case (no early stop).",
        },
        "5_accounting": {
            "pass": t5["pass"],
            "per_stage": {k: {"ledger_files": v["ledger_files"], "requests": v["requests"],
                              "failed_requests": v["failed_requests"], "bytes": v["bytes"], "GB": v["GB"],
                              "retried_then_succeeded": v["retried_requests"], "purposes": v["purposes"],
                              "first_utc": v["first_utc"], "last_utc": v["last_utc"]}
                          for k, v in t5["stages"].items()},
            "totals": t5["totals"],
            "receipt_cross_check": t5["receipt_cross_check"],
        },
    },
    "discrepancies": [
        {"item": "M2 mean corrected SE differs from the study by up to 1.45e-10 absolute (relative <= 4.8e-7); "
                 "M0 by <= 1.5e-11.",
         "explanation": "float16 storage of training STATE forecasts in the study's panel mean; reproduced by "
                        "emulation (residual -> ~3e-12). Immaterial.", "material": False},
        {"item": "WORLD_PROTOCOL.json code_sha256['freeze_agent.py'] no longer matches the file.",
         "explanation": "freeze_agent.py was rewritten at 08:04:06.61 UTC, 12 s after WORLD_FREEZE and 0.85 s before "
                        "AGENT_FREEZE; AGENT_PROTOCOL records the current hash. All 21 other world-protocol code hashes "
                        "match. Does not affect the world evaluation.", "material": False},
        {"item": "DEVIATIONS.json dates its last entry (agent development gates) '~16:10' local.",
         "explanation": "DEVIATIONS.json was last modified at 16:03:53 local and agent_dev outputs at 16:00-16:03, "
                        "before both freezes; the '~16:10' label is wrong, not the order of events.", "material": False},
        {"item": "c39.h5ad (training context NCI-H596) has no census or extraction ledger.",
         "explanation": "Read from a local copy (data/external/arc_state/tahoe_metadata_source/c39.h5ad), as its "
                        "receipts state. Verifier fetched one control window from the pinned remote: identical to "
                        "rows.npy and to the local copy; file sizes equal.", "material": False},
    ],
    "observations_not_failures": [
        "532 of 700 STATE basal sets were drawn with replacement, all on training plates: training plates hold a "
        "median of 240 basal full-QC cells (range 4-282; 532 of 630 below 256, since 512 DMSO rows were sampled per "
        "plate), held-out plates 310-1049 (median 969; none with replacement). Training-panel STATE forecasts (the "
        "devS reference mean) therefore use partly duplicated 256-cell inputs; held-out forecasts do not.",
        "c36 and c39 have 4-38 full-QC reference DMSO cells per plate; their panel weights are small but their noise "
        "estimates rest on few cells.",
        "Evaluation-line raw rows (treated included) were on disk from 06:18-06:46 UTC and their STATE forecasts "
        "from 07:35-07:41 UTC, before the 08:03:54 freeze. Timestamps show the observation files were built after "
        "the freeze; they cannot show that the raw rows were not inspected earlier. That rests on the code guards.",
        "Not verified here: X_hvg column (gene) alignment across the 45 training files. The study's axis_check "
        "covers only the five held-out files against an identity receipt from c39 and c0-c2.",
    ],
}
summary["overall_pass"] = all(t["pass"] for t in summary["tasks"].values())
with open(os.path.join(V, "verification_complete.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=1, default=list)
print(json.dumps({k: v["pass"] for k, v in summary["tasks"].items()} | {"overall": summary["overall_pass"]}, indent=1))
