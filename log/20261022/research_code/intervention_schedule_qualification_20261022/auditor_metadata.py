"""Two-request official GSE30516 metadata worker; never export measurement tables."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/intervention_schedule_qualification"
OUT = BASE / "auditor_sources"
REQUESTS = [
    ("FAMILY_MINIML", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=all&view=full&form=xml", "xml"),
    ("SERIES_SOFT", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=self&view=full&form=text", "text"),
]
SAMPLE_FIELDS = {"Title", "Type", "Source", "Organism", "Characteristics", "Growth-Protocol",
                 "Treatment-Protocol", "Molecule", "Extract-Protocol", "Label", "Label-Protocol",
                 "Hybridization-Protocol", "Scan-Protocol", "Data-Processing", "Platform-Ref",
                 "Supplementary-Data"}
SERIES_FIELDS = {"Series_title", "Series_geo_accession", "Series_type", "Series_pubmed_id",
                 "Series_summary", "Series_overall_design", "Series_platform_id", "Series_sample_id",
                 "Series_supplementary_file", "Series_status", "Series_last_update_date"}


def local(tag):
    return tag.rsplit("}", 1)[-1]


def project_miniml(raw):
    # Mask entire measurement tables at the byte level before decoding XML text.
    table = rb"<(?:[A-Za-z0-9_]+:)?Data-Table\b[^>]*?(?<!/)>.*?</(?:[A-Za-z0-9_]+:)?Data-Table\s*>"
    clean, removed = re.subn(table, b"", raw, flags=re.S)
    clean, empty = re.subn(rb"<(?:[A-Za-z0-9_]+:)?Data-Table\b[^>]*/>", b"", clean)
    root = ET.fromstring(clean)
    if local(root.tag) != "MINiML":
        raise ValueError("Not MINiML metadata")
    samples = []
    series = []
    for element in root:
        if local(element.tag) == "Sample":
            fields = []
            for child in element.iter():
                tag = local(child.tag)
                if tag in SAMPLE_FIELDS:
                    fields.append({"field": tag, "attributes": dict(child.attrib),
                                   "text": " ".join(child.itertext()).strip()})
            samples.append({"accession": element.attrib.get("iid"), "metadata": fields})
        if local(element.tag) == "Series":
            fields = []
            for child in element:
                tag = local(child.tag)
                if tag in {"Title", "Summary", "Overall-Design", "Pubmed-ID", "Sample-Ref", "Supplementary-Data", "Type"}:
                    fields.append({"field": tag, "attributes": dict(child.attrib), "text": " ".join(child.itertext()).strip()})
            series.append({"accession": element.attrib.get("iid"), "metadata": fields})
    return {"samples": samples, "series": series, "measurement_table_blocks_discarded": removed + empty,
            "measurement_values_exported": False}


def project_soft(raw):
    cutoff = raw.lower().find(b"!sample_table_begin")
    prefix = raw if cutoff < 0 else raw[:cutoff]
    fields = []
    for line in prefix.decode("utf-8").splitlines():
        if not line.startswith("!") or " = " not in line:
            continue
        name, value = line[1:].split(" = ", 1)
        if name in SERIES_FIELDS:
            fields.append({"field": name, "text": value})
    if not any(r["field"] == "Series_geo_accession" and r["text"] == "GSE30516" for r in fields):
        raise ValueError("Exact series identity missing")
    return {"series": fields, "stopped_before_sample_table_begin": cutoff >= 0,
            "measurement_values_exported": False}


def main():
    receipt_path = OUT / "NETWORK.json"
    if receipt_path.exists():
        raise RuntimeError("Auditor request ledger exists; no restart")
    freeze = json.loads((OUT / "PRE_OPEN_FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Frozen input changed")
    (OUT / "sealed_source").mkdir(parents=True, exist_ok=True)
    ledger, received = [], 0
    for name, url, mode in REQUESTS:
        record = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
        try:
            with requests.get(url, timeout=40, stream=True) as response:
                record.update({"status": response.status_code, "final_url": response.url,
                               "headers": dict(response.headers)})
                parts = []
                while received < 2_000_000:
                    part = response.raw.read(min(16384, 2_000_000 - received), decode_content=True)
                    if not part:
                        break
                    received += len(part)
                    parts.append(part)
                raw = b"".join(parts)
            (OUT / "sealed_source" / f"{name}.{mode}").write_bytes(raw)
            record.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            if received >= 2_000_000:
                record["truncated_at_shared_cap"] = True
                raise RuntimeError("Two-request body cap reached; no further bytes read")
            if record["status"] != 200:
                raise RuntimeError("HTTP request unsuccessful")
            projected = project_miniml(raw) if mode == "xml" else project_soft(raw)
            (OUT / f"{name}_METADATA.json").write_text(json.dumps(projected, indent=2, ensure_ascii=False), encoding="utf-8")
            record["projection"] = "SUCCESS"
        except Exception as exc:
            record["failure_type"] = type(exc).__name__
            record["projection"] = "FAILED_NO_RAW_CONTENT_ECHO"
        record["receipt_utc"] = datetime.now(timezone.utc).isoformat()
        ledger.append(record)
        receipt_path.write_text(json.dumps({"response_body_bytes": received, "requests": ledger}, indent=2), encoding="utf-8")
        print(json.dumps({k: record[k] for k in ["name", "projection", "status", "bytes"] if k in record}))
        if received >= 2_000_000:
            break


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"worker_status": "FAILED", "error_type": type(exc).__name__}))
        raise SystemExit(1)
