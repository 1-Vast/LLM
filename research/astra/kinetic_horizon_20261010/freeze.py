"""Hash the registered protocol, code, gate and development receipts (writes FREEZE.json once)."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = [
    "PROTOCOL.md", "LITERATURE.md", "GATE.json", "SPLIT.json", "MIXSEQ_SPLIT.json", "DRUG_MATCH.json",
    "horizon_data.py", "drug_match.py", "split.py", "prism_extract.py", "mixseq_index.py", "mixseq_extract.py",
    "mixseq_state.py", "mixseq_panel.py", "ccle.py", "gate.py", "timecourse.py", "evaluate.py", "verify.py",
    "freeze.py", "run_sealed.sh",
    "PRISM_DEVELOPMENT_RECEIPT.json", "PRISM_MIX_DEVELOPMENT_RECEIPT.json", "PRISM_EXTERNAL_MIX_RECEIPT.json",
    "PRISM_EXTERNAL_TAHOE_RECEIPT.json",
    "mixseq/A_control.json", "mixseq/C_control.json", "mixseq/D_control.json", "mixseq/A_treated_dev.json",
    "mixseq_state/A_v0.json", "mixseq_state/A_v1.json", "mixseq_state/A_v2.json", "mixseq_state/C_v1.json", "mixseq_state/D_v1.json",
    "development/kinetic_probe.py", "development/kinetic_probe.json", "development/dev_horizon.py", "development/dev_horizon.json",
    "development/dev_perdrug.py", "development/dev_perdrug.json", "development/dev_direction.py", "development/dev_direction.json",
    "development/dev_inspect.py", "development/dev_gate.py", "development/dev_gate.json", "development/axis_probe.py",
    "development/axis_probe.json", "development/dev_mixseq_rna.py", "development/dev_mixseq_rna.json",
    "development/dev_mixseq_late.py", "development/dev_mixseq_late.json", "development/dev_ccle.py", "development/dev_ccle.json",
    "development/dev_complement.py", "development/dev_complement.json", "development/dry_run.py", "development/dry_run.log",
]


def main() -> dict:
    out = HERE / "FREEZE.json"
    if out.exists():
        raise SystemExit("FREEZE.json exists; the freeze is written once")
    missing = [f for f in FROZEN if not (HERE / f).exists()]
    if missing:
        raise SystemExit(f"missing frozen files: {missing}")
    rec = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "files": {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in FROZEN}}
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    r = main()
    print(r["frozen_utc"], len(r["files"]), "files")
