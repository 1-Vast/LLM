from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cleanup/CLEANUP_MANIFEST.json"
STATS = ROOT / "cleanup/PRE_CLEANUP_STATS.json"
KEEP = {
    "paper_01286/state_readout_repair",
    "paper_01286/state_feedback_repair",
    "paper_01286/released_test",
    "decision_value_validation_20261009",
    "viability_contrast_20260928/prepared",
    "viability_contrast_20261008/run10_repair",
}
KEEP_TRACKED = (
    "research/astra/state_readout_repair_20261009/",
    "research/astra/state_feedback_repair_20261009/",
    "research/decision_value/",
    "research/astra/map_knowledge_pilot_20261008/",
    "research/astra/map_release_test_20261008/",
    "research/astra/boundary_acquisition_20261007/packet2/",
)
REMOVE_LOCAL_TREES = (
    "research/identifiability_audit",
    "research/dual_core_live",
    "research/dual_core_followup",
    "research/astra/knowledge_transfer_20261004",
    "research/astra/mono_pretraining_20261005",
    "research/astra/repeat_signal_20261005",
    "research/astra/feedback_validation_20261003",
    "research/astra/confirmation_campaign_20261004",
    "research/astra/zeroshot_context_20261007",
    "research/astra/results",
    "research/viability_contrast/run3.py",
    "research/viability_contrast/run4.py",
    "research/viability_contrast/run5.py",
    "research/viability_contrast/run5b.py",
    "research/viability_contrast/llm_arm.py",
    "log/20260915",
    "research/astra/agent_closed_loop_20261007",
    "research/astra/state_dual_core_20261007",
    "research/astra/state_resolution_20261007",
    "research/astra/functional_data_20261007",
    "research/astra/boundary_acquisition_20261007/packet1",
    "research/astra/boundary_acquisition_20261007/affordable_replay_check1",
    "research/astra/decision_opportunity_20261007/affordable_replay_check1",
    "research/astra/decision_opportunity_20261007/compact_packet",
    "research/astra/decision_opportunity_20261007/development_run1",
    "research/astra/decision_opportunity_20261007/packet_replay2",
    "research/astra/decision_opportunity_20261007/transfer_run1",
    "research/astra/decision_opportunity_20261007/trust_run1",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in manifest["planned_deletions"]
            if not row["path"].startswith(KEEP_TRACKED)]
    manifest["planned_deletions"] = rows
    known = {row["path"] for row in rows}
    for path in sorted((ROOT / "outputs").rglob("*")):
        if not path.is_file():
            continue
        subpath = path.relative_to(ROOT / "outputs").as_posix()
        if any(subpath == keep or subpath.startswith(keep + "/") for keep in KEEP):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in known:
            continue
        size = path.stat().st_size
        rows.append({
            "path": relative,
            "size_bytes": size,
            "sha256": digest(path),
            "commit_blob": None,
            "reason": "Ignored local generated output is not read by any retained current verifier; canonical results and scientific limitations remain summarized in research/EVIDENCE.md.",
            "evidence_conclusion": "research/EVIDENCE.md: historical output copies add no independent evidence.",
            "recovery": {"kind": "none", "note": "Ignored working-tree output has no Git blob or baseline commit recovery source."},
            "status": "PLANNED_DELETE_LOCAL_OUTPUT",
        })
        known.add(relative)
    for item in REMOVE_LOCAL_TREES:
        candidate = ROOT / item
        paths = [candidate] if candidate.is_file() else list(candidate.rglob("*")) if candidate.is_dir() else []
        for path in sorted(path for path in paths if path.is_file()):
            relative = path.relative_to(ROOT).as_posix()
            if relative in known:
                continue
            rows.append({
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
                "commit_blob": None,
                "reason": "Untracked residue in a historical study tree explicitly excluded from the release checkout.",
                "evidence_conclusion": "research/EVIDENCE.md: historical studies are indexed without duplicated methods or assets.",
                "recovery": {"kind": "none", "note": "Untracked local file has no Git recovery source."},
                "status": "PLANNED_DELETE_LOCAL",
            })
            known.add(relative)
    manifest["planned_deletions"] = sorted(rows, key=lambda row: row["path"])
    manifest["review_required"] = [{
        "path": "ignored local data/ and non-output assets not used by current verifiers",
        "status": "REVIEW_REQUIRED",
        "reason": "Local assets have no baseline blob; only unreferenced ignored outputs are included for deletion.",
    }]
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    tracked_rows = [row for row in rows if row["commit_blob"]]
    local_rows = [row for row in rows if row["commit_blob"] is None]
    stats["planned_tracked_file_count"] = len(tracked_rows)
    stats["planned_tracked_bytes"] = sum(row["size_bytes"] for row in tracked_rows)
    stats["planned_local_output_file_count"] = len(local_rows)
    stats["planned_local_output_bytes"] = sum(row["size_bytes"] for row in local_rows)
    stats["planned_total_file_count"] = len(rows)
    stats["planned_total_bytes"] = sum(row["size_bytes"] for row in rows)
    stats["planned_paths_include_untracked_or_ignored"] = bool(local_rows)
    STATS.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tracked_deletions": len(tracked_rows), "local_output_deletions": len(local_rows),
                      "total_bytes": stats["planned_total_bytes"]}))


if __name__ == "__main__":
    main()
