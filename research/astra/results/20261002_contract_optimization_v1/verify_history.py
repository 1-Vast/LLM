"""Verify the pre-change history receipt without rewriting archived files."""
from pathlib import Path
import hashlib
import json


def verify():
    root = Path(__file__).resolve().parents[4]
    receipt = json.loads(Path(__file__).with_name("historical_hashes.json").read_text(encoding="utf-8"))
    mismatches = [name for name, expected in receipt["files"].items()
                  if not (root / name).is_file()
                  or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
    result = {"historical_files": len(receipt["files"]), "mismatches": mismatches,
              "all_match": not mismatches, "base_commit": receipt["base_commit"]}
    print(json.dumps(result, indent=2))
    return not mismatches


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
