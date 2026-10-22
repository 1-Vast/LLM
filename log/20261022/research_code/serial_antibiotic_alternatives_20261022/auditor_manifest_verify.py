"""Verify finite metadata failure/ambiguity and supplement identity without values."""
import hashlib
import json
from pathlib import Path

from auditor_manifest import project_esearch, project_supplements

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives"
OUT = BASE / "manifest_followup"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Manifest verification exists")
    checks = 0
    def check(value):
        nonlocal checks
        if not value:
            raise AssertionError("Manifest evidence invariant failed")
        checks += 1
    def load(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    freeze = load("PRE_REQUEST_FREEZE.json")
    for name, expected in freeze["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    ledger = load("NETWORK.json")
    check(len(ledger["requests"]) == 2)
    check(sum(r["bytes"] for r in ledger["requests"]) == ledger["consumed_HTTP_body_bytes"] == 1953)
    for receipt in ledger["requests"]:
        path = OUT / f"{receipt['name']}_SOURCE.body"
        check(path.stat().st_size == receipt["bytes"])
        check(hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"])
        check(not receipt["truncated_at_shared_cap"])
    check(ledger["requests"][0]["status"] == 404 and ledger["requests"][0]["projection"] == "FAILED_NO_RAW_CONTENT_ECHO")
    check(not (OUT / "PMC_OA_METADATA.json").exists())
    bio = load("BIOSAMPLE_COUNT_METADATA.json")
    check(project_esearch((OUT / "BIOSAMPLE_COUNT_SOURCE.body").read_bytes()) == bio)
    check(bio["count"] == "0" and bio["retmax"] == "0")
    check(bio["querytranslation"] == "(PRJNA1254677[All Fields])")
    check(bio["errorlist"]["phrasesnotfound"] == ["PRJNA1254677[All Fields]"])
    supplements = load("SUPPLEMENT_MEDIA_METADATA.json")
    check(project_supplements((BASE / "TRIPARTITE.xml").read_bytes()) == supplements)
    check(any(r["type"] == "doi" and r["value"] == "10.1093/molbev/msaf115" for r in supplements["article_identifiers"]))
    check(len(supplements["supplements"]) == 1)
    check(supplements["supplements"][0]["media"][0]["href"] == "msaf115_supplementary_data.pdf")
    result = {"status": "PASS", "checks": checks, "pre_request_frozen_files_unchanged": len(freeze["sha256"]),
              "HTTP_requests": 2, "consumed_HTTP_body_bytes": 1953,
              "OA_entry_failure_retained_not_reinterpreted_as_article_access_status": True,
              "zero_BioSample_result_not_a_validated_exact_project_link_count": True,
              "supplement_genome_or_phenotype_payloads_read": False,
              "scope": "Metadata/failure provenance, query translation caveat and retained supplement filename; not functional data eligibility"}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
