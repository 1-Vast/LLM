"""Verify completed qualification evidence and inventory only this phase."""
import ast
from datetime import datetime, timezone
import json
import subprocess

from historical_choice_audit import LOG, ROOT, sha, write
from preservation import verify


def main():
    checks = []
    baseline = json.loads((LOG / "BASELINE_PRESERVATION.json").read_text(encoding="utf-8"))
    prior = verify()
    checks.append({"name": "888_prior_files_unchanged", "passed": prior["passed"]
                   and len(prior["checks"]) == 888
                   and prior["manifest_sha256"] == baseline["manifest_sha256"]})
    freeze = json.loads((LOG / "HISTORICAL_AUDIT_FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["files"].items():
        checks.append({"name": name, "passed": sha(ROOT / name) == expected})
    audit = json.loads((LOG / "HISTORICAL_CHOICE_AUDIT.json").read_text(encoding="utf-8"))
    comparison = json.loads((LOG / "skeptic/HISTORICAL_COMPARISON.json").read_text(encoding="utf-8"))
    checks.append({"name": "historical_choice_audit_independent_comparison", "passed":
                   comparison["passed"] and comparison["checks"] == 3161
                   and comparison["maxdiff"] < 1e-12 and audit["campaigns"] == 36
                   and not audit["descriptive_both_direction_screen"]
                   and audit["frozen_inputs_unchanged"]})
    checks.append({"name": "root_audit_binding_independent_comparison", "passed":
                   comparison["source_hashes"]["root_frozen_audit"] == sha(LOG / "HISTORICAL_CHOICE_AUDIT.json")})
    source_count = 0
    statuses = []
    for reviewer in ("advocate", "skeptic"):
        receipts = [json.loads(line) for line in (LOG / reviewer / "HTTP_RECEIPTS.jsonl").read_text(encoding="utf-8").splitlines()]
        for receipt in receipts:
            path = LOG / reviewer / (receipt["name"] + ".body")
            checks.append({"name": f"primary_body:{reviewer}:{receipt['name']}", "passed":
                           path.stat().st_size == receipt["bytes"] and sha(path) == receipt["sha256"]})
            source_count += 1
            statuses.append(receipt["status"])
    receipt = json.loads((LOG / "data/prism_primary.http.json").read_text(encoding="utf-8"))
    body = LOG / "data/prism_primary.body"
    checks.append({"name": "retained_HTTP500_body", "passed": body.stat().st_size == receipt["bytes"]
                   and sha(body) == receipt["sha256"] and receipt["status"] == 500})
    source_count += 1
    statuses.append(receipt["status"])
    checks.append({"name": "bounded_request_receipts", "passed": source_count == 9
                   and statuses.count(200) == 8 and statuses.count(500) == 1})
    for reviewer in ("advocate", "skeptic", "data"):
        for name in ("INDEPENDENT.md", "CROSS.md"):
            path = LOG / reviewer / name
            checks.append({"name": f"saved_review:{reviewer}/{name}", "passed": path.is_file() and path.stat().st_size > 100})
    code = ROOT / "research/update_value_qualification_20261022"
    for path in code.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8-sig"))
    diff = subprocess.run(["git", "diff", "--check", "--", str(code.relative_to(ROOT)), str(LOG.relative_to(ROOT)),
                           "research/REPORT.md", "log/README.md"], cwd=ROOT, capture_output=True, text=True)
    checks.append({"name": "scoped_diff_check", "passed": diff.returncode == 0})
    passed = all(row["passed"] for row in checks)
    write(LOG / "FINAL_INTEGRITY.json", {"utc": datetime.now(timezone.utc).isoformat(), "passed": passed,
          "checks": checks, "prior_inventoried_files_unchanged": 888,
          "python_files_parse": len(list(code.glob("*.py"))), "new_HTTP_receipts": source_count,
          "new_fits": 0, "new_measurements": 0, "new_provider_calls": 0,
          "diff_stdout": diff.stdout, "diff_stderr": diff.stderr})
    if not passed:
        raise RuntimeError("Phase integrity check failed")
    files = sorted(path for folder in (LOG, code) for path in folder.rglob("*")
                   if path.is_file() and path.name != "FINAL_FILE_INVENTORY.json")
    write(LOG / "FINAL_FILE_INVENTORY.json", {"utc": datetime.now(timezone.utc).isoformat(), "files": [
        {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files]})
    print(json.dumps({"passed": passed, "checks": len(checks), "prior_files": 888, "phase_files": len(files)}))


if __name__ == "__main__":
    main()
