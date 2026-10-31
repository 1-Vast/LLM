"""Check metadata grouping, paired-control candidates, and gene-bearing input text."""
import collections
import csv
import json
import pathlib
import re

import numpy as np

AUDIT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
with (AUDIT / "metadata_census_source.csv").open(newline="", encoding="utf-8") as handle:
    all_rows = list(csv.DictReader(handle))
rows = [row for row in all_rows if row["yearfold0"] == "train"]
data = np.load(ROOT / "biogrid_temporal_train_gene_hits_csr.npz", allow_pickle=False)
universe = set(data["genes"].tolist())
fields = ["phenotype", "condition_clause", "screen_rationale", "notes", "ranking_rationale", "significance_criteria"]
field_matches = {}
for field in fields:
    matching_rows = []
    for row in rows:
        # Symbol matching is a text-content flag, not proof of leakage. Common English gene names
        # (e.g. "WAS", "SET") and receptor/readout names require manual interpretation.
        tokens = set(re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", row[field])) & universe
        if tokens:
            matching_rows.append({"dataset_name": row["dataset_name"], "gene_tokens": sorted(tokens), "text": row[field]})
    field_matches[field] = matching_rows

by_cell = collections.defaultdict(list)
for row in rows:
    by_cell[row["cell_line"]].append(row)
cell_support = collections.Counter(len({row["source_id"] for row in values}) for values in by_cell.values())
by_study_cell = collections.defaultdict(list)
for row in rows:
    by_study_cell[(row["source_id"], row["cell_line"], row["library_type"])].append(row)
pairs = []
for key, values in by_study_cell.items():
    unspecified = [row for row in values if row["condition_name"] == "Not specified"]
    treated = [row for row in values if row["condition_name"] != "Not specified"]
    for control in unspecified:
        for treatment in treated:
            pairs.append({"source_id": key[0], "cell_line": key[1], "library_type": key[2], "unspecified_task": control["dataset_name"], "treated_task": treatment["dataset_name"], "unspecified_phenotype": control["phenotype"], "treated_phenotype": treatment["phenotype"], "same_phenotype_text": control["phenotype"] == treatment["phenotype"], "same_screen_type": control["screen_type"] == treatment["screen_type"], "same_duration": control["duration"] == treatment["duration"], "treated_condition": treatment["condition_name"], "unspecified_notes": control["notes"]})
split_by_source = collections.defaultdict(set)
split_by_original = collections.defaultdict(set)
for row in all_rows:
    split_by_source[row["source_id"]].add(row["yearfold0"])
    for original in re.findall(r"\d+", row["dataset_name"]):
        split_by_original[original].add(row["yearfold0"])
summary = {
    "cell_line_publication_count_distribution": {str(k): v for k, v in sorted(cell_support.items())},
    "cell_line_strings_seen_in_multiple_publications": sum(value > 1 for value in [len({row["source_id"] for row in values}) for values in by_cell.values()]),
    "training_gene_symbol_text_flags": {field: len(matches) for field, matches in field_matches.items()},
    "symbol_flags_are_not_verified_outcome_leakage": True,
    "same_study_cell_library_unspecified_vs_treatment_pairs": len(pairs),
    "pair_study_count": len({pair["source_id"] for pair in pairs}),
    "pairs_with_identical_phenotype_text": sum(pair["same_phenotype_text"] for pair in pairs),
    "pairs_same_phenotype_screen_type_duration": sum(pair["same_phenotype_text"] and pair["same_screen_type"] and pair["same_duration"] for pair in pairs),
    "known_absence_of_drug_control_task": "2374 (PMID32028983, HAP-1, negative-selection viability); treated tasks2375–2401 are positive-selection drug resistance and are not the same endpoint",
    "publication_ids_crossing_temporal_splits": {key: sorted(values) for key, values in split_by_source.items() if len(values) > 1},
    "original_screens_crossing_temporal_splits": {key: sorted(values) for key, values in split_by_original.items() if len(values) > 1},
}
(AUDIT / "text_and_pair_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(AUDIT / "gene_tokens_in_text.json").write_text(json.dumps(field_matches, indent=2, ensure_ascii=False), encoding="utf-8")
(AUDIT / "unspecified_treatment_pair_candidates.json").write_text(json.dumps(pairs, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2))
print("SAFE_FIELD_GENE_TOKEN_EXAMPLES")
for field in ("phenotype", "condition_clause", "screen_rationale"):
    print(field, json.dumps(field_matches[field][:12], indent=2, ensure_ascii=False))
