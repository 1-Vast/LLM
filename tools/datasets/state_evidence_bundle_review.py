"""Verify supplied evidence package against independently downloaded originals."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def review(bundle, independent, receipts, out):
    with zipfile.ZipFile(bundle) as archive:
        if len(set(archive.namelist())) != len(archive.namelist()):
            raise ValueError("duplicate package member")
        manifest = json.loads(archive.read("SHA256SUMS.json"))
        for name, expected in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError("package member checksum mismatch")
        claimed = json.loads(archive.read("audit_results.json"))
        actual = json.loads((independent / "summary.json").read_text())
        pinned = {r["id"]: r for r in json.loads(receipts.read_text())}
        for item in claimed["datasets"]:
            name = item["file"].removesuffix(".mat")
            if item["sha256"] != pinned[name]["sha256"]:
                raise ValueError("package/original source hash mismatch")
            found = next(r for r in actual["experiments"] if r["file"] == name + ".raw")
            keys = {"replayable": "replayed_frames", "matches": "action_matches",
                    "same_row_mismatches": "wrong_same_row_reference_mismatches",
                    "label_references": "phase_label_mentions_all_postcalibration",
                    "missing_current_frame_fluorescence": "label_mentions_without_finite_same_label_next_observation"}
            for actual_key, claim_key in keys.items():
                if found[actual_key] != item["counts"][claim_key]:
                    raise ValueError("independent reconstruction disagrees")
        supplied_rows = [json.loads(line) for line in archive.read("decision_log_reconstruction.jsonl").decode().splitlines()]
        if len(supplied_rows) != 2000:
            raise ValueError("unexpected package decision count")
        result = {"package_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
                  "package_bytes": bundle.stat().st_size, "members_hashed": len(manifest),
                  "source_hashes_match": True, "independent_summary_matches": True,
                  "supplied_decision_rows": len(supplied_rows),
                  "supplied_test_receipt": json.loads(archive.read("verification.json")),
                  "supplied_script_executed": False, "supplied_tests_rerun": False,
                  "scope": "Byte integrity and original-source/reconstruction cross-check; not validation of efficacy."}
    out.mkdir(parents=True, exist_ok=False)
    (out / "bundle_review.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "reviewer_source.py.txt").write_bytes(Path(__file__).read_bytes())
    (out / ".gitattributes").write_text("* binary\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "independent", "receipts", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.bundle, args.independent, args.receipts, args.out), indent=2))
