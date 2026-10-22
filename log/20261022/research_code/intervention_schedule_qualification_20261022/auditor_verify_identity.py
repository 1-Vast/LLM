"""Verify metadata export, sample identity and source/freeze accounting without tables."""
import hashlib
import json
from pathlib import Path

from auditor_brief import ALLOWED

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/intervention_schedule_qualification"
OUT = BASE / "auditor_sources"


def main():
    target = OUT / "IDENTITY_VERIFICATION.json"
    if target.exists():
        raise RuntimeError("Identity verification exists")
    checks = 0
    def check(condition):
        nonlocal checks
        if not condition:
            raise AssertionError("Identity audit invariant failed")
        checks += 1
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))
    original = load(OUT / "PRE_OPEN_FREEZE.json")["sha256"]
    for relative, expected in original.items():
        check(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected)
    brief_freeze = load(OUT / "BRIEF_PRE_REQUEST_FREEZE.json")
    check(hashlib.sha256((OUT / "AMENDMENT_BRIEF_METADATA.md").read_bytes()).hexdigest() == brief_freeze["amendment_sha256"])
    check(hashlib.sha256((ROOT / "research/intervention_schedule_qualification_20261022/auditor_brief.py").read_bytes()).hexdigest() == brief_freeze["worker_sha256"])
    first = load(OUT / "NETWORK.json")
    check(len(first["requests"]) == 1)
    check(first["response_body_bytes"] == 2_000_000)
    check(first["requests"][0]["truncated_at_shared_cap"])
    second = load(OUT / "BRIEF_NETWORK.json")
    check(second["bytes"] == 57_292 <= second["additional_cap_bytes"])
    check(not second["truncated_at_additional_cap"])
    for filename, receipt in [("FAMILY_MINIML.xml", first["requests"][0]), ("SAMPLES_BRIEF.txt", second)]:
        path = OUT / "sealed_source" / filename
        check(path.stat().st_size == receipt["bytes"])
        check(hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"])
    metadata = load(OUT / "SAMPLES_BRIEF_METADATA.json")
    scout = load(BASE / "advocate_sources/GEO_SUMMARY.json")["result"]["200030516"]
    check(len(metadata["samples"]) == len(scout["samples"]) == 25)
    check({s["accession"] for s in metadata["samples"]} == {s["accession"] for s in scout["samples"]})
    check(not metadata["measurement_values_exported"] and not metadata["body_truncated_at_additional_cap"])
    check(not metadata["stopped_before_sample_table_begin"])
    for sample in metadata["samples"]:
        check(set(sample) == {"accession", "metadata"})
        check(all(set(item) == {"field", "text"} and item["field"] in ALLOWED for item in sample["metadata"]))
        fields = {}
        for item in sample["metadata"]:
            fields.setdefault(item["field"], []).append(item["text"])
        check(fields["Sample_geo_accession"] == [sample["accession"]])
        check(fields["Sample_organism_ch1"] == ["Homo sapiens"])
        check(fields["Sample_platform_id"] == ["GPL570"])
        check(fields["Sample_series_id"] == ["GSE30516"])
        check(fields["Sample_treatment_protocol_ch1"] == ["Erlotinib was added to a final concentration of 10µM"])
        check(len(fields["Sample_supplementary_file"]) == 1 and fields["Sample_supplementary_file"][0].endswith(".CEL.gz"))
    census = load(OUT / "SAMPLE_IDENTITY_CENSUS.json")
    check(sum(c["array_samples"] for c in census["conditions"]) == 25)
    check(len(census["conditions"]) == 8)
    check(census["unique_accessions"] == 25)
    check(not census["missing_scout_accessions"] and not census["extra_accessions_vs_scout"])
    prefix = load(OUT / "PARTIAL_PREFIX_METADATA.json")
    check(prefix["stopped_before_first_Data_Table"] and prefix["metadata_prefix_bytes"] == 10492)
    check(prefix["entries"] == [])
    result = {"status": "PASS", "checks": checks,
              "original_frozen_files_unchanged": len(original),
              "explicit_amendment_worker_and_protocol_unchanged": True,
              "actual_new_HTTP_requests": 2,
              "initial_consumed_response_body_bytes": first["response_body_bytes"],
              "explicitly_amended_additional_response_body_bytes": second["bytes"],
              "total_consumed_response_body_bytes": first["response_body_bytes"] + second["bytes"],
              "verifier_decoded_source_response_tables": False,
              "scope": "Source/freeze hashes, exact 25 sample identity set, allowed metadata fields, treatment/platform/series/supplement keys; not biological or model validation",
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
