"""Write FREEZE.json: the digests that must match before sealed predictions are made or outcomes opened.

File summary
- Path: research/knowledge_reality_20261013/freeze.py
- Purpose: record the protocol, code, census and development artifacts by sha256 (CRLF normalised to
  LF). `require_freeze` refuses to predict or evaluate after any change.
- Core points:
  - Write-once. A second run compares the stored digests with the current ones and reports MATCH
    or the first mismatch; it never rewrites the freeze.
  - DEVIATIONS.json, README.md and the claim files are not hashed, so a later disclosure cannot
    break the freeze it discloses against.
- Interfaces: `digests`, `require_freeze`, `main`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ["PROTOCOL.md", "DEV_PLAN.md", "sources.py", "census.py", "build.py", "models.py", "develop.py", "leakage.py",
         "sealed_census.py", "power.py", "confirm.py", "freeze.py", "CENSUS.json", "BUILD.json", "DEVELOPMENT.json",
         "LEAKAGE.json", "SEALED_CENSUS.json", "POWER.json", "compounds.csv", "sealed_compounds.csv", "sealed_overlap.csv"]
SHARED = ["src/maestro/information_tier.py", "tools/evaluation/scoring.py"]
NOT_HASHED = ["DEVIATIONS.json", "README.md", "verify.py", "claims.py", "CLAIMS.json", "RUNS.json", "SMOKE_DEVELOPMENT.json",
              "PREDICTION_LOCK.json", "RESULTS.json"]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def digests() -> dict:
    files = [str((HERE / f).relative_to(ROOT)).replace("\\", "/") for f in STUDY] + SHARED
    return {f: _digest(ROOT / f) for f in files}


def require_freeze() -> dict:
    path = HERE / "FREEZE.json"
    if not path.is_file():
        raise SystemExit("NOT_FROZEN: run freeze.py first")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    current = digests()
    bad = [f for f, d in freeze["sha256"].items() if current.get(f) != d]
    if bad:
        raise SystemExit(f"FREEZE_MISMATCH: {bad[0]}")
    return freeze


def main() -> None:
    path = HERE / "FREEZE.json"
    current = digests()
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))["sha256"]
        bad = [f for f in stored if stored[f] != current.get(f)]
        print("MATCH" if not bad else f"FREEZE_MISMATCH: {bad[0]}")
        return
    freeze = {"locked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "purpose": "stage-2 protocol, prediction code, eligibility and knowledge snapshots fixed before any PRISM 24Q2 "
                         "response value is downloaded",
              "not_hashed": NOT_HASHED, "sha256": current}
    path.write_bytes((json.dumps(freeze, indent=1) + "\n").encode())
    print("FROZEN", freeze["locked_utc"], len(current), "files")


if __name__ == "__main__":
    main()
