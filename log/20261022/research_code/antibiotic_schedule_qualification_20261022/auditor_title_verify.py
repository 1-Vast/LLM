"""Verify finite registry evidence and normalize exported bibliography, without files."""
import hashlib
from html import unescape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Registry verification exists")
    checks = 0
    def check(value):
        nonlocal checks
        if not value:
            raise AssertionError("Registry evidence invariant failed")
        checks += 1
    def read(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    for name, digest in read("PRE_REQUEST_FREEZE.json")["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest)
    ledger = read("NETWORK.json")
    check(len(ledger["requests"]) == 4)
    check(sum(r["bytes"] for r in ledger["requests"]) == ledger["combined_consumed_body_bytes"] == 41111)
    for receipt in ledger["requests"]:
        source = OUT / "sealed_metadata" / f"{receipt['name']}.json"
        check(source.stat().st_size == receipt["bytes"])
        check(hashlib.sha256(source.read_bytes()).hexdigest() == receipt["sha256"])
        check(receipt["status"] == 200 and receipt["projection"] == "SUCCESS" and not receipt["truncated_at_shared_cap"])
    check(read("ZENODO_TITLE_IDENTITY.json")["total"] == 0)
    check(read("DATACITE_TITLE_IDENTITY.json")["total"] == 0)
    author = read("ZENODO_AUTHORS_IDENTITY.json")
    check(author["total"] == len(author["records"]) == 4)
    record = next(r for r in author["records"] if r["id"] == 22118144)
    citation = next(r for r in read("ZENODO_DESCRIPTION_CITATIONS.json")["records"] if r["registry_id"] == 22118144)
    normalize = lambda text: unescape(text).split()[0].rstrip(".,;)")
    urls = [normalize(u) for u in citation["citation_URL_strings"]]
    dois = [normalize(d) for d in citation["citation_DOI_strings"]]
    check(citation["target_paper_DOI_literal_present"])
    check("https://www.biorxiv.org/content/10.1101/2025.10.30.684665v1" in urls)
    check("10.1101/2025.10.30.684665v1" in dois)
    check(any(c["name"] == "Jeong, Yoon" for c in record["creators"]))
    check(record["related_identifiers"] is None)
    check(len(record["files"]) == 6)
    check(sum(f["key"].endswith(".zip") for f in record["files"]) == 4)
    check(sum(f["key"].endswith(".png") for f in record["files"]) == 2)
    check(record["record_links"]["parent"] == "https://zenodo.org/api/records/18362220")
    linked = {"record": {k: record[k] for k in ["id", "title", "creators", "doi", "publication_date", "related_identifiers", "files"]},
              "parent_record": record["record_links"]["parent"],
              "normalized_description_citation_URLs": urls, "normalized_description_citation_DOIs": dois,
              "normalization": "HTML entity decoding, first whitespace-delimited token, trailing bibliographic punctuation removed; original literal projection retained",
              "direct_data_paper_link": "EXPLICIT_TARGET_PAPER_DOI_IN_REGISTRY_DESCRIPTION_PLUS_MATCHED_AUTHOR",
              "manifest_total_bytes": sum(f["size"] for f in record["files"]),
              "manifest_is_archive_contents_or_schedule_table_schema": False,
              "payload_files_downloaded": False}
    (OUT / "LINKED_RECORD_MANIFEST.json").write_text(json.dumps(linked, indent=2, ensure_ascii=False), encoding="utf-8")
    result = {"status": "PASS", "checks": checks, "original_frozen_files_unchanged": 3,
              "new_HTTP_requests": 4, "consumed_HTTP_body_bytes": ledger["combined_consumed_body_bytes"],
              "authenticated_target_paper_linked_record": 22118144,
              "data_payload_read": False,
              "scope": "Registry source/hash/count accounting and explicit bibliography/author/manifest authentication; no treatment-menu or biological validation"}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
