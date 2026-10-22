"""Six bounded metadata queries for the complete pooled one-anchor operation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

OUT = Path("log/20261022/operator_renewal/functional/POSTFINAL_sources")
OUT.mkdir(exist_ok=True)
QUERIES = [
    "pooled CRISPR screen absolute cell abundance normalization total cell count",
    "Chronos cell population dynamics model CRISPR experiments",
    "heterogeneous population dose response sharp bounds moments survival",
    "compositional response absolute reference partial identification dose response",
    "frailty relative survival nonparametric moment bounds",
    "moment problem common unknown normalization multiple populations survival",
]


def get(index_query):
    index, query = index_query
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": query, "rows": 8,
        "select": "DOI,title,author,published,URL,link,abstract,type",
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MAESTRO research audit"})
    receipt = {"index": index, "query": query, "url": url,
               "utc": datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read()
            receipt.update(status=response.status, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
        (OUT/f"query_{index}.json").write_bytes(body)
        data = json.loads(body)
        receipt["items"] = [{"DOI": item.get("DOI"), "title": item.get("title"),
                             "type": item.get("type"), "link": item.get("link", [])}
                            for item in data["message"]["items"]]
    except Exception as exc:
        receipt["error"] = repr(exc)
    return receipt


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(get, enumerate(QUERIES, 1)))
    (OUT/"query_receipts.json").write_text(json.dumps(receipts, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipts, indent=2))
