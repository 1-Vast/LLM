"""Audit authenticated sample conditions from the brief whitelist only."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/intervention_schedule_qualification"
OUT = BASE / "auditor_sources"


def main():
    target = OUT / "SAMPLE_IDENTITY_CENSUS.json"
    if target.exists():
        raise RuntimeError("Identity census exists")
    payload = json.loads((OUT / "SAMPLES_BRIEF_METADATA.json").read_text(encoding="utf-8"))
    scout = json.loads((BASE / "advocate_sources/GEO_SUMMARY.json").read_text(encoding="utf-8"))["result"]["200030516"]
    identities, values, conditions, supplements = [], defaultdict(Counter), Counter(), []
    for sample in payload["samples"]:
        fields = defaultdict(list)
        for item in sample["metadata"]:
            fields[item["field"]].append(item["text"])
            values[item["field"]][item["text"]] += 1
        characteristic = {}
        for text in fields["Sample_characteristics_ch1"]:
            if ": " in text:
                k, v = text.split(": ", 1)
                characteristic[k] = v
        conditions[(characteristic.get("cell line"), characteristic.get("time post treatment"), characteristic.get("treatment"))] += 1
        identities.append({"accession": sample["accession"], "title": fields["Sample_title"],
                           "source": fields["Sample_source_name_ch1"], "characteristics": characteristic,
                           "treatment_protocol": fields["Sample_treatment_protocol_ch1"],
                           "growth_protocol": fields["Sample_growth_protocol_ch1"],
                           "platform": fields["Sample_platform_id"], "series": fields["Sample_series_id"]})
        supplements.extend(fields["Sample_supplementary_file"])
    actual = [r["accession"] for r in identities]
    expected = {r["accession"] for r in scout["samples"]}
    result = {"sample_entries": len(identities), "unique_accessions": len(set(actual)),
              "missing_scout_accessions": sorted(expected - set(actual)),
              "extra_accessions_vs_scout": sorted(set(actual) - expected),
              "body_truncated": payload["body_truncated_at_additional_cap"],
              "table_marker_encountered": payload["stopped_before_sample_table_begin"],
              "conditions": [{"cell_line": k[0], "time_post_treatment": k[1], "treatment": k[2], "array_samples": v} for k, v in conditions.items()],
              "distinct_metadata_values": {k: dict(v) for k, v in values.items() if k in
                  {"Sample_organism_ch1", "Sample_treatment_protocol_ch1", "Sample_growth_protocol_ch1", "Sample_platform_id",
                   "Sample_series_id", "Sample_label_protocol_ch1", "Sample_hyb_protocol", "Sample_data_processing"}},
              "sample_supplementary_files": supplements, "identities": identities,
              "metadata_projection_sha256": hashlib.sha256((OUT / "SAMPLES_BRIEF_METADATA.json").read_bytes()).hexdigest(),
              "measurement_values_used": False}
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"sample_supplementary_files", "identities"}}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
