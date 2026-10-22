"""Verify reported endpoint tables and preserve adjacent finalized inventories."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/az_paid_reference_gate"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    checks = []
    scores = json.loads((LOG / "TEST_METRICS.json").read_text(encoding="utf-8"))
    report = (LOG / "RESULTS.md").read_text(encoding="utf-8")
    families = {
        "Bliss": "bliss", "Historical pair-dose": "historical",
        "Effect-coordinate residual": "effect", "Dose-coordinate residual": "dose",
        "Full direct": "direct", "Without-mono direct": "combo_direct",
        "Effect + local offset family": "effect_offset",
        "Dose + local offset family": "dose_offset",
        "Full direct + local offset family": "direct_offset",
        "Validation mixture": "mixture", "Finite-menu enumerator": "enumerator",
    }
    rows = {cells[0]: cells[1:] for line in report.splitlines()
            if line.startswith("| ")
            and (cells := [cell.strip() for cell in line.strip("|").split("|")])}
    for label, family in families.items():
        expected = [f"{scores[family + '__mae']['mae']:.9f}",
                    f"{scores[family + '__utility']['utility']:.9f}",
                    f"{scores[family + '__utility']['regret']:.9f}"]
        checks.append({"check": "reported_endpoint_table:" + family,
                       "passed": rows.get(label) == expected})
    gates = json.loads((LOG / "GATES.json").read_text(encoding="utf-8"))["gates"]
    checks.append({"check": "reported_STOP_matches_gates", "passed":
                   gates == {"coverage": True, "mae": False, "utility": False, "both": False}
                   and "STOP_THIS_EXACT_CONFIGURATION_FOR_AGENT_RSI_EXPANSION" in
                   (LOG / "DECISION.md").read_text(encoding="utf-8")})
    for relative, expected_count in (
            ("log/20261022/rsi_later_task_literature/FINAL_FILE_INVENTORY.json", 181),
            ("log/20261022/az_chemical_identity/INTEGRITY.json", 23)):
        inventory = json.loads((ROOT / relative).read_text(encoding="utf-8"))["files"]
        checks.append({"check": relative + ":count", "passed": len(inventory) == expected_count})
        for item in inventory:
            path = ROOT / item["path"]
            checks.append({"check": item["path"], "passed": path.is_file()
                           and path.stat().st_size == item["bytes"]
                           and digest(path) == item["sha256"]})
    output = LOG / "REPORTING_INTEGRITY.json"
    if output.exists():
        raise FileExistsError(output)
    passed = all(check["passed"] for check in checks)
    output.write_text(json.dumps({"passed": passed, "checks": checks,
                                  "scope": "reporting and already finalized adjacent files only"},
                                 indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "checks": len(checks),
                      "failed": [check for check in checks if not check["passed"]]}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
