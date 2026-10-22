"""Verify approved metadata projection and exact 21-ID contract, without raw XML decode."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from auditor_biosample import safe_identity

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives"
OUT = BASE / "biosample_identity_followup"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("BioSample verification exists")
    checks = 0
    def check(value):
        nonlocal checks
        if not value:
            raise AssertionError("BioSample identity invariant failed")
        checks += 1
    def read(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    freeze = read("PRE_REQUEST_FREEZE.json")
    for name, expected in freeze["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    receipt = read("NETWORK.json")
    source = OUT / "sealed_source/BIOSAMPLE.xml"
    check(source.stat().st_size == receipt["bytes"] == 42136 <= 500000)
    check(hashlib.sha256(source.read_bytes()).hexdigest() == receipt["sha256"])
    check(receipt["status"] == 200 and not receipt["truncated_at_cap"] and receipt["projection"] == "SUCCESS")
    projection = read("IDENTITY_METADATA.json")
    samples = projection["samples"]
    check(len(samples) == receipt["returned_samples"] == 21)
    expected = json.loads((BASE / "manifest_followup/amendment2_sources/RELATION_SUMMARY.json").read_text(encoding="utf-8"))["unique_linked_BioSample_Entrez_ids"]
    check({s["entrez_id"] for s in samples} == set(expected) == set(receipt["requested_Entrez_ids"]))
    check(len({s["accession"] for s in samples}) == len({s["entrez_id"] for s in samples}) == 21)
    allowed_sample_fields = {"entrez_id", "accession", "submission_date", "publication_date", "last_update", "title", "sample_name_ids", "taxonomy", "owner", "collection_dates", "attribute_names", "strain_isolate_sample_identity"}
    labels, strain_values, isolate_values = [], [], []
    for sample in samples:
        check(set(sample) == allowed_sample_fields)
        check(sample["accession"] == f"SAMN{sample['entrez_id']}")
        check(sample["taxonomy"] == {"taxonomy_id": "562", "taxonomy_name": "Escherichia coli", "organism_name": "Escherichia coli"})
        check(sample["owner"]["name"] == "Concordia University")
        check(sample["title"] == {"value": None, "withheld": True, "reason": "POSSIBLE_PHENOTYPE_OR_RESPONSE_CONTENT"})
        check(len(sample["sample_name_ids"]) == 1)
        identifier = sample["sample_name_ids"][0]
        check(not identifier["withheld"] and safe_identity(identifier["value"])["value"] == identifier["value"])
        labels.append(identifier["value"])
        check({a["attribute_name"] for a in sample["attribute_names"]} == {"strain", "isolate", "host", "isolation_source", "collection_date", "geo_loc_name", "sample_type"})
        check(len(sample["strain_isolate_sample_identity"]) == 2)
        for item in sample["strain_isolate_sample_identity"]:
            check(item["attribute_name"] in {"strain", "isolate"})
            check(not item["withheld"] and not safe_identity(item["value"])["withheld"])
            if item["attribute_name"] == "strain":
                strain_values.append(item["value"])
            else:
                isolate_values.append(item["value"])
        check(sample["collection_dates"] == [{"attribute_name": "collection_date", "value": "2024-04-23"}])
    check(len(set(labels)) == 21)
    check(set(strain_values) == {"K-12"})
    check(set(isolate_values) == {f"Laboratory strain {i}" for i in range(1, 22)})
    check(Counter("-".join(name.split("-")[:2]) for name in labels) == {"PN-GR": 9, "PN-FR": 9, "NG-NR": 3})
    check({n for n in labels if n.startswith("PN-GR-")} == {f"PN-GR-{s}-{r}" for s in [2, 3, 4] for r in [2, 4, 6]})
    check({n for n in labels if n.startswith("PN-FR-")} == {f"PN-FR-{s}-{r}" for s in [2, 3, 4] for r in [3, 6, 8]})
    check({n for n in labels if n.startswith("NG-NR-")} == {f"NG-NR-1-{r}" for r in [2, 4, 6]})
    census = read("IDENTITY_CENSUS.json")
    check(census["returned_records"] == census["unique_accessions"] == census["unique_entrez_ids"] == 21)
    check(not census["missing_requested_entrez_ids"] and not census["unexpected_entrez_ids"])
    check(census["explicit_loop_stage_figure_row_or_first_retry_attribute_names"] == [])
    check(hashlib.sha256((OUT / "IDENTITY_METADATA.json").read_bytes()).hexdigest() == census["input_projection_sha256"])
    result = {"status": "PASS", "checks": checks, "pre_request_frozen_files_unchanged": len(freeze["sha256"]),
              "actual_HTTP_requests": 1, "consumed_HTTP_body_bytes": receipt["bytes"],
              "exact_requested_and_returned_unique_BioSample_ID_count": 21,
              "source_XML_decoded_by_verifier": False,
              "scope": "Frozen bytes, exact IDs/accessions, approved field schema and identity-name arithmetic; not semantic loop/stage/row matching or phenotype validation"}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
