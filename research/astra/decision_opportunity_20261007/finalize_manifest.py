"""Write a new dated follow-up manifest; never repair old hashes in place."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLOCKS = (HERE, HERE.with_name("efficiency_followup_20261007"),
          HERE.with_name("cheap_data_direction_20261007"))


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise ValueError("Use a new manifest path")
    preservation = load(HERE / "PRIOR_PRESERVATION.json")["files"]
    assert all((ROOT / name).is_file() and digest(ROOT / name) == sha
               for name, sha in preservation.items()), "Predecessor bytes changed"
    child_checks = []
    for block in BLOCKS[1:]:
        manifest = block / "RUN_MANIFEST.json"
        records = load(manifest)["artifacts"]
        entries = records.items() if isinstance(records, dict) else (
            (str((block / r["path"]).relative_to(ROOT)), r["sha256"]) for r in records)
        checked = 0
        for name, expected in entries:
            assert digest(ROOT / name) == expected, "Child artifact changed: " + name
            checked += 1
        child_checks.append(dict(path=manifest.relative_to(ROOT).as_posix(),
                                 sha256=digest(manifest), verified_artifacts=checked))
    sources = ["src/agent/tool_runtime.py", "tests/test_tool_catalog_efficiency.py",
               "tools/README.md", "pyproject.toml", ".gitattributes", "research/astra/.gitignore",
               "research/CURRENT_INDEX.md", "research/README.md", "research/astra/README.md",
               "log/20261007/README.md"]
    paths = {ROOT / name for name in sources}
    for block in BLOCKS:
        paths.update(p for p in block.rglob("*") if p.is_file()
                     and not any(part in {"__pycache__", ".pytest_cache"} for part in p.parts)
                     and p != out and p.name != "FINAL_VERIFICATION.json")
    names = sorted(p.relative_to(ROOT).as_posix() for p in paths)
    ignored = subprocess.run(["git", "check-ignore", "--stdin", "-z"], cwd=ROOT,
                             input="\0".join(names) + "\0", text=True, capture_output=True)
    assert ignored.returncode in (0, 1), "Git distribution check failed"
    local = set(ignored.stdout.split("\0"))
    artifacts = {name: dict(sha256=digest(ROOT / name), bytes=(ROOT / name).stat().st_size,
                            included_by_git_ignore_policy=name not in local) for name in names}
    tests = []
    for name, scope in (("research/astra/efficiency_followup_20261007/core_final.xml", "default core"),
                        ("research/astra/decision_opportunity_20261007/final_study_contracts.xml", "study, shape, scope")):
        suite = ET.parse(ROOT / name).getroot().find("testsuite")
        assert int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
        tests.append(dict(path=name, scope=scope, **suite.attrib))
    manifest = dict(schema="state_decision_efficiency_followup_v1",
        created_utc=datetime.now(timezone.utc).isoformat(),
        git_baseline_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        workspace_uncommitted=True, production_change_this_task="Scoped dependency-byte reuse in tool_runtime.py",
        model_foundation=dict(checkpoint="official pretrained final.ckpt",
            sha256="2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3",
            new_inference_or_weight_updates=0),
        execution_sources=dict(before="research/astra/efficiency_followup_20261007/tool_runtime_before.py.txt",
            after="research/astra/efficiency_followup_20261007/tool_runtime_after.py.txt",
            research_drift_receipt="SOURCE_REPAIR.json", transfer_pins="TRANSFER_PROTOCOL.json",
            byte_identity="Snapshots preserve executed source bytes; LF-normalized Git source is a separate identity"),
        canonical_research_runs=[dict(path="development_run1", episodes=90, simulated_profiles=930),
            dict(path="trust_run1", episodes=12, simulated_profiles=140),
            dict(path="transfer_run1", episodes=15, simulated_profiles=177)],
        diagnostic_runs=dict(exact_packet="packet_replay2", isolated_asset_replays="affordable_replay_check1",
            failed_packets=["compact_packet", "packet_replay1"], budget_frontier_points=144,
            new_independent_observations=0),
        resource_receipts=["development_run1/SUMMARY.json", "trust_run1/SUMMARY.json",
            "transfer_run1/SUMMARY.json", "transfer_run1/COST_INTERPRETATION.json",
            "../cheap_data_direction_20261007/RUN_MANIFEST.json"],
        new_provider_calls=0, new_physical_measurements=0,
        source_exposure="All five cells previously exposed; fixed transferred task is exploratory, not untouched confirmation",
        scientific_result="Development cost-saving signal failed transfer; equal-cost signal concentrated; shared trust update did not win",
        test_scopes=tests, test_overlap="Scopes overlap; do not sum counts",
        predecessor_preservation=dict(files=len(preservation), mismatches=0, receipt="PRIOR_PRESERVATION.json"),
        unchanged_child_manifests=child_checks,
        artifacts=artifacts,
        omissions="Only generated Python/pytest caches and this self-referential manifest/verification are omitted; local raw arrays and case DBs are hash-pinned but not required in Git")
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(artifacts=len(artifacts), preserved=len(preservation),
                         git_distributable=sum(r["included_by_git_ignore_policy"] for r in artifacts.values()))))


if __name__ == "__main__":
    main()
