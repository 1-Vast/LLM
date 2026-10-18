"""Check the freeze, the records and the registered analysis of the feedback-propagation study.

File summary
- Path: research/feedback_propagation_20261018/verify.py
- Purpose: one command that says whether the reported numbers follow from the frozen code and the per-compound
  records, and that no frozen predecessor study was edited.
- Checks:
  - every FREEZE.json digest (LF-normalised) and that the file list equals `seal.FILES`;
  - `analyse.analyse()` on records/E_fold{2,3,4}.json reproduces RESULTS.json exactly (no PRISM data are read);
  - the development selection recorded in DEVELOPMENT.json equals the programs hard-wired in compare.py;
  - THRESHOLDS.json was derived from DEVELOPMENT.json (delta* recomputable from the stored budget curve);
  - the seed_attribution erratum files exist and its frozen files still match their digests;
  - ACCESS.json records no sealed tier; the frozen predecessor studies still match their own FREEZE.json digests.
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

PREDECESSORS = ("seed_attribution_20261017", "indication_triage_20261016", "feedback_attribution_20261017", "program_revision_20261017")


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

    dev = json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    sel = dev["selection"]
    import compare
    wired = (compare.REGISTERED_R1 == {"K": sel["K"], "lam": sel["lam"]} and compare.C_STAR == {"K": int(sel["C_star"].replace("knn", ""))}
             and compare.REGISTERED_GATE == {"K": sel["K"], "lam": sel["lam"], "loss": sel["gated"].split("_")[-1], "gate": "lopo"})
    print("PASS" if wired else "FAIL", "compare.py hard-wires the Phase D selection")
    if not wired:
        fail.append("selection not wired")

    thr = json.loads((HERE / "THRESHOLDS.json").read_text(encoding="utf-8"))
    ridge = [thr["cost_equivalence"]["hits_per_64_compounds"][str(b)]["ridge"] for b in (1, 2, 3, 4)]
    delta = max(sum(ridge[i + 1] - ridge[i] for i in range(3 - 1)) / 2, 0.10 * thr["relative_floor"]["ridge_hits_per_64_compounds_at_primary_budget"])
    ok = abs(delta - thr["delta_star_hits_per_64_compounds"]) < 1e-12
    print("PASS" if ok else "FAIL", "delta* recomputed from the stored budget curve and relative floor")
    if not ok:
        fail.append("delta*")

    results_path = HERE / "RESULTS.json"
    if results_path.exists():
        import analyse
        stored = json.loads(results_path.read_text(encoding="utf-8"))
        again = analyse.analyse(analyse.load())
        same = again == stored
        print("PASS" if same else "FAIL", "RESULTS.json recomputed from records/E_fold*.json")
        if not same:
            fail.append("RESULTS.json")
        access = json.loads((HERE / "ACCESS.json").read_text(encoding="utf-8"))
        ok = not access.get("sealed_tiers_opened")
        print("PASS" if ok else "FAIL", "no sealed tier opened")
        if not ok:
            fail.append("ACCESS.json lists a sealed tier")
    else:
        print("NOTE no run output yet (RESULTS.json missing)")

    erratum = ROOT / "research" / "seed_attribution_20261017"
    for name in ("ERRATUM_20261018.md", "ERRATUM_equal_lineage_bootstrap.json", "erratum_equal_lineage_bootstrap.py"):
        ok = (erratum / name).exists()
        print("PASS" if ok else "FAIL", "erratum present", name)
        if not ok:
            fail.append(name)
    for name in ("DEVIATIONS.json",):
        ok = (HERE / name).exists()
        print("PASS" if ok else "FAIL", "present", name)
        if not ok:
            fail.append(name)

    for study in PREDECESSORS:
        freeze_path = ROOT / "research" / study / "FREEZE.json"
        if not freeze_path.exists():
            print("NOTE no FREEZE.json in", study)
            continue
        rec = json.loads(freeze_path.read_text(encoding="utf-8"))
        bad = []
        files = rec.get("sha256_lf") or rec.get("sha256") or {}
        for rel, digest in files.items():
            path = ROOT / rel if "/" in rel else ROOT / "research" / study / rel
            if not path.exists() or lf_bytes_digest(path) != digest:
                bad.append(rel)
        print("PASS" if not bad else "FAIL", "predecessor unchanged", study, len(files), "files")
        if bad:
            fail.append(f"{study}: {bad[:5]}")

    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
