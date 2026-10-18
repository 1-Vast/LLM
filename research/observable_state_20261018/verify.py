"""Verify the scaffolding of the observable-state study: prior numbers, power file, qualification file, tests, untouched history.

Prints VERIFIED or exits non-zero. Local, cheap: no outcome tables, no network, no LLM.
"""
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
    import audit_priors

    before = {f: (HERE / f).read_bytes() for f in ("PRIOR_CHECK.json", "POWER.json")}
    out = audit_priors.main()
    if not all(c["match"] for c in out["checks"]):
        fail.append("prior numbers do not match records")
    for f, b in before.items():
        if (HERE / f).read_bytes() != b:
            fail.append(f"{f} does not recompute")
    import stage0_families

    b0 = (HERE / "STAGE0.json").read_bytes()
    s0 = stage0_families.main()
    if (HERE / "STAGE0.json").read_bytes() != b0:
        fail.append("STAGE0.json does not recompute")
    if "no outcome" not in s0["scope"] or s0["families_eligible"] < 80:
        fail.append("stage0 scope/eligibility unexpected")
    import obs_seal

    for st in (0, 1):
        try:
            obs_seal.check(st)
        except SystemExit as e:
            fail.append(f"freeze {st}: {e}")
    import analyse_obs

    br = (HERE / "RESULTS_OBS.json").read_bytes()
    analyse_obs.main()
    if (HERE / "RESULTS_OBS.json").read_bytes() != br:
        fail.append("RESULTS_OBS.json does not recompute")
    q = json.loads((HERE / "QUALIFICATION_L1000.json").read_text(encoding="utf-8"))
    if q["compound_overlap"] < 1000 or "metadata only" not in q["scope"]:
        fail.append("qualification file unexpected")
    reg = json.loads((ROOT / "research/STUDIES.json").read_text(encoding="utf-8"))["studies"]
    if not any(s["path"] == "observable_state_20261018" and s["status"] != "frozen" for s in reg):
        fail.append("study not registered as non-frozen")
    st = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout.splitlines()
    allowed = ("research/observable_state_20261018", "research/STUDIES.json", "log/DIRECTIONS.md", "research/acquisition_program_20261018",
               "research/feedback_propagation_20261018", "research/seed_attribution_20261017", "research/EVIDENCE.md", "research/REPORT.md")
    stray = [l for l in st if not any(a in l.replace("\\", "/") for a in allowed)]
    if stray:
        fail.append(f"unexpected modified paths: {stray}")
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(HERE / "test_science.py"), str(HERE / "test_campaign.py"), str(HERE / "test_obs.py")], capture_output=True, text=True)
    if r.returncode:
        fail.append("tests failed: " + r.stdout[-300:])
    print("VERIFIED" if not fail else "FAILED: " + "; ".join(fail))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
