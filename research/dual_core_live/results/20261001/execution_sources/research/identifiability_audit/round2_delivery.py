"""Seal final delivery without changing earlier audit artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from research.identifiability_audit import round2 as R
from research.identifiability_audit.round2_report import render


def run(out: Path):
    original_log = subprocess.check_output(
        ["git", "show", "11f7e57:log/20260930/README.md"], cwd=R.ROOT)
    log = R.ROOT / "log/20260930/README.md"
    report = out / "ROUND2_REPORT.md"
    logged = log.read_bytes()
    assert logged.startswith(original_log), "dated log original prefix changed"
    assert logged[len(original_log):].decode("utf-8") == render(out), "dated section does not reproduce"
    assert report.read_text(encoding="utf-8") == render(out), "report does not reproduce"
    recovery = json.loads((out / "recovery.json").read_text())
    for item in recovery:
        if item["path"] != "log/20260930/README.md":
            assert R.file_hash(R.ROOT / item["path"]) == item["sha256"], item["path"]
    original = json.loads((out / "round1_input_hashes.json").read_text())
    for rel, expected in original.items():
        assert R.file_hash(R.ROOT / rel) == expected, "original changed: " + rel
    predeclared = json.loads((out / "interventions/predeclared.json").read_text())
    src = {rel: sha for rel, sha in predeclared["inputs"].items() if rel.startswith("src/")}
    for rel, expected in src.items():
        assert R.file_hash(R.ROOT / rel) == expected, "production changed: " + rel
    validation = json.loads((out / "result_validation.json").read_text())
    assert validation["passed"]
    tests = ElementTree.parse(out / "delivery_tests.xml").getroot().find("testsuite")
    assert tests is not None and all(tests.get(k) == "0" for k in ("failures", "errors", "skipped"))

    source_files = sorted((R.ROOT / "research/identifiability_audit").glob("*.py")) + [
        R.ROOT / "research/identifiability_audit/README.md",
        R.ROOT / "tests/test_identifiability_audit.py",
        R.ROOT / "tests/test_identifiability_round2.py", log, R.ROOT / "log/INDEX.md"]
    snapshot = out / "delivery_source"
    snapshot.mkdir(exist_ok=False)
    source_hashes = {}
    for path in source_files:
        rel = path.relative_to(R.ROOT)
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as f:
            f.write(path.read_bytes())
        source_hashes[rel.as_posix()] = R.file_hash(path)
        assert R.file_hash(target) == source_hashes[rel.as_posix()]
    outputs = {p.relative_to(R.ROOT).as_posix(): R.file_hash(p) for p in sorted(out.rglob("*"))
               if p.is_file() and not any("tmp" in part or part == "__pycache__"
                                         for part in p.relative_to(out).parts)}
    earlier = json.loads((out / "artifact_ledger.json").read_text())
    R.save(out / "delivery_ledger.json", {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=R.ROOT, text=True).strip(),
        "command": [sys.executable, *sys.argv], "environment": earlier["environment"],
        "source_sha256": source_hashes, "outputs_sha256": outputs,
        "original_inputs_sha256": original, "unchanged_production_sha256": src,
        "initial_execution_source_sha256": earlier["initial_execution_source_sha256"],
        "command_receipts": earlier["command_receipts"] + ["ROUND2_REPORT.md", "delivery_tests.xml"],
        "checks": ["original Round 1 log is byte-exact prefix; appended section equals final report text",
                   "final report reproduces exactly from sealed results",
                   "all inherited source/test files and original inputs remain byte-exact",
                   "all manifested production src hashes unchanged",
                   "every final artifact and delivered source has full SHA-256"],
        "path_validation": validation["counts"],
        "tests": {"delivery_contracts_and_log_layout": int(tests.get("tests")),
                  "earlier_planner_selector_state_scope": 50, "complete_production_suite_rerun": False},
        "scope": "This ledger seals post-validation physical/risk supplements, report and code. Earlier "
                 "ledgers/outputs are preserved. The ledger does not hash itself. Per-query digest validation "
                 "remains sampled as explicitly recorded; every file is fully hashed. Exposure and not-run "
                 "limitations are in the report."})
    print(json.dumps({"passed": True, "sealed_files": len(outputs), "source_files": len(source_hashes),
                      "production_files_unchanged": len(src)}), flush=True)


if __name__ == "__main__":
    run(R.OUT)
