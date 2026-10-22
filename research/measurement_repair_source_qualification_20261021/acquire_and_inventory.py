"""Download a pinned CSV and inventory whitelisted metadata in a child process."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/measurement_repair_source_qualification"
SEALED = OUT / "sealed_source/ncats_20429398.csv"
IDENTITY = {"sample_id", "sample_name", "pubchem_sid", "assay_name", "library", "cas", "alias", "drug_name", "smiles", "supplier", "supplier_id"}
IDENTITY |= {f"conc{i}" for i in range(15)}


def child():
    import csv
    import pyarrow as pa
    import pyarrow.csv as pcsv
    manifest = json.loads((OUT / "CSV_SOURCE.json").read_text())
    if hashlib.sha256(SEALED.read_bytes()).hexdigest() != manifest["sha256"]:
        raise RuntimeError("Source changed")
    with SEALED.open(encoding="utf-8-sig", newline="") as stream:
        names = next(csv.reader(stream))
    approved = [n for n in names if n.strip() in IDENTITY]
    required = {"sample_id", "assay_name", "smiles"}
    if not required <= {n.strip() for n in approved}:
        raise RuntimeError("Required metadata missing from header")
    table = pcsv.read_csv(SEALED, read_options=pcsv.ReadOptions(use_threads=False),
        convert_options=pcsv.ConvertOptions(include_columns=approved, column_types={n: pa.string() for n in approved}, strings_can_be_null=True))
    table = table.rename_columns([n.strip() for n in table.column_names])
    rows = table.to_pylist()
    by_assay = collections.defaultdict(set)
    keys = collections.Counter()
    concentration_counts = collections.defaultdict(collections.Counter)
    for r in rows:
        sid = r["sample_id"]
        assay = r["assay_name"]
        by_assay[assay].add(sid)
        keys[(sid, assay)] += 1
        concentration_counts[assay][sum(r.get(f"conc{i}") is not None for i in range(15))] += 1
    assays = sorted(by_assay)
    intersects = [{"a": a, "b": b, "shared_samples": len(by_assay[a] & by_assay[b])}
                  for i, a in enumerate(assays) for b in assays[:i]]
    report = {"scope": "Sample/assay/chemical/concentration metadata only", "rows": len(rows),
              "columns_read": table.column_names, "response_columns_read": [],
              "assays": {a: {"unique_sample_ids": len(by_assay[a]), "dose_count_histogram": dict(concentration_counts[a])} for a in assays},
              "pairwise_sample_intersections": intersects, "duplicate_sample_assay_keys": sum(n - 1 for n in keys.values()),
              "unique_samples": len({r["sample_id"] for r in rows}),
              "rows_with_smiles": sum(bool(r.get("smiles")) for r in rows),
              "plate_replicate_time_columns_in_dictionary": False,
              "individual_outcomes_exposed": False}
    (OUT / "IDENTITY_ROWS.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (OUT / "BLIND_COVERAGE.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "pairwise_sample_intersections"}))


def main():
    import requests
    start = time.perf_counter()
    meta = json.loads((OUT / "METADATA_RECEIPT.json").read_text())
    item = next(x for x in meta["files"] if x["key"].endswith(".csv"))
    if SEALED.exists():
        raise RuntimeError("Source already acquired; do not repeat or overwrite")
    if item["size"] > 40_000_000:
        raise RuntimeError("Pinned source outside continuation budget")
    chunks, total = [], 0
    with requests.get(item["links"]["self"], timeout=35, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(65536):
            total += len(chunk)
            if total > 40_000_000:
                raise RuntimeError("Acquisition budget exceeded")
            chunks.append(chunk)
        payload = b"".join(chunks)
        if len(payload) != item["size"] or hashlib.md5(payload).hexdigest() != item["checksum"].removeprefix("md5:"):
            raise RuntimeError("Source size/checksum mismatch")
        SEALED.parent.mkdir(parents=True, exist_ok=True)
        SEALED.write_bytes(payload)
        record = {"url": response.url, "bytes": len(payload), "md5": hashlib.md5(payload).hexdigest(),
                  "sha256": hashlib.sha256(payload).hexdigest(), "status": response.status_code,
                  "last_modified": response.headers.get("Last-Modified"), "etag": response.headers.get("ETag"),
                  "wall_seconds": time.perf_counter() - start}
    (OUT / "CSV_SOURCE.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    result = subprocess.run([sys.executable, "-B", str(Path(__file__)), "--child"], capture_output=True, text=True, timeout=120)
    (OUT / "blind_worker_console.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Blind worker failed; see retained console, do not restart acquisition")
    print(result.stdout)


if __name__ == "__main__":
    child() if "--child" in sys.argv else main()
