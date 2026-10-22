"""Further identifier-only coverage summaries. Does not open sealed Parquet files."""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261021/oasis_source_qualification"


def summarize(rows):
    by_compound = collections.defaultdict(list)
    by_action = collections.defaultdict(list)
    for row in rows:
        by_compound[row["compound_id"]].append(row)
        by_action[(row["compound_id"], row["dose_um"])].append(row)
    return {
        "rows": len(rows), "compound_labels": len(by_compound),
        "actions": len(by_action),
        "dose_counts_per_compound": dict(collections.Counter(len({x["dose_um"] for x in v}) for v in by_compound.values())),
        "observations_per_action": dict(collections.Counter(len(v) for v in by_action.values())),
        "distinct_plates_per_action": dict(collections.Counter(len({x["plate"] for x in v}) for v in by_action.values())),
        "duplicate_source_plate_well": len(rows) - len({(x["source"], x["plate"], x["well"]) for x in rows}),
        "raw_functionally_complete_rows": sum(all(x["functional_present"].get(k, False)
                                                   for k in ("mtt_lumi", "ldh_abs_signal", "ldh_abs_background", "ldh_abs")) for x in rows),
    }


def main():
    rows = json.loads((LOG / "BLIND_IDENTIFIERS.json").read_text())
    manifest = json.loads((LOG / "SOURCE_MANIFEST.json").read_text())
    profiles = json.loads((LOG / "PROFILE_SOURCE_CATALOGUE.json").read_text())
    raw_profiles = {}
    for item in profiles["objects"]:
        parts = item["Key"].split("/")
        if len(parts) > 2 and parts[-1] == parts[-2] + ".csv.gz":
            raw_profiles[(parts[-3], parts[-2])] = item
    biochemical = {(x["Key"].split("/")[-3], x["Key"].split("/")[-2]) for x in manifest}
    sha_groups = collections.defaultdict(list)
    for item in manifest:
        sha_groups[item["sha256"]].append(item["local_path"])
    result = {
        "all_non_dmso": summarize([x for x in rows if not x["is_dmso_control"]]),
        "library_oasis_non_dmso": summarize([x for x in rows if not x["is_dmso_control"] and x["library"] == "oasis"]),
        "compound_plate_non_dmso": summarize([x for x in rows if not x["is_dmso_control"] and x["plate_type"] == "compound"]),
        "reference_plate_non_dmso": summarize([x for x in rows if not x["is_dmso_control"] and x["plate_type"] == "reference"]),
        "source_counts": dict(collections.Counter(str(x["source"]) for x in rows)),
        "byte_identical_file_groups": [x for x in sha_groups.values() if len(x) > 1],
        "profile_catalogue_truncated": profiles["truncated"],
        "biochemical_batch_plate_count": len(biochemical),
        "raw_profile_batch_plate_count": len(raw_profiles),
        "paired_batch_plate_count": len(biochemical & set(raw_profiles)),
        "biochemical_without_raw_profile": sorted(biochemical - set(raw_profiles)),
        "pairable_raw_profile_objects": [raw_profiles[x] for x in sorted(biochemical & set(raw_profiles))],
        "exact_profile_well_keys_verified": False,
        "boundary": "Plate catalogue linkage only; profile feature bodies and within-file well keys were not read",
    }
    (LOG / "COVERAGE_FINAL.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "pairable_raw_profile_objects"}))


if __name__ == "__main__":
    main()
