"""Bounded metadata-only source listing, with a persisted response-body ledger."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261021/oasis_source_qualification"
LIMIT = 10_000_000


def get(url, params=None):
    ledger_path = LOG / "NETWORK.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"budget": LIMIT, "body_bytes": 0, "requests": []}
    remaining = LIMIT - ledger["body_bytes"]
    with requests.get(url, params=params, timeout=25, stream=True) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > remaining:
            raise RuntimeError("Network body budget would be exceeded")
        chunks = []
        for chunk in response.iter_content(65536):
            ledger["body_bytes"] += len(chunk)
            if ledger["body_bytes"] > LIMIT:
                raise RuntimeError("Network body budget exceeded")
            chunks.append(chunk)
        content = b"".join(chunks)
        ledger["requests"].append({"url": response.url, "status": response.status_code,
                                   "bytes": len(content), "utc": datetime.now(timezone.utc).isoformat()})
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        response.raise_for_status()
        return content


def listing(prefix, delimiter=None):
    params = {"list-type": "2", "prefix": prefix, "max-keys": 1000}
    if delimiter:
        params["delimiter"] = delimiter
    body = get("https://cellpainting-gallery.s3.amazonaws.com/", params)
    doc = ET.fromstring(body)
    ns = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
    return {"prefix": prefix, "sha256": hashlib.sha256(body).hexdigest(),
            "truncated": doc.findtext("s:IsTruncated", namespaces=ns),
            "common_prefixes": [x.findtext("s:Prefix", namespaces=ns) for x in doc.findall("s:CommonPrefixes", ns)],
            "objects": [{k: x.findtext("s:" + k, namespaces=ns)
                         for k in ("Key", "Size", "LastModified", "ETag")}
                        for x in doc.findall("s:Contents", ns)]}


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    record = {"metadata": listing("cpg0037-oasis/axiom/workspace/metadata/"),
              "dataset_root": listing("cpg0037-oasis/", "/"),
              "axiom_root": listing("cpg0037-oasis/axiom/", "/"),
              "profile_roots": listing("cpg0037-oasis/axiom/workspace/", "/")}
    (LOG / "SOURCE_LISTING.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    entries = record["metadata"]["objects"]
    biochem = [x for x in entries if x["Key"].endswith("/biochem.parquet")]
    print(json.dumps({"metadata_objects": len(entries), "biochem_objects": len(biochem),
                      "biochem_total_bytes": sum(int(x["Size"]) for x in biochem),
                      "truncated": record["metadata"]["truncated"],
                      "root_objects": record["dataset_root"]["objects"],
                      "axiom_objects": record["axiom_root"]["objects"],
                      "workspace_prefixes": record["profile_roots"]["common_prefixes"]}))


if __name__ == "__main__":
    main()
