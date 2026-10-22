"""One sequential PubMed search/fetch for published protocol/data leads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_schedule_qualification/root_sources"
QUERY = ('("sequential drug"[Title/Abstract] OR "drug sequence"[Title/Abstract] OR '
         '"time-staggered"[Title/Abstract] OR "order-dependent"[Title/Abstract]) AND '
         '(transcriptom*[Title/Abstract] OR proteom*[Title/Abstract] OR '
         '"high-throughput"[Title/Abstract] OR screen*[Title/Abstract]) AND '
         '("1900/01/01"[Date - Publication] : "2026/10/22"[Date - Publication])')


def fetch(name, endpoint, params, ledger):
    target = OUT / name
    if target.exists():
        raise RuntimeError("Refusing source overwrite")
    receipt = {"name": name, "utc": datetime.now(timezone.utc).isoformat()}
    body = bytearray()
    try:
        with requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint,
                          params=params, timeout=35, stream=True) as response:
            receipt.update({"url": response.url, "status": response.status_code,
                            "content_type": response.headers.get("Content-Type")})
            for chunk in response.iter_content(16384):
                body.extend(chunk)
                if sum(r.get("bytes", 0) for r in ledger) + len(body) > 1_000_000:
                    raise RuntimeError("Body limit reached")
            target.write_bytes(body)
            receipt.update({"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
            response.raise_for_status()
        return bytes(body)
    except Exception as exc:
        receipt["failure_type"] = type(exc).__name__
        raise
    finally:
        ledger.append(receipt)
        (OUT / "NETWORK.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "NETWORK.json").exists():
        raise RuntimeError("Search already attempted; no implicit repeat")
    ledger = []
    search_bytes = fetch("SEARCH.xml", "esearch.fcgi", {"db": "pubmed", "term": QUERY,
                         "retmode": "xml", "retmax": "20", "sort": "pub_date"}, ledger)
    search = ET.fromstring(search_bytes)
    if search.find("ErrorList") is not None or search.find("ERROR") is not None:
        raise RuntimeError("Entrez query semantics failed; retain source")
    ids = [x.text for x in search.findall("./IdList/Id")]
    if not ids:
        (OUT / "PRIMARY_SUMMARY.json").write_text(json.dumps({"query": QUERY, "count": search.findtext("Count"), "records": []}, indent=2), encoding="utf-8")
        return
    records_bytes = fetch("ARTICLES.xml", "efetch.fcgi", {"db": "pubmed", "id": ",".join(ids),
                          "retmode": "xml"}, ledger)
    records = []
    for item in ET.fromstring(records_bytes).findall("./PubmedArticle"):
        article = item.find("./MedlineCitation/Article")
        records.append({"pmid": item.findtext("./MedlineCitation/PMID"),
                        "title": "".join(article.find("ArticleTitle").itertext()),
                        "abstract": ["".join(x.itertext()) for x in article.findall("./Abstract/AbstractText")],
                        "ids": {x.attrib["IdType"]: x.text for x in item.findall("./PubmedData/ArticleIdList/ArticleId")},
                        "data_banks": [ET.tostring(x, encoding="unicode") for x in article.findall("./DataBankList/DataBank")]})
    result = {"query": QUERY, "count": search.findtext("Count"), "retrieved_ids": ids, "records": records}
    (OUT / "PRIMARY_SUMMARY.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total_hits": result["count"], "returned": len(records),
                      "titles": [{"pmid": r["pmid"], "title": r["title"], "ids": r["ids"]} for r in records]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
