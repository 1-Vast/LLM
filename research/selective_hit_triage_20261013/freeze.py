"""Write FREEZE.json: the digests that must match before any test outcome opens (DEVIATIONS.json is never hashed).

File summary
- Path: research/selective_hit_triage_20261013/freeze.py
- Purpose: record the protocol, code and design artifacts by sha256 (CRLF normalised to LF), so
  `outcomes.require_freeze` refuses test outcomes after any change.
- Core points: write-once. A second run compares the current digests with the stored ones and
  reports MATCH or the first mismatch; it never rewrites the freeze.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from census import HERE, ROOT

STUDY = ["PROTOCOL.md", "census.py", "split.py", "features.py", "outcomes.py", "arms.py", "dev.py", "dev_explore.py",
         "dev_explore2.py", "dev_explore3.py", "dev_review.py", "review.py", "leakage.py", "test_choose.py", "evaluate.py",
         "agent_arms.py", "agent_review.py", "freeze.py", "CENSUS.json", "SPLIT.json", "census_pairs.npz", "features.npz",
         "compounds.json", "DESIGN_LOCK.json", "DEVELOPMENT.json", "DEV_EXPLORE.json", "DEV_EXPLORE2.json", "DEV_EXPLORE3.json",
         "DEV_REVIEW.json", "LEAKAGE.json"]
SHARED = ["src/maestro/decision_review.py", "tools/evaluation/scoring.py"]


def digests() -> dict:
    files = [str((HERE / f).relative_to(ROOT)).replace("\\", "/") for f in STUDY] + SHARED
    return {f: hashlib.sha256((ROOT / f).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for f in files}


def main() -> None:
    path = HERE / "FREEZE.json"
    current = digests()
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))["sha256"]
        bad = [f for f in stored if stored[f] != current.get(f)]
        print("MATCH" if not bad else f"FREEZE_MISMATCH: {bad[0]}")
        return
    freeze = {"locked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "purpose": "protocol, code and design artifacts fixed before any test (CTRP v2) outcome is opened; families P and R",
              "not_hashed": ["DEVIATIONS.json", "README.md", "verify.py", "TEST_CHOICES.json", "CHOICES_LOCK.json", "TEST_RESULTS.json"],
              "sha256": current}
    path.write_bytes((json.dumps(freeze, indent=1) + "\n").encode())
    print("FROZEN", freeze["locked_utc"], len(current), "files")


if __name__ == "__main__":
    main()
