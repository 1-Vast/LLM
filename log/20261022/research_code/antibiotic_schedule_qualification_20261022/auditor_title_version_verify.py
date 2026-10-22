"""Offline time/manifest verification for two authenticated Zenodo versions."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"
OUT = BASE / "version_followup"


def main():
    target = OUT / "VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Version verification exists")
    checks = 0
    def check(value):
        nonlocal checks
        if not value:
            raise AssertionError("Version metadata invariant failed")
        checks += 1
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))
    freeze = load(OUT / "PRE_REQUEST_FREEZE.json")
    for name, expected in freeze["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    receipt = load(OUT / "NETWORK.json")
    raw_path = OUT / "SOURCE_METADATA.json"
    check(receipt["status"] == 200 and not receipt["truncated"] and receipt["projection"] == "SUCCESS")
    check(raw_path.stat().st_size == receipt["bytes"] == 6692 <= receipt["additional_body_cap"])
    check(hashlib.sha256(raw_path.read_bytes()).hexdigest() == receipt["sha256"])
    old = load(OUT / "OLD_VERSION_IDENTITY.json")
    new_raw = next(r for r in load(BASE / "sealed_metadata/ZENODO_AUTHORS.json")["hits"]["hits"] if r["id"] == 22118144)
    # Only these explicitly allowed metadata times/version fields leave this offline worker.
    new_times = {k: new_raw.get(k) for k in ["created", "updated", "revision"]}
    new_times["metadata_version"] = new_raw.get("metadata", {}).get("version")
    new_times["publication_date"] = new_raw.get("metadata", {}).get("publication_date")
    comparison = load(OUT / "VERSION_COMPARISON.json")
    check(old["id"] == 18362221 and comparison["same_concept_parent"])
    check(old["description_citations"]["target_paper_DOI_literal_present"])
    check(old["metadata_version"] == "v1")
    check(old["title"] == "Multiplex Microfluidics(TAY LAB)_All 512 Chamber Images")
    check(len(old["files"]) == comparison["old_files"] == 7)
    check(sum(f["size"] for f in old["files"]) == comparison["old_total_file_bytes"] == 8282569524)
    check(len({f["key"] for f in old["files"]}) == 7)
    check(len(comparison["names_only_old"]) == 7 and len(comparison["names_only_new"]) == 6)
    check(not comparison["common_file_identity_equal"])
    readme = (ROOT / "log/20261022/antibiotic_schedule_qualification/code_discovery/LIST_README.md").read_text(encoding="utf-8")
    check("Additional image data are available at DOI:10.5281/zenodo.18362221" in readme)
    timestamps = {"old": {k: old.get(k) for k in ["created", "updated", "record_revision", "metadata_version", "publication_date"]},
                  "new": new_times, "latest_metadata_source_sha256": hashlib.sha256((BASE / "sealed_metadata/ZENODO_AUTHORS.json").read_bytes()).hexdigest(),
                  "publication_date_is_not_assumed_equal_to_created_or_updated": True}
    (OUT / "TIMESTAMP_COMPARISON.json").write_text(json.dumps(timestamps, indent=2), encoding="utf-8")
    result = {"status": "PASS", "checks": checks, "exact_followup_HTTP_requests": 1,
              "followup_response_body_bytes": 6692, "pre_request_frozen_files_unchanged": len(freeze["sha256"]),
              "same_concept_different_disjoint_file_manifests": True,
              "source_image_archive_or_presentation_payload_read": False,
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"verification": result, "metadata_timestamps": timestamps}, indent=2))


if __name__ == "__main__":
    main()
