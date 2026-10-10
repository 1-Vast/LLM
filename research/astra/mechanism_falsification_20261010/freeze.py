"""Hash the registered protocol, code, agent hypotheses and development receipts (writes FREEZE.json once).

After FREEZE.json exists, study.load_tier("sealed") opens the confirmation drugs. Every file listed
here keeps its hash; verify.py checks that none changed after the freeze.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = ["split.py", "extract.py", "literature.py", "emh.py", "emh_critic.py", "falsify.py", "study.py", "knowledge.py",
        "episodes.py", "components.py", "identifiability.py", "revision.py", "agent_arms.py", "intervals.py",
        "dev_run.py", "dev_agent.py", "dev_describe.py", "dev_programs.py", "dev_strata.py", "dev_ceiling.py",
        "dev_batch.py", "dev_block_check.py", "dev_scorers.py", "dev_identifiability.py", "dev_revision.py",
        "analogy.py", "dev_analogy.py", "evaluate.py", "verify.py", "freeze.py", "make_receipt.py", "test_block_m.py", "run_sealed.sh"]
DOCS = ["PROBLEM.md", "LITERATURE.md", "DIAGNOSIS.md", "PROTOCOL.md", "PROTOCOL_CONFIG.json", "SPLIT.json", "EXTRACT_RECEIPT.json"]


def frozen_files() -> list[str]:
    files = CODE + DOCS
    for sub in ("literature", "emh/nolit", "emh/lit", "emh/lit_critic", "analogy"):
        files += sorted(str(p.relative_to(HERE)).replace("\\", "/") for p in (HERE / sub).glob("*.json"))
    for pattern in ("*.json", "*.log", "*.sh"):
        files += sorted(str(p.relative_to(HERE)).replace("\\", "/") for p in (HERE / "development").glob(pattern))
    return files


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
           "files": {f: sha(HERE / f) for f in files}}
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    r = main()
    print(r["frozen_utc"], len(r["files"]), "files")
