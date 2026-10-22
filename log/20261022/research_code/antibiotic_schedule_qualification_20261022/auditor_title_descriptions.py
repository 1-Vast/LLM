"""Offline source-explanation text with numbers masked and time/citation identity only."""
import hashlib
from html import unescape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"
OUT = BASE / "version_followup"


def project(description):
    text = unescape(re.sub(r"<[^>]*>", " ", description))
    text = " ".join(text.split())
    urls = sorted({u.rstrip(".,;)") for u in re.findall(r"https?://[^\s<>\"']+", text)})
    for index, url in enumerate(urls):
        text = text.replace(url, f"[citation {chr(65 + index)}]")
    times = re.findall(r"\b\d+(?:\.\d+)?\s*[-–]?\s*(?:milliseconds?|seconds?|minutes?|hours?|days?|hr|min|h|s)\b", text, flags=re.I)
    redacted = re.sub(r"\d+(?:\.\d+)?", "[NUMBER]", text)
    return {"source_description_numeric_tokens_redacted": redacted,
            "literal_time_mentions_in_source_description": times,
            "source_description_citation_URLs": urls,
            "time_lapse_literal_mentioned": bool(re.search(r"time[ -]?lapse", text, re.I)),
            "time_mentions_are_not_independently_verified_acquisition_schedule": True}


def main():
    target = OUT / "DESCRIPTION_SOURCE_EVIDENCE.json"
    if target.exists():
        raise RuntimeError("Description source projection exists")
    old_path = OUT / "SOURCE_METADATA.json"
    latest_path = BASE / "sealed_metadata/ZENODO_AUTHORS.json"
    old = json.loads(old_path.read_bytes())
    latest = next(r for r in json.loads(latest_path.read_bytes())["hits"]["hits"] if r["id"] == 22118144)
    result = {"records": [{"registry_id": record["id"], **project(record["metadata"].get("description", ""))} for record in [old, latest]],
              "source_sha256": {"old": hashlib.sha256(old_path.read_bytes()).hexdigest(), "new": hashlib.sha256(latest_path.read_bytes()).hexdigest()},
              "projection_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "image_or_observed_numerical_response_payload_read": False}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
