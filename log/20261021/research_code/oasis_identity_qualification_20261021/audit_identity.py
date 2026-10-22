"""Identity-only child process. No biochemical values or morphology features loaded."""
import collections
import hashlib
import json
import re
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "log/20261021/oasis_source_qualification"
LOG = ROOT / "log/20261021/oasis_identity_qualification"
ALLOWED = {"well_id", "source", "plate", "well", "row", "col", "compound_name",
           "compound_concentration_um", "compound_scode", "OASIS_ID", "compound_smiles",
           "compound_inchi", "compound_saltdata", "compound_formula", "library", "plate_type"}


def well_norm(value):
    match = re.fullmatch(r"([A-Za-z]+)0*(\d+)", str(value))
    return f"{match[1].upper()}{int(match[2]):02d}" if match else str(value)


def main():
    manifest = json.loads((OLD / "SOURCE_MANIFEST.json").read_text())
    rows = []
    schemas = {}
    for item in manifest:
        path = ROOT / item["local_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Original sealed source hash mismatch")
        file = pq.ParquetFile(path)
        fields = [x for x in file.schema_arrow.names if x in ALLOWED]
        schemas[item["Key"]] = fields
        for row in file.read(columns=fields).to_pylist():
            row["source_file"] = item["Key"]
            row["compound_id"] = hashlib.sha256(str(row.get("compound_name")).encode()).hexdigest()[:20]
            row["well_normalized"] = well_norm(row.get("well"))
            rows.append(row)
    by_well = collections.defaultdict(list)
    by_action = collections.defaultdict(list)
    for row in rows:
        by_well[(row.get("source"), row.get("plate"), row.get("well"))].append(row)
        if row.get("library") == "oasis" and str(row.get("compound_name")).upper() != "DMSO":
            by_action[(row["compound_id"], row.get("compound_concentration_um"))].append(row)
    duplicate_details = []
    for key, group in by_well.items():
        if len(group) <= 1:
            continue
        differing = [field for field in sorted(ALLOWED) if len({json.dumps(x.get(field), sort_keys=True) for x in group}) > 1]
        duplicate_details.append({"key": key, "rows": len(group), "differing_identity_fields": differing,
                                  "source_files": sorted({x["source_file"] for x in group}),
                                  "compound_ids": sorted({x["compound_id"] for x in group})})
    summary = {
        "row_count": len(rows), "duplicate_well_groups": len(duplicate_details),
        "duplicate_extra_rows": sum(x["rows"] - 1 for x in duplicate_details),
        "duplicate_difference_patterns": dict(collections.Counter("|".join(x["differing_identity_fields"]) for x in duplicate_details)),
        "multi_observation_actions": sum(len(v) > 2 for v in by_action.values()),
        "action_unique_physical_well_counts": dict(collections.Counter(len({(x.get("source"), x.get("plate"), x["well_normalized"]) for x in v}) for v in by_action.values())),
        "identity_nonnull_counts": {key: sum(x.get(key) is not None for x in rows) for key in sorted(ALLOWED)},
        "rows_loaded_only_from_whitelisted_columns": True,
        "schemas": schemas,
    }
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "IDENTITY_ROWS.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (LOG / "DUPLICATE_IDENTITY_DETAILS.json").write_text(json.dumps(duplicate_details, indent=2), encoding="utf-8")
    (LOG / "IDENTITY_AUDIT.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "schemas"}))


if __name__ == "__main__":
    main()
