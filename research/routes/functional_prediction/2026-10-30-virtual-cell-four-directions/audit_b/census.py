"""Descriptive census of public historical train labels; no fitting or scoring."""
import collections
import csv
import json
import pathlib
import re

import numpy as np

AUDIT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
with (AUDIT / "metadata_census_source.csv").open(newline="", encoding="utf-8") as handle:
    metadata = list(csv.DictReader(handle))
train = [row for row in metadata if row["yearfold0"] == "train"]
data = np.load(ROOT / "biogrid_temporal_train_gene_hits_csr.npz", allow_pickle=False)
genes = data["genes"].tolist()
names = data["dataset_names"].tolist()
assert names == [row["dataset_name"] for row in train]
measured_indptr, hit_indptr = data["measured_indptr"], data["hit_indptr"]
measured_indices, hit_indices = data["measured_indices"], data["hit_indices"]
measured_rows = [measured_indices[a:b] for a, b in zip(measured_indptr[:-1], measured_indptr[1:])]
hit_rows = [hit_indices[a:b] for a, b in zip(hit_indptr[:-1], hit_indptr[1:])]
counts = np.diff(measured_indptr)
hit_counts = np.diff(hit_indptr)
assert len(train) == len(counts) == 1349
assert all(set(hits).issubset(set(measured)) for measured, hits in zip(measured_rows, hit_rows))


def frequencies(rows, field):
    return dict(collections.Counter(row[field] for row in rows).most_common())


def quantiles(values):
    return dict(zip(["min", "q25", "median", "q75", "max"], map(float, np.quantile(values, [0, .25, .5, .75, 1]))))


def original_ids(name):
    return list(map(int, re.findall(r"\d+", name)))


source_rows = collections.defaultdict(list)
for i, row in enumerate(train):
    source_rows[row["source_id"]].append(i)
original_groups = collections.defaultdict(list)
for i, row in enumerate(train):
    for original in original_ids(row["dataset_name"]):
        original_groups[original].append(i)
variant_groups = {key: value for key, value in original_groups.items() if len(value) > 1}
variant_hits = []
for original, indices in variant_groups.items():
    sets = [set(hit_rows[index]) for index in indices]
    variant_hits.append({"original_screen": original, "dataset_names": [names[index] for index in indices], "hit_counts": [len(values) for values in sets], "all_hit_sets_identical": all(values == sets[0] for values in sets)})

measured_gene_counts = np.bincount(measured_indices, minlength=len(genes))
hit_gene_counts = np.bincount(hit_indices, minlength=len(genes))
global_frequency = np.divide(hit_gene_counts, measured_gene_counts, out=np.zeros(len(genes)), where=measured_gene_counts > 0)
top_gene_indices = sorted(np.flatnonzero(measured_gene_counts >= 50), key=lambda i: (-global_frequency[i], genes[i]))[:30]
top_genes = [{"gene": genes[i], "hit_screens": int(hit_gene_counts[i]), "measured_screens": int(measured_gene_counts[i]), "hit_frequency": float(global_frequency[i])} for i in top_gene_indices]

nominal = collections.defaultdict(list)
for i, row in enumerate(train):
    nominal[(row["source_id"], row["cell_line"], row["screen_type"], row["library_type"])].append(i)
nominal_pair_groups = []
for key, indices in nominal.items():
    unspecified = [i for i in indices if train[i]["condition_name"] == "Not specified"]
    specified = [i for i in indices if train[i]["condition_name"] != "Not specified"]
    if unspecified and specified:
        nominal_pair_groups.append({"key": key, "unspecified_condition_tasks": [names[i] for i in unspecified], "specified_condition_tasks": [names[i] for i in specified]})

provenance_notes = []
seen = set()
for row in train:
    if re.search(r"re.?analys|re.?analyz|same (?:dataset|data)|reused|previously (?:published|reported)", row["notes"], re.I):
        key = (row["source_id"], row["notes"])
        if key not in seen:
            provenance_notes.append({"source_id": row["source_id"], "notes": row["notes"]})
            seen.add(key)

summary = {
    "scope": "Descriptive historical training-label census only; no model or held-out score",
    "source_revision": "fa2ed4195d2eea1e5ed570d1a67c21e47650962d",
    "historical_rows": len(metadata), "temporal_splits": frequencies(metadata, "yearfold0"),
    "training_rows": len(train), "training_publications": len(source_rows),
    "training_unique_original_screen_ids": len(original_groups),
    "all_historical_unique_original_screen_ids": len({original for row in metadata for original in original_ids(row["dataset_name"])}),
    "training_distinct_source_id_tuples_after_replicate_merging": len({tuple(original_ids(row["dataset_name"])) for row in train}),
    "training_unique": {field: len(set(row[field] for row in train)) for field in ["cell_line", "cell_type", "phenotype", "screen_rationale", "condition_name", "condition_dosage", "screen_type", "library_type"]},
    "training_field_missing_or_unspecified": {field: sum(row[field].strip().lower() in ("", "not specified", "none", "nan") for row in train) for field in ["cell_line", "cell_type", "phenotype", "screen_rationale", "condition_name", "condition_dosage", "duration", "notes"]},
    "training_coarse_categories": frequencies(train, "cleaned_phenotype"),
    "all_historical_coarse_categories": frequencies(metadata, "cleaned_phenotype"),
    "training_screen_categories": frequencies(train, "screen_category"),
    "training_screen_types": frequencies(train, "screen_type"),
    "training_libraries": frequencies(train, "library_type"),
    "training_category_publications": {category: len({row["source_id"] for row in train if row["cleaned_phenotype"] == category}) for category in frequencies(train, "cleaned_phenotype")},
    "largest_training_publications": [{"source_id": key, "author": train[indices[0]]["author"], "tasks": len(indices)} for key, indices in sorted(source_rows.items(), key=lambda item: -len(item[1]))[:15]],
    "train_genes_union": len(genes), "observed_gene_task_pairs": int(counts.sum()), "hit_gene_task_pairs": int(hit_counts.sum()),
    "micro_hit_prevalence": float(hit_counts.sum() / counts.sum()), "macro_hit_prevalence": float(np.mean(hit_counts / counts)),
    "screen_gene_count": quantiles(counts), "screen_hit_count": quantiles(hit_counts), "screen_hit_prevalence": quantiles(hit_counts / counts),
    "zero_hit_tasks": [names[i] for i in np.flatnonzero(hit_counts == 0)],
    "tasks_with_duplicate_gene_symbols": [names[i] for i, row in enumerate(measured_rows) if len(row) != len(set(row))],
    "tasks_with_duplicate_hit_symbols": [names[i] for i, row in enumerate(hit_rows) if len(row) != len(set(row))],
    "variant_original_screens": len(variant_groups), "variant_hit_sets_identical_groups": sum(row["all_hit_sets_identical"] for row in variant_hits),
    "top_training_hit_frequency_genes_min50_screens": top_genes,
    "nominal_treated_unspecified_pair_groups": len(nominal_pair_groups),
    "nominal_pair_warning": "Not specified is not proof of untreated control; screen_type and endpoint direction also differ in some real baseline/drug studies.",
    "explicit_control_condition_names": sorted({row["condition_name"] for row in train if re.search(r"untreat|DMSO|vehicle|control|none", row["condition_name"], re.I)}),
    "provenance_reanalysis_notes": provenance_notes,
    "recommended_group_merge": [["27260156", "29083409"]],
    "recommended_input_fields": ["phenotype", "condition_clause", "screen_rationale", "cell_line", "cell_type", "screen_type", "library_type", "condition_name", "condition_dosage", "duration"],
    "forbidden_predictor_fields": ["dataset_name", "author", "source_id", "answer", "notes", "ranking_rationale", "significance_criteria", "relevance_scores", "combined_scores", "raw_scores", "unmasked_scores", "hit"],
}
(AUDIT / "census.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
(AUDIT / "variant_hit_set_audit.json").write_text(json.dumps(variant_hits, indent=2), encoding="utf-8")
(AUDIT / "nominal_pair_candidates.json").write_text(json.dumps(nominal_pair_groups, indent=2), encoding="utf-8")
full_train_rows = []
for index, row in enumerate(train):
    original = original_ids(row["dataset_name"])
    full_train_rows.append(row | {"row_index": metadata.index(row), "original_screen_ids": original, "gene_count": int(counts[index]), "hit_count": int(hit_counts[index])})
(ROOT / "biogrid_temporal_train_metadata.json").write_text(json.dumps(full_train_rows, indent=2, ensure_ascii=False), encoding="utf-8")
with (ROOT / "biogrid_temporal_train_metadata.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(full_train_rows[0]))
    writer.writeheader()
    writer.writerows(full_train_rows)
with (AUDIT / "gene_hit_frequency_train_descriptive.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["gene", "measured_screen_count", "hit_screen_count", "hit_frequency"])
    writer.writerows((genes[i], int(measured_gene_counts[i]), int(hit_gene_counts[i]), float(global_frequency[i])) for i in range(len(genes)))
print(json.dumps({key: value for key, value in summary.items() if key not in ("provenance_reanalysis_notes", "zero_hit_tasks", "forbidden_predictor_fields", "recommended_input_fields")}, indent=2, ensure_ascii=False))
