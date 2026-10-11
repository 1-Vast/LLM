"""Hash the registered protocol, code, development receipts, literature and agent outputs (FREEZE.json, once).

After FREEZE.json exists, tiers.load("sealed") opens the confirmation drugs. verify.py checks that
no file listed here changed and that every confirmation agent output was created after the freeze.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = ["split.py", "tiers.py", "literature.py", "predictors.py", "mining.py", "scientist.py", "explain.py", "models.py",
        "trust.py", "dev_pilot.py", "dev_explain.py", "dev_capability.py", "dev_trust.py", "prereg_power.py",
        "evaluate.py", "verify.py", "freeze.py", "test_block_n.py"]
DOCS = ["PROBLEM.md", "PROTOCOL.md", "PROTOCOL_CONFIG.json", "SPLIT.json", "TIERS_RECEIPT.json"]


def rel(p: Path) -> str:
    return str(p.relative_to(HERE)).replace("\\", "/")


def frozen_files() -> list[str]:
    files = CODE + DOCS
    for sub in ("feasibility", "development", "rehearsal", "literature"):
        files += sorted(rel(p) for p in (HERE / sub).rglob("*") if p.is_file())
    return files


def agent_outputs() -> list[str]:
    return sorted(rel(p) for p in (HERE / "agent_outputs").rglob("*.json"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> dict:
    out = HERE / "FREEZE.json"
    if out.exists():
        raise SystemExit("FREEZE.json exists; the freeze is written once")
    files = frozen_files()
    missing = [f for f in files if not (HERE / f).exists()]
    if missing:
        raise SystemExit(f"missing frozen files: {missing}")
    rec = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "files": {f: sha(HERE / f) for f in files},
           "agent_outputs": {f: sha(HERE / f) for f in agent_outputs()}}
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    r = main()
    print(r["frozen_utc"], len(r["files"]), "files,", len(r["agent_outputs"]), "agent outputs")
