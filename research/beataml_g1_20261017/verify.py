"""Check the freeze, the records and the registered analysis of gate G1, and that predecessors are unchanged.

File summary
- Path: research/beataml_g1_20261017/verify.py
- Purpose: one command that says whether the reported G1 numbers follow from the frozen code and the
  per-sample records, and that the studies this one imports were not edited.
- Checks:
  - every FREEZE.json digest (LF-normalised), including the parity reference;
  - the records file is the one RESULTS.json names, and `g1_analyse.analyse()` on it reproduces RESULTS.json
    exactly (no Beat AML data are read);
  - the parity record says the low-rank arms and the S_ridge probabilities reproduce the attribution study;
  - ACCESS.json records no download and no sealed tier;
  - the frozen predecessors still match their own FREEZE.json (files under ``research/`` and ``src/`` only;
    data files are not rehashed here).
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

PREDECESSORS = ("context_transfer_20261017", "feedback_attribution_20261017")


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

    records = HERE / "records" / "records.json"
    results = HERE / "RESULTS.json"
    if records.exists() and results.exists():
        import g1_analyse
        stored = json.loads(results.read_text(encoding="utf-8"))
        obj = json.loads(records.read_text(encoding="utf-8"))
        ok = stored.get("records_sha256") == lf_bytes_digest(records)
        print("PASS" if ok else "FAIL", "records digest named by RESULTS.json")
        if not ok:
            fail.append("records digest")
        again = json.loads(json.dumps(g1_analyse.analyse(obj), allow_nan=False))
        again["records_sha256"] = stored.get("records_sha256")
        same = again == stored
        print("PASS" if same else "FAIL", "RESULTS.json recomputed from the per-sample records")
        if not same:
            fail.append("RESULTS.json")
        par = obj["meta"]["parity"]
        ok = bool(par["all_match"]) and all(par["S_ridge_probabilities_equal_strong_state"].values())
        print("PASS" if ok else "FAIL", "parity with the attribution study")
        if not ok:
            fail.append("parity")
        ok = obj["meta"]["freeze_sha256"] == lf_digest(HERE / "FREEZE.json")
        print("PASS" if ok else "FAIL", "records were produced under this FREEZE.json")
        if not ok:
            fail.append("records/freeze mismatch")
        ok = all(c["inner_patient_overlap"] == 0 for c in obj["meta"]["choices"].values())
        print("PASS" if ok else "FAIL", "inner folds patient-disjoint")
        if not ok:
            fail.append("inner folds")
    else:
        print("NOTE no run output yet")

    access = HERE / "ACCESS.json"
    if access.exists():
        rec = json.loads(access.read_text(encoding="utf-8"))
        ok = not rec.get("sealed_tiers_opened") and not rec.get("new_downloads")
        print("PASS" if ok else "FAIL", "no sealed tier opened, no download")
        if not ok:
            fail.append("ACCESS.json")

    for study in PREDECESSORS:
        rec = json.loads((ROOT / "research" / study / "FREEZE.json").read_text(encoding="utf-8"))
        table = rec.get("sha256_lf") or rec.get("sha256")
        bad, checked = [], 0
        for rel, digest in table.items():
            if not (rel.startswith("research/") or rel.startswith("src/")):
                continue
            checked += 1
            path = ROOT / rel
            if not path.exists() or lf_bytes_digest(path) != digest:
                bad.append(rel)
        print("PASS" if not bad else "FAIL", "predecessor unchanged", study, checked, "files")
        if bad:
            fail.append(f"{study}: {bad[:5]}")

    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
