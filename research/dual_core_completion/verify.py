"""Verify the engineering workflow and preserve historical audit inputs and outputs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "outputs/identifiability_round2_20260930"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    ledger = json.loads((AUDIT / "delivery_ledger.json").read_text())
    frozen = {**ledger["original_inputs_sha256"], **ledger["outputs_sha256"]}
    frozen["outputs/identifiability_round2_20260930/delivery_ledger.json"] = sha(AUDIT / "delivery_ledger.json")
    mismatches = []
    for rel, expected in frozen.items():
        path = ROOT / rel.replace("\\", "/")
        if not path.is_file() or sha(path) != expected:
            mismatches.append(rel)
    write(out / "frozen_integrity.json", {
        "passed": not mismatches, "checked_files": len(frozen), "mismatches": mismatches,
        "expected_sha256": frozen, "ledger_sha256": sha(AUDIT / "delivery_ledger.json"),
        "scope": "Historical research files, data and frozen output snapshots; current production source is allowed to change."})
    if mismatches:
        raise RuntimeError("historical_frozen_artifact_changed")
    readiness_path = ROOT / "research/dual_core_completion/data_readiness.json"
    readiness = json.loads(readiness_path.read_text())
    readiness_mismatches = [name for name, item in readiness["sources"].items()
                            if sha(ROOT / item["path"]) != item["sha256"]]
    write(out / "data_readiness_integrity.json", {
        "passed": not readiness_mismatches, "checked_sources": len(readiness["sources"]),
        "mismatches": readiness_mismatches, "readiness_sha256": sha(readiness_path),
        "scope": "Source identities of the data qualification review; not a fresh recomputation of every reported statistic."})
    if readiness_mismatches:
        raise RuntimeError("data_readiness_source_changed")
    files = [p for folder in ("src", "tests", "tools", "research/dual_core_completion")
             for p in (ROOT / folder).rglob("*.py")]
    source = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "tests",
               "-k", "not small_response_fit and not training_refuses",
               "--tb=short", "--junitxml", str(out / "tests.xml")]
    write(out / "execution.json", {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "code_sha256": source, "command": command,
        "entrypoint_command": [sys.executable, *sys.argv],
        "data_readiness_sha256": sha(readiness_path),
        "environment": {"python": sys.version, "interpreter": sys.executable,
                        "packages": {p: importlib.metadata.version(p) for p in
                                     ("pytest", "numpy", "pandas", "scipy", "torch", "arc-state")}},
        "exclusions": "Two existing constructed model-fitting tests are excluded; no new research model is fitted.",
        "interpretation": "Contract and execution correctness, including synthetic fixtures. No biological gain or external validity claim."})
    with (out / "pytest.txt").open("xb") as f:
        completed = subprocess.run(command, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    changed = [rel for rel, expected in source.items() if sha(ROOT / rel) != expected]
    tree = ElementTree.parse(out / "tests.xml").getroot()
    suites = [tree] if tree.tag == "testsuite" else list(tree.findall("testsuite"))
    counts = {key: sum(int(s.get(key, "0")) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    write(out / "validation.json", {
        "passed": completed.returncode == 0 and not changed, "pytest_exit_code": completed.returncode,
        "counts": counts, "changed_sources_during_verification": changed,
        "output_sha256": {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({"exit_code": completed.returncode, "counts": counts,
                      "frozen_files_unchanged": len(frozen), "changed_sources": changed}), flush=True)
    return completed.returncode or bool(changed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Fresh write-once verification directory.")
    raise SystemExit(run(parser.parse_args().out))
