"""Write FREEZE.json: the digests that confirm.py requires before it reads any Beat AML outcome.

File summary
- Path: research/context_transfer_20261017/freeze.py
- Purpose: fix the protocol, the code that runs the confirmation, the development evidence it was
  chosen from, the census and the bytes of every confirmation input, before the one-shot run.
- Core points:
  - Digest rule: sha256 of the file bytes with CRLF normalised to LF (confirm.py and verify.py
    accept either the raw or the normalised digest).
  - Hashed:
    - PROTOCOL.md;
    - every study module that confirm.py imports;
    - the development records (DEVELOPMENT.json, POWER.json, RANK_CHECK.json, LLM_PILOT.json,
      PARITY.json, CENSUS.json) and the rule-choice declaration with its result;
    - the provider client loaded by the LLM arm;
    - the Beat AML release files.
  - Not hashed: files written or edited after the freeze, or that check it (FREEZE.json,
    RESULTS.json, DEVIATIONS.json, README.md, verify.py), and development-only scripts.
  - Refuses to overwrite an existing FREEZE.json (FREEZE_EXISTS).
- Interfaces: `python -B freeze.py`.
"""
from __future__ import annotations

import hashlib
import time

from common import BEATAML, HERE, ROOT, write_json

STUDY = ["PROTOCOL.md", "common.py", "vc.py", "agent.py", "replay.py", "procedure.py", "llm_arm.py",
         "data_beataml.py", "confirm.py", "CENSUS.json", "DEVELOPMENT.json", "POWER.json", "RANK_CHECK.json",
         "LLM_PILOT.json", "PARITY.json", "RULE_CHOICE.md", "RULE_CHOICE.json", "rule_choice.py"]
NOT_HASHED = ["FREEZE.json", "RESULTS.json", "DEVIATIONS.json", "README.md", "verify.py", "freeze.py",
              "develop.py", "power.py", "census.py", "data_prism.py", "parity.py", "procedure_variant_a.py"]
EXTRA = ["src/agent/llm.py"]


def digest(path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    out_path = HERE / "FREEZE.json"
    if out_path.exists():
        raise SystemExit("FREEZE_EXISTS: the study is already frozen")
    rel = [f"research/{HERE.name}/{name}" for name in STUDY] + EXTRA
    rel += [p.relative_to(ROOT).as_posix() for p in sorted(BEATAML.iterdir()) if p.is_file()]
    missing = [r for r in rel if not (ROOT / r).is_file()]
    if missing:
        raise SystemExit(f"MISSING: {missing}")
    write_json(out_path, {
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "one-shot confirmation on Beat AML 2.0 (P1-P6, claims C1-C4); everything else is development",
        "digest_rule": "sha256 of file bytes with CRLF normalised to LF",
        "not_hashed": NOT_HASHED,
        "sha256": {r: digest(ROOT / r) for r in rel},
    })
    print("frozen", len(rel), "files")


if __name__ == "__main__":
    main()
