"""Bind biological opposing opinion before direct reviewer exchange."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"
paths = [OUT / "INDEPENDENT_SEAL.json", OUT / "OPPOSING_BIOLOGY_INITIAL.md",
         ROOT / "log/20261022/native_operation/biology/INDEPENDENT_POSITION.md",
         ROOT / "log/20261022/native_operation/biology/INDEPENDENT_SEAL.json",
         Path(__file__)]
output = OUT / "OPPOSING_BIOLOGY_SEAL.json"
if output.exists():
    raise FileExistsError(output)
record = {"time_utc": datetime.now(timezone.utc).isoformat(), "biology_contact_before_seal": False,
          "files": [{"path": str(p), "bytes": p.stat().st_size,
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
output.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({"seal": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))
