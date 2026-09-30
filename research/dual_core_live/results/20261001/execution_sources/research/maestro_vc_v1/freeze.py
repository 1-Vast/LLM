"""Write-once freeze records for MAESTRO-VC v1: hashes of protocol, code and data before any score.

File summary
- Path: research/maestro_vc_v1/freeze.py
- Purpose: write `research/maestro_vc_v1/freeze.json` once, before the full replay runs. Later stages
  (the stress test, the closed-loop update, the system demonstration) write their own write-once
  addenda for the files they add, so a file written after the main freeze is never silently folded in.
- Core points:
  - The record lists every file the replay's results depend on and its SHA-256. Running `--verify`
    compares the disk with the record and names each file that changed; it never rewrites the record.
  - `addendum(name, files, note)` writes `freeze_<name>.json` once, with the time it was written, so the
    order of decisions stays reconstructible.
- Interfaces: `FILES`, `DATA`, `digest`, `freeze`, `addendum`, `verify`
- Depends on: hashlib
- Run: python -m research.maestro_vc_v1.freeze [--verify] [--note TEXT]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "maestro_vc_v1"
RECORD = HERE / "freeze.json"
FILES = (
    "research/maestro_vc_v1/protocol.json", "research/maestro_vc_v1/arms.py", "research/maestro_vc_v1/replay.py",
    "research/scientific_case_memory/case_schema.py", "research/scientific_case_memory/case_store.py",
    "research/scientific_case_memory/case_index.py", "research/scientific_case_memory/case_retrieval.py",
    "research/scientific_case_memory/adaptation_model.py", "research/scientific_case_memory/protocol_library.py",
    "research/scientific_case_memory/hypothesis_graph.py", "research/scientific_case_memory/evidence_cards.py",
    "research/scientific_case_memory/build_cases.py", "research/scientific_case_memory/world.py",
    "research/scientific_case_memory/evaluate_case_retrieval.py", "research/scientific_case_memory/evaluate_decision_policy.py",
    "research/belief_planning/world.py", "research/belief_planning/arms.py", "research/belief_planning/planner.py",
    "research/belief_planning/tasks.py", "research/external_validation/arms.py", "research/external_validation/statistics.py",
    "research/protocol_v2/runner.py", "research/protocol_v2/contracts.py", "research/protocol_v2/tasks_v21.py",
    "research/protocol_v2/design.py", "research/protocol_v2/protocol_v2_1.json", "research/protocol_v2/protocol.json",
    "research/protocol_v2/registry.py", "research/protocol_v2/safe.py",
    "research/dual_core/agent.py", "research/dual_core/world2.py", "research/dual_core/ledger.py",
    "research/dual_core/transfer.py", "research/incontext_world/world.py", "research/incontext_world/transition.py",
    "research/incontext_world/metrics.py", "research/dynamic_world_model/common.py",
    "research/dynamic_world_model/episodes.py", "research/sequence_audit/policies.py",
    "src/maestro/acquisition.py", "src/maestro/outcome.py",
)
DATA = (
    "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
    "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
    "outputs/biological_depth_20260926/prepared/compounds.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz",
    "outputs/protocol_v2_1_20260927/design/sciplex3_design.csv",
    "outputs/protocol_v2_1_20260927/design/l1000_design.csv",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _lf_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def freeze(note: str) -> dict:
    if RECORD.exists():
        raise FileExistsError(f"{RECORD} exists; the freeze is write-once (use --verify)")
    record = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "note": note,
              "sha256": {f: digest(ROOT / f) for f in (*FILES, *DATA)},
              "sha256_lf_normalised": {f: _lf_digest(ROOT / f) for f in FILES}}
    RECORD.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def addendum(name: str, files, note: str) -> dict:
    path = HERE / f"freeze_{name}.json"
    if path.exists():
        raise FileExistsError(f"{path} exists; addenda are write-once")
    record = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "note": note,
              "sha256": {f: digest(ROOT / f) for f in files}}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def verify(record_path: Path = RECORD) -> list[str]:
    record = json.loads(record_path.read_text(encoding="utf-8"))
    changed = []
    for f, expected in record["sha256"].items():
        path = ROOT / f
        if not path.is_file():
            changed.append(f"missing:{f}")
        elif digest(path) != expected:
            changed.append(f"changed:{f}")
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--note", default="written before the full 20-task replay; see protocol.json exposure_disclosure")
    args = parser.parse_args()
    if args.verify:
        problems = verify()
        print("unchanged" if not problems else "\n".join(problems))
        return 1 if problems else 0
    record = freeze(args.note)
    print("froze", len(record["sha256"]), "files at", record["written_at"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
