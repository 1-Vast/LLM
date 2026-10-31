"""Isolate an administrative-review pin drift for saved B arithmetic only.

Preserves original pins, outputs, and first verifier failure. Never opens raw
profile files, imports model code, or fits. This does not repair the original
freeze chain or create a new preexecution scientific freeze.
"""

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    review = Path(__file__).resolve().parent
    repo = review.parents[4]
    data = repo / "data/processed/functional_anchor_binding_20261030/b"
    destination = review / "b_review_metadata_adapter"
    run = json.loads((data / "run.json").read_text(encoding="utf-8"))
    access = json.loads((data / "access_receipt.json").read_text(encoding="utf-8"))
    first = json.loads((review / "b_arithmetic_verification.json").read_text(encoding="utf-8"))
    pins = run["freeze"]["sha256"]
    review_path = review / "b_code_access_review.md"
    original_review_pin = pins[str(review_path)]
    verifier = review / "verify_b_independent.py"
    assert sha256(verifier) == "82fd45c61ceae21162c3f65227dd1a4b3e8f1e490198eeb5159a18cea0aceec1"
    raw_paths = {Path(item["path"]).resolve() for item in access["per_plate"].values()}
    assert len(raw_paths) == 8 and access["all_hashes_checked"] is True
    changed = []
    manifest_path = None
    for filename, expected in pins.items():
        path = Path(filename).resolve()
        if path in raw_paths:
            continue
        actual = sha256(path)
        if expected != actual:
            changed.append({"path": str(path), "expected": expected, "actual": actual})
        if path.name == "source_manifest.tsv":
            manifest_path = path
    assert len(changed) == 1 and Path(changed[0]["path"]) == review_path.resolve(), changed
    assert manifest_path is not None
    with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
        source_manifest = list(csv.DictReader(handle, delimiter="\t"))
    raw_declarations = {}
    for path in sorted(raw_paths):
        records = [row for row in source_manifest if row.get("original_file")
                   and Path(row["original_file"]).resolve() == path]
        assert records and all(row["sha256"] == pins[str(path)] for row in records)
        raw_declarations[str(path)] = {"run_pin": pins[str(path)], "matches_unchanged_source_manifest": True,
                                       "loader_all_hashes_checked": True, "file_opened_by_adapter": False}
    for filename, expected in first["output_sha256"].items():
        assert sha256(filename) == expected, f"original output changed: {filename}"
    destination.mkdir(exist_ok=False)
    output_hashes = {}
    for path in sorted(data.iterdir()):
        if path.is_file() and path.suffix in {".npz", ".json"} and path.name != "run.json":
            # Immutable byte-identical view: linked artifacts are never modified.
            os.link(path, destination / path.name)
            output_hashes[path.name] = sha256(path)
    snapshot = destination / "b_code_access_review.snapshot.md"
    shutil.copy2(review_path, snapshot)
    assert sha256(snapshot) == changed[0]["actual"]
    del run["freeze"]["sha256"][str(review_path)]
    run["freeze"]["sha256"][str(snapshot)] = sha256(snapshot)
    (destination / "run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "status": "ADMINISTRATIVE_REVIEW_PIN_DRIFT_ISOLATED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_freeze_integrity": "FAIL: pinned review document changed; not retroactively repaired",
        "changed_pin": changed[0], "original_review_pin": original_review_pin,
        "all_other_nonraw_scientific_code_protocol_checker_input_pins_match": True,
        "raw_declarations": raw_declarations,
        "raw_hash_limit": "Declaration consistency and loader receipt only; no independent raw-file byte hash here.",
        "first_verifier_report_sha256": sha256(review / "b_arithmetic_verification.json"),
        "verifier_sha256": sha256(verifier), "adapter_script_sha256": sha256(__file__),
        "original_run_sha256": sha256(data / "run.json"),
        "derived_run_sha256": sha256(destination / "run.json"),
        "snapshot_sha256": sha256(snapshot), "output_hashes_unchanged": output_hashes,
        "derived_data_dir": str(destination),
        "metadata_change": "Replace only administrative review pin with snapshot identity in derived metadata.",
        "interpretation": "Enables separate numerical audit with declared provenance exception, not PASS of original freeze.",
        "original_outputs_modified": False, "verifier_modified": False, "refits": 0,
        "raw_source_files_opened": 0, "http_attempts": 0,
    }
    (review / "b_review_pin_adapter_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
