"""Append a raw-audit seal while verifying, not rewriting, older seals."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
base = root/"log/20261023/cxcl9_source_feasibility"
role = base/"constructive"
verified = {}
for name in ("FIRST_SEAL.json", "FINAL_SEAL.json"):
    payload = json.loads((role/name).read_text(encoding="utf-8"))
    drift = [path for path, digest in payload["files"].items()
             if hashlib.sha256((root/path).read_bytes()).hexdigest() != digest]
    if drift:
        raise SystemExit(repr({name: drift}))
    verified[name] = {"files": len(payload["files"]), "drift": []}
paths = [p for p in role.iterdir() if p.is_file() and p.name != "RAW_AUDIT_SEAL.json"]
paths += list(Path(__file__).parent.glob("*.py"))
audit = json.loads((role/"RAW_AUDIT.json").read_text())
paths += [root/name for name in audit["input_sha256"]]
paths = sorted(set(paths))
payload = {"stage": "independent raw aggregation audit", "prior_verified": verified,
           "files": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in paths}}
target = role/"RAW_AUDIT_SEAL.json"
if target.exists():
    raise SystemExit("Preserving existing raw-audit seal")
target.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"files": len(paths), "prior_verified": verified}))
