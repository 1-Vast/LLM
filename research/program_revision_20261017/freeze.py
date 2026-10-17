"""Write FREEZE.json once and check it: digests of the protocol and every file the arms execute.

File summary
- Path: research/program_revision_20261017/freeze.py
- Purpose: fix the registered design (PROTOCOL.md), the split and the code of every arm before the
  development arms run and before any future-project outcome is opened. Digests are of
  LF-normalised bytes (`sha256_lf`), so they do not depend on the checkout's line endings.
- Not hashed: DEVIATIONS.json (a freeze must not hash its own deviations log), freeze.py and
  verify.py (integrity tooling), STAGE_A.json (written before the freeze, hashed separately in
  ``stage_a_sha256``), outputs.
- Interfaces: ``python -B freeze.py`` (refuses FREEZE_EXISTS); `check_freeze()` raises
  SystemExit(FREEZE_MISSING / FREEZE_MISMATCH: <file>).
"""
from __future__ import annotations

import json
import time

from common import HERE, ROOT, lf_digest, sha256, write_json

STUDY = "research/program_revision_20261017"
FILES = [f"{STUDY}/{n}" for n in ("PROTOCOL.md", "SPLITS.json", "drugs.csv", "lines.csv", "build_splits.py",
                                  "common.py", "features.py", "vc.py", "engine.py", "revise.py", "llm_proposer.py",
                                  "policy.py", "develop.py", "evaluate.py", "stage_a.py", "test_science.py")]
FILES.append("src/agent/llm.py")


def main() -> None:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE_EXISTS: the design is already frozen")
    write_json(HERE / "FREEZE.json", {
        "study": "program_revision_20261017",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "registered arms, acceptance rule, budgets, endpoints and analysis of PROTOCOL.md; frozen after "
                 "Stage A (source development data only) and before the development arms and any future outcome",
        "sha256_lf": {f: lf_digest(ROOT / f) for f in FILES},
        "stage_a_sha256": sha256(HERE / "STAGE_A.json"),
    })
    print("frozen", len(FILES), "files")


def check_freeze() -> None:
    path = HERE / "FREEZE.json"
    if not path.exists():
        raise SystemExit("FREEZE_MISSING: run freeze.py after PROTOCOL.md is final")
    rec = json.loads(path.read_text(encoding="utf-8"))
    for f, digest in rec["sha256_lf"].items():
        if not (ROOT / f).exists() or lf_digest(ROOT / f) != digest:
            raise SystemExit(f"FREEZE_MISMATCH: {f}")


if __name__ == "__main__":
    main()
