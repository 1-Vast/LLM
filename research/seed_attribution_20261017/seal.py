"""Write FREEZE.json once and check it; write the exposure record ACCESS.json once.

File summary
- Path: research/seed_attribution_20261017/seal.py
- Purpose: fix the registered design (PROTOCOL.md), the matched null collection and the code of the
  attribution run before the run. Digests are of LF-normalised bytes, so they do not depend on the
  checkout's line endings (a CRLF checkout of a frozen file must not look like an edit).
- Not hashed: DEVIATIONS.json (a freeze must not hash its own deviations log), seal.py and verify.py
  (integrity tooling), the audit and cost scripts with their JSON outputs, and run outputs.
- Interfaces: ``python seal.py freeze`` (refuses FREEZE_EXISTS); `check()` raises SystemExit
  (FREEZE_MISSING / FREEZE_MISMATCH: <file>); `record_access()` writes ACCESS.json once.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["PROTOCOL.md", "contract.py", "corrected.py", "replay.py", "nulls.py", "NULLS.json", "run.py", "analyse.py",
         "test_science.py"]


def lf_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write(path: Path, data: dict) -> None:
    path.write_bytes((json.dumps(data, indent=1) + "\n").encode("utf-8"))


def freeze() -> None:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE_EXISTS: the design is already frozen")
    _write(HERE / "FREEZE.json", {
        "study": "seed_attribution_20261017",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "contract, corrected predictor, replay contract, null collection, arms, layers, analysis and reading rules of "
                 "PROTOCOL.md; frozen before the attribution run. The target strata are exposed data (program_revision_20261017).",
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
    """First read of the exposed target strata by this study (write-once)."""

    path = HERE / "ACCESS.json"
    if path.exists():
        return
    _write(path, {"opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "freeze_sha256": lf_digest(HERE / "FREEZE.json"), "nulls_sha256": lf_digest(HERE / "NULLS.json"),
                  "tier": "PRISM 19Q4 future_line and future_lineage strata",
                  "prior_exposure": "opened and analysed by program_revision_20261017 (its ACCESS.json); exposed, not confirmation",
                  "sealed_tiers_opened": []})


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        freeze()
    else:
        check()
        print("FREEZE OK")
