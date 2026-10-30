"""Stream the official DepMap GeneEffect CSV and retain only the FLT3 row.

This is a bounded, episode-local extraction. It is deliberately not a core
tool: the full matrix is a genetic reference and cannot establish drug
engagement or causal mediation.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from pathlib import Path

import requests


URL = "https://ndownloader.figshare.com/files/67214582"
EXPECTED_BYTES = 413_544_937
MAX_BYTES = 500_000_000
MAX_SECONDS = 600
EXPECTED_MD5 = "c89e3ec7e2c3682e5c3535172177a1ee"
OUT = Path(__file__).parent / "raw" / "resource_metadata" / "DepMap_26Q1_gene_effect_FLT3.csv"
META = Path(__file__).parent / "raw" / "resource_metadata" / "DepMap_26Q1_gene_effect_FLT3.json"


def main() -> None:
    started = time.monotonic()
    digest = hashlib.md5()
    total = 0
    header: list[str] | None = None
    target_indexes: list[int] = []
    rows: list[tuple[str, str]] = []

    with requests.get(URL, stream=True, timeout=(30, 60)) as response:
        response.raise_for_status()
        content_length = int(response.headers.get("content-length", "0"))
        if content_length and content_length > MAX_BYTES:
            raise RuntimeError(f"advertised file exceeds budget: {content_length}")
        iterator = response.iter_lines(decode_unicode=False, chunk_size=1024 * 1024)
        for raw_line in iterator:
            if time.monotonic() - started > MAX_SECONDS:
                raise TimeoutError("stream exceeded wall-time budget")
            # Figshare serves LF-delimited CSV. Account for the delimiter in
            # the transfer budget while retaining the exact payload hash.
            total += len(raw_line) + 1
            if total > MAX_BYTES:
                raise RuntimeError("stream exceeded transfer budget")
            digest.update(raw_line)
            digest.update(b"\n")
            line = raw_line.decode("utf-8")
            fields = next(csv.reader([line]))
            if header is None:
                header = fields
                target_indexes = [
                    i for i, name in enumerate(header)
                    if name == "FLT3 (2322)" or name == "FLT3"
                ]
                if not target_indexes:
                    raise RuntimeError("FLT3 column not found in GeneEffect header")
                continue
            if len(fields) != len(header):
                raise RuntimeError(
                    f"malformed row with {len(fields)} fields; expected {len(header)}"
                )
            model_id = fields[0]
            for index in target_indexes:
                rows.append((model_id, fields[index]))

    if total != EXPECTED_BYTES:
        raise RuntimeError(f"unexpected byte count: {total} != {EXPECTED_BYTES}")
    if digest.hexdigest() != EXPECTED_MD5:
        raise RuntimeError(
            f"MD5 mismatch: {digest.hexdigest()} != {EXPECTED_MD5}"
        )
    if not rows:
        raise RuntimeError("no FLT3 values extracted")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["DepMap_ID", "gene_effect_FLT3"])
        writer.writerows(rows)
    metadata = {
        "source_url": URL,
        "expected_bytes": EXPECTED_BYTES,
        "observed_bytes": total,
        "expected_md5": EXPECTED_MD5,
        "observed_md5": digest.hexdigest(),
        "target_columns": [header[i] for i in target_indexes],
        "rows": len(rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "interpretation": "genetic reference only; not cellular target engagement",
    }
    META.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
