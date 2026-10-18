"""Check the freeze, the records and the registered analysis of the attribution study.

File summary
- Path: research/seed_attribution_20261017/verify.py
- Purpose: one command that says whether the reported numbers follow from the frozen code and the per-line
  records, and that no frozen predecessor study was edited.
- Checks:
  - every FREEZE.json digest (LF-normalised) and the null collection;
  - the records file is the one RESULTS.json names, and `analyse.analyse()` on it reproduces RESULTS.json
    exactly (so no PRISM data are read here);
  - the contract parity record says the frozen implementation was reproduced;
  - the audit and cost outputs exist and ACCESS.json records no sealed tier;
  - the frozen predecessor studies still match their own FREEZE.json digests (file by file, LF-normalised).
- Interfaces: ``python -B verify.py``; prints VERIFIED or exits non-zero with the failures.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from seal import FILES, lf_digest  # noqa: E402

PREDECESSORS = ("program_revision_20261017", "feedback_attribution_20261017")


def lf_bytes_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    fail = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for f, digest in freeze["sha256_lf"].items():
        ok = (HERE / f).exists() and lf_digest(HERE / f) == digest
        print("PASS" if ok else "FAIL", "freeze", f)
        if not ok:
            fail.append(f)
    if set(freeze["sha256_lf"]) != set(FILES):
        fail.append("FREEZE file list differs from seal.FILES")

    records = HERE / "records" / "units.json"
    results_path = HERE / "RESULTS.json"
    if records.exists() and results_path.exists():
        import analyse
        stored = json.loads(results_path.read_text(encoding="utf-8"))
        units = json.loads(records.read_text(encoding="utf-8"))
        ok = stored.get("units_sha256") == lf_bytes_digest(records)
        print("PASS" if ok else "FAIL", "records digest named by RESULTS.json")
        if not ok:
            fail.append("records digest")
        again = json.loads(json.dumps(analyse.analyse(units), allow_nan=False))
        again["units_sha256"] = stored.get("units_sha256")
        same = again == stored
        print("PASS" if same else "FAIL", "RESULTS.json recomputed from the per-line records")
        if not same:
            fail.append("RESULTS.json")
        if not stored["meta"]["parity_with_frozen_implementation"].get("all_match"):
            fail.append("contract parity with the frozen implementation")
    else:
        print("NOTE no run output yet (records/units.json or RESULTS.json missing)")

    for name in ("AUDIT_CONTRACT.json", "AUDIT_ACCESS.json", "COST_UNITS.json", "NULLS.json", "DEVIATIONS.json"):
        ok = (HERE / name).exists()
        print("PASS" if ok else "FAIL", "present", name)
        if not ok:
            fail.append(name)
    access = HERE / "ACCESS.json"
    if access.exists():
        rec = json.loads(access.read_text(encoding="utf-8"))
        if rec.get("sealed_tiers_opened"):
            fail.append("ACCESS.json lists a sealed tier")
        print("PASS" if not rec.get("sealed_tiers_opened") else "FAIL", "no sealed tier opened")

    for study in PREDECESSORS:
        base = ROOT / "research" / study
        rec = json.loads((base / "FREEZE.json").read_text(encoding="utf-8"))
        bad = []
        for rel, digest in rec["sha256_lf"].items():
            path = ROOT / rel
            if not path.exists() or lf_bytes_digest(path) != digest:
                bad.append(rel)
        print("PASS" if not bad else "FAIL", "predecessor unchanged", study, len(rec["sha256_lf"]), "files")
        if bad:
            fail.append(f"{study}: {bad[:5]}")

    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
