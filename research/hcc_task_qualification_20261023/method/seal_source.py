"""Seal source addendum and verify the earlier independent seal remains exact."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "log/20261023/hcc_task_qualification"
EARLIER = BASE / "method/INDEPENDENT_SEAL.json"
OUT = BASE / "method/SOURCE_SEAL.json"
if OUT.exists():
    raise SystemExit("Refusing to overwrite source seal")
bindings = json.loads(EARLIER.read_text(encoding="utf-8"))["files"]
for relative, expected in bindings.items():
    if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f"Independent seal drift: {relative}")
paths = [EARLIER, BASE / "method/SOURCE_ADDENDUM.md", Path(__file__).resolve()]
paths += [BASE / name for name in ("ATTACHMENT_SCHEMA.json", "PDF_CAPTIONS.json", "PDF_STRUCTURE.json")]
result = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "independent_seal_drift": 0,
    "files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "scope": "source addendum, inspected metadata, prior seal and verification code",
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
