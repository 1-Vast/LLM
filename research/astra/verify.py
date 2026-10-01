"""Record scoped maestro regression checks and original/frozen input integrity."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


TESTS = [
    "research/astra", "tests/test_case_memory_integration.py",
    "tests/test_case_memory_forecast_modes.py", "tests/test_case_memory_orchestrator.py",
    "tests/test_case_memory_state_visibility.py", "tests/test_case_memory_scientific_boundaries.py",
    "tests/test_acquisition.py", "tests/test_discriminating_acquisition.py",
    "tests/test_decision_sensitive_acquisition.py", "tests/test_state_adapter.py",
    "tests/test_state_adapter_intervals.py", "tests/test_state_prospective_input.py",
    "tests/test_state_response_research.py", "tests/test_repository_shape.py",
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


PROMOTED_PATHS = {"src/agent/orchestrator.py", "src/agent/memory.py",
                  "src/maestro/case_update.py", "tools/datasets/state_prospective_input.py"}


def integrity(root, allow_promotion=False):
    astra = root / "research/astra"
    originals = json.loads((astra / "baseline_20261002/manifest.json").read_text())
    backup_matches = {name: digest(astra / "baseline_20261002" / (name + ".txt")) == expected
                      for name, expected in originals.items()}
    grid = astra / "results/20261002_paired_matrix_v1"
    frozen = json.loads((grid / "freeze.json").read_text())
    frozen_matches = {name: digest(name) == expected for name, expected in frozen["inputs"].items()}
    output_manifest = json.loads((grid / "manifest.json").read_text())
    output_matches = {name: digest(grid / name) == expected for name, expected in output_manifest.items()}
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", "src", "tools/datasets", "log/20261001"],
        cwd=root, text=True).splitlines()
    unauthorized = set(changed) - PROMOTED_PATHS if allow_promotion else set(changed)
    return dict(original_copy_matches=backup_matches, frozen_grid_input_matches=frozen_matches,
                grid_output_files=len(output_matches), grid_outputs_all_match=all(output_matches.values()),
                protected_tracked_changes=changed,
                unauthorized_protected_changes=sorted(unauthorized),
                all_match=all(backup_matches.values()) and all(frozen_matches.values())
                and all(output_matches.values()) and not unauthorized)


def run(out, *, allow_promotion=False, full=False):
    root = Path(__file__).resolve().parents[2]
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    sources = {str(p.relative_to(root)): digest(p) for p in (root / "research/astra").glob("*.py")}
    if allow_promotion:
        sources.update({p: digest(root / p) for p in PROMOTED_PATHS})
    before = integrity(root, allow_promotion)
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q",
               *(["tests", "research/astra"] if full else TESTS),
               "--junitxml", str(out / "pytest.xml")]
    (out / "freeze.json").write_text(json.dumps(dict(
        frozen_at_utc=datetime.now(timezone.utc).isoformat(), source_hashes=sources,
        command=command, integrity_before=before), indent=2) + "\n", encoding="utf-8")
    started = time.perf_counter()
    done = subprocess.run(command, cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=600)
    (out / "stdout.txt").write_text(done.stdout, encoding="utf-8")
    (out / "stderr.txt").write_text(done.stderr, encoding="utf-8")
    cases = list(ET.parse(out / "pytest.xml").getroot().iter("testcase"))
    counts = dict(total=len(cases), failures=sum(c.find("failure") is not None for c in cases),
                  errors=sum(c.find("error") is not None for c in cases),
                  skipped=sum(c.find("skipped") is not None for c in cases))
    counts["passed"] = counts["total"] - sum(counts[k] for k in ("failures", "errors", "skipped"))
    research_cases = [c for c in cases if c.get("classname", "").startswith("research.astra.")]
    after = integrity(root, allow_promotion)
    source_matches = all(digest(root / name) == value for name, value in sources.items())
    receipt = dict(command=command, python=sys.executable, python_version=sys.version,
                   git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                   tests=counts, research_test_count=len(research_cases), returncode=done.returncode,
                   elapsed_seconds=time.perf_counter() - started, integrity_after=after,
                   source_hashes_unchanged=source_matches,
                   all_passed=done.returncode == 0 and before["all_match"] and after["all_match"] and source_matches,
                   full_repository_suite="tests plus ASTRA" if full else "not_run; scoped relevant regressions only")
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if receipt["all_passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-promotion", action="store_true",
                        help="Allow only the four explicitly reviewed existing production/tool files")
    parser.add_argument("--full", action="store_true", help="Run all tests/ plus ASTRA contracts")
    args = parser.parse_args()
    raise SystemExit(run(args.out, allow_promotion=args.allow_promotion, full=args.full))
