"""Independently bind retained primary-source bodies and review artifacts."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
LOG = ROOT / "log/20261022/rsi_later_task_literature"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    receipts = []
    for folder, ledger in (("advocate", "SOURCE_RECEIPTS.jsonl"), ("skeptic", "HTTP_RECEIPTS.jsonl")):
        receipts.extend((folder, json.loads(line)) for line in (LOG / folder / ledger).read_text(encoding="utf-8").splitlines() if line.strip())
    receipts.extend(("data", json.loads(path.read_text(encoding="utf-8"))) for path in sorted((LOG / "data").glob("*.http.json")))
    checks, missing = [], []
    for folder, receipt in receipts:
        if not receipt.get("sha256"):
            missing.append({"folder": folder, "url": receipt.get("url", receipt.get("requested_url")),
                            "status": receipt.get("status"), "error_type": receipt.get("error_type")})
            continue
        if "body_file" in receipt:
            path = LOG / folder / receipt["body_file"]
        else:
            path = ROOT / receipt.get("body", receipt.get("body_path"))
        checks.append({"path": path.relative_to(ROOT).as_posix(),
                       "passed": path.exists() and path.stat().st_size == receipt["bytes"] and sha(path) == receipt["sha256"]})
    for path in CODE.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    for folder in ("advocate", "skeptic", "data"):
        for name in ("INDEPENDENT.md", "CROSS.md"):
            checks.append({"path": f"{folder}/{name}", "passed": (LOG / folder / name).exists()})
    passed = all(c["passed"] for c in checks)
    write(LOG / "FINAL_INTEGRITY.json", {"utc": datetime.now(timezone.utc).isoformat(), "passed": passed,
          "checks": checks, "retained_receipt_rows": len(receipts), "body_checks": sum(".body" in c["path"] for c in checks),
          "status_counts": dict(Counter(str(r.get("status")) for _, r in receipts)),
          "receipts_without_body_hash": missing,
          "transport_attempt_count": "Not reconstructed from receipt rows; advocate discloses initial discovery parsing/capture gaps",
          "new_biological_fits": 0, "new_dataset_response_conversion": False,
          "note": "Verifies retained bytes and files, not scientific truth, exhaustive novelty or reproduced paper results"})
    if not passed:
        raise RuntimeError("Literature integrity failures: " + str([c for c in checks if not c["passed"]]))
    files = sorted(p for folder in (CODE, LOG) for p in folder.rglob("*") if p.is_file() and p.name != "FINAL_FILE_INVENTORY.json")
    write(LOG / "FINAL_FILE_INVENTORY.json", {"utc": datetime.now(timezone.utc).isoformat(), "files": [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]})
    print(json.dumps({"passed": passed, "checks": len(checks), "phase_files": len(files), "receipt_rows": len(receipts)}))


if __name__ == "__main__":
    main()
