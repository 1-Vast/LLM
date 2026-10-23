"""Verify the independent seal, then bind cross-review and read peer reports."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
role = root / "log/20261023/cxcl9_source_feasibility/constructive"
first = json.loads((role / "FIRST_SEAL.json").read_text(encoding="utf-8"))
drift = [name for name, digest in first["files"].items()
         if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest]
if drift:
    raise SystemExit("First-seal drift: " + repr(drift))
paths = [p for p in role.iterdir() if p.is_file() and p.name != "FINAL_SEAL.json"]
paths += list(Path(__file__).parent.glob("*.py"))
base = root / "log/20261023/cxcl9_source_feasibility"
paths += [base/name for name in ["method/INDEPENDENT.md", "method/SOURCE_ADDENDUM.md",
          "method/ROOT_STAGE3_REVIEW.md", "biology/ROOT_STAGE3_REVIEW.md"]]
payload = {"stage": "actual post-seal reciprocal cross-review", "first_files_verified": len(first["files"]),
           "first_seal_drift": drift,
           "files": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(paths)}}
target = role / "FINAL_SEAL.json"
if target.exists():
    raise SystemExit("Preserving existing final seal")
target.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"files": len(payload["files"]), "first_seal_drift": drift}))
