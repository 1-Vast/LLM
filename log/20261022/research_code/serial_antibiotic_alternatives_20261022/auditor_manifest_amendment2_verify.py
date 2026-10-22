"""Verify actual project relation, preserving earlier failures and data boundaries."""
import hashlib
import json
from pathlib import Path

from auditor_manifest_amendment2 import project_link, project_search

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives/manifest_followup/amendment2_sources"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Amendment2 verification exists")
    checks = 0
    def check(condition):
        nonlocal checks
        if not condition:
            raise AssertionError("Amendment2 invariant failed")
        checks += 1
    def read(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    freeze = read("PRE_REQUEST_FREEZE.json")
    for name, expected in freeze["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    ledger = read("NETWORK.json")
    check(len(ledger["requests"]) == 3)
    check(sum(r["bytes"] for r in ledger["requests"]) == ledger["additional_consumed_HTTP_body_bytes"] == 1446)
    for receipt in ledger["requests"]:
        source = OUT / f"{receipt['name']}_SOURCE.body"
        check(source.stat().st_size == receipt["bytes"])
        check(hashlib.sha256(source.read_bytes()).hexdigest() == receipt["sha256"])
        check(not receipt["truncated_at_shared_cap"])
    check(ledger["requests"][0]["status"] == 403 and ledger["requests"][0]["projection"] == "FAILED_NO_RAW_CONTENT_ECHO")
    check(not (OUT / "CURRENT_PMC_OA_METADATA.json").exists())
    search = read("BIOPROJECT_SEARCH_METADATA.json")
    check(project_search((OUT / "BIOPROJECT_SEARCH_SOURCE.body").read_bytes()) == search)
    check(search["count"] == "1" and search["idlist"] == ["1254677"])
    check(not search["errorlist"] and not search["warninglist"])
    link = read("BIOPROJECT_BIOSAMPLE_LINK_METADATA.json")
    check(project_link((OUT / "BIOPROJECT_BIOSAMPLE_LINK_SOURCE.body").read_bytes()) == link)
    check(len(link["linksets"]) == 1)
    entries = link["linksets"][0]
    check(entries["input_project_ids"] == search["idlist"] and entries["dbfrom"] == "bioproject")
    check(len(entries["linksetdbs"]) == 3)
    sets = []
    for relation in entries["linksetdbs"]:
        check(relation["dbto"] == "biosample")
        check(len(relation["ids"]) == len(set(relation["ids"])) == relation["linked_record_count"] == 21)
        sets.append(set(relation["ids"]))
    check(sets[0] == sets[1] == sets[2])
    union = sorted(set.union(*sets), key=int)
    check(len(union) == 21)
    summary = {"BioProject_accession_query": "PRJNA1254677", "BioProject_Entrez_id": search["idlist"],
               "actual_querytranslation": search["querytranslation"], "unique_linked_BioSample_Entrez_ids": union,
               "unique_linked_BioSample_records": len(union),
               "relation_names": [r["linkname"] for r in entries["linksetdbs"]],
               "all_relation_id_sets_identical": True,
               "linked_records_are_independent_strain_lineage_context_or_task_counts": False,
               "BioSample_attributes_or_genomic_phenotypic_values_retrieved": False}
    (OUT / "RELATION_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    result = {"status": "PASS", "checks": checks, "pre_request_frozen_artifacts_unchanged": len(freeze["sha256"]),
              "new_requests": 3, "new_response_body_bytes": 1446,
              "authenticated_unique_linked_BioSample_records": 21,
              "earlier_original_failure_report_unchanged": True,
              "scope": "Source/accounting/unchanged old failure record and actual project-to-sample relation; no sample attributes, biology, functional coverage or model validation"}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
