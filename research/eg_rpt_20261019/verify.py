"""Verify the EG-RPT scaffolding: experience records, noise-headroom file, tests, registry, untouched history. Prints VERIFIED or exits non-zero."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    fail = []
    sys.path.insert(0, str(HERE))
    import audit_experiences

    before = {f: (HERE / f).read_bytes() for f in ("EXPERIENCES_CHECK.json", "NOISE_HEADROOM.json")}
    out = audit_experiences.main()
    c = out["check"]
    if not (c["all_valid"] and c["all_patterns_found"] and all(c["recomputed_match"].values())):
        fail.append("experience records invalid or not matching evidence/results")
    for f, b in before.items():
        if (HERE / f).read_bytes() != b:
            fail.append(f"{f} does not recompute")
    if out["noise"]["campaigns"] != 36:
        fail.append("noise headroom campaigns != 36")
    reg = json.loads((ROOT / "research/STUDIES.json").read_text(encoding="utf-8"))["studies"]
    if not any(s["path"] == "eg_rpt_20261019" and s["status"] != "frozen" for s in reg):
        fail.append("study not registered as non-frozen")
    st = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout.splitlines()
    allowed = ("research/eg_rpt_20261019", "research/STUDIES.json", "log/DIRECTIONS.md", "research/EVIDENCE.md")
    stray = [l for l in st if not any(a in l.replace("\\", "/") for a in allowed)]
    if stray:
        fail.append(f"unexpected modified paths: {stray}")
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(HERE / "test_eg_rpt.py")], capture_output=True, text=True)
    if r.returncode:
        fail.append("tests failed: " + r.stdout[-300:])
    print("VERIFIED" if not fail else "FAILED: " + "; ".join(fail))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
