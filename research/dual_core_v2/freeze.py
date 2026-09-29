"""Freeze record for dual-core v2: hashes of code, protocol and prepared data, written before any v2 score.

File summary
- Path: research/dual_core_v2/freeze.py
- Purpose: write `research/dual_core_v2/freeze.json` once. Running it again compares the disk with
  the record and reports every file that changed; it never overwrites the record.
- Interfaces: `FILES`, `digest`, `freeze`, `verify`; CLI `python -m research.dual_core_v2.freeze [--verify]`
- Depends on: hashlib
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "research/dual_core_v2/freeze.json"
FILES = (
    "research/dual_core_v2/protocol.json", "research/dual_core_v2/risk_control.py", "research/dual_core_v2/nested.py",
    "research/dual_core_v2/world3.py", "research/dual_core_v2/arms.py", "research/dual_core_v2/run.py",
    "research/dual_core_v2/test_dual_core_v2.py",
    "research/dual_core/transfer.py", "research/dual_core/world2.py", "research/dual_core/ledger.py",
    "research/dual_core/agent.py", "research/dual_core/e2.py", "research/dual_core/splits.py",
    "research/incontext_world/world.py", "research/belief_planning/world.py", "research/belief_planning/arms.py",
    "research/belief_planning/planner.py", "research/belief_planning/tasks.py", "research/protocol_v2/runner.py",
    "research/protocol_v2/contracts.py", "research/protocol_v2/tasks_v21.py", "research/protocol_v2/design.py",
    "research/dynamic_world_model/common.py", "src/maestro/acquisition.py", "src/maestro/outcome.py",
    "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
    "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
    "outputs/biological_depth_20260926/prepared/compounds.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz",
    "outputs/dual_core_20260927/split_manifest.json",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def freeze(note: str) -> dict:
    if RECORD.exists():
        raise FileExistsError(f"{RECORD} exists; the freeze is write-once (use --verify)")
    record = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "note": note,
              "sha256": {f: digest(ROOT / f) for f in FILES}}
    RECORD.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def addendum(name: str, files, note: str) -> dict:
    """A separate write-once record (`freeze_<name>.json`) for files written after the main freeze."""
    path = ROOT / f"research/dual_core_v2/freeze_{name}.json"
    if path.exists():
        raise FileExistsError(f"{path} exists; addenda are write-once")
    record = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "note": note,
              "sha256": {f: digest(ROOT / f) for f in files}}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def verify() -> dict:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    changed = {f: h for f, h in record["sha256"].items() if not (ROOT / f).exists() or digest(ROOT / f) != h}
    return {"written_at": record["written_at"], "files": len(record["sha256"]), "changed": sorted(changed)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    print(json.dumps(verify() if args.verify else freeze(args.note), indent=1)[:3000])
