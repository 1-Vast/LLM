"""Preserve both exact cross-review versions; never rewrite original seals."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "log/20261023/inherited_update_renewal/constructive"
path = OUT/"CROSS.md"
current = path.read_bytes()
original = current.split(b"\nAfter sealing API_REVIEW",1)[0]
digest = lambda b: hashlib.sha256(b).hexdigest()
expected = json.loads((OUT/"API_REVIEW_SEAL.json").read_text())["files"][str(path.relative_to(ROOT)).replace("\\","/")]
assert digest(original) == expected
assert original != current
before = {}
for seal in sorted(OUT.glob("*SEAL.json")):
    payload = json.loads(seal.read_text())
    mismatches = []
    for name,h in payload.get("files",{}).items():
        fp=ROOT/name
        actual=digest(fp.read_bytes()) if fp.exists() else None
        if actual!=h: mismatches.append({"path":name,"expected":h,"actual":actual})
    before[seal.name]=mismatches
(OUT/"CROSS_APPENDED_SNAPSHOT.md").write_bytes(current)
(OUT/"CROSS_LATER_API_DISCUSSION.md").write_bytes(current[len(original):])
path.write_bytes(original)
after = {}
for seal in sorted(OUT.glob("*SEAL.json")):
    payload=json.loads(seal.read_text())
    mismatches=[]
    for name,h in payload.get("files",{}).items():
        fp=ROOT/name
        actual=digest(fp.read_bytes()) if fp.exists() else None
        if actual!=h:
            archived=digest((OUT/"CROSS_APPENDED_SNAPSHOT.md").read_bytes()) if fp==path else None
            mismatches.append({"path":name,"expected":h,"current":actual,
                               "exact_historical_bytes":str((OUT/"CROSS_APPENDED_SNAPSHOT.md").relative_to(ROOT)).replace("\\","/") if archived==h else None})
    after[seal.name]=mismatches
result={"cause":"Post-API-seal CROSS append was disclosed in role notes but violated path-level historical seal continuity; root final audit correctly failed.",
        "original_sha256":digest(original),"appended_sha256":digest(current),
        "before_mismatches":before,"after_mismatches":after,
        "repair":"Original CROSS restored exactly; appended bytes and later discussion preserved separately; no original seal modified.",
        "claim":"Historical same-path drift occurred. Archived-byte resolution is not zero historical drift or global provenance repair."}
(OUT/"CROSS_VERSION_REPAIR.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
files={str(p.relative_to(ROOT)).replace("\\","/"):digest(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="CURRENT_REPAIRED_SEAL.json"}
(OUT/"CURRENT_REPAIRED_SEAL.json").write_text(json.dumps({"files":files,"history":"See CROSS_VERSION_REPAIR.json; no blanket drift0 claim"},indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
