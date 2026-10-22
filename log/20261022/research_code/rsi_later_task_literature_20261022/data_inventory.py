"""Verify saved public HTTP bodies and freeze the independent source audit receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/rsi_later_task_literature/data"
target = OUT / "HTTP_INTEGRITY.json"
if target.exists():
    raise RuntimeError("HTTP integrity receipt exists")
records = []
for meta in sorted(OUT.glob("*.http.json")):
    r = json.loads(meta.read_text(encoding="utf-8"))
    body = OUT / r["body_file"] if "body_file" in r else None
    passed = (body is None and r["status"] is None) or (body.exists() and hashlib.sha256(body.read_bytes()).hexdigest() == r["sha256"])
    records.append({"receipt": meta.name, "status": r["status"], "body_hash_pass": bool(passed), "url": r["requested_url"]})
independent = OUT / "INDEPENDENT.md"
result = {"utc": datetime.now(timezone.utc).isoformat(), "work_families": ["State", "CellFlow", "Tahoe-100M", "Virtual Cell Challenge", "CellScientist", "Biomni/Biomni-R0"],
          "substantive_work_count": 6, "http_captures": records, "all_http_body_hashes_pass": all(r["body_hash_pass"] for r in records),
          "independent_sha256": hashlib.sha256(independent.read_bytes()).hexdigest(), "new_dataset_expression_or_hdf5_downloads": 0,
          "model_fits": 0, "az_or_reserve_access": False, "authentication_used": False}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"http_captures": len(records), "all_http_body_hashes_pass": result["all_http_body_hashes_pass"], "independent_sha256": result["independent_sha256"]}))
