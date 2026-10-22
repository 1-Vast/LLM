"""Bind final messages additively without modifying the completed review seal."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"
output = OUT / "POSTSEAL_REJOINDERS_SEAL.json"
if output.exists():
    raise FileExistsError(output)
prior = json.loads((OUT / "FINAL_REVIEW_SEAL.json").read_text(encoding="utf-8"))
for entry in prior["current_files"]:
    assert hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
paths = [OUT / "FINAL_REVIEW_SEAL.json", OUT / "POSTSEAL_REJOINDERS.md", Path(__file__)]
record = {"time_utc": datetime.now(timezone.utc).isoformat(), "prior_final_files_verified": len(prior["current_files"]),
          "files": [{"path": str(p), "bytes": p.stat().st_size,
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
output.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({"seal": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))
