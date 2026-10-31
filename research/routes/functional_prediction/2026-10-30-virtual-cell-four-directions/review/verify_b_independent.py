"""B1/v1.1 independent output arithmetic and split/eligibility verification.

No fitting, primary implementation import, primary scores, or official held-out
data. Rarity and metrics are reconstructed from the original train-only CSR.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np


REVIEW = Path(__file__).resolve().parent
EPISODE = REVIEW.parent
ROOT = Path(r"D:\MAESTRO")
TRAIN = ROOT / "data/external/virtual_cell_four_directions_20261030/assaybench"
DEFAULT_RUN = ROOT / "data/processed/virtual_cell_four_directions_20261030/pilot_b_maestro"
COMPONENT = {"27260156", "29083409", "29038160", "27760321", "28162770"}
CANDIDATE = "conditional_residual"
DIAGNOSTIC = "permuted_context"
BASELINES = [
    "global", "source_balanced_global", "screen_type", "balanced_screen_type",
    "coarse_phenotype", "balanced_coarse_phenotype", "rationale", "balanced_rationale",
    "official_style_knn", "same_info_knn", "balanced_same_info_knn",
    "full_rank_ridge", "nonlinear_tree",
]
METHODS = set(BASELINES + [CANDIDATE, DIAGNOSTIC])
FITNESS = "Fitness / Proliferation / Viability"
DRUG = "Drug / Chemical / Environmental Response"
METRICS = ["precision", "recall", "prevalence", "adjusted_precision"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    require(bool(rows), f"No rows to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_id(value):
    match = re.fullmatch(r"(?:PMID)?(\d+)", str(value).strip())
    require(match is not None, f"Unexpected source identifier: {value!r}")
    return match.group(1)


def canonical(value):
    source = source_id(value)
    return "29083409" if source in COMPONENT else source


def fold_for(group):
    digest = hashlib.sha256(("maestro-vc-b1:" + group).encode()).hexdigest()
    return int(digest[:8], 16) % 5


def endpoint_reason(row):
    category = row["screen_category"]
    if category == "unidirectional":
        return ""
    if category == "bidirectional" and row["dataset_name"].endswith(("_dec", "_inc")):
        return ""
    if category == "bidirectional":
        return "merged_any_direction"
    if category == "recovered_bidirectional":
        return "recovered_bidirectional"
    raise ValueError(f"Unexpected endpoint category: {category!r}")


def average(values):
    available = [value for value in values if value is not None]
    return float(np.mean(available)) if available else None


def aggregate(rows, evaluation, method, subset):
    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(row)
    result = {"evaluation": evaluation, "method": method, "subset": subset,
              "eligible_tasks": len(rows), "eligible_groups": len(by_group),
              "zero_hit_tasks": sum(row["available_true_hits"] == 0 for row in rows),
              "available_true_hits": sum(row["available_true_hits"] for row in rows)}
    for metric in METRICS:
        group_means = [average([row[metric] for row in members]) for members in by_group.values()]
        result[metric + "_source_macro"] = average(group_means)
        result[metric + "_task_weighted"] = average([row[metric] for row in rows])
        result[metric + "_defined_groups"] = sum(value is not None for value in group_means)
        result[metric + "_defined_tasks"] = sum(row[metric] is not None for row in rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    run_dir = parser.parse_args().run_dir
    paths = {
        "training_metadata": TRAIN / "biogrid_temporal_train_metadata.csv",
        "training_csr": TRAIN / "biogrid_temporal_train_gene_hits_csr.npz",
        "roster": run_dir / "roster.csv", "predictions": run_dir / "top50.json",
        "protocol": EPISODE / "protocol_b.md", "protocol_v1_1": EPISODE / "protocol_b_v1_1.md",
    }
    metadata = read_csv(paths["training_metadata"])
    require(len(metadata) == 1349, "Expected exactly 1,349 official training rows")
    require(all(row["yearfold0"] == "train" for row in metadata), "Nontraining row in training metadata")
    meta_by_name = {row["dataset_name"]: row for row in metadata}
    require(len(meta_by_name) == len(metadata), "Duplicate training metadata dataset_name")
    valid_meta = {name: row for name, row in meta_by_name.items() if not endpoint_reason(row)}
    excluded = [{"dataset_name": name, "reason": endpoint_reason(row)}
                for name, row in meta_by_name.items() if endpoint_reason(row)]
    require(len(valid_meta) == 1231, "Frozen endpoint rule did not yield exactly 1,231 rows")

    # Only schema-listed arrays in the official-training-only cache are opened.
    with np.load(paths["training_csr"], allow_pickle=False) as archive:
        genes = archive["genes"].astype(str).tolist()
        names = archive["dataset_names"].astype(str).tolist()
        measured_indices, measured_indptr = archive["measured_indices"], archive["measured_indptr"]
        hit_indices, hit_indptr = archive["hit_indices"], archive["hit_indptr"]
        declared_shape = tuple(int(value) for value in archive["shape"])
    require(len(set(genes)) == len(genes), "Duplicate gene symbols in CSR vocabulary")
    require(len(set(names)) == len(names) and set(names) == set(meta_by_name), "CSR/metadata task universe differs")
    require(declared_shape == (len(names), len(genes)), "CSR declared shape differs from task/gene arrays")
    measured = np.zeros(declared_shape, dtype=bool)
    hits = np.zeros(declared_shape, dtype=bool)
    for label, indices, pointers, target in [
        ("measured", measured_indices, measured_indptr, measured),
        ("hit", hit_indices, hit_indptr, hits),
    ]:
        require(len(pointers) == len(names) + 1 and pointers[0] == 0 and pointers[-1] == len(indices), f"Invalid {label} CSR pointers")
        require(bool(np.all(np.diff(pointers) >= 0)), f"Nonmonotone {label} CSR pointers")
        require(bool(np.all((indices >= 0) & (indices < len(genes)))), f"Out-of-range {label} gene index")
        for index in range(len(names)):
            values = indices[pointers[index]:pointers[index + 1]]
            require(len(np.unique(values)) == len(values), f"Duplicate {label} gene within {names[index]}")
            target[index, values] = True
    require(not bool(np.any(hits & ~measured)), "A hit is absent from its measured library")
    name_to_row = {name: index for index, name in enumerate(names)}

    roster = read_csv(paths["roster"])
    roster_by_name = {row["dataset_name"]: row for row in roster}
    require(len(roster_by_name) == len(roster), "Duplicate roster task")
    require(set(roster_by_name) == set(valid_meta), "Roster must include every and only the 1,231 valid training endpoints")
    groups, folds = {}, {}
    for name, row in roster_by_name.items():
        original = valid_meta[name]
        group = canonical(original["source_id"])
        fold = fold_for(group)
        require(source_id(row["source_id"]) == source_id(original["source_id"]), f"Roster source mismatch: {name}")
        require(source_id(row["group"]) == group, f"Incorrect five-source canonical group: {name}")
        require(int(row["fold"]) == fold, f"Incorrect SHA256 outer fold: {name}")
        for field in ["screen_category", "cleaned_phenotype"]:
            require(row[field] == original[field], f"Roster metadata mismatch in {field}: {name}")
        groups[name], folds[name] = group, fold
    component_present = sorted({source_id(row["source_id"]) for row in valid_meta.values()} & COMPONENT)
    group_names = sorted(set(groups.values()))
    group_rows = {group: [name_to_row[name] for name in valid_meta if groups[name] == group] for group in group_names}

    rarity, eligible, task_libraries, fold_audit, task_eligibility = {}, set(), {}, [], []
    for fold in range(5):
        final_fit_names = [name for name in valid_meta if folds[name] != fold]
        fit_rows = [name_to_row[name] for name in final_fit_names]
        measured_count = measured[fit_rows].sum(axis=0, dtype=np.int64)
        hit_count = hits[fit_rows].sum(axis=0, dtype=np.int64)
        final_fit_groups = [group for group in group_names if fold_for(group) != fold]
        support = np.zeros(len(genes), dtype=np.int64)
        for group in final_fit_groups:
            support += np.any(measured[group_rows[group]], axis=0)
        # Integer comparison exactly implements p <= .10 without float-boundary drift.
        rarity[fold] = (10 * hit_count <= measured_count) & (support >= 3)
        frequency = np.divide(hit_count, measured_count, out=np.zeros(len(genes), dtype=float), where=measured_count > 0)
        test_names = [name for name in valid_meta if folds[name] == fold]
        for name in test_names:
            index = name_to_row[name]
            rare_library = measured[index] & rarity[fold]
            rare_library_size = int(rare_library.sum())
            task_eligibility.append({
                "dataset_name": name, "group": groups[name], "fold": fold,
                "measured_genes": int(measured[index].sum()), "fit_defined_rare_measured_genes": rare_library_size,
                "eligible": rare_library_size >= 50,
                "exclusion_reason": "" if rare_library_size >= 50 else "fewer_than_50_fit_defined_rare_measured_genes",
            })
            if rare_library_size >= 50:
                eligible.add(name)
                task_libraries[(name, "all")] = measured[index]
                task_libraries[(name, "rare")] = rare_library
        test_groups = [group for group in group_names if fold_for(group) == fold]
        validation_groups = [group for group in group_names if fold_for(group) == (fold + 1) % 5]
        inner_fit_groups = [group for group in group_names if group not in test_groups + validation_groups]
        require(not (set(test_groups) & set(final_fit_groups)), "Test/final-fit group overlap")
        require(not (set(inner_fit_groups) & (set(test_groups) | set(validation_groups))), "Inner fit/validation/test group overlap")
        fold_audit.append({
            "fold": fold, "test_groups": test_groups, "validation_groups": validation_groups,
            "inner_fit_groups": inner_fit_groups, "final_fit_groups": final_fit_groups,
            "final_fit_tasks": len(fit_rows), "test_valid_endpoints": len(test_names),
            "eligible_test_tasks": sum(name in eligible for name in test_names),
            "fit_defined_rare_genes": int(rarity[fold].sum()),
            "rare_gene_index_sha256": hashlib.sha256(np.flatnonzero(rarity[fold]).astype("<i8").tobytes()).hexdigest(),
            "fit_gene_hit_frequency_sha256": hashlib.sha256(frequency.astype("<f8").tobytes()).hexdigest(),
            "canonical_source_support_sha256": hashlib.sha256(support.astype("<i8").tobytes()).hexdigest(),
        })
    require(bool(eligible), "No task meets fit-defined rare-library eligibility")

    payload = json.loads(paths["predictions"].read_text(encoding="utf-8"))
    require(payload["gene_symbols"] == genes, "Prediction index vocabulary differs from original train CSR")
    predictions = payload["predictions"]
    observed_keys, scores = set(), []
    for prediction in predictions:
        name, method, subset = prediction["dataset_name"], prediction["method"], prediction["subset"]
        key = name, method, subset
        require(key not in observed_keys, f"Duplicate prediction: {key}")
        observed_keys.add(key)
        require(name in eligible, f"Prediction is not an eligible held-out training endpoint: {key}")
        require(method in METHODS and subset in {"all", "rare"}, f"Unexpected method/subset: {key}")
        picks = prediction["genes"]
        require(isinstance(picks, list) and len(picks) == 50 and all(type(value) is int for value in picks), f"Need exactly 50 integer gene indices: {key}")
        require(len(set(picks)) == 50 and min(picks) >= 0 and max(picks) < len(genes), f"Duplicate/out-of-range gene picks: {key}")
        library = task_libraries[(name, subset)]
        require(bool(np.all(library[picks])), f"Unmeasured or nonrare pick: {key}")
        row_index = name_to_row[name]
        available_hits = int(np.count_nonzero(hits[row_index] & library))
        library_size = int(library.sum())
        picked_hits = int(hits[row_index, picks].sum())
        precision, prevalence = picked_hits / 50, available_hits / library_size
        scores.append({
            "dataset_name": name, "source_id": source_id(valid_meta[name]["source_id"]),
            "group": groups[name], "fold": folds[name], "method": method, "subset": subset,
            "screen_category": valid_meta[name]["screen_category"], "cleaned_phenotype": valid_meta[name]["cleaned_phenotype"],
            "prediction_type": "ranked", "eligible_library_size": library_size,
            "available_true_hits": available_hits, "picked_hits": picked_hits,
            "precision": precision, "recall": picked_hits / available_hits if available_hits else None,
            "prevalence": prevalence,
            "adjusted_precision": (precision - prevalence) / (1 - prevalence) if prevalence < 1 else None,
        })
    expected_keys = {(name, method, subset) for name in eligible for method in METHODS for subset in ["all", "rare"]}
    require(observed_keys == expected_keys, f"Method/all/rare task sets differ; missing={len(expected_keys - observed_keys)}, extra={len(observed_keys - expected_keys)}")

    # Uniform-ranking expectation uses the same observed library and task set.
    exemplar = {(row["dataset_name"], row["subset"]): row for row in scores if row["method"] == CANDIDATE}
    for row in exemplar.values():
        expected = dict(row)
        expected.update({"method": "random_expectation", "prediction_type": "uniform_expectation",
                         "picked_hits": None, "precision": row["prevalence"],
                         "recall": 50 / row["eligible_library_size"] if row["available_true_hits"] else None,
                         "adjusted_precision": 0.0 if row["prevalence"] < 1 else None})
        scores.append(expected)
    scores.sort(key=lambda row: (row["dataset_name"], row["method"], row["subset"]))

    summary = []
    by_method_subset = defaultdict(list)
    for row in scores:
        by_method_subset[(row["method"], row["subset"])].append(row)
    for (method, subset), members in sorted(by_method_subset.items()):
        selections = {
            "overall": members,
            "non_fitness": [row for row in members if row["cleaned_phenotype"] != FITNESS],
            "drug_response": [row for row in members if row["cleaned_phenotype"] == DRUG],
            "preset_source_sensitivity": [row for row in members if row["group"] not in {"29083409", "30971826"}],
        }
        for evaluation, selected in selections.items():
            summary.append(aggregate(selected, evaluation, method, subset))
    lookup = {(row["evaluation"], row["method"], row["subset"]): row for row in summary}

    def score(method, subset="rare", evaluation="overall"):
        return lookup[(evaluation, method, subset)]["precision_source_macro"]

    def best_baseline(evaluation="overall", subset="rare"):
        available = [method for method in BASELINES if score(method, subset, evaluation) is not None]
        return min(available, key=lambda method: (-score(method, subset, evaluation), method)) if available else None

    best = best_baseline()
    best_all = best_baseline(subset="all")
    source_values = defaultdict(list)
    for row in scores:
        if row["subset"] == "rare" and row["method"] in {CANDIDATE, best}:
            source_values[(row["group"], row["method"])].append(row["precision"])
    paired = []
    for group in sorted({groups[name] for name in eligible}):
        a, b = average(source_values[(group, CANDIDATE)]), average(source_values[(group, best)])
        paired.append({"group": group, "fold": fold_for(group), "candidate_precision": a,
                       "baseline_precision": b, "candidate_minus_baseline": a - b,
                       "eligible_tasks": sum(groups[name] == group for name in eligible)})
    differences = np.array([row["candidate_minus_baseline"] for row in paired])
    rng = np.random.default_rng(1030)
    bootstrap = differences[rng.integers(0, len(differences), size=(2000, len(differences)))].mean(axis=1)
    lower, upper = [float(value) for value in np.percentile(bootstrap, [2.5, 97.5])]
    fold_differences = []
    for fold in range(5):
        members = [row for row in paired if row["fold"] == fold]
        fold_differences.append({"fold": fold, "eligible_groups": len(members),
                                 "candidate_minus_fixed_baseline": average([row["candidate_minus_baseline"] for row in members])})
    subset_inputs = {}
    for evaluation in ["non_fitness", "drug_response"]:
        rival = best_baseline(evaluation)
        candidate_score = score(CANDIDATE, evaluation=evaluation)
        baseline_score = score(rival, evaluation=evaluation) if rival else None
        n_groups = lookup[(evaluation, CANDIDATE, "rare")]["eligible_groups"]
        subset_inputs[evaluation] = {"eligible_groups": n_groups, "minimum_10_groups_met": n_groups >= 10,
                                    "candidate_precision": candidate_score, "best_baseline": rival,
                                    "best_baseline_precision": baseline_score,
                                    "candidate_exceeds_best_baseline": candidate_score > baseline_score if baseline_score is not None else None}
    candidate_score, baseline_score = score(CANDIDATE), score(best)
    absolute_gain = candidate_score - baseline_score
    improving_folds = sum(row["candidate_minus_fixed_baseline"] is not None and row["candidate_minus_fixed_baseline"] > 0 for row in fold_differences)
    gate_inputs = {
        "fixed_best_overall_rare_baseline": best, "candidate_rare_precision": candidate_score,
        "best_baseline_rare_precision": baseline_score, "absolute_gain": absolute_gain,
        "relative_gain": absolute_gain / baseline_score if baseline_score else None,
        "absolute_margin_0_05_met": absolute_gain >= 0.05,
        "relative_margin_20_percent_met": candidate_score >= 1.20 * baseline_score,
        "paired_source_bootstrap_95_percent": [lower, upper], "bootstrap_lower_above_zero": lower > 0,
        "improving_outer_folds": improving_folds, "at_least_3_of_5_folds_improve": improving_folds >= 3,
        "candidate_all_precision": score(CANDIDATE, "all"), "fixed_rival_all_precision": score(best, "all"),
        "all_library_difference_vs_fixed_rare_rival": score(CANDIDATE, "all") - score(best, "all"),
        "best_all_library_baseline": best_all, "best_all_library_baseline_precision": score(best_all, "all"),
        "all_library_difference_vs_best_all_rival": score(CANDIDATE, "all") - score(best_all, "all"),
        "permuted_context_rare_precision": score(DIAGNOSTIC),
        "real_context_exceeds_permuted": candidate_score > score(DIAGNOSTIC),
        "required_subsets": subset_inputs,
        "preset_sensitivity_candidate_minus_fixed_rival": score(CANDIDATE, evaluation="preset_source_sensitivity") - score(best, evaluation="preset_source_sensitivity"),
    }
    zero_rare_hit_tasks = [name for name in sorted(eligible) if not bool(np.any(hits[name_to_row[name]] & task_libraries[(name, "rare")]))]
    verification = {
        "scope": "Same-observation output arithmetic and roster/eligibility verification; no biological replication or fitted-transform audit.",
        "script_sha256": sha256(Path(__file__)),
        "input_sha256": {label: {"path": str(path), "sha256": sha256(path)} for label, path in paths.items()},
        "checks": {"original_train_only": True, "official_validation_test_rows_consumed": 0,
                   "all_1231_valid_endpoints_in_roster": True, "canonical_component_mapping_valid": True,
                   "deterministic_group_folds_valid": True, "identical_all_rare_method_tasksets": True,
                   "every_pick_exactly_50_unique_measured_and_rare_when_required": True,
                   "all_fit_rarity_excludes_test_fold": True, "target_hit_counts_not_used_for_eligibility": True},
        "denominators": {"official_train_rows": len(metadata), "valid_endpoints": len(valid_meta),
                         "endpoint_exclusions": len(excluded), "eligible_tasks": len(eligible),
                         "ineligible_valid_endpoints": len(valid_meta) - len(eligible),
                         "eligible_canonical_groups": len(paired), "actual_methods": sorted(METHODS),
                         "prediction_records": len(predictions), "zero_rare_hit_eligible_tasks": len(zero_rare_hit_tasks)},
        "component_mapping": {source: "29083409" for source in sorted(COMPONENT)},
        "component_sources_present": component_present, "endpoint_exclusions": excluded,
        "task_eligibility": sorted(task_eligibility, key=lambda row: row["dataset_name"]),
        "ineligible_valid_endpoints": sorted(set(valid_meta) - eligible),
        "zero_rare_hit_eligible_tasks": zero_rare_hit_tasks, "fold_audit": fold_audit,
        "source_paired_differences": paired, "outer_fold_differences": fold_differences,
        "bootstrap": {"draws": 2000, "seed": 1030, "numpy_generator": "default_rng/PCG64", "percentiles": [2.5, 97.5],
                      "unit": "canonical source", "rival_held_fixed": best, "source_order": [row["group"] for row in paired]},
        "gate_inputs": gate_inputs,
        "limitations": ["No primary code, scores.csv, summary.csv, selection validation scores, or model objects are read.",
                        "Fit/validation/test group lists are inferred from the audited roster; actual fitted transformations and hyperparameter selection are outside this verifier.",
                        "Both all-library rival comparisons are supplied as gate inputs; this verifier does not issue an overall continuation decision.",
                        "The bootstrap conditions on the selected rival, shared training, and observed canonical groups; it is exploratory, not biological uncertainty."],
    }
    # Standalone artifacts are written before any separate primary-score comparison.
    write_csv(REVIEW / "b_independent_scores.csv", scores)
    write_csv(REVIEW / "b_independent_summary.csv", summary)
    (REVIEW / "b_verification.json").write_text(json.dumps(verification, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"denominators": verification["denominators"], "gate_inputs": gate_inputs}, sort_keys=True))


if __name__ == "__main__":
    main()
