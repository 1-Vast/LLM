"""Offline integrity audit of this review's retained sources; no outcome access."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("D:/MAESTRO/log/20261022/functional_dynamics_gate/skeptic")
rows = []
for path in sorted(BASE.glob("*_RECEIPT.json")):
    receipt = json.loads(path.read_text(encoding="utf-8"))
    body_path = BASE / (path.name.removesuffix("_RECEIPT.json") + ".body")
    body = body_path.read_bytes()
    rows.append({"receipt": path.name, "status": receipt.get("status"),
                 "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                 "pass": len(body) == receipt["retained_bytes"]
                 and hashlib.sha256(body).hexdigest() == receipt["sha256"]
                 and receipt["complete_body"] and receipt["status"] == 200
                 and len(body) <= 3 * 1024 * 1024
                 and receipt["timeout_seconds"] == 25
                 and receipt["retries"] == 0 and not receipt["redirects_allowed"]})
report = {"utc": datetime.now(timezone.utc).isoformat(), "requests": len(rows),
          "retained_bytes": sum(row["bytes"] for row in rows), "sources": rows,
          "pass": len(rows) == 6 and all(row["pass"] for row in rows),
          "independent_draft_sha256": hashlib.sha256((BASE / "INDEPENDENT.md").read_bytes()).hexdigest(),
          "scope": "Source integrity only; no biological/model/novelty-performance validation"}
(BASE / "SOURCE_AUDIT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
