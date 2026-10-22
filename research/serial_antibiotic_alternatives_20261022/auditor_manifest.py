"""Official OA package manifest and BioSample count only; never download data files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives"
OUT = BASE / "manifest_followup"
REQUESTS = [
    ("PMC_OA", "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12164588"),
    ("BIOSAMPLE_COUNT", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({"db": "biosample", "term": "PRJNA1254677[BioProject]", "retmax": 0, "retmode": "json"})),
]


def project_oa(raw):
    root = ET.fromstring(raw)
    records = []
    for record in root.iter("record"):
        records.append({"attributes": dict(record.attrib), "links": [dict(link.attrib) for link in record.findall("link")]})
    return {"response_date": root.findtext("responseDate"), "records_attributes": [dict(e.attrib) for e in root.findall("records")],
            "records": records, "errors": [{"attributes": dict(e.attrib), "text": e.text} for e in root.iter("error")]}


def project_esearch(raw):
    data = json.loads(raw)
    result = data.get("esearchresult", {})
    return {"db": "biosample", "exact_requested_term": "PRJNA1254677[BioProject]",
            "count": result.get("count"), "retmax": result.get("retmax"), "retstart": result.get("retstart"),
            "querytranslation": result.get("querytranslation"), "errorlist": result.get("errorlist"),
            "warninglist": result.get("warninglist"), "top_level_error": data.get("error"),
            "ids_exported": False}


def project_supplements(raw):
    root = ET.fromstring(raw)
    href = "{http://www.w3.org/1999/xlink}href"
    supplements = []
    for element in root.iter("supplementary-material"):
        item = {"attributes": dict(element.attrib),
                "label": " ".join(element.find("label").itertext()).strip() if element.find("label") is not None else None,
                "media": []}
        for media in element.iter("media"):
            item["media"].append({"href": media.get(href), "mimetype": media.get("mimetype"), "mime-subtype": media.get("mime-subtype"),
                                  "title": " ".join(media.itertext()).strip()})
        supplements.append(item)
    article = root.find(".//article-meta")
    ids = [{"type": e.get("pub-id-type"), "value": e.text} for e in article.findall("article-id")] if article is not None else []
    return {"article_identifiers": ids, "supplements": supplements,
            "supplement_payloads_opened": False, "figure_or_result_values_exported": False}


def main():
    receipt_path = OUT / "NETWORK.json"
    if receipt_path.exists():
        raise RuntimeError("Manifest ledger exists; no retry")
    freeze_paths = [Path(__file__), OUT / "PROTOCOL.md", BASE / "TRIPARTITE.xml"]
    freeze = {"utc": datetime.now(timezone.utc).isoformat(), "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in freeze_paths}}
    (OUT / "PRE_REQUEST_FREEZE.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    projected = project_supplements((BASE / "TRIPARTITE.xml").read_bytes())
    (OUT / "SUPPLEMENT_MEDIA_METADATA.json").write_text(json.dumps(projected, indent=2), encoding="utf-8")
    ledger, received = [], 0
    for name, url in REQUESTS:
        source = OUT / f"{name}_SOURCE.body"
        if source.exists() or (OUT / f"{name}_METADATA.json").exists():
            raise RuntimeError("Manifest source overwrite prohibited")
        receipt = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
        try:
            parts = []
            with requests.get(url, stream=True, timeout=35) as response:
                receipt.update({"status": response.status_code, "final_url": response.url, "headers": dict(response.headers)})
                while received < 500000:
                    part = response.raw.read(min(16384, 500000 - received), decode_content=True)
                    if not part:
                        break
                    received += len(part)
                    parts.append(part)
            raw = b"".join(parts)
            source.write_bytes(raw)
            receipt.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated_at_shared_cap": received == 500000})
            if receipt["status"] != 200 or received == 500000:
                raise RuntimeError("HTTP failure or body cap")
            metadata = project_oa(raw) if name == "PMC_OA" else project_esearch(raw)
            (OUT / f"{name}_METADATA.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            receipt["projection"] = "SUCCESS"
        except Exception as exc:
            receipt.update({"projection": "FAILED_NO_RAW_CONTENT_ECHO", "failure_type": type(exc).__name__})
        receipt["receipt_utc"] = datetime.now(timezone.utc).isoformat()
        ledger.append(receipt)
        receipt_path.write_text(json.dumps({"consumed_HTTP_body_bytes": received, "requests": ledger}, indent=2), encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in ["name", "status", "bytes", "projection"] if k in receipt}))
        if received == 500000:
            break


if __name__ == "__main__":
    main()
