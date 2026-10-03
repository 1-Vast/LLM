"""Rebuild receipt summaries and source-linked metadata without inventing events."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from tools.datasets.state_prospective_input import digest, write_json


def run(raw, out):
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    for receipt_path in sorted(raw.glob("*/receipts.json")):
        for record in json.loads(receipt_path.read_text(encoding="utf-8")):
            source = receipt_path.parent / record["path"]
            if source.exists() and digest(source) != record["sha256"]:
                raise ValueError("source checksum mismatch: " + str(source))
            record["source_path"] = str(source)
            record["elapsed_seconds"] = (datetime.fromisoformat(record["finished_at_utc"]) - datetime.fromisoformat(record["started_at_utc"])).total_seconds()
            receipts.append(record)
    services = {}
    for record in receipts:
        service = record.get("service", record["url"].split("/")[2])
        group = services.setdefault(service, {"requests": 0, "failures": 0, "retry_requests": 0, "elapsed_request_seconds_sum": 0.0, "cost": "unknown", "model": "not_applicable"})
        group["requests"] += 1
        group["failures"] += record["error"] is not None
        group["retry_requests"] += record.get("retry", 0) > 0
        group["elapsed_request_seconds_sum"] += record["elapsed_seconds"]
    write_json(out / "api_summary.json", {"services": services, "requests": len(receipts),
               "failures": sum(r["error"] is not None for r in receipts), "cost": "unknown",
               "model_api_requests": 0, "local_state_requests": "see certification_v1/v2; no remote model substitution",
               "interpretation": "HTTP success only certifies acquisition, never scientific qualification", "receipts": receipts})
    search_hits = []
    for record in receipts:
        if "/europepmc/webservices/rest/search?" in record["url"] and record["error"] is None:
            data = json.loads(Path(record["source_path"]).read_text(encoding="utf-8"))
            search_hits.append({"source_id": record["id"], "query": record.get("query"), "hit_count": data.get("hitCount"),
                                "retrieved_results": [{k: item.get(k) for k in ("id", "pmcid", "doi", "title", "firstPublicationDate")} for item in data.get("resultList", {}).get("result", [])]})
    write_json(out / "search_coverage.json", {"queries": search_hits, "coverage": "bounded first pages, not an exhaustive systematic review", "screening": "targeted mechanistic and protocol follow-up; broad default-ranked queries retained as noisy discovery, not qualification evidence"})
    for record in receipts:
        if record["error"] or not (record["id"].endswith("_xml") or record["id"].endswith("_bioc")):
            continue
        tree = ET.fromstring(Path(record["source_path"]).read_bytes())
        if record["id"].endswith("_bioc"):
            paragraphs = [" ".join((el.text or "").split()) for el in tree.iter("text")]
        else:
            paragraphs = [" ".join("".join(el.itertext()).split()) for el in tree.iter() if el.tag in ("p", "title", "license", "ext-link")]
        (out / (record["id"] + ".paragraphs.txt")).write_text("\n".join(f"{i+1}\t{line}" for i, line in enumerate(paragraphs)) + "\n", encoding="utf-8")
    source = raw / "metadata/liveseq_metadata.raw"
    with source.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        metadata = list(reader)
    # Preserve all published rows, including unavailable endpoints. No enrollment
    # denominator or physical independence is inferred from this filtered metadata.
    records = []
    for index, row in enumerate(metadata, 2):
        records.append({"source_row_csv_including_header": index, "source_sha256": digest(source),
                        "source_record_id": row["sample_ID"], "native_sample_name": row["sample_name"],
                        "native_fields": row, "physical_batch": None, "state_available_at": None,
                        "decision_at": None, "execution_ack": None, "attempt_status": "unknown",
                        "endpoint_present": row["mCherry.log.slope"] not in ("", "NA"),
                        "classification": "replay_only", "cost": None})
    with (out / "liveseq_metadata_rows.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_json(out / "liveseq_inventory.json", {"rows": len(records), "fields": fields,
               "rows_with_published_slope": sum(r["endpoint_present"] for r in records),
               "source_sha256": digest(source), "missingness": {key: sum(row[key] in ("", "NA") for row in metadata) for key in ("Date", "Extraction_time_h", "mCherry.log.slope")},
               "paper_analysis_subset": "Methods reports 40 jointly tracked/sampled cells, 17 pass stated QC; 24 populated metadata slopes are not 24 certified independent trials",
               "viewed_outcomes": "published metadata endpoint columns inspected this round; development/exploratory only",
               "complete_attempt_denominator": "unknown; published metadata is not enrollment ledger"})
    samples = []
    for record in receipts:
        if not record["id"].startswith("GSM") or record["error"]:
            continue
        for row_number, line in enumerate(Path(record["source_path"]).read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("!Sample_") and " = " in line:
                field, value = line.split(" = ", 1)
                samples.append(dict(accession=record["id"].removesuffix("_retry"), source_row=row_number,
                                    source_sha256=record["sha256"], field=field, value=value))
    with (out / "geo_sample_fields.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["accession", "source_row", "source_sha256", "field", "value"])
        writer.writeheader()
        writer.writerows(samples)
    write_json(out / "geo_inventory.json", {"sample_accessions": sorted({s["accession"] for s in samples}),
               "field_rows": len(samples), "execution": "GEO title/treatment are sample annotations, not actuator acknowledgements"})
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    write_json(out / "manifest.json", {p.name: digest(p) for p in out.iterdir() if p.is_file()})
    return {"requests": len(receipts), "liveseq_rows": len(records), "sample_accessions": len({s["accession"] for s in samples})}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.raw, args.out)))
