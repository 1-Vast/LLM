"""Blind consistency check: return equality flags, never biochemical values."""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import time

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/oasis_evaluation_contract"
SOURCE = ROOT / "log/20261021/oasis_source_qualification"
FIELDS = ["mtt_lumi", "ldh_abs_signal", "ldh_abs_background", "ldh_abs"]


def key(source, plate, well):
    match = re.fullmatch(r"([A-Za-z]+)0*(\d+)", str(well))
    normal = f"{match[1].upper()}{int(match[2]):02d}" if match else str(well)
    return str(source).removeprefix("assayworks_"), str(plate), normal


def main():
    start = time.perf_counter()
    groups = collections.defaultdict(list)
    manifest = json.loads((SOURCE / "SOURCE_MANIFEST.json").read_text())
    for item in manifest:
        path = ROOT / item["local_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Source changed")
        # Values remain in this independent checker; output is equality only.
        file = pq.ParquetFile(path)
        required = {"source", "plate", "well", *FIELDS}
        if not required <= set(file.schema_arrow.names):
            raise RuntimeError("Raw functional schema incomplete")
        for row in file.read(columns=sorted(required)).to_pylist():
            values = tuple(None if v is None or (isinstance(v, float) and math.isnan(v)) else v for v in [row[x] for x in FIELDS])
            groups[key(row["source"], row["plate"], row["well"])].append(values)
    flags = []
    for ident, values in sorted(groups.items()):
        if len(values) > 1:
            flags.append({"well_id_hash": hashlib.sha256("|".join(ident).encode()).hexdigest(),
                          "records": len(values), "raw_values_identical": all(v == values[0] for v in values)})
    report = {"scope": "Duplicate-read equality only; no activity values/statistics/selection",
              "duplicate_well_groups": len(flags), "extra_records": sum(x["records"] - 1 for x in flags),
              "identical_groups": sum(x["raw_values_identical"] for x in flags),
              "conflicting_groups": sum(not x["raw_values_identical"] for x in flags),
              "fields_compared": FIELDS, "flags": flags, "files_authenticated": len(manifest),
              "wall_seconds": time.perf_counter() - start, "numeric_values_exported": False,
              "rule": "Only if equality holds may duplicate physical wells count once; never pick the stronger response"}
    (OUT / "DUPLICATE_READ_CONSISTENCY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "flags"}))


if __name__ == "__main__":
    main()
