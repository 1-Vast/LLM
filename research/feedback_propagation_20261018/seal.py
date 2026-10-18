"""Write FREEZE.json once and check it; write the exposure record ACCESS.json once.

File summary
- Path: research/feedback_propagation_20261018/seal.py
- Purpose: fix the registered design (PROTOCOL.md), the development-selected programs (DEVELOPMENT.json), the
  derived threshold (THRESHOLDS.json) and the code of the comparison before any estimation-fold outcome is scored
  for the new arms. Digests are of LF-normalised bytes, so a CRLF checkout of a frozen file does not look like an edit.
- Not hashed: DEVIATIONS.json (a freeze must not hash its own deviations log), seal.py and verify.py (integrity
  tooling), the audit script and AUDIT.json, and run outputs (records/, RESULTS.json, REPORT.md).
- Interfaces: ``python seal.py freeze`` (refuses FREEZE_EXISTS); `check()` raises SystemExit (FREEZE_MISSING /
  FREEZE_MISMATCH: <file>); `record_access()` writes ACCESS.json once.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["PROTOCOL.md", "bench.py", "rules.py", "repair.py", "loop.py", "metrics.py", "develop.py", "DEVELOPMENT.json", "thresholds.py",
         "THRESHOLDS.json", "compare.py", "analyse.py", "test_science.py"]


def lf_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write(path: Path, data: dict) -> None:
    path.write_bytes((json.dumps(data, indent=1) + "\n").encode("utf-8"))


def freeze() -> None:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE_EXISTS: the design is already frozen")
    _write(HERE / "FREEZE.json", {
        "study": "feedback_propagation_20261018",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "task, hypotheses, programs (R1 and comparators), selection by Phase D, practical threshold, uncertainty analysis, "
                 "decision rule and stop rule of PROTOCOL.md; frozen before the estimation-fold comparison. Folds 2-4 are exposed data.",
        "sha256_lf": {f: lf_digest(HERE / f) for f in FILES}})
    print("frozen", len(FILES), "files")


def check() -> None:
    path = HERE / "FREEZE.json"
    if not path.exists():
        raise SystemExit("FREEZE_MISSING: run `python seal.py freeze` after PROTOCOL.md is final")
    rec = json.loads(path.read_text(encoding="utf-8"))
    for f, digest in rec["sha256_lf"].items():
        if not (HERE / f).exists() or lf_digest(HERE / f) != digest:
            raise SystemExit(f"FREEZE_MISMATCH: {f}")


def record_access() -> None:
    """First scoring of the new arms on the estimation folds (write-once)."""

    path = HERE / "ACCESS.json"
    if path.exists():
        return
    _write(path, {"opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "freeze_sha256": lf_digest(HERE / "FREEZE.json"),
                  "tier": "PRISM 19Q4 primary screen, estimation folds 2, 3, 4",
                  "prior_exposure": "opened by indication_triage_20261016 (estimation) and, in aggregate (event counts, reproduced old-loop "
                                    "totals), by this study's audit_task.py; no outcome of a new arm had been scored on these folds",
                  "sealed_tiers_opened": []})


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        freeze()
    else:
        check()
        print("FREEZE OK")
