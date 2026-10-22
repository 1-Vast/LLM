"""Bounded primary metadata/fulltext acquisition; never run author code."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_dynamics_renewal/advocate"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
if len(ledger) >= 4:
    raise RuntimeError("Four GET limit reached")
limit = min(2000000, 6000000 - sum(r.get("body_bytes", 0) for r in ledger))
mode = sys.argv[1]
base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
if mode == "search":
    query = ('(cancer[tiab] OR tumor[tiab] OR tumour[tiab]) AND '
             '(withdrawal[tiab] OR washout[tiab] OR rechallenge[tiab]) AND '
             '("drug tolerant"[tiab] OR persister*[tiab] OR "non-genetic"[tiab] OR adaptation[tiab]) AND '
             '("single cell"[tiab] OR "single-cell"[tiab] OR transcriptom*[tiab]) AND '
             '("2024/01/01"[dp] : "2026/10/22"[dp]) NOT review[pt]')
    name = "SEARCH.json"
    url = base + "esearch.fcgi?" + urlencode({"db": "pubmed", "term": query,
        "retmax": 8, "retmode": "json", "sort": "relevance"})
elif mode == "abstracts":
    ids = json.loads((OUT / "SEARCH.json").read_text())["esearchresult"]["idlist"]
    if not ids or len(ids) > 8:
        raise RuntimeError("No IDs or >8 IDs")
    name = "ABSTRACTS.xml"
    url = base + "efetch.fcgi?" + urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
else:
    name, url = sys.argv[2:4]
target = OUT / name
if target.exists():
    raise FileExistsError("Refusing source overwrite")
receipt = {"name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat()}
try:
    with requests.get(url, timeout=50, stream=True, allow_redirects=False) as response:
        body = response.raw.read(limit, decode_content=True)
        target.write_bytes(body)
        receipt.update(status=response.status_code, body_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(), complete_under_cap=len(body) < limit,
            location=response.headers.get("Location"))
except Exception as exc:
    receipt["exception"] = {"type": type(exc).__name__, "message": str(exc)}
finally:
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    ledger.append(receipt)
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
print(json.dumps(receipt))
if receipt.get("status") != 200 or not receipt.get("complete_under_cap"):
    raise RuntimeError("Failure/redirect/cap: no retry")
if mode == "search":
    print(body.decode())
elif mode == "abstracts":
    entries = []
    for article in ET.fromstring(body).findall("PubmedArticle"):
        citation = article.find("MedlineCitation")
        item = citation.find("Article")
        entries.append({"pmid": citation.findtext("PMID"),
            "title": " ".join(item.find("ArticleTitle").itertext()),
            "abstract": [" ".join(p.itertext()) for p in item.findall("Abstract/AbstractText")],
            "ids": [{"type": p.get("IdType"), "value": p.text}
                    for p in article.findall("PubmedData/ArticleIdList/ArticleId")]})
    (OUT / "ABSTRACTS_PROJECTED.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(entries, ensure_ascii=False, indent=2))
