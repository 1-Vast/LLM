"""Seal the independent opinion once; do not alter an existing seal."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "log/20261023/hcc_task_qualification/method/INDEPENDENT.md"
OUT = REPORT.with_name("INDEPENDENT_SEAL.json")
if OUT.exists():
    raise SystemExit("Refusing to overwrite independent seal")
paths = [REPORT, Path(__file__).resolve()]
result = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "scope": "independent opinion and sealing code; no numerical data access",
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
