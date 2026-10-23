"""Verify prior method seals and bind all later reviewer artifacts once."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "log/20261023/hcc_task_qualification"
OUT = BASE / "method/FINAL_SEAL.json"
if OUT.exists():
    raise SystemExit("Refusing overwrite")
for name in ("INDEPENDENT_SEAL.json", "SOURCE_SEAL.json"):
    for relative, expected in json.loads((BASE / "method" / name).read_text(encoding="utf-8"))["files"].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Earlier seal drift: {relative}")
paths = sorted(p for p in (BASE / "method").iterdir() if p.is_file())
paths += sorted(p for p in Path(__file__).resolve().parent.iterdir() if p.is_file())
paths += [BASE / "PDF_ASSAY_METHODS.json", BASE / "epmc_fulltext.xml", BASE / "epmc_supplements.zip"]
result = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "prior_seal_drift": 0,
    "files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "scope": "reviewer closure; original seals retained; two metadata audit failures disclosed",
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"file_count": len(result["files"]), "prior_seal_drift": 0}))
