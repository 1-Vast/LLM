"""Check the freeze and recompute the registered analysis from the cached records.

File summary
- Path: research/feedback_attribution_20261017/verify.py
- Purpose: one command that says whether this study's reported numbers follow from its frozen code
  and cached records.
- Checks:
  - every FREEZE.json digest (LF-normalised) and the Beat AML domain cache digest;
  - the confirmation records this study's parity check reads are the ones its RESULTS.json names;
  - if RESULTS.json exists: `attribution.analyse()` on the cached records equals it exactly, the
    vc-probe parity holds and the inner parity of the tuned replay holds;
  - every diagnostic file present names records whose digest still matches.
- Interfaces: ``python -B verify.py``; prints VERIFIED or exits non-zero with the failures.
"""
from __future__ import annotations

import json
import sys

from common import DOMAIN_CACHE, HERE, ROOT, SOURCE_STUDY, sha256
from freeze import lf_digest


def main() -> None:
    fail = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for f, digest in freeze["sha256_lf"].items():
        ok = (ROOT / f).exists() and lf_digest(f) == digest
        print("PASS" if ok else "FAIL", "freeze", f)
        if not ok:
            fail.append(f)
    if sha256(DOMAIN_CACHE) != freeze["domain_cache_sha256"]:
        fail.append("domain cache")
    conf = json.loads((SOURCE_STUDY / "RESULTS.json").read_text(encoding="utf-8"))
    if sha256(ROOT / "tmp/context_transfer_20261017/confirm_records.json") != conf["records_sha256"]:
        fail.append("confirmation records")
    if (HERE / "RESULTS.json").exists():
        import attribution
        stored = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        again = json.loads(json.dumps(attribution.analyse(), default=float))
        same = again == stored
        print("PASS" if same else "FAIL", "RESULTS.json recomputed from cached records")
        if not same:
            fail.append("RESULTS.json")
        par = stored["parity_probes_vc"]
        if not (par["D_equals_confirmed_b_exploit"] and par["C_plus_probes_equals_confirmed_vc0"]):
            fail.append("vc-probe parity")
        if not all(stored["tuned"]["inner_parity_with_confirmation"].values()):
            fail.append("tuned inner parity")
    for name in ("COHERENCE.json", "DECOMPOSITION.json"):
        p = HERE / name
        if p.exists():
            diag = json.loads(p.read_text(encoding="utf-8"))
            for rel, digest in diag.get("inputs_sha256", {}).items():
                if sha256(ROOT / rel) != digest:
                    fail.append(f"{name}: {rel}")
    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("VERIFIED")


if __name__ == "__main__":
    main()
