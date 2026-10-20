"""Source freeze, stage ledger and preservation receipt.

`python pi_freeze.py write`    hashes every pi_*.py (except this file), CONFIG.json and PROTOCOL.md into FREEZE.json (refuses to overwrite)
`python pi_freeze.py check`    recomputes and compares
`python pi_freeze.py preserve-write|preserve-check`  byte-level receipt of the four predecessor packages (write-once; compared by the verifier)
Stage ledger RUN/LEDGER.json: a stage (eval, xplant) can be claimed once; a second evaluation is refused.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRESERVED = ["functional_rule_revision_20261020", "self_improving_virtual_cell_20261020", "innovation_validation_20261020", "innovation_validation_repair1_20261020"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def current() -> dict:
    names = sorted(p.name for p in HERE.glob("pi_*.py") if p.name != "pi_freeze.py") + ["CONFIG.json", "PROTOCOL.md"]
    return {n: sha(HERE / n) for n in names if (HERE / n).exists()}


def write():
    path = HERE / "FREEZE.json"
    if path.exists():
        raise SystemExit("FREEZE.json exists: refusing to overwrite a frozen protocol")
    cfg = json.loads((HERE / "CONFIG.json").read_text(encoding="utf-8"))
    out = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "config": cfg, "files": current()}
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("frozen", len(out["files"]), "files")


def check() -> list:
    frozen = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    now = current()
    problems = []
    amend = HERE / "FREEZE_AMENDMENT.json"
    if amend.exists():                                   # documented verifier-only repair; the original FREEZE.json stays untouched
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
    for n in now:
        if n not in frozen["files"]:
            problems.append(f"unfrozen code file: {n}")
    return problems


def tree_hashes() -> dict:
    out = {}
    for d in PRESERVED:
        base = ROOT / "research" / d
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                out[p.relative_to(ROOT).as_posix()] = sha(p)
    return out


def preserve_write():
    path = HERE / "PRESERVED_BEFORE.json"
    if path.exists():
        raise SystemExit("PRESERVED_BEFORE.json exists")
    t = tree_hashes()
    path.write_text(json.dumps({"files": t, "n": len(t)}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("preserved", len(t))


def preserve_check() -> list:
    before = json.loads((HERE / "PRESERVED_BEFORE.json").read_text(encoding="utf-8"))["files"]
    now = tree_hashes()
    return [f"preserved file changed/missing/added: {k}" for k in sorted(set(before) | set(now)) if before.get(k) != now.get(k)]


def claim_stage(run_dir: Path, stage: str, meta: dict):
    p = Path(run_dir) / "LEDGER.json"
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
    elif cmd == "preserve-write":
        preserve_write()
    elif cmd == "preserve-check":
        pr = preserve_check()
        print("PRESERVED OK" if not pr else "\n".join(pr))
        sys.exit(1 if pr else 0)
    else:
        pr = check()
        print("FREEZE OK" if not pr else "FREEZE PROBLEMS: " + "; ".join(pr))
        sys.exit(1 if pr else 0)
