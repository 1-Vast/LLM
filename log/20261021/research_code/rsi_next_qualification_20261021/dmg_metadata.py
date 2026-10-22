"""Bounded DMG metadata census. Never GET counts, source XLSX or TAR payloads."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/rsi_next_qualification/agents/dmg_metadata_receipt.json"
GEO = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
SERIES = ["GSE264130", "GSE264412", "GSE267415", "GSE262774", "GSE262775"]
SAMPLES = ["GSM8212608", "GSM8212609", "GSM8212610", "GSM8212611",
           "GSM8217750", "GSM8217751", "GSM8217752"]
ALLOWED = ("title", "status", "submission_date", "last_update_date", "sample_id",
           "supplementary_file", "relation", "platform_id", "source_name_ch1",
           "characteristics_ch1", "type")


def geo_metadata(acc: str) -> dict:
    r = requests.get(GEO, params={"acc": acc, "targ": "self", "form": "text",
                                  "view": "brief"}, timeout=25)
    r.raise_for_status()
    fields: dict[str, list[str]] = {}
    for line in r.content.decode("utf-8").splitlines():
        if not line.startswith(("!Series_", "!Sample_")) or " = " not in line:
            continue
        key, value = line[1:].split(" = ", 1)
        name = key.split("_", 1)[1]
        if any(name == x or name.startswith(x + "_") for x in ALLOWED):
            fields.setdefault(name, []).append(value)
    return {"accession": acc, "url": r.url, "status": r.status_code,
            "metadata_bytes": len(r.content),
            "metadata_sha256": hashlib.sha256(r.content).hexdigest(),
            "fields": fields}


def head(url: str) -> dict:
    r = requests.head(url, timeout=25, allow_redirects=True)
    return {"url": url, "status": r.status_code,
            "headers": {k: v for k, v in r.headers.items() if k.lower() in
                        ("content-length", "last-modified", "content-type", "etag")}}


def sample_layout(url: str) -> dict:
    # Filename is the metadata supplement, never its adjacent expression counts.
    if not url.endswith("-samples.tsv.gz") or "/suppl/" not in url:
        raise ValueError("Only the explicit sample-layout metadata file is allowed")
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    if len(r.content) > 100_000:
        raise ValueError("Metadata size bound exceeded")
    rows = list(csv.reader(io.StringIO(gzip.decompress(r.content).decode("utf-8")),
                           delimiter="\t"))
    if any(len(row) != 3 for row in rows):
        raise ValueError("Unexpected metadata schema")
    # These files have no header. Row 1 is a real well and must be retained.
    records = [{"barcode": row[0], "well": row[1], "condition": row[2]}
               for row in rows]
    return {"url": url, "status": r.status_code, "compressed_bytes": len(r.content),
            "sha256": hashlib.sha256(r.content).hexdigest(), "has_header": False,
            "schema": ["barcode", "well", "condition_drug_dose_time"],
            "row_count": len(rows), "unique_wells": len({x[1] for x in rows}),
            "records": records}


def safe_call(fn, value):
    try:
        return fn(value)
    except Exception as exc:
        return {"input": value, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(lambda x: safe_call(geo_metadata, x), SERIES + SAMPLES))
    sample_urls = []
    all_files = []
    for item in metadata:
        for key, values in item.get("fields", {}).items():
            if key.startswith("supplementary_file"):
                for url in values:
                    url = url.replace("ftp://", "https://", 1)
                    if url.startswith("https://"):
                        all_files.append(url)
                        if url.endswith("-samples.tsv.gz"):
                            sample_urls.append(url)
    media = ("https://media.springernature.com/original/springer-static/esm/"
             "art%3A10.1038%2Fs41588-026-02550-w/MediaObjects/")
    publisher = [media + f"41588_2026_2550_MOESM{i}_ESM." +
                 ("pdf" if i <= 2 else "xlsx") for i in range(1, 8)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        layouts = list(pool.map(lambda x: safe_call(sample_layout, x), sample_urls))
        headers = list(pool.map(lambda x: safe_call(head, x), sorted(set(all_files)) + publisher))
    receipt = {"retrieved_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "GEO brief metadata + explicit well-layout metadata; HEAD only for all outcomes",
               "method": "No numeric response, count, XLSX, TAR, SRA or PDF body requested by this script",
               "series_and_samples": metadata, "sample_layouts": layouts,
               "file_head_receipts": headers,
               "wall_seconds": perf_counter() - start,
               "payload_outcome_bytes_downloaded_by_this_script": 0,
               "random_seed": None}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"receipt": str(OUT), "layouts": len(layouts),
                      "layout_rows": [x.get("row_count") for x in layouts],
                      "metadata_errors": [x for x in metadata if "error" in x],
                      "layout_errors": [x for x in layouts if "error" in x],
                      "head_statuses": [x.get("status") for x in headers],
                      "wall_seconds": receipt["wall_seconds"]}))


if __name__ == "__main__":
    main()
