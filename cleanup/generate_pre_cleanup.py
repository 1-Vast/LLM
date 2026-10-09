from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "540bc85801fa78a3a58780b37b81b4197449d107"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def tracked_files() -> list[str]:
    return [p for p in git("ls-files", "-z").decode().split("\0") if p]


def commit_blobs() -> dict[str, str]:
    rows = git("ls-tree", "-r", "-z", BASE).decode().split("\0")
    result = {}
    for row in rows:
        if not row:
            continue
        metadata, path = row.split("\t", 1)
        _mode, kind, blob = metadata.split()
        if kind == "blob":
            result[path] = blob
    return result


def explicit_keep(path: str, freeze_paths: set[str], core_tests: set[str]) -> bool:
    p = path.replace("\\", "/")
    if p in {"README.md", ".gitignore", ".gitattributes", "conftest.py", "pyproject.toml",
             "research/REPORT.md", "research/EVIDENCE.md", "log/INDEX.md"}:
        return True
    if p.startswith(("src/agent/", "src/maestro/", "src/virtual_cell/")):
        return True
    if p.startswith("tools/") and not p.startswith("tools/datasets/audit_results/"):
        if p.startswith("tools/datasets/") and p not in {
            "tools/datasets/__init__.py", "tools/datasets/condition_sources.py",
            "tools/datasets/README.md", "tools/datasets/.gitattributes",
        }:
            return False
        return True
    if p in {
        "research/astra/zeroshot_context_20261007/PROTOCOL.json",
        "research/astra/zeroshot_context_20261007/FREEZE.json",
        "research/astra/zeroshot_context_20261007/README.md",
        "research/astra/zeroshot_context_20261007/VERIFY.json",
        "research/astra/zeroshot_context_20261007/RESULTS.json",
    }:
        return True
    if (p.startswith("tests/fixtures/") and p.endswith(".py")) or p in core_tests or p in {
        "tests/__init__.py", "tests/test_repository_shape.py"
    }:
        return True
    if p.startswith("research/astra/state_readout_repair_20261009/"):
        return Path(p).name in {"FREEZE.json", "PROTOCOL.json", "README.md", "run.py", "verify.py", "test_readout.py", "PUBLIC_RECOVERY.json", "PUBLIC_COMMENTS.json", "ALTERNATE_TREE.json", "ALTERNATE_PERT.py.txt"}
    if p.startswith("research/astra/state_feedback_repair_20261009/"):
        return Path(p).name not in {"PROTOCOL.json", "FREEZE.json", "VERIFY_FREEZE.json", "README.md", "LITERATURE_AND_SCOPE.md", "posterior.py", "run.py", "verify.py", "test_posterior.py"}
    if p.startswith("research/decision_value/"):
        return Path(p).name not in {"PROTOCOL.json", "FREEZE.json", "VERIFY_FREEZE.json", "README.md", "SOURCES.md", "utility.py", "validation.py", "verify.py", "test_utility.py"}
    if p.startswith("research/astra/map_knowledge_pilot_20261008/"):
        return Path(p).name in {
            "ACQUISITION.json", "CONTRASTIVE_FREEZE.json", "CONTRASTIVE_PROTOCOL.json",
            "FREEZE.json", "PROTOCOL.json", "QUALIFIED_KNOWLEDGE.json", "RESULTS.json",
            "PREDICTIONS.npz", "CONTRASTIVE_RESULTS.json", "CONTRASTIVE_PREDICTIONS.npz",
            "SUMMARY.json", "CONTRASTIVE_SUMMARY.json", "run.py", "verify.py",
            "contrastive.py", "README.md",
        }
    if p.startswith("research/astra/map_release_test_20261008/"):
        return Path(p).name in {
            "ASSET_MANIFEST.json", "FREEZE.json", "PROTOCOL.json", "README.md", "acquire.py",
            "compare.py", "encoder.py", "features.py", "forward_probe.py", "native.py",
            "repeat.py", "verify.py",
        }
    if p.startswith("research/astra/boundary_acquisition_20261007/packet2/"):
        return True
    if p.startswith("research/astra/boundary_acquisition_20261007/"):
        return p in {
            "research/astra/boundary_acquisition_20261007/PROTOCOL.json",
            "research/astra/boundary_acquisition_20261007/FREEZE.json",
            "research/astra/boundary_acquisition_20261007/method.py",
            "research/astra/boundary_acquisition_20261007/execute.py",
            "research/astra/boundary_acquisition_20261007/verify_affordable_replay.py",
        } or (p.startswith("research/astra/boundary_acquisition_20261007/run1/") and Path(p).name in {
            "EPISODES.jsonl", "purchases.jsonl", "policy.jsonl", "REPLACEMENT_AUDIT.json",
            "PREFIX_FRONTIER.csv", "SUMMARY.json",
        })
    if p.startswith("research/astra/zeroshot_context_20261007/"):
        return False
    boundary_files = {
        "research/astra/boundary_acquisition_20261007/PROTOCOL.json",
        "research/astra/boundary_acquisition_20261007/FREEZE.json",
        "research/astra/boundary_acquisition_20261007/method.py",
        "research/astra/boundary_acquisition_20261007/execute.py",
        "research/astra/boundary_acquisition_20261007/verify_affordable_replay.py",
        "research/astra/decision_opportunity_20261007/verify_affordable_replay.py",
    }
    if p in boundary_files:
        return True
    if p.startswith("research/viability_contrast/") and p in freeze_paths:
        if p.endswith(".py"):
            return True
        if p in {
            "research/viability_contrast/freeze10.json",
            "research/viability_contrast/protocol10.json",
        }:
            return True
        return False
    if p in {
        "research/viability_contrast/__init__.py",
        "research/viability_contrast/conditional_world.py",
        "research/viability_contrast/freeze10.json",
        "research/viability_contrast/protocol10.json",
        "research/viability_contrast/run10.py",
        "research/viability_contrast/verify10.py",
    }:
        return True
    if p.startswith("log/20261008/"):
        return Path(p).name in {
            "README.md", "MAP_RELEASE_TEST.json", "MAP_NATIVE_FORWARD.txt",
            "VIABILITY_CONTRAST_V9.json",
        }
    if p.startswith("log/20261009/"):
        return Path(p).name in {
            "README.md", "STATE_READOUT_REPAIR.json", "STATE_FEEDBACK_REPAIR.json",
            "DECISION_VALUE_REPAIR.json",
        }
    if p == "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json":
        return True
    return False


def reason(path: str) -> tuple[str, str]:
    p = path.replace("\\", "/")
    if p.startswith("tools/datasets/audit_results/"):
        return (
            "Historical audit evidence and cached source/model payloads are outside the release input closure; canonical scientific conclusions remain summarized in EVIDENCE.md.",
            "research/EVIDENCE.md: historical evidence is reduced to indexed conclusions; current canonical claims and their limits are retained.",
        )
    if p.startswith("log/") and not p.startswith(("log/20261008/", "log/20261009/")):
        return (
            "Pre-2026-10-08 daily logs are historical execution detail; Git history remains the recovery source and canonical conclusions remain in EVIDENCE.md.",
            "research/EVIDENCE.md: legacy studies are index-only and do not support the current scientific claims.",
        )
    if p.startswith("outputs/"):
        return (
            "Tracked generated output belongs to superseded case-memory integration and is not read by a current canonical verifier.",
            "research/REPORT.md: independent decision benefit and general agent advantage are not established.",
        )
    if p.startswith("research/"):
        return (
            "Study is outside the declared canonical research scope or is a duplicate narrative/result artifact; current scientific conclusions are retained in the compact evidence register.",
            "research/EVIDENCE.md: noncanonical historical research is represented by a one-line index; no claim is promoted from its removed artifact.",
        )
    if p in {"Innovation.md", "task.md"}:
        return (
            "Superseded root-level narrative is replaced by the current claim boundary and next decisive experiment in REPORT.md.",
            "research/REPORT.md: Scope and claim boundary; Next decisive experiment.",
        )
    if p.startswith("reference/report/"):
        return (
            "Redundant historical report copy; the authoritative current synthesis is research/REPORT.md.",
            "research/REPORT.md: canonical release claims and limitations.",
        )
    if p.startswith("tests/"):
        return (
            "Historical or asset-dependent test is outside the asset-free core default and the three explicit current research scopes.",
            "research/REPORT.md: scientific evidence is bounded to the named canonical studies; missing inputs are reported as blocked.",
        )
    return (
        "Outside the production, core-test, current-study and necessary-input release closure.",
        "research/REPORT.md: Scope and claim boundary.",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    core_tests = set(pyproject["tool"]["pytest"]["ini_options"]["testpaths"])
    core_tests.discard("tests/test_state_evidence_followup.py")
    core_tests.add("tests/test_repository_shape.py")
    freeze = json.loads((ROOT / "research/viability_contrast/freeze10.json").read_text())
    freeze_paths = set(freeze["files"])
    freeze_paths.add("research/viability_contrast/freeze10.json")
    tracked = tracked_files()
    blobs = commit_blobs()
    keep = {p for p in tracked if explicit_keep(p, freeze_paths, core_tests)}
    delete = sorted(set(tracked) - keep)
    rows = []
    removed_bytes = 0
    for path in delete:
        full = ROOT / Path(path)
        size = full.stat().st_size
        blob = blobs[path]
        why, evidence = reason(path)
        rows.append({
            "path": path,
            "size_bytes": size,
            "sha256": sha256_file(full),
            "commit_blob": blob,
            "reason": why,
            "evidence_conclusion": evidence,
            "recovery": {"kind": "git_path", "commit": BASE, "path": path},
            "status": "PLANNED_DELETE",
        })
        removed_bytes += size
    post_edit_paths = {
        "cleanup/generate_pre_cleanup.py", "cleanup/PRE_CLEANUP_STATS.json", "cleanup/CLEANUP_MANIFEST.json",
        "tools/log_manifest.py", "tests/test_repository_shape.py", "tests/test_research_validation.py",
        "pyproject.toml", "README.md", "tools/registry.yaml", "tools/research_validation.py",
        "research/REPORT.md", "research/EVIDENCE.md", "log/INDEX.md", "log/20261008/README.md",
        "log/20261009/README.md",
    }
    rows = [row for row in rows if row["path"] not in post_edit_paths]
    retained_output_roots = {
        "paper_01286/state_readout_repair",
        "paper_01286/state_feedback_repair",
        "paper_01286/released_test",
        "decision_value_validation_20261009",
        "viability_contrast_20260928/prepared",
        "viability_contrast_20261008/run10_repair",
    }
    for path in sorted((ROOT / "outputs").rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        subpath = path.relative_to(ROOT / "outputs").as_posix()
        if any(subpath == keep or subpath.startswith(keep + "/") for keep in retained_output_roots):
            continue
        size = path.stat().st_size
        rows.append({
            "path": relative,
            "size_bytes": size,
            "sha256": sha256_file(path),
            "commit_blob": None,
            "reason": "Ignored local generated output is not read by any retained current verifier; canonical results and scientific limitations remain summarized in research/EVIDENCE.md.",
            "evidence_conclusion": "research/EVIDENCE.md: preserve only canonical study results and limitations; historical output copies do not add independent evidence.",
            "recovery": {"kind": "none", "note": "Ignored working-tree output has no Git blob or baseline commit recovery source."},
            "status": "PLANNED_DELETE_LOCAL_OUTPUT",
        })
    removed_bytes = sum(row["size_bytes"] for row in rows)
    tracked_bytes = sum((ROOT / Path(p)).stat().st_size for p in tracked)
    pack = git("count-objects", "-vH").decode().splitlines()
    object_stats = dict(line.split(": ", 1) for line in pack if ": " in line)
    pre = {
        "baseline_commit": BASE,
        "branch": "cleanup/max-compress-20261009",
        "tracked_file_count": len(tracked),
        "tracked_bytes": tracked_bytes,
        "tracked_python_file_count": sum(p.endswith(".py") for p in tracked),
        "tracked_python_lines": sum(len((ROOT / Path(p)).read_bytes().splitlines()) for p in tracked if p.endswith(".py")),
        "git_count_objects": object_stats,
        "planned_tracked_file_count": len(rows),
        "planned_tracked_bytes": removed_bytes,
        "planned_paths_include_untracked_or_ignored": False,
        "created_before_any_tracked_file_deletion": True,
    }
    manifest = {
        "baseline_commit": BASE,
        "created_before_any_tracked_file_deletion": True,
        "deletion_policy": "Only files absent from the reviewed production, core-test, canonical-study, manifest, verifier and frozen-input closure are included.",
        "planned_deletions": rows,
        "review_required": [
            {
                "path": "ignored local data/ and outputs/ not tracked at the baseline commit",
                "status": "REVIEW_REQUIRED",
                "reason": "These local files have no commit blob or Git recovery source; they were excluded from automatic deletion pending an explicit local-data recovery decision.",
            }
        ],
    }
    (ROOT / "cleanup/PRE_CLEANUP_STATS.json").write_text(json.dumps(pre, indent=2) + "\n", encoding="utf-8")
    (ROOT / "cleanup/CLEANUP_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tracked": len(tracked), "kept": len(keep), "planned_delete": len(rows), "planned_bytes": removed_bytes}))


if __name__ == "__main__":
    main()
