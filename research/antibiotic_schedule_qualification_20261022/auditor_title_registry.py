"""Finite sequential title/author metadata registry queries; no research data files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/title_registry_audit"
REQUESTS = [
    ("ZENODO_TITLE", "GET", "https://zenodo.org/api/records/?" + urlencode({"q": '"Massively multiplexed microfluidics"', "size": 10}), None),
    ("DATACITE_TITLE", "GET", "https://api.datacite.org/dois?" + urlencode({"query": 'titles.title:"Massively multiplexed microfluidics"', "page[size]": 10}), None),
    ("FIGSHARE_TITLE", "POST", "https://api.figshare.com/v2/articles/search", {"search_for": "Massively multiplexed microfluidics", "page_size": 10}),
    ("ZENODO_AUTHORS", "GET", "https://zenodo.org/api/records/?" + urlencode({"q": '(creators.name:"Jeong" OR creators.name:"Tay") AND (antibiotic OR microfluidics)', "size": 10}), None),
]


def project_zenodo(data):
    records = []
    for record in data.get("hits", {}).get("hits", []):
        meta = record.get("metadata", {})
        files = [{k: f.get(k) for k in ["key", "size", "type", "checksum", "links"] if k in f}
                 for f in record.get("files", [])]
        records.append({"id": record.get("id"), "title": meta.get("title"), "creators": meta.get("creators"),
                        "doi": meta.get("doi"), "publication_date": meta.get("publication_date"),
                        "related_identifiers": meta.get("related_identifiers"), "resource_type": meta.get("resource_type"),
                        "record_links": record.get("links"), "files": files})
    return {"total": data.get("hits", {}).get("total"), "records": records}


def project_datacite(data):
    records = []
    for record in data.get("data", []):
        meta = record.get("attributes", {})
        records.append({"id": record.get("id"), **{k: meta.get(k) for k in
                        ["doi", "titles", "creators", "publisher", "publicationYear", "types", "url", "relatedIdentifiers", "sizes", "formats", "version"]}})
    return {"total": data.get("meta", {}).get("total"), "records": records}


def project_figshare(data):
    if not isinstance(data, list):
        raise ValueError("Expected public article search list")
    allowed = ["id", "title", "doi", "url", "url_public_html", "url_public_api", "resource_doi", "resource_title", "published_date", "group_id", "size"]
    return {"returned_records": len(data), "records": [{k: r.get(k) for k in allowed if k in r} for r in data]}


def main():
    ledger_path = OUT / "NETWORK.json"
    if ledger_path.exists():
        raise RuntimeError("Title registry ledger exists; no overwrite/restart")
    code = Path(__file__)
    protocol = OUT / "PROTOCOL.md"
    freeze = {"utc": datetime.now(timezone.utc).isoformat(), "requests_before_freeze": 0,
              "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [code, protocol, OUT / "SYNTHETIC_TESTS.txt"]}}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    (OUT / "sealed_metadata").mkdir(parents=True, exist_ok=True)
    ledger, received = [], 0
    for name, method, url, body in REQUESTS:
        target = OUT / "sealed_metadata" / f"{name}.json"
        if target.exists() or (OUT / f"{name}_IDENTITY.json").exists():
            raise RuntimeError("Refusing registry source overwrite")
        receipt = {"name": name, "method": method, "url": url, "request_json": body,
                   "started_utc": datetime.now(timezone.utc).isoformat()}
        try:
            parts = []
            with requests.request(method, url, json=body, stream=True, timeout=35) as response:
                receipt.update({"status": response.status_code, "headers": dict(response.headers), "final_url": response.url})
                while received < 2_000_000:
                    part = response.raw.read(min(16384, 2_000_000 - received), decode_content=True)
                    if not part:
                        break
                    parts.append(part)
                    received += len(part)
            raw = b"".join(parts)
            target.write_bytes(raw)
            receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_shared_cap": received == 2_000_000})
            if received == 2_000_000 or receipt["status"] != 200:
                raise RuntimeError("HTTP failure or body cap reached")
            parsed = json.loads(raw)
            projected = project_zenodo(parsed) if name.startswith("ZENODO") else project_datacite(parsed) if name.startswith("DATACITE") else project_figshare(parsed)
            (OUT / f"{name}_IDENTITY.json").write_text(json.dumps(projected, indent=2, ensure_ascii=False), encoding="utf-8")
            receipt["projection"] = "SUCCESS"
        except Exception as exc:
            receipt.update({"projection": "FAILED_NO_RAW_CONTENT_ECHO", "failure_type": type(exc).__name__})
        receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
        ledger.append(receipt)
        ledger_path.write_text(json.dumps({"combined_consumed_body_bytes": received, "requests": ledger}, indent=2), encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in ["name", "status", "bytes", "projection"] if k in receipt}))
        if received == 2_000_000:
            break


if __name__ == "__main__":
    main()
