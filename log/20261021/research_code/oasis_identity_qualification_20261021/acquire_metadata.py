"""Single-writer bounded acquisition of mixed metadata/index sources only."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261021/oasis_identity_qualification"
LIMIT = 20_000_000


def get(url, target=None):
    ledger_path = LOG / "NETWORK.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"limit_bytes": LIMIT, "body_bytes": 0, "requests": []}
    remaining = LIMIT - ledger["body_bytes"]
    with requests.get(url, timeout=30, stream=True) as response:
        size = response.headers.get("Content-Length")
        if size and int(size) > remaining:
            raise RuntimeError("Network response exceeds remaining budget")
        chunks = []
        for chunk in response.iter_content(65536):
            if len(chunk) > remaining:
                raise RuntimeError("Network body budget exceeded")
            chunks.append(chunk)
            remaining -= len(chunk)
        body = b"".join(chunks)
        receipt = {"url": response.url, "status": response.status_code, "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(),
                   "headers": {k: v for k, v in response.headers.items() if k.lower() in {"content-length", "etag", "last-modified"}},
                   "utc": datetime.now(timezone.utc).isoformat()}
        ledger["body_bytes"] += len(body)
        ledger["requests"].append(receipt)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        response.raise_for_status()
        if target:
            if target.exists():
                raise RuntimeError("Refusing to overwrite an existing source")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        return body, receipt


def main():
    body, receipt = get("https://zenodo.org/api/records/17067683")
    record = json.loads(body)
    manifest = {"record": {"id": record["id"], "metadata": {x: record["metadata"].get(x) for x in ("publication_date", "version", "license")}},
                "api_receipt": receipt, "files": []}
    for file in record["files"]:
        if file["key"] not in {"metadata.parquet", "index.parquet"}:
            continue
        target = LOG / "sealed_source" / file["key"]
        body, received = get(file["links"]["self"], target)
        if "md5:" + hashlib.md5(body).hexdigest() != file["checksum"]:
            raise RuntimeError("Zenodo checksum mismatch")
        manifest["files"].append({"name": file["key"], "declared_bytes": file["size"],
                                  "declared_checksum": file["checksum"], "local_path": str(target.relative_to(ROOT)),
                                  **received})
        print(json.dumps({"acquired": file["key"], "bytes": len(body)}), flush=True)
    (LOG / "NEW_SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
