"""Write FREEZE.json once and check it; write the exposure record ACCESS.json once.

File summary
- Path: research/beataml_g1_20261017/seal.py
- Purpose: fix the registered design (PROTOCOL.md), the arms, the run and analysis code, the tests and the
  parity reference before the G1 run. Digests are of LF-normalised bytes.
- Not hashed: DEVIATIONS.json (a freeze must not hash its own deviations log), seal.py and verify.py
  (integrity tooling), and run outputs.
- Interfaces: ``python seal.py freeze``; ``check()`` raises SystemExit (FREEZE_MISSING / FREEZE_MISMATCH);
  ``record_access()`` writes ACCESS.json once; ``python seal.py`` checks.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["PROTOCOL.md", "g1_arms.py", "g1_run.py", "g1_analyse.py", "test_science.py", "records/parity_reference.json"]


def lf_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write(path: Path, data: dict) -> None:
    path.write_bytes((json.dumps(data, indent=1) + "\n").encode("utf-8"))


def freeze() -> None:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE_EXISTS: the design is already frozen")
    _write(HERE / "FREEZE.json", {
        "study": "beataml_g1_20261017",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "gate G1 of feedback_attribution_20261017: candidate, ridge-plus-feedback arm, inner choice of k, "
                 "analysis and gate rule of PROTOCOL.md. Beat AML 2.0 is exposed (development evidence).",
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
    path = HERE / "ACCESS.json"
    if path.exists():
        return
    _write(path, {"opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "freeze_sha256": lf_digest(HERE / "FREEZE.json"),
                  "data": "Beat AML 2.0 (520 samples, 479 patients, 165 inhibitors), already local and already exposed",
                  "prior_exposure": "opened by context_transfer_20261017 and analysed by feedback_attribution_20261017; "
                                    "development evidence, not confirmation",
                  "new_downloads": [], "sealed_tiers_opened": []})


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        freeze()
    else:
        check()
        print("FREEZE OK")
