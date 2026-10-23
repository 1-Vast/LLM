"""Freeze exact acquisition/projection contract before the two metadata requests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/intervention_schedule_qualification"
OUT = BASE / "auditor_sources"
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / "PRE_OPEN_FREEZE.json"
if target.exists():
    raise RuntimeError("Auditor freeze exists")
paths = sorted((ROOT / "research/intervention_schedule_qualification_20261022").glob("auditor_*.py"))
paths += [BASE / "PROTOCOL_AUDITOR_IDENTITY.md", BASE / "ADVOCATE_SOURCE_REPORT.md",
          BASE / "advocate_sources/GEO_SUMMARY.json", OUT / "SYNTHETIC_TESTS.txt", OUT / "SYNTHETIC_TESTS_FINAL.txt"]
result = {"frozen_utc": datetime.now(timezone.utc).isoformat(),
          "new_metadata_requests_sent_before_freeze": 0,
          "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": "FROZEN", "files": len(paths)}))
