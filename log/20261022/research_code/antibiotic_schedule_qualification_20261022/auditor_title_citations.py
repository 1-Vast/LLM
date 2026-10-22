"""Offline citation-only projection of saved registry descriptions; no full prose/data."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"
TARGET_DOI = "10.1101/2025.10.30.684665"
TARGET_TITLE = "Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D"


def project(metadata):
    description = metadata.get("description", "")
    if not isinstance(description, str):
        raise ValueError("Nontext registry description")
    normalized = " ".join(re.sub("<[^>]*>", " ", description).split()).casefold()
    return {"target_paper_DOI_literal_present": TARGET_DOI in description.casefold(),
            "target_paper_fulltitle_present": TARGET_TITLE.casefold() in normalized,
            "citation_DOI_strings": sorted({x.rstrip(".,;)") for x in re.findall(r"\b10\.\d{4,9}/[^\s<>\"']+", description)}),
            "citation_URL_strings": sorted({x.rstrip(".,;)") for x in re.findall(r"https?://[^\s<>\"']+", description)})}


def main():
    target = OUT / "ZENODO_DESCRIPTION_CITATIONS.json"
    if target.exists():
        raise RuntimeError("Citation projection exists")
    source = OUT / "sealed_metadata/ZENODO_AUTHORS.json"
    body = json.loads(source.read_bytes())
    results = [{"registry_id": record["id"], **project(record.get("metadata", {}))}
               for record in body["hits"]["hits"]]
    result = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "projection_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "records": results,
              "description_text_or_measurement_values_exported": False}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
