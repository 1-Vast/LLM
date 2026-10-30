"""Freeze the protocol before any evaluation stream is scored: hashes of every code file, the configuration, the generators and the stage ledger.

`python iv_freeze.py write`   writes FREEZE.json (refuses to overwrite)
`python iv_freeze.py check`   recomputes hashes and compares (used by the verifier)
Stage ledger RUN/LEDGER.json: a stage (dev, eval, real, api, example) can be recorded once; a second evaluation of a completed stage is refused.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = sorted(p.name for p in HERE.glob("iv_*.py") if p.name not in ("iv_freeze.py",))
CODE_EXTRA = ["PROTOCOL.md", "CONFIG.json"]
ROOT = HERE.parents[1]
TEST_FILES = [ROOT / "tests" / "test_innovation_validation.py", ROOT / "tests" / "fixtures" / "innovation_validation.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def current() -> dict:
    files = {n: sha(HERE / n) for n in CODE + CODE_EXTRA if (HERE / n).exists()}
    return {"files": files}


def write():
    path = HERE / "FREEZE.json"
    if path.exists():
        raise SystemExit("FREEZE.json exists: refusing to overwrite a frozen protocol")
    cfg = json.loads((HERE / "CONFIG.json").read_text(encoding="utf-8"))
    out = {"frozen_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z", "config": cfg, **current()}
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("frozen", len(out["files"]), "files")


def check() -> list:
    frozen = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    now = current()["files"]
    problems = []
    amend = HERE / "FREEZE_AMENDMENT.json"
    if amend.exists():                                  # documented repair cycle: original FREEZE.json stays untouched
        a = json.loads(amend.read_text(encoding="utf-8"))
        for n, rec in a["files"].items():
            if frozen["files"].get(n) != rec["pre_repair_sha256"]:
                problems.append(f"amendment for {n} does not start from the frozen hash")
            frozen["files"][n] = rec["post_repair_sha256"]
    for n, h in frozen["files"].items():
        if n not in now:
            problems.append(f"missing {n}")
        elif now[n] != h:
            problems.append(f"changed after freeze: {n}")
    return problems


def ledger_path(run_dir: Path) -> Path:
    return run_dir / "LEDGER.json"


def claim_stage(run_dir: Path, stage: str, meta: dict):
    p = ledger_path(run_dir)
    led = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if stage in led:
        raise SystemExit(f"stage '{stage}' already completed: a second evaluation is refused")
    led[stage] = meta
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(led, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "write":
        write()
    else:
        pr = check()
        print("FREEZE OK" if not pr else "FREEZE PROBLEMS: " + "; ".join(pr))
        sys.exit(1 if pr else 0)
