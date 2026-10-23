"""Freeze before response use and verify immutable historical/phase evidence."""
import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from prepare import LOG, ROOT, sha, write, ARCHIVE

CODE = Path(__file__).resolve().parent
PRIOR = ("functional_dynamics_gate", "dead_stock_information_gate", "stack_raw_qualification",
         "stack_conditional_information", "intervention_program_renewal")


def historical_checks():
    checks = []
    for phase in PRIOR:
        manifest = json.loads((ROOT / f"log/20261022/{phase}/FINAL_FILE_INVENTORY.json").read_text(encoding="utf-8"))
        for item in manifest["files"]:
            path = ROOT / item["path"]
            checks.append({"path": item["path"], "passed": path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]})
    if len(checks) != 460 or not all(c["passed"] for c in checks):
        raise RuntimeError("Historical frozen evidence changed")
    return checks


def freeze():
    output = LOG / "PRE_RESPONSE_FREEZE.json"
    if output.exists() or (LOG / "INPUTS_STARTED.json").exists():
        raise RuntimeError("Cannot replace freeze or freeze after real numeric use")
    historical_checks()
    names = ["PROTOCOL.md", "MEASURED_PROTOCOL.md", "DESIGN.json", "EPISODES.json", "SELECTED_DESIGN.json", "FEATURE_SCHEMA.json",
             "ADVOCATE_INDEPENDENT.md", "DATA_INDEPENDENT.md", "SKEPTIC_INDEPENDENT.md",
             "ADVOCATE_PROTOCOL_CROSS.md", "SKEPTIC_PROTOCOL_CROSS.md", "SKEPTIC_FINAL_IMPLEMENTATION_REVIEW.md", "DATA_IMPLEMENTATION_REVIEW.md", "DATA_DRIVER_CROSS_RECHECK.md",
             "DRIVER_SYNTHETIC_03.txt", "PREPARE_SYNTHETIC_TESTS_04.txt", "MODELS_SYNTHETIC.json", "METRICS_SYNTHETIC.json"]
    paths = sorted(CODE.glob("*.py")) + [LOG / name for name in names] + [ARCHIVE]
    for path in CODE.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    write(output, {"utc": datetime.now(timezone.utc).isoformat(),
          "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
          "historical_files_verified": 460, "test_target_conversion": False,
          "scope": "ordinary structure opportunity only; no novelty/world/agent/RSI performance claim"})
    print(json.dumps({"freeze": str(output), "files": len(paths), "historical_unchanged": 460}))


def final():
    checks = historical_checks()
    freeze_receipt = json.loads((LOG / "PRE_RESPONSE_FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze_receipt["files"].items():
        checks.append({"path": name, "passed": sha(ROOT / name) == expected})
    for path in CODE.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    for receipt_name in ("INPUTS_RECEIPT.json", "TEST_TARGETS_RECEIPT.json"):
        path = LOG / receipt_name
        if path.exists():
            receipt = json.loads(path.read_text(encoding="utf-8"))
            for name, expected in receipt["outputs_sha256"].items():
                checks.append({"path": name, "passed": sha(LOG / name) == expected})
    seal_path = LOG / "PREDICTIONS_SEAL.json"
    if seal_path.exists():
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        for name, field in (("TEST_PREDICTIONS.npz", "predictions_sha256"), ("TEST_ACTIONS.json", "actions_sha256"), ("SELECTION.json", "selection_sha256")):
            checks.append({"path": name, "passed": sha(LOG / name) == seal[field]})
    diff = subprocess.run(["git", "diff", "--check", "--", str(CODE.relative_to(ROOT)), str(LOG.relative_to(ROOT)), "research/REPORT.md", "log/README.md"], cwd=ROOT, text=True, capture_output=True)
    checks.append({"path": "scoped_git_diff_check", "passed": diff.returncode == 0})
    passed = all(c["passed"] for c in checks)
    write(LOG / "FINAL_INTEGRITY.json", {"passed": passed, "checks": checks,
          "prior_inventoried_files_unchanged": 460, "phase_python_files_parse": len(list(CODE.glob("*.py"))),
          "scoped_diff_stdout": diff.stdout, "scoped_diff_stderr": diff.stderr})
    if not passed:
        raise RuntimeError("Integrity verification failed")
    files = sorted(p for folder in (LOG, CODE) for p in folder.rglob("*") if p.is_file() and p.name != "FINAL_FILE_INVENTORY.json")
    write(LOG / "FINAL_FILE_INVENTORY.json", {"utc": datetime.now(timezone.utc).isoformat(), "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]})
    print(json.dumps({"passed": passed, "checks": len(checks), "prior_files": 460, "phase_files": len(files)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("freeze", "final"))
    args = parser.parse_args()
    (freeze if args.stage == "freeze" else final)()
