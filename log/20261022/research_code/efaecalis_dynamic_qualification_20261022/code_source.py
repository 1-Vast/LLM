"""Three pinned GitHub metadata/blob GETs; never execute source or fetch data."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/efaecalis_dynamic_qualification/code_io"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
if len(ledger) >= 3:
    raise RuntimeError("Registered three GET budget exhausted")
name, url = sys.argv[1:3]
target = OUT / name
if target.exists():
    raise FileExistsError("Refusing source overwrite before request")
receipt = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
try:
    with requests.get(url, timeout=50, stream=True, allow_redirects=False,
                      headers={"Accept": "application/vnd.github+json", "User-Agent": "MAESTRO-source-qualification"}) as response:
        body = response.raw.read(5000000, decode_content=True)
        target.write_bytes(body)
        receipt.update(status=response.status_code, body_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(), complete_under_cap=len(body) < 5000000,
            location=response.headers.get("Location"), remaining=response.headers.get("X-RateLimit-Remaining"))
except Exception as exc:
    receipt["exception"] = {"type": type(exc).__name__, "message": str(exc)}
finally:
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    ledger.append(receipt)
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
print(json.dumps(receipt))
if receipt.get("status") != 200 or not receipt.get("complete_under_cap"):
    raise RuntimeError("Failure/redirect/cap; stop without retry")
obj = json.loads(body)
if "tree" in obj:
    projection = {"full_tree_sha": obj["sha"], "truncated": obj.get("truncated"),
        "tree": [{key: item.get(key) for key in ("path", "type", "size", "sha", "url")}
                 for item in obj["tree"]]}
    (OUT / "TREE_MANIFEST.json").write_text(json.dumps(projection, indent=2), encoding="utf-8")
    print(json.dumps(projection, indent=2))
else:
    if obj.get("encoding") != "base64":
        raise RuntimeError("Unexpected blob encoding")
    decoded = base64.b64decode(obj["content"])
    git_sha = hashlib.sha1(b"blob " + str(len(decoded)).encode() + b"\0" + decoded).hexdigest()
    if git_sha != obj.get("sha"):
        raise RuntimeError("Git blob identity mismatch")
    decoded_path = OUT / (target.stem + ".source")
    if decoded_path.exists():
        raise FileExistsError("Refusing decoded source overwrite")
    decoded_path.write_bytes(decoded)
    info = {"sha": git_sha, "decoded_bytes": len(decoded), "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
            "decoded_path": str(decoded_path), "encoding": obj["encoding"]}
    (OUT / (target.stem + "_IDENTITY.json")).write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info))
