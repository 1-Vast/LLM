"""Bounded primary-source metadata scout; no retries or redirected requests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/dynamic_source_followup/ncbi_scout"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
if len(ledger) >= 4:
    raise RuntimeError("Registered four-request limit reached")
mode = sys.argv[1]
base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
if mode == "search":
    query = ('(antibiotic*[tiab] OR antibacterial*[tiab]) AND '
             '(evolution[tiab] OR evolving[tiab] OR "serial passage"[tiab] OR adaptation[tiab]) AND '
             '(sequential[tiab] OR switching[tiab] OR cycling[tiab] OR longitudinal[tiab]) AND '
             '("2024/01/01"[dp] : "2026/10/22"[dp]) NOT '
             '(40478208[uid] OR 39623067[uid] OR 41278959[uid]) NOT review[pt]')
    name = "SEARCH.json"
    url = base + "esearch.fcgi?" + urlencode({"db": "pubmed", "term": query,
        "retmax": 10, "retmode": "json", "sort": "relevance"})
elif mode == "abstracts":
    search = json.loads((OUT / "SEARCH.json").read_text(encoding="utf-8"))
    ids = search["esearchresult"]["idlist"]
    if not ids or len(ids) > 10:
        raise RuntimeError("No IDs or more than registered 10 IDs")
    name = "ABSTRACTS.xml"
    url = base + "efetch.fcgi?" + urlencode({"db": "pubmed", "id": ",".join(ids),
        "retmode": "xml"})
else:
    name, url = sys.argv[2:4]
target = OUT / name
if target.exists():
    raise FileExistsError("Refusing source overwrite before request")
receipt = {"index": len(ledger) + 1, "name": name, "url": url,
           "started_utc": datetime.now(timezone.utc).isoformat()}
try:
    with requests.get(url, timeout=50, stream=True, allow_redirects=False) as response:
        body = response.raw.read(2_000_000, decode_content=True)
        target.write_bytes(body)
        receipt.update(status=response.status_code, body_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            complete_under_cap=len(body) < 2_000_000,
            location=response.headers.get("Location"))
except Exception as exc:
    receipt["exception"] = {"type": type(exc).__name__, "message": str(exc)}
finally:
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    ledger.append(receipt)
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False))
if receipt.get("status") != 200 or not receipt.get("complete_under_cap"):
    raise RuntimeError("Acquisition failed/incomplete; do not retry or redirect")
if mode == "search":
    print(body.decode("utf-8"))
elif mode == "abstracts":
    entries = []
    for article in ET.fromstring(body).findall("PubmedArticle"):
        citation = article.find("MedlineCitation")
        item = citation.find("Article")
        entries.append({"pmid": citation.findtext("PMID"),
            "title": " ".join(item.find("ArticleTitle").itertext()),
            "authors": [" ".join(x.itertext()) for x in item.findall("AuthorList/Author")],
            "journal": item.findtext("Journal/Title"),
            "abstract": [{"label": p.get("Label"), "text": " ".join(p.itertext())}
                         for p in item.findall("Abstract/AbstractText")],
            "ids": [{"type": p.get("IdType"), "value": p.text}
                    for p in article.findall("PubmedData/ArticleIdList/ArticleId")],
            "databanks": [" ".join(p.itertext()) for p in item.findall("DataBankList/DataBank")]})
    (OUT / "ABSTRACTS_PROJECTED.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(entries, ensure_ascii=False, indent=2))
