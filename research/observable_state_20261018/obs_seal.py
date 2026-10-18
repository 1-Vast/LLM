"""Two-stage freeze for the per-family bets study: FREEZE0 (contract + code, before any proposal) and FREEZE1 (edits, before confirmation).

Write-once, LF-normalised sha256 digests. `check(stage)` raises SystemExit(FREEZE_MISSING / FREEZE_MISMATCH). Not hashed: DEVIATIONS.json,
obs_seal.py, verify.py, and outputs written after the stage. Usage: python obs_seal.py freeze0|freeze1|check0|check1
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES0 = ["STAGE0_CONTRACT.md", "STAGE0.json", "stage0_families.py", "obs_core.py", "obs_arms.py", "run_stage1.py", "run_confirm.py",
          "analyse_obs.py", "research_edit.py", "masked_interface.py", "test_obs.py"]
FILES1 = ["EDITS.json", "LLM_LOG.json"]


def lf_digest(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def freeze(stage):
    out = HERE / f"FREEZE{stage}.json"
    if out.exists():
        raise SystemExit(f"FREEZE{stage}_EXISTS")
    files = FILES0 if stage == 0 else FILES1
    out.write_bytes((json.dumps({"study": "observable_state_20261018", "stage": stage, "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "sha256_lf": {f: lf_digest(HERE / f) for f in files}}, indent=1) + "\n").encode())
    print("frozen", stage, len(files))


def check(stage):
    p = HERE / f"FREEZE{stage}.json"
    if not p.exists():
        raise SystemExit(f"FREEZE{stage}_MISSING")
    for f, d in json.loads(p.read_text(encoding="utf-8"))["sha256_lf"].items():
        if not (HERE / f).exists() or lf_digest(HERE / f) != d:
            raise SystemExit(f"FREEZE{stage}_MISMATCH: {f}")


if __name__ == "__main__":
    c = sys.argv[1]
    freeze(int(c[-1])) if c.startswith("freeze") else (check(int(c[-1])), print("OK"))
