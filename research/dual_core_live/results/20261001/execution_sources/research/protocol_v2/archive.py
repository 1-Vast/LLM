"""Archive protocol-v1 evidence: digest every original artefact, record its status, make it read-only.

File summary
- Path: research/protocol_v2/archive.py
- Purpose: fix, once, what the two protocol-v1 experiments (`external-validation-1`, block 1 of
  2026-09-27, and `belief-planning-1`, block 2) actually left behind, so no later session can
  reinterpret or rewrite it unnoticed. Nothing is deleted, moved or edited.
- Core points:
  - For each experiment `research/experiments/<name>/EVIDENCE.json` lists every original
    artefact (freeze, protocol, manifests, replay folds, summaries, vault log) with SHA-256, size,
    modification time, record counts, the counts the experiment registered, and a status.
  - Each freeze is verified at the archival commit (`registry.verify_at_commit`), which is where
    a historical experiment must be replayed. External-validation-1 has two freezes: the
    original (00:27, copy in `log/20260927/0927/`) and the one a Codex session regenerated at
    02:53. Neither verifies at any commit, because the original files were edited before the
    first commit that contains them; the archive records exactly which files differ.
  - A replay fold whose record count differs from the registered count, or which was written
    after the registered run finished, is marked `rewritten_post_hoc`.
  - The untracked originals under `outputs/` are set read-only (attribute only; content unchanged).
    Tracked originals are protected by git history and by the digests here.
- Run: python -m research.protocol_v2.archive [--write]
- Interfaces: `external_validation_1`, `belief_planning_1`, `ARCHIVE_COMMIT`
- Depends on: registry.py
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from . import registry as G

ROOT = G.ROOT
ARCHIVE_COMMIT = "83b9aa90129128eb75166825b582f32cbda2dc99"
"""The first commit that contains both protocol-v1 experiments (2026-09-27, 'Add belief-space planning ...')."""
OUT = ROOT / "research" / "experiments"
EV1_OUT = ROOT / "outputs" / "external_validation_20260927"
BP1_OUT = ROOT / "outputs" / "belief_planning_20260927"
EV1_REGISTERED_COMPLETED = "2026-09-26T16:32:57+00:00"
EDITED_AFTER_WITNESS = ("research/dynamic_world_model/common.py", "research/dynamic_world_model/episodes.py")
"""Frozen files whose checkout had CRLF or mixed line endings and that protocol v2 later edited (the
truth guard in `episode_list`, the removal of unreferenced aliases). Their frozen digests can no longer
be re-derived from disk; their tie to the archive-commit blob rests on `SESSION_START_WITNESS`."""
SESSION_START_WITNESS = {
    "at": "2026-09-27T11:33+08:00",
    "head": ARCHIVE_COMMIT,
    "git_status_clean": True,
    "belief_planning_1_freeze": "all 54 digests matched the files on disk",
    "external_validation_1_regenerated_freeze": "78 of 79 digests matched; src/maestro/acquisition.py did not",
    "consequence": "with a clean status, each tracked file's content equalled its blob at the archive commit "
                   "modulo line endings, so a file frozen from a CRLF or mixed-ending checkout that the protocol-v2 "
                   "edits later changed (research/dynamic_world_model/episodes.py) is still tied to that blob",
    "source": "log/20260927/README.md block 3, record control",
}


def _count(path: Path) -> int | None:
    if not path.name.endswith(".gz"):
        return None
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def _artefact(path: Path, *, registered_records=None, completed_utc: str | None = None, count=True) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    if not path.is_file():
        return {"path": rel, "status": "missing"}
    info = path.stat()
    mtime = datetime.fromtimestamp(info.st_mtime, timezone.utc)
    entry = {"path": rel, "sha256": G.sha256_file(path), "bytes": info.st_size,
             "modified_utc": mtime.isoformat(timespec="seconds"), "tracked": _tracked(rel)}
    if count and path.name.endswith(".jsonl.gz"):
        entry["records"] = _count(path)
    if registered_records is not None:
        entry["registered_records"] = registered_records
    status = "original"
    if registered_records is not None and entry.get("records") not in (None, registered_records):
        status = "rewritten_post_hoc"
    if completed_utc and mtime > datetime.fromisoformat(completed_utc) and not entry["tracked"]:
        status = "rewritten_post_hoc"
    entry["status"] = status
    return entry


def _tracked(rel: str) -> bool:
    return G._git(ROOT, "ls-files", "--error-unmatch", rel) is not None


def _freeze(path: Path, commit: str) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    check = G.verify_at_commit(freeze.get("sha256", {}), commit)
    git = freeze.get("git", {})
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": G.sha256_file(path),
            "frozen_at": freeze.get("frozen_at"), "status_text": freeze.get("status"),
            "registered_commit": git.get("commit"), "registered_from_dirty_tree": bool(git.get("uncommitted_paths")),
            "uncommitted_paths_at_freeze": git.get("uncommitted_paths", []),
            "files_frozen": len(freeze.get("sha256", {})),
            "verification_at_archive_commit": {
                "commit": commit, "problems": check["problems"],
                "status_counts": {k: sum(v == k for v in check["status"].values())
                                  for k in ("exact", "eol_equivalent", "disk", "changed", "missing")},
                "eol_equivalent_files": sorted(k for k, v in check["status"].items() if v == "eol_equivalent")}}


def external_validation_1() -> dict:
    manifest = json.loads((ROOT / "log/20260927/0927/external_validation_replay_manifest.json").read_text(encoding="utf-8"))
    registered = manifest["files"]
    folds = [_artefact(Path(p), registered_records=registered.get(Path(p).name.replace(".jsonl.gz", "")),
                       completed_utc=EV1_REGISTERED_COMPLETED)
             for p in sorted(glob.glob(str(EV1_OUT / "replay" / "*.jsonl.gz")))]
    return {
        "experiment": "external-validation-1", "protocol_dir": "research/external_validation/",
        "record": "log/20260927/README.md (block 1)",
        "freezes": {"original": _freeze(ROOT / "log/20260927/0927/external_validation_freeze.json", ARCHIVE_COMMIT),
                    "regenerated_02_53": _freeze(ROOT / "research/external_validation/freeze.json", ARCHIVE_COMMIT)},
        "registered_run": {"started_utc": manifest["started_at_utc"], "completed_utc": manifest["completed_at_utc"],
                           "records": manifest["records"], "arms": manifest["arms"]},
        "replay_folds": folds,
        "other_artefacts": [_artefact(ROOT / p, count=False) for p in (
            "log/20260927/0927/external_validation_replay_manifest.json",
            "log/20260927/0927/external_validation_gates.json",
            "log/20260927/0927/external_validation_report.md",
            "log/20260927/0927/external_validation_baseline_selection.json",
            "outputs/external_validation_20260927/replay_manifest.json",
            "outputs/external_validation_20260927/summary.json",
            "outputs/external_validation_20260927/report.md")],
        "interpretation": [
            "The original freeze no longer verifies at any commit: nine frozen files were edited by a Codex "
            "session (00:59-02:56) before the first commit that contains them.",
            "The regenerated freeze does not verify either: src/maestro/acquisition.py changed after it was "
            "written (the coherence fix).",
            "Folds whose status is `original` match the registered record counts and predate any later edit; "
            "a replay of l1000_T_0 at the archive commit reproduces every original arm's decisions exactly "
            "(research/protocol_v2 test).",
            "l1000_T_1 was rewritten at 02:52 with an added arm; its original content is lost. Do not cite it "
            "as registered evidence.",
        ],
    }


def belief_planning_1() -> dict:
    freeze_path = ROOT / "research/belief_planning/freeze.json"
    manifest = json.loads((BP1_OUT / "registered/dev/manifest.json").read_text(encoding="utf-8"))
    dev = [_artefact(Path(p), registered_records=manifest["tasks"].get(Path(p).name.replace(".jsonl.gz", ""), {})
                     .get("records"), completed_utc=manifest["completed_at_utc"])
           for p in sorted(glob.glob(str(BP1_OUT / "registered/dev/*.jsonl.gz")))]
    external = json.loads((BP1_OUT / "external/replay_manifest.json").read_text(encoding="utf-8"))
    vault_log = BP1_OUT / "external/vault_access.jsonl"
    events = [json.loads(line) for line in vault_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    freeze_sha = G.sha256_file(freeze_path)
    return {
        "experiment": "belief-planning-1", "protocol_dir": "research/belief_planning/",
        "record": "log/20260927/README.md (block 2)",
        "freeze": {**_freeze(freeze_path, ARCHIVE_COMMIT),
                   "copy_in_log_sha256": G.sha256_file(ROOT / "log/20260927/0927/belief_planning_freeze.json"),
                   "sha256_recorded_by_vault": events[0].get("freeze_sha256") if events else None,
                   "unchanged_since_vault_opened": bool(events) and events[0].get("freeze_sha256") == freeze_sha},
        "vault": {"log": _artefact(vault_log, count=False), "events": events,
                  "opened_once": sum(e.get("event") == "vault_opened" for e in events) == 1,
                  "status": "consumed: GSE70138 labels were opened once; the study can no longer serve as an "
                            "untouched external test for any MAESTRO policy"},
        "external_run": {"records": _artefact(BP1_OUT / "external/records.jsonl.gz",
                                              registered_records=external["records"]),
                         "manifest": _artefact(BP1_OUT / "external/replay_manifest.json", count=False),
                         "study_summary": _artefact(BP1_OUT / "external/study_summary.json", count=False),
                         "opened_study": {**_artefact(BP1_OUT / "external/opened_study.pkl", count=False),
                                          "note": "pickled vault contents (labels included); evaluation-side only"}},
        "development_run": {"manifest": _artefact(BP1_OUT / "registered/dev/manifest.json", count=False),
                            "folds": dev},
        "interpretation": [
            "The freeze verifies at the archive commit with no problem, and the vault log recorded its digest "
            "when the vault opened, so the external result was produced under the registered files.",
            "It was nonetheless frozen from a dirty working tree (uncommitted_paths_at_freeze); protocol v2 "
            "refuses that.",
            "GSE70138 is consumed. Protocol v2 may analyse these records post hoc but cannot use the study for "
            "confirmation, and must not tune on its labels.",
        ],
    }


def make_read_only(entries: list[dict]) -> list[str]:
    changed = []
    for e in entries:
        path = ROOT / e["path"]
        if e.get("status") in ("original", "rewritten_post_hoc") and path.is_file() and not e.get("tracked"):
            os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            changed.append(e["path"])
    return changed


def _flatten(evidence: dict) -> list[dict]:
    out = []

    def walk(value):
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                out.append(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(evidence)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write EVIDENCE.json files and set read-only")
    args = parser.parse_args()
    for name, builder in (("external-validation-1", external_validation_1), ("belief-planning-1", belief_planning_1)):
        evidence = builder()
        evidence["archived_at"] = datetime.now(G.TIMEZONE).isoformat(timespec="seconds")
        evidence["archive_commit"] = ARCHIVE_COMMIT
        evidence["session_start_witness"] = SESSION_START_WITNESS
        summary = {e["path"]: e.get("status") for e in _flatten(evidence) if e.get("status") != "original"}
        print(name, "artefacts", len(_flatten(evidence)), "non-original:", summary)
        if args.write:
            target = OUT / name / "EVIDENCE.json"
            if target.exists():
                raise G.AlreadyRegistered(f"{target} exists; the archive is written once")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(json.dumps(evidence, indent=1).encode("utf-8") + b"\n")
            evidence["read_only_set"] = make_read_only(_flatten(evidence))
            print(" read-only:", len(evidence["read_only_set"]))


if __name__ == "__main__":
    main()
