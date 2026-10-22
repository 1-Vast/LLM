"""Two exact primary-prior metadata requests; no substitute search or full text."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_state_refinement_review/primary_prior"
OBJECTS = [
    ("ARXIV", "https://export.arxiv.org/api/query?id_list=cs%2F0406011%2C1207.4167&max_results=2"),
    ("CROSSREF", "https://api.crossref.org/works/10.1016%2F0890-5401%2887%2990052-6"),
]


def arxiv_metadata(raw):
    feed = ET.fromstring(raw)
    atom = "{http://www.w3.org/2005/Atom}"
    result = []
    for entry in feed.findall(f"{atom}entry"):
        result.append({"id": entry.findtext(f"{atom}id"),
                       "title": " ".join(entry.findtext(f"{atom}title", "").split()),
                       "authors": [a.findtext(f"{atom}name") for a in entry.findall(f"{atom}author")],
                       "abstract": " ".join(entry.findtext(f"{atom}summary", "").split()),
                       "published": entry.findtext(f"{atom}published"),
                       "updated": entry.findtext(f"{atom}updated")})
    return {"source_kind": "OFFICIAL_ARXIV_AUTHOR_ABSTRACT_METADATA; NOT_FULLTEXT", "records": result}


def crossref_metadata(raw):
    data = json.loads(raw)["message"]
    return {"source_kind": "CROSSREF_PUBLISHER_DEPOSITED_METADATA; NOT_FULLTEXT",
            "records": [{k: data.get(k) for k in ["DOI", "title", "author", "publisher", "published", "type", "abstract", "URL"]}]}


def main():
    ledger_path = OUT / "NETWORK.json"
    if ledger_path.exists():
        raise RuntimeError("Prior audit receipt exists; no restart")
    frozen = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [Path(__file__), OUT / "PROTOCOL.md"]}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "sha256": frozen}, indent=2), encoding="utf-8")
    ledger, received = [], 0
    for name, url in OBJECTS:
        target = OUT / f"{name}_SOURCE.body"
        if target.exists() or (OUT / f"{name}_METADATA.json").exists():
            raise RuntimeError("Prior source overwrite prohibited")
        receipt = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
        try:
            parts = []
            with requests.get(url, stream=True, timeout=35) as response:
                receipt.update({"status": response.status_code, "headers": dict(response.headers), "final_url": response.url})
                while received < 500_000:
                    part = response.raw.read(min(16384, 500_000 - received), decode_content=True)
                    if not part:
                        break
                    received += len(part)
                    parts.append(part)
            raw = b"".join(parts)
            target.write_bytes(raw)
            receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_shared_cap": received == 500_000})
            if receipt["status"] != 200 or received == 500_000:
                raise RuntimeError("Metadata HTTP failure or body cap")
            metadata = arxiv_metadata(raw) if name == "ARXIV" else crossref_metadata(raw)
            (OUT / f"{name}_METADATA.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
            receipt["metadata_projection"] = "SUCCESS"
        except Exception as exc:
            receipt.update({"metadata_projection": "FAILED", "failure_type": type(exc).__name__})
        receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
        ledger.append(receipt)
        ledger_path.write_text(json.dumps({"consumed_HTTP_body_bytes": received, "requests": ledger}, indent=2), encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in ["name", "status", "bytes", "metadata_projection"] if k in receipt}))
        if received == 500_000:
            break


if __name__ == "__main__":
    main()
