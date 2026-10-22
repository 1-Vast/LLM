"""Fixed two-request Entrez scout; literature only, never assay matrices."""
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives"
QUERY = '((antibiotic*[Title/Abstract] AND (bacteria*[Title/Abstract] OR bacterial[Title/Abstract])) AND (morbidostat[Title/Abstract] OR eVOLVER[Title/Abstract] OR "collateral sensitivity"[Title/Abstract]) AND (temporal[Title/Abstract] OR sequential[Title/Abstract] OR cycling[Title/Abstract] OR "time-resolved"[Title/Abstract] OR "drug switching"[Title/Abstract])) AND ("1900/01/01"[Date - Publication] : "2026/10/22"[Date - Publication])'
ledger = []
used = 0


def request(name, endpoint, parameters):
    global used
    path = OUT / name
    if path.exists():
        raise FileExistsError(path)
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" + urllib.parse.urlencode(parameters)
    receipt = {"name": name, "url": url}
    payload = b""
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = response.read(1_000_001 - used)
            receipt["status"] = response.status
    except urllib.error.HTTPError as exc:
        payload = exc.read(1_000_001 - used)
        receipt.update({"status": exc.code, "error": str(exc)})
    except Exception as exc:
        receipt.update({"error": str(exc), "bytes": None})
    if payload:
        path.write_bytes(payload)
        receipt.update({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
        used += len(payload)
    ledger.append(receipt)
    (OUT / "NETWORK.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    if used > 1_000_000:
        raise RuntimeError("Source ceiling reached; do not parse truncated document")
    if receipt.get("status") != 200:
        raise RuntimeError("Primary request failed; do not silently retry")
    return payload


search = ET.fromstring(request("SEARCH.xml", "esearch.fcgi", {"db": "pubmed", "term": QUERY, "retmode": "xml", "retmax": "12"}))
ids = [item.text for item in search.findall("./IdList/Id")]
if not ids:
    raise RuntimeError("No records from fixed query; no replacement query authorised")
article_set = ET.fromstring(request("PRIMARY.xml", "efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}))
records = []
for article in article_set.findall("./PubmedArticle"):
    record = {"pmid": article.findtext("./MedlineCitation/PMID"), "title": " ".join(article.find("./MedlineCitation/Article/ArticleTitle").itertext())}
    record["abstract"] = [" ".join(p.itertext()) for p in article.findall("./MedlineCitation/Article/Abstract/AbstractText")]
    record["ids"] = {p.attrib.get("IdType"): p.text for p in article.findall("./PubmedData/ArticleIdList/ArticleId")}
    record["databanks"] = [ET.tostring(p, encoding="unicode") for p in article.findall(".//DataBank")]
    records.append(record)
(OUT / "SUMMARY.json").write_text(json.dumps({"query": QUERY, "count": search.findtext("Count"), "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"count": search.findtext("Count"), "records": [{"pmid": r["pmid"], "title": r["title"], "ids": r["ids"]} for r in records], "requests": len(ledger), "bytes": used}, ensure_ascii=False))
