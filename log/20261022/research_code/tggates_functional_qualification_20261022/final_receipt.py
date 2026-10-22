"""Recheck actual original hashes; separately pin code/results added after safe export."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"


def main():
    target = OUT / "POST_PROJECTION_FREEZE.json"
    if target.exists():
        raise RuntimeError("Final receipt exists; no overwrite")
    frozen = json.loads((OUT / "PRE_OPEN_FREEZE.json").read_text(encoding="utf-8"))["sha256"]
    original = {}
    for name, expected in frozen.items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("Original frozen artifact changed")
        original[name] = actual
    paths = sorted((ROOT / "research/tggates_functional_qualification_20261022").glob("*.py"))
    paths += [OUT / name for name in ["PRE_OPEN_FREEZE.json", "HUMAN_FUNCTIONAL_FLAGS.json", "FUNCTIONAL_SCHEMA.json",
              "FUNCTIONAL_CENSUS.json", "JOINED_IDENTITY_FLAGS.json", "EARLY_LATE_MENU_COUNTS.json",
              "CONCENTRATION_IDENTITY_DIAGNOSTICS.json", "VERIFICATION.json", "REPORT.md", "STATUS.json", "EXECUTION_LOG.md",
              "WORKER_EXECUTION.txt", "CENSUS_EXECUTION.txt", "PAIRWISE_EXECUTION.txt", "IDENTITY_DIAGNOSTICS_EXECUTION.txt", "VERIFIER_EXECUTION.txt"]]
    later = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
             if p.relative_to(ROOT).as_posix() not in frozen}
    result = {"receipt_utc": datetime.now(timezone.utc).isoformat(),
              "original_pre_worker_frozen_files_reverified": len(original),
              "original_pre_worker_sha256_unchanged": original,
              "later_code_and_output_sha256": later,
              "later_files_were_frozen_before_official_worker": False,
              "receipt_is_filesystem_immutability_guarantee": False,
              "raw_response_rows_decoded_by_receipt": False}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "original_pre_worker_files_unchanged": len(original), "separately_recorded_later_files": len(later)}))


if __name__ == "__main__":
    main()
