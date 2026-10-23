"""Final append-only review seal and prior-seal verification."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"
output = OUT / "FINAL_REVIEW_SEAL.json"
if output.exists():
    raise FileExistsError(output)
verified = []
for name in ["INDEPENDENT_SEAL.json", "OPPOSING_STENCIL_SEAL.json", "OPPOSING_BIOLOGY_SEAL.json"]:
    seal = json.loads((OUT / name).read_text(encoding="utf-8"))
    for entry in seal["files"]:
        actual = hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest()
        assert actual == entry["sha256"], entry["path"]
        verified.append({"seal": name, "path": entry["path"], "pass": True})
paths = sorted(p for p in OUT.iterdir() if p.is_file() and p != output)
paths += sorted((ROOT / "research/native_improver_20261022").glob("*.py"))
record = {"time_utc": datetime.now(timezone.utc).isoformat(), "prior_seal_bindings": verified,
          "current_files": [{"path": str(p), "bytes": p.stat().st_size,
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
          "new_biological_accesses": 0, "new_predictive_fits": 0, "new_api_calls": 0}
output.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({"seal": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                  "prior_bindings_passed": len(verified), "current_files": len(paths)}, indent=2))
