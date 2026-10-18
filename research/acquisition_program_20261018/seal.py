"""Two-stage freeze: FREEZE1 (protocol and code, before any search) and FREEZE2 (selected incumbents and traces, before held-out).

File summary
- Path: research/acquisition_program_20261018/seal.py
- Purpose: LF-normalised sha256 digests, write-once. `check(stage)` raises SystemExit(FREEZE_MISSING / FREEZE_MISMATCH).
  Not hashed: DEVIATIONS.json, seal.py, verify.py, run outputs after the stage (RESULTS.json, REPORT.md).
- Usage: ``python seal.py freeze1`` / ``python seal.py freeze2`` / ``python seal.py check1|check2``.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES1 = ["PROTOCOL.md", "ap_task.py", "ap_build.py", "ap_search.py", "ap_analyse.py", "run_search.py", "evaluate.py", "test_science.py",
          "hindsight_clarification.py", "HINDSIGHT_CLARIFICATION.json"]
FILES2 = ["INCUMBENTS.json", "SEARCH_TRACE_conventional.json", "SEARCH_TRACE_agent.json"]


def lf_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def freeze(stage: int) -> None:
    out = HERE / f"FREEZE{stage}.json"
    if out.exists():
        raise SystemExit(f"FREEZE{stage}_EXISTS")
    files = FILES1 if stage == 1 else FILES2
    out.write_bytes((json.dumps({"study": "acquisition_program_20261018", "stage": stage,
                                 "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "sha256_lf": {f: lf_digest(HERE / f) for f in files}}, indent=1) + "\n").encode())
    print("frozen", stage, len(files))


def check(stage: int) -> None:
    path = HERE / f"FREEZE{stage}.json"
    if not path.exists():
        raise SystemExit(f"FREEZE{stage}_MISSING")
    for f, d in json.loads(path.read_text(encoding="utf-8"))["sha256_lf"].items():
        if not (HERE / f).exists() or lf_digest(HERE / f) != d:
            raise SystemExit(f"FREEZE{stage}_MISMATCH: {f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd.startswith("freeze"):
        freeze(int(cmd[-1]))
    else:
        check(int(cmd[-1]))
        print("OK")
