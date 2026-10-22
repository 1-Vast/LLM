"""Read-only validation of completed-phase inventories; receipts stay in this phase."""
import argparse
import json

from historical_choice_audit import LOG, ROOT, sha, write


MANIFESTS = [f"log/20261022/{phase}/FINAL_FILE_INVENTORY.json" for phase in (
    "functional_dynamics_gate", "dead_stock_information_gate", "stack_raw_qualification",
    "stack_conditional_information", "intervention_program_renewal", "az_paid_reference_gate",
    "rsi_later_task_literature")] + ["log/20261022/az_chemical_identity/INTEGRITY.json"]


def verify():
    checks, manifests = [], {}
    for name in MANIFESTS:
        manifests[name] = sha(ROOT / name)
        inventory = json.loads((ROOT / name).read_text(encoding="utf-8"))
        for item in inventory["files"]:
            path = ROOT / item["path"]
            checks.append({"path": item["path"], "passed": path.is_file()
                           and path.stat().st_size == item["bytes"] and sha(path) == item["sha256"]})
    passed = all(check["passed"] for check in checks)
    return {"passed": passed, "checks": checks, "manifest_sha256": manifests}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label", choices=("BASELINE", "FINAL"))
    args = parser.parse_args()
    result = verify()
    write(LOG / (args.label + "_PRESERVATION.json"), result)
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "failed": [row for row in result["checks"] if not row["passed"]]}))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
