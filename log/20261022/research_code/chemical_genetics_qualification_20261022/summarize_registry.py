"""Summarize filename identity only; never open a registered data file."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/chemical_genetics_qualification"
record = json.loads((OUT / "ZENODO_MANIFEST.json").read_text(encoding="utf-8"))
matched = []
unmatched = []
for item in record["files"]:
    match = re.fullmatch(r"(?P<drug>.+)_lineage(?P<lineage>\d+)_day(?P<day>\d+)\.fastq", item["key"])
    if match:
        matched.append({"file": item["key"], "drug": match["drug"],
                        "lineage": int(match["lineage"]), "day": int(match["day"])})
    else:
        unmatched.append(item["key"])
drugs = sorted({item["drug"] for item in matched})
lineages = sorted({item["lineage"] for item in matched})
days = sorted({item["day"] for item in matched})
expected = {(drug, lineage, day) for drug in drugs for lineage in lineages for day in days}
observed = {(item["drug"], item["lineage"], item["day"]) for item in matched}
network = json.loads((OUT / "sources/NETWORK.json").read_text(encoding="utf-8"))
summary = {
    "record_doi": record["doi"], "file_count": len(record["files"]),
    "registered_file_bytes_not_downloaded": sum(item["size"] for item in record["files"]),
    "parsed_evolution_filename_count": len(matched), "filename_drugs": drugs,
    "filename_lineages": lineages, "filename_days": days,
    "missing_filename_cartesian_cells": sorted(expected - observed),
    "duplicate_filename_identity_count": len(matched) - len(observed),
    "unmatched_filenames": unmatched, "identities_from_filenames_only": True,
    "functional_join_authenticated": False, "data_files_downloaded": 0,
    "http_requests": len(network), "response_body_bytes": sum(item["body_bytes"] for item in network),
}
(OUT / "REGISTRY_IDENTITY_SUMMARY.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
