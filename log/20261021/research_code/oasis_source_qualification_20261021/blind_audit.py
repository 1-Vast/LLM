"""Independent subprocess. Output identifiers/coverage/null counts, never outcomes."""
import collections
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import pyarrow as pa
import pyarrow.compute as pc

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261021/oasis_source_qualification"
IDENTITY = {"well_id", "source", "plate", "well", "row", "col", "compound_name",
            "compound_concentration_um", "compound_scode", "OASIS_ID", "replicate",
            "replicate_id", "batch", "plate_type", "library"}
FUNCTION = {"mtt_lumi", "ldh_abs_signal", "ldh_abs_background", "ldh_abs",
            "mtt_normalized", "ldh_normalized", "mtt_ridge_norm", "ldh_ridge_norm"}


def main():
    manifest = json.loads((LOG / "SOURCE_MANIFEST.json").read_text())
    schema_groups = {}
    files = []
    rows = []
    nulls = collections.Counter()
    missing_totals = collections.Counter()
    for item in manifest:
        path = ROOT / item["local_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Sealed file hash mismatch")
        parquet = pq.ParquetFile(path)
        names = parquet.schema_arrow.names
        signature = tuple((f.name, str(f.type)) for f in parquet.schema_arrow)
        schema_groups.setdefault(str(signature), []).append(item["local_path"])
        allowed = [x for x in names if x in IDENTITY | FUNCTION]
        table = parquet.read(columns=allowed)
        id_names = [x for x in allowed if x in IDENTITY]
        ids = table.select(id_names).to_pylist()
        fn = [x for x in allowed if x in FUNCTION]
        missing = {}
        for name in fn:
            mask = pc.is_null(table[name])
            if pa.types.is_floating(table[name].type):
                mask = pc.or_(mask, pc.fill_null(pc.is_nan(table[name]), False))
            missing[name] = mask.to_pylist()
            missing_totals[name] += sum(missing[name])
        for name in fn:
            nulls[name] += table[name].null_count
        files.append({"path": item["local_path"], "row_count": table.num_rows,
                      "functional_columns": fn,
                      "functional_null_counts": {x: table[x].null_count for x in fn},
                      "functional_missing_counts_null_or_nan": {x: sum(missing[x]) for x in fn},
                      "identifier_null_counts": {x: table[x].null_count for x in id_names}})
        for index, row in enumerate(ids):
            compound = row.get("compound_name")
            compound_id = hashlib.sha256(str(compound).encode()).hexdigest()[:20] if compound is not None else None
            # No functional value is converted, serialised or used for selection.
            rows.append({"compound_id": compound_id,
                         "is_dmso_control": str(compound).upper() == "DMSO",
                         "dose_um": row.get("compound_concentration_um"),
                         "plate": row.get("plate"), "well": row.get("well"),
                         "source": row.get("source"),
                         "oasis_id": row.get("OASIS_ID"),
                         "library": row.get("library"),
                         "plate_type": row.get("plate_type"),
                         "replicate": row.get("replicate", row.get("replicate_id")),
                         "functional_present": {x: not missing[x][index] for x in fn}})
    compounds = collections.defaultdict(list)
    for row in rows:
        if row["compound_id"] is not None and not row["is_dmso_control"]:
            compounds[row["compound_id"]].append(row)
    actions = collections.defaultdict(list)
    for key, records in compounds.items():
        for row in records:
            actions[(key, row["dose_um"])].append(row)
    audit = {"scope": "Identifiers, schemas, missingness and coverage only; no outcome statistics",
             "files": files, "schemas": schema_groups,
             "row_count": len(rows), "compound_label_count_excluding_exact_dmso": len(compounds),
             "non_dmso_labels_not_automatically_authenticated_as_study_drugs": True,
             "rows_with_oasis_id": sum(x["oasis_id"] is not None for x in rows),
             "library_counts": dict(collections.Counter(str(x["library"]) for x in rows)),
             "plate_type_counts": dict(collections.Counter(str(x["plate_type"]) for x in rows)),
             "dose_counts_per_compound_histogram": dict(collections.Counter(len({x["dose_um"] for x in v}) for v in compounds.values())),
             "observations_per_action_histogram": dict(collections.Counter(len(v) for v in actions.values())),
             "distinct_plates_per_action_histogram": dict(collections.Counter(len({x["plate"] for x in v}) for v in actions.values())),
             "explicit_replicate_column_present": any(x["replicate"] is not None for x in rows),
             "functional_null_counts": dict(nulls),
             "functional_missing_counts_null_or_nan": dict(missing_totals),
             "missing_compound_ids": sum(x["compound_id"] is None for x in rows),
             "missing_doses": sum(x["dose_um"] is None for x in rows),
             "duplicate_plate_well_keys": len(rows) - len({(x["plate"], x["well"]) for x in rows})}
    (LOG / "BLIND_IDENTIFIERS.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (LOG / "BLIND_AUDIT.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k not in {"schemas", "files"}}))


if __name__ == "__main__":
    main()
