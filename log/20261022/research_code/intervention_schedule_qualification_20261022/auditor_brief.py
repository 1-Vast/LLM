"""Single separately amended 64KiB sample-only brief metadata worker."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/intervention_schedule_qualification"
OUT = BASE / "auditor_sources"
URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=gsm&form=text&view=brief"
ALLOWED = {"Sample_title", "Sample_geo_accession", "Sample_type", "Sample_source_name_ch1",
           "Sample_organism_ch1", "Sample_characteristics_ch1", "Sample_treatment_protocol_ch1",
           "Sample_growth_protocol_ch1", "Sample_molecule_ch1", "Sample_extract_protocol_ch1",
           "Sample_label_ch1", "Sample_label_protocol_ch1", "Sample_hyb_protocol", "Sample_scan_protocol",
           "Sample_data_processing", "Sample_platform_id", "Sample_series_id", "Sample_supplementary_file"}


def project(raw):
    marker = raw.lower().find(b"!sample_table_begin")
    prefix = raw if marker < 0 else raw[:marker]
    lines = prefix.decode("utf-8").splitlines()
    samples, active = [], None
    for line in lines:
        if line.startswith("^SAMPLE = "):
            active = {"accession": line.split(" = ", 1)[1], "metadata": []}
            samples.append(active)
        elif active is not None and line.startswith("!") and " = " in line:
            field, text = line[1:].split(" = ", 1)
            if field in ALLOWED:
                active["metadata"].append({"field": field, "text": text})
    return {"samples": samples, "stopped_before_sample_table_begin": marker >= 0,
            "measurement_values_exported": False}


def main():
    receipt = OUT / "BRIEF_NETWORK.json"
    if receipt.exists():
        raise RuntimeError("Amended one-request receipt exists")
    amendment = OUT / "AMENDMENT_BRIEF_METADATA.md"
    freeze = {"amendment_sha256": hashlib.sha256(amendment.read_bytes()).hexdigest(),
              "worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT / "BRIEF_PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    record = {"url": URL, "started_utc": datetime.now(timezone.utc).isoformat(), "additional_cap_bytes": 65536}
    received, parts = 0, []
    try:
        with requests.get(URL, stream=True, timeout=40) as response:
            record.update({"status": response.status_code, "final_url": response.url, "headers": dict(response.headers)})
            while received < 65536:
                part = response.raw.read(min(4096, 65536 - received), decode_content=True)
                if not part:
                    break
                received += len(part)
                parts.append(part)
        raw = b"".join(parts)
        (OUT / "sealed_source/SAMPLES_BRIEF.txt").write_bytes(raw)
        record.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_additional_cap": received == 65536})
        if record["status"] != 200:
            raise RuntimeError("Amended metadata HTTP failure")
        projected = project(raw)
        projected["body_truncated_at_additional_cap"] = received == 65536
        (OUT / "SAMPLES_BRIEF_METADATA.json").write_text(json.dumps(projected, indent=2, ensure_ascii=False), encoding="utf-8")
        record.update({"projection": "COMPLETE_OR_EXPLICIT_PREFIX", "sample_entries": len(projected["samples"])})
    except Exception as exc:
        record.update({"failure_type": type(exc).__name__, "projection": "FAILED_NO_SOURCE_ECHO"})
    record["receipt_utc"] = datetime.now(timezone.utc).isoformat()
    receipt.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["status", "bytes", "truncated_at_additional_cap", "projection", "sample_entries"] if k in record}))


if __name__ == "__main__":
    main()
