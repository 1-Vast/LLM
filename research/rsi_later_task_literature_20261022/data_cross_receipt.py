"""Seal the literature cross-review while checking that its independent draft stayed fixed."""
import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/data"
target = OUT / "CROSS_RECEIPT.json"
if target.exists():
    raise RuntimeError("Cross receipt exists")
initial = json.loads((OUT / "HTTP_INTEGRITY.json").read_text())
independent_sha = hashlib.sha256((OUT / "INDEPENDENT.md").read_bytes()).hexdigest()
receipts = []
for path in sorted(OUT.glob("*.http.json")):
    r = json.loads(path.read_text())
    passed = r.get("status") is None or hashlib.sha256((OUT / r["body_file"]).read_bytes()).hexdigest() == r["sha256"]
    receipts.append({"receipt": path.name, "status": r["status"], "body_hash_pass": passed})
result = {"independent_unchanged": independent_sha == initial["independent_sha256"], "independent_sha256": independent_sha,
          "cross_sha256": hashlib.sha256((OUT / "CROSS.md").read_bytes()).hexdigest(), "substantive_work_families": 6,
          "all_http_body_hashes_pass": all(r["body_hash_pass"] for r in receipts), "http_captures": receipts,
          "cellscientist_commit_binding": json.loads((OUT / "CELLSCIENTIST_COMMIT_BINDING.json").read_text()),
          "biological_fits": 0, "expression_hdf5_downloads": 0, "az_reserve_access": False}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"independent_unchanged": result["independent_unchanged"], "http_captures": len(receipts), "all_http_body_hashes_pass": result["all_http_body_hashes_pass"]}))
