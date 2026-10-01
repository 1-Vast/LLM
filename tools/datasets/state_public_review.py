"""Acquire pinned public metadata without promoting a source to an eligible task."""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


PINS = Path(__file__).with_name("state_public_sources_20261001.json")
DECOMPRESSED_LIMIT = 32 << 20


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def parse_metadata(body: bytes, source: dict[str, Any]) -> dict[str, Any]:
    """Check identity and report literal fields; none certify predecision availability."""
    kind = source["format"]
    if kind.startswith("gzip_"):
        with gzip.GzipFile(fileobj=io.BytesIO(body)) as handle:
            body = handle.read(DECOMPRESSED_LIMIT + 1)
        if len(body) > DECOMPRESSED_LIMIT:
            raise ValueError("decompressed metadata exceeds declared 32 MiB limit")
    text = body.decode("utf-8")
    if kind == "json":
        payload = json.loads(text)
        identity = payload
        for key in source["identity_path"]:
            identity = identity[key]
        if identity != source["identity"]:
            raise ValueError("registry identity mismatch")
        return {"identity": identity, "format": kind}
    if kind == "xml":
        root = ET.fromstring(text)
        if not any(element.tag == "article-id" and (element.text or "").strip() == source["identity"] for element in root.iter()):
            raise ValueError("article identity missing")
        return {"identity": source["identity"], "format": kind}
    if kind == "markdown":
        if source["identity"] not in text:
            raise ValueError("author data identity missing")
        return {"identity": source["identity"], "format": kind}
    if kind == "gzip_soft":
        if f"^SERIES = {source['identity']}" not in text.splitlines():
            raise ValueError("GEO series identity missing")
        samples = []
        for block in text.split("^SAMPLE = ")[1:]:
            fields: dict[str, list[str]] = collections.defaultdict(list)
            lines = block.splitlines()
            for line in lines[1:]:
                if " = " in line:
                    key, value = line.split(" = ", 1)
                    fields[key].append(value)
            samples.append({
                "sample_id": lines[0], "title": fields["!Sample_title"],
                "characteristics": fields["!Sample_characteristics_ch1"],
                "execution_status": "record_level_only",
            })
        return {"identity": source["identity"], "samples": samples, "format": kind}
    if kind == "gzip_mtx":
        lines = text.splitlines()
        if not lines or lines[0] != "%%MatrixMarket matrix coordinate integer general":
            raise ValueError("unexpected clone matrix format")
        values = [line for line in lines[1:] if line and not line.startswith("%")]
        rows, columns, count = map(int, values[0].split())
        entries = [tuple(map(int, line.split())) for line in values[1:]]
        if rows <= 0 or columns <= 0 or len(entries) != count:
            raise ValueError("clone matrix dimensions or entry count invalid")
        if any(len(entry) != 3 or not 1 <= entry[0] <= rows or not 1 <= entry[1] <= columns or entry[2] != 1 for entry in entries):
            raise ValueError("invalid binary clone membership")
        return {"format": kind, "rows": rows, "columns": columns, "memberships": entries}
    if kind == "gzip_tsv":
        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
        if reader.fieldnames != source["columns"]:
            raise ValueError("cell metadata schema changed")
        rows = list(reader)
        counts = collections.Counter((row["Time point"], row["Cytokine condition"]) for row in rows)
        return {"format": kind, "columns": reader.fieldnames, "rows": len(rows),
                "time_points": [row["Time point"] for row in rows],
                "action_rows": [{"day": day, "action": action, "rows": count} for (day, action), count in sorted(counts.items())]}
    if kind == "csv_counts":
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames != source["columns"]:
            raise ValueError("count CSV schema changed")
        row_count = zero_count = 0
        wells: dict[tuple[str, str], float] = {}
        plates: dict[str, set[str]] = collections.defaultdict(set)
        drugs = set()
        actions = collections.Counter()
        for row in reader:
            exposure, count, dose = map(float, (row["time"], row["cell.count"], row["drug1.conc"]))
            if not all(math.isfinite(value) and value >= 0 for value in (exposure, count, dose)):
                raise ValueError("invalid count/dose/exposure value")
            row_count += 1
            zero_count += exposure == 0
            key = (row["upid"], row["well"])
            wells[key] = min(wells.get(key, exposure), exposure)
            plates[row["cell.line"]].add(row["upid"])
            drugs.add(row["drug1"])
            actions[(row["drug1"], dose)] += 1
        if not wells:
            raise ValueError("count CSV contains no measurements")
        return {"format": kind, "columns": reader.fieldnames, "rows": row_count,
                "plates_by_cell_line": {key: sorted(value) for key, value in plates.items()},
                "drug_name_tokens": len(drugs), "zero_exposure_rows": zero_count,
                "first_well_exposure_min_h": min(wells.values()), "first_well_exposure_max_h": max(wells.values()),
                "action_rows": [{"drug": drug, "dose_M": dose, "rows": count} for (drug, dose), count in sorted(actions.items())]}
    raise ValueError("unregistered metadata format")


def run(out: Path, *, pins_path: Path = PINS, fixtures: Path | None = None) -> dict[str, Any]:
    plan_bytes = pins_path.read_bytes()
    plan = json.loads(plan_bytes)
    sources = plan["sources"]
    ids = [source["id"] for source in sources]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z0-9_]+", name) for name in ids):
        raise ValueError("source IDs must be unique safe basenames")
    if any(not source["url"].startswith("https://") or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"]) or not 0 < source["max_bytes"] <= 8 << 20 for source in sources):
        raise ValueError("sources require HTTPS, SHA256 pins and bounded responses")
    out.mkdir(parents=True, exist_ok=False)
    (out / "source_pins.json").write_bytes(plan_bytes)
    receipts = []
    parsed = {}
    for source in sources:
        status = None
        headers = {}
        errors = []
        started = datetime.now(timezone.utc).isoformat()
        body = b""
        try:
            if fixtures is not None:
                with (fixtures / (source["id"] + ".raw")).open("rb") as handle:
                    body = handle.read(source["max_bytes"] + 1)
            else:
                request = urllib.request.Request(source["url"], headers={"User-Agent": "MAESTRO-source-audit/1.0"})
                try:
                    response = urllib.request.urlopen(request, timeout=35)
                except urllib.error.HTTPError as exc:
                    response = exc
                with response:
                    status = response.code
                    headers = dict(response.headers.items())
                    body = response.read(source["max_bytes"] + 1)
                if status != 200:
                    errors.append("http_status")
        except (OSError, urllib.error.URLError) as exc:
            errors.append(type(exc).__name__ + ": " + str(exc))
        complete = len(body) <= source["max_bytes"]
        if not complete:
            errors.append("byte_budget_exceeded")
        actual = _digest(body)
        if actual != source["sha256"]:
            errors.append("source_hash_changed")
        (out / (source["id"] + ".raw")).write_bytes(body)
        try:
            metadata = parse_metadata(body, source) if complete else None
        except (ValueError, KeyError, IndexError, TypeError, ET.ParseError, EOFError, OSError) as exc:
            metadata = None
            errors.append("metadata_parse_failed: " + str(exc))
        if not errors:
            parsed[source["id"]] = metadata
        receipts.append({
            "id": source["id"], "url": source["url"], "retrieved_at_utc": started,
            "mode": "offline_fixture" if fixtures is not None else "remote",
            "http_status": status, "response_headers": headers, "expected_format": source["format"],
            "sha256": actual, "expected_sha256": source["sha256"], "bytes": len(body),
            "retained_response_complete": complete, "errors": errors,
            "license": source["license"], "license_scope": source["license_scope"], "version": source["version"],
            "qualification": "verified_metadata_only" if not errors else "negative_receipt",
        })
        _receipt_path = out / "receipts.json"
        _receipt_path.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    linkage = None
    if "larry_cytokine_metadata" in parsed and "larry_cytokine_clones" in parsed:
        cells, matrix = parsed["larry_cytokine_metadata"], parsed["larry_cytokine_clones"]
        if matrix["columns"] == cells["rows"]:
            early, late = set(), set()
            for clone, cell, _ in matrix["memberships"]:
                (early if cells["time_points"][cell - 1] == "2" else late).add(clone)
            linkage = {"axis": "clones_by_cells", "early_clones": len(early), "late_clones": len(late),
                       "shared_early_late_clones": len(early & late), "scope": "membership only; not independent batches"}
        else:
            linkage = {"error": "clone_to_metadata_axis_mismatch"}
    for metadata in parsed.values():
        metadata.pop("memberships", None)
        metadata.pop("time_points", None)
    summary = {"sources": len(sources), "negative_receipts": sum(bool(row["errors"]) for row in receipts),
               "parsed_metadata": parsed, "clone_linkage": linkage,
               "state_gain_gate_passed": False, "eligible_state_gain_tasks": 0,
               "qualification": "Metadata reproduction cannot establish decision-time availability, complete attempts, independent batches or checkpoint nonexposure.",
               "models_called": [], "models_trained": 0, "scientific_effect_estimates": [],
               "source_pins_sha256": _digest(plan_bytes), "code_sha256": _digest(Path(__file__).read_bytes()),
               "python": sys.version, "command": [sys.executable, "-m", "tools.datasets.state_public_review", *sys.argv[1:]]}
    _write(out / "summary.json", summary)
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pins", type=Path, default=PINS)
    parser.add_argument("--fixtures", type=Path, help="Replay saved raw bytes without any network calls")
    arguments = parser.parse_args(argv)
    summary = run(arguments.out, pins_path=arguments.pins, fixtures=arguments.fixtures)
    print(json.dumps({key: summary[key] for key in ("sources", "negative_receipts", "state_gain_gate_passed")}))
    return int(summary["negative_receipts"] > 0 or bool(summary["clone_linkage"] and "error" in summary["clone_linkage"]))


if __name__ == "__main__":
    raise SystemExit(main())
