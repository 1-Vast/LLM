"""Seal opposing assessment before direct proposer contact."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"
PATHS = [OUT / "INDEPENDENT_SEAL.json", OUT / "OPPOSING_STENCIL_INITIAL.md",
         ROOT / "log/20261022/native_operation/proposer/INDEPENDENT_INITIAL.md",
         ROOT / "log/20261022/native_operation/proposer/INITIAL_SEAL.json",
         ROOT / "log/20261022/native_operation/root/SOURCE_READING.md",
         Path(__file__)]
output = OUT / "OPPOSING_STENCIL_SEAL.json"
if output.exists():
    raise FileExistsError(output)
record = {"time_utc": datetime.now(timezone.utc).isoformat(), "proposer_contact_before_seal": False,
          "peer_reply_read": False,
          "files": [{"path": str(path), "bytes": path.stat().st_size,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in PATHS]}
output.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps({"seal": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))
