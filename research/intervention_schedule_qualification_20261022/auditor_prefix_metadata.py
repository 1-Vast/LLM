"""Offline metadata-prefix projection; stop before first MINiML Data-Table."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from auditor_metadata import SAMPLE_FIELDS, local

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_schedule_qualification/auditor_sources"
SERIES_FIELDS = {"Title", "Summary", "Overall-Design", "Pubmed-ID", "Sample-Ref", "Supplementary-Data", "Type"}


def project_prefix(raw):
    marker = re.search(rb"<(?:[A-Za-z0-9_]+:)?Data-Table\b", raw)
    prefix = raw[:marker.start()] if marker else raw
    parser = ET.XMLPullParser(events=("start", "end"))
    parser.feed(prefix)
    active = None
    entries = []
    for event, element in parser.read_events():
        tag = local(element.tag)
        if event == "start" and tag in {"Sample", "Series"}:
            active = {"kind": tag, "accession": element.attrib.get("iid"), "metadata": [], "complete_before_table_cutoff": False}
        if event == "end" and active is not None:
            allowed = SAMPLE_FIELDS if active["kind"] == "Sample" else SERIES_FIELDS
            if tag in allowed:
                active["metadata"].append({"field": tag, "attributes": dict(element.attrib), "text": " ".join(element.itertext()).strip()})
            if tag == active["kind"]:
                active["complete_before_table_cutoff"] = True
                entries.append(active)
                active = None
    if active is not None:
        entries.append(active)
    return {"metadata_prefix_bytes": len(prefix), "stopped_before_first_Data_Table": marker is not None,
            "entries": entries, "measurement_values_exported": False, "full_family_coverage_authenticated": False}


def main():
    target = OUT / "PARTIAL_PREFIX_METADATA.json"
    if target.exists():
        raise RuntimeError("Partial projection exists")
    source = OUT / "sealed_source/FAMILY_MINIML.xml"
    raw = source.read_bytes()
    result = project_prefix(raw)
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    result["recovery_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["metadata_prefix_bytes", "stopped_before_first_Data_Table", "full_family_coverage_authenticated"]}))
    print(json.dumps({"partial_sample_entries": sum(r["kind"] == "Sample" for r in result["entries"]),
                      "partial_series_entries": sum(r["kind"] == "Series" for r in result["entries"])}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "PREFIX_WORKER_FAILED", "error_type": type(exc).__name__}))
        raise SystemExit(1)
