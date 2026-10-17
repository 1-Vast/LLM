"""Write FREEZE.json once: digests of the protocol, the study code and the promoted modules it calls.

File summary
- Path: research/feedback_attribution_20261017/freeze.py
- Purpose: fix the pre-registered design before any group outcome is computed. Digests are of
  LF-normalised bytes, so they do not depend on the platform's line endings.
- Not hashed: DEVIATIONS.json (a freeze must not hash its own deviations log), freeze.py and
  verify.py (integrity tooling), and outputs.
- Interfaces: ``python -B freeze.py``; refuses (FREEZE_EXISTS) if FREEZE.json is present.
"""
from __future__ import annotations

import hashlib
import time

from common import DOMAIN_CACHE, HERE, ROOT, sha256, write_json

FILES = [
    "research/feedback_attribution_20261017/PROTOCOL.md",
    "research/feedback_attribution_20261017/common.py",
    "research/feedback_attribution_20261017/coherent.py",
    "research/feedback_attribution_20261017/planner.py",
    "research/feedback_attribution_20261017/attribution.py",
    "research/feedback_attribution_20261017/tuned.py",
    "research/feedback_attribution_20261017/test_science.py",
    "research/feedback_attribution_20261017/audit_units.py",
    "research/feedback_attribution_20261017/audit_missingness.py",
    "src/virtual_cell/bridged_transfer.py",
    "src/agent/bridge_design.py",
    "src/agent/procedure_selection.py",
]


def lf_digest(path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE_EXISTS: the design is already frozen")
    write_json(HERE / "FREEZE.json", {
        "study": "feedback_attribution_20261017",
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "attribution groups, planner arms, tuned arms and registered analysis of PROTOCOL.md; "
                 "no group outcome computed before this freeze",
        "sha256_lf": {f: lf_digest(f) for f in FILES},
        "domain_cache_sha256": sha256(DOMAIN_CACHE),
    })
    print("frozen", len(FILES), "files")


if __name__ == "__main__":
    main()
