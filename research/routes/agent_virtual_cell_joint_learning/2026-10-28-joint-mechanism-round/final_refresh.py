"""Bounded public metadata/source refresh; never retries a rejected request."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent / "sources/final_refresh"
ROOT.mkdir(exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument("target", choices=["zenodo", "arxiv"])
args = parser.parse_args()
queries = {
    "zenodo": [None],
    "arxiv": ['all:"Hankel" AND (all:"commutator" OR all:"difference") AND (all:"realization" OR all:"predictive state")',
              'all:"predictive state" AND (all:"abstraction" OR all:"task") AND submittedDate:[202501010000 TO 202610282359]'],
}
receipts = []
for index, query in enumerate(queries[args.target]):
    if args.target == "zenodo":
        url = "https://zenodo.org/api/records/14890339"
    else:
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "start": 0, "max_results": 10})
    receipt = {"date": "2026-10-28", "query": query, "url": url, "automatic_retry": False}
    path = ROOT / f"{args.target}_{index}.raw"
    if path.exists():
        raise SystemExit("Source artifact exists: no automatic replay")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO bounded scholarly evidence check", "Accept": "application/json, application/atom+xml;q=0.9, */*;q=0.1"})
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(10_000_001)
            if len(body) > 10_000_000:
                raise ValueError("response size budget exceeded")
            receipt.update(status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"),
                           bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        path.write_bytes(body)
        if args.target == "zenodo":
            record = json.loads(body)
            summary = {"id": record.get("id"), "doi": record.get("doi"), "metadata": record.get("metadata"),
                       "files": record.get("files"), "links": record.get("links")}
            (ROOT / "zenodo_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"target": args.target, "title": record.get("metadata", {}).get("title"), "files": [{"key": f.get("key"), "size": f.get("size"), "links": f.get("links")} for f in record.get("files", [])]}, ensure_ascii=False))
        else:
            import xml.etree.ElementTree as ET
            tree = ET.fromstring(body)
            ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
            entries = [{"id": e.findtext("a:id", namespaces=ns), "title": e.findtext("a:title", namespaces=ns),
                        "summary": e.findtext("a:summary", namespaces=ns), "published": e.findtext("a:published", namespaces=ns)} for e in tree.findall("a:entry", ns)]
            summary = {"query": query, "total_results": tree.findtext("o:totalResults", namespaces=ns), "entries": entries}
            (ROOT / f"arxiv_{index}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"target": args.target, "query": query, "total_results": summary["total_results"], "entries": [{k:v for k,v in e.items() if k != "summary"} for e in entries]}, ensure_ascii=False))
    except Exception as error:
        receipt["error"] = f"{type(error).__name__}: {error}"
        print(json.dumps({"target": args.target, "error": receipt["error"]}))
    receipts.append(receipt)
    # A rate/access rejection disables further requests to the same host in this pass.
    if "error" in receipt and any(code in receipt["error"] for code in ["403", "429"]):
        break
(ROOT / f"{args.target}_receipts.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
