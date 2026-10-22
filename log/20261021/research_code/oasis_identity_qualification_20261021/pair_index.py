"""Exact identity-only join of raw biochem, compiled metadata and image index."""
import collections
import hashlib
import json
import math
from pathlib import Path

import pyarrow.parquet as pq

from audit_identity import ROOT, LOG, well_norm

META_FIELDS = {"Metadata_well_id", "Metadata_source", "Metadata_Plate",
               "Metadata_Concentration", "Metadata_Compound", "Metadata_Well",
               "Metadata_row", "Metadata_col", "Metadata_OASIS_ID"}
INDEX_FIELDS = {"Metadata_Batch", "Metadata_Plate", "Metadata_Well", "Filename"}


def batch(value):
    return str(value).removeprefix("assayworks_")


def digest(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:20]


def key(source, plate, well):
    return batch(source), str(plate), well_norm(well)


def main():
    raw = json.loads((LOG / "IDENTITY_ROWS.json").read_text())
    raw_by_key = collections.defaultdict(list)
    for row in raw:
        raw_by_key[key(row["source"], row["plate"], row["well"])].append(row)
    meta_file = pq.ParquetFile(LOG / "sealed_source/metadata.parquet")
    metadata = meta_file.read(columns=[x for x in meta_file.schema_arrow.names if x in META_FIELDS]).to_pylist()
    meta_by_key = collections.defaultdict(list)
    for row in metadata:
        meta_by_key[key(row["Metadata_source"], row["Metadata_Plate"], row["Metadata_Well"])].append(row)
    index_file = pq.ParquetFile(LOG / "sealed_source/index.parquet")
    image_counts = collections.Counter()
    image_examples = {}
    for table in index_file.iter_batches(batch_size=65536, columns=sorted(INDEX_FIELDS)):
        for row in table.to_pylist():
            ident = key(row["Metadata_Batch"], row["Metadata_Plate"], row["Metadata_Well"])
            image_counts[ident] += 1
            image_examples.setdefault(ident, row["Filename"])
    raw_keys = set(raw_by_key)
    meta_keys = set(meta_by_key)
    index_keys = set(image_counts)
    conflicting = []
    paired = []
    for ident in sorted(raw_keys & meta_keys & index_keys):
        raw_conditions = {(x["compound_id"], float(x["compound_concentration_um"])) for x in raw_by_key[ident]}
        meta_conditions = {(digest(x["Metadata_Compound"]), float(x["Metadata_Concentration"])) for x in meta_by_key[ident]}
        # The original same-source compound/dose keys must agree exactly.
        if raw_conditions != meta_conditions:
            conflicting.append({"key": ident, "raw": sorted(raw_conditions), "metadata": sorted(meta_conditions)})
            continue
        sample = raw_by_key[ident][0]
        paired.append({"batch": ident[0], "plate": ident[1], "well": ident[2],
                       "compound_id": sample["compound_id"], "dose_um": sample["compound_concentration_um"],
                       "is_oasis": sample["library"] == "oasis",
                       "is_dmso": str(sample["compound_name"]).upper() == "DMSO",
                       "raw_identity_rows": len(raw_by_key[ident]),
                       "compiled_metadata_rows": len(meta_by_key[ident]),
                       "indexed_image_rows": image_counts[ident],
                       "image_example": image_examples[ident]})
    action_counts = collections.Counter((x["compound_id"], x["dose_um"]) for x in paired if x["is_oasis"] and not x["is_dmso"])
    compound_doses = collections.defaultdict(set)
    for compound, dose in action_counts:
        compound_doses[compound].add(dose)
    summary = {
        "source_raw_rows": len(raw), "raw_unique_physical_wells": len(raw_keys),
        "compiled_metadata_rows": len(metadata), "compiled_metadata_unique_wells": len(meta_keys),
        "index_rows": index_file.metadata.num_rows, "index_unique_wells": len(index_keys),
        "raw_without_compiled_metadata": len(raw_keys - meta_keys),
        "raw_without_image_index": len(raw_keys - index_keys),
        "compiled_metadata_without_raw": len(meta_keys - raw_keys),
        "index_without_raw": len(index_keys - raw_keys),
        "three_way_paired_unique_wells": len(paired), "compound_dose_conflicting_wells": len(conflicting),
        "paired_oasis_compound_labels": len(compound_doses), "paired_oasis_actions": len(action_counts),
        "paired_dose_counts_per_compound": dict(collections.Counter(map(len, compound_doses.values()))),
        "paired_physical_wells_per_action": dict(collections.Counter(action_counts.values())),
        "images_per_well_histogram": dict(collections.Counter(image_counts.values())),
        "real_count_column_schema": str(meta_file.schema_arrow.field("Metadata_Count_Cells").type),
        "real_count_values_loaded": False,
        "profile_feature_values_loaded": False,
        "unpaired_raw_wells_by_batch_plate": dict(collections.Counter("/".join(x[:2]) for x in raw_keys - (meta_keys & index_keys))),
        "metadata_whitelist": sorted(META_FIELDS), "index_whitelist": sorted(INDEX_FIELDS),
        "source_schemas": {"metadata": [(x.name, str(x.type)) for x in meta_file.schema_arrow],
                           "index": [(x.name, str(x.type)) for x in index_file.schema_arrow]},
    }
    (LOG / "PAIRING_AUDIT.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (LOG / "PAIRED_IDENTITIES.json").write_text(json.dumps(paired, indent=2), encoding="utf-8")
    (LOG / "PAIRING_CONFLICTS.json").write_text(json.dumps(conflicting, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "source_schemas"}))


if __name__ == "__main__":
    main()
