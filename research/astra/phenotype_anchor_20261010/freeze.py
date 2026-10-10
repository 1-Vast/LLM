"""Write FREEZE.json: hashes of the protocol, code and reference-only receipts, before held-out access.

Refuses if any held-out phenotype, expression, STATE forecast or LLM answer already exists.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "data/external/tahoe_phenotype_20261010"
HELDOUT = ("c12.h5ad", "c20.h5ad", "c26.h5ad", "c27.h5ad", "c31.h5ad")
FROZEN = ("PROTOCOL.md", "phenotypes.py", "analysis.py", "gate.py", "evaluate.py", "state_forecast.py", "phase_classifier.py",
          "llm_arm.py", "obs_extract.py", "extract_expression.py", "test_phenotype_anchor.py", "verify.py", "freeze.py", "LITERATURE.md", "run_heldout.sh", "make_receipt.py",
          "GATE.json", "MENU.json", "PHASE_CLASSIFIER.json", "phase_classifier.npz", "reference_loo.npz",
          "STATE_STAGING.json", "METADATA_RECEIPTS.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (HERE / "FREEZE.json").exists():
        raise SystemExit("FREEZE.json exists; a freeze is never rewritten")
    exposed = [str(p) for f in HELDOUT for p in (CACHE / "obs" / f"{f}.npz", CACHE / "expression" / f, HERE / "obs" / f"{f}.json",
                                               CACHE / "state_forecasts" / f"{f}.npz", HERE / "llm" / f"{f}.json") if p.exists()]
    if exposed:
        raise SystemExit(f"held-out artefacts already exist: {exposed}")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    body = {"frozen_utc": datetime.now(timezone.utc).isoformat(), "git_head": head, "git_dirty_entries": len(dirty),
            "files": {name: sha(HERE / name) for name in FROZEN},
            "heldout_artefacts_present_at_freeze": exposed,
            "gate": json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))["gate"],
            "statement": "No held-out phenotype, held-out treated/basal RNA, held-out STATE forecast or LLM answer exists at this time."}
    (HERE / "FREEZE.json").write_text(json.dumps(body, indent=1), encoding="utf-8")
    print(json.dumps(body, indent=1))


if __name__ == "__main__":
    main()
