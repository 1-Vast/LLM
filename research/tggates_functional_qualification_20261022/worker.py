"""Only this separate process decodes official DNA/LDH strings, without exporting them."""
import csv
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"
IDENTITY = ["EXP_ID", "GROUP_ID", "INDIVIDUAL_ID", "COMPOUND_NAME", "SPECIES",
            "SEX_TYPE", "SACRIFICE_PERIOD", "DOSE", "DOSE_UNIT", "DOSE_LEVEL"]
KEY = IDENTITY[:3]
RESPONSES = {"DNA": "DNA(%)", "LDH": "LDH(%)"}
MISSING = {"", "na", "n/a", "nan", "null", "none", "-", "--", "no data", "no_data", "not available"}
FLAGS = ["DNA_missing", "LDH_missing", "identity_conflict", "DNA_conflict", "LDH_conflict"]


def missing(value):
    return value.strip().casefold() in MISSING


def project_rows(rows):
    """Raw values remain local; exactly whitelisted identities/booleans leave."""
    groups = defaultdict(list)
    for row in rows:
        if set(row) != set(IDENTITY) | set(RESPONSES.values()):
            raise ValueError("Functional schema mismatch")
        if any(row[c] is None for c in IDENTITY + list(RESPONSES.values())):
            raise ValueError("Functional row width mismatch")
        groups[tuple(row[c] for c in KEY)].append(row)
    result = []
    for members in groups.values():
        conflict = any(len({r[c] for r in members}) > 1 for c in IDENTITY)
        endpoint_conflict = {name: len({r[column] for r in members if not missing(r[column])}) > 1
                             for name, column in RESPONSES.items()}
        for row in members:
            if row["SPECIES"].strip().casefold() != "human":
                continue
            projected = {c: row[c] for c in IDENTITY}
            projected.update({f"{name}_missing": missing(row[column]) for name, column in RESPONSES.items()})
            projected["identity_conflict"] = conflict
            projected.update({f"{name}_conflict": endpoint_conflict[name] for name in RESPONSES})
            assert set(projected) == set(IDENTITY + FLAGS)
            result.append(projected)
    return result, {"all_source_rows": sum(map(len, groups.values())),
                    "all_source_unique_keys": len(groups),
                    "human_source_rows": len(result),
                    "nonhuman_source_rows": sum(map(len, groups.values())) - len(result)}


def check_freeze():
    freeze = json.loads((OUT / "PRE_OPEN_FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["sha256"].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Pre-open frozen input changed")


def main():
    targets = [OUT / "HUMAN_FUNCTIONAL_FLAGS.json", OUT / "FUNCTIONAL_SCHEMA.json"]
    if any(p.exists() for p in targets):
        raise RuntimeError("Projection exists; refusing overwrite")
    check_freeze()
    with zipfile.ZipFile(OUT / "sealed_source/open_tggates_cell_viability.zip") as archive:
        members = [i for i in archive.infolist() if i.filename.lower().endswith(".csv")]
        if len(members) != 1 or members[0].file_size > 10_000_000:
            raise ValueError("Archive CSV member qualification failed")
        raw = archive.read(members[0])
        reader = csv.DictReader(io.StringIO(raw.decode("cp932")))
        if set(reader.fieldnames or []) != set(IDENTITY) | set(RESPONSES.values()):
            raise ValueError("Functional header schema mismatch")
        projected, counts = project_rows(reader)
        schema = {"member": members[0].filename, "uncompressed_bytes": members[0].file_size,
                  "encoding": "cp932", "source_headers": reader.fieldnames,
                  "allowed_export_columns": IDENTITY + FLAGS,
                  "parser_dtype_policy": "all fields preserved as original strings; no outcome numeric cast",
                  "missing_tokens": sorted(MISSING), "counts": counts,
                  "numeric_validity_established": False,
                  "isolation": "Separate process and restricted projection; not an OS security boundary"}
    targets[0].write_text(json.dumps(projected, indent=2, ensure_ascii=False), encoding="utf-8")
    targets[1].write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "WHITELIST_PROJECTION_COMPLETE", **counts}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not allow csv/parser tracebacks to print source rows or response strings.
        print(json.dumps({"status": "WORKER_FAILED", "error_type": type(exc).__name__}))
        raise SystemExit(1)
