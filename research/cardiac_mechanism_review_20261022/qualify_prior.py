"""Retain legitimate primary-index responses and primary full text."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

OUT = Path(__file__).resolve().parents[2] / "log/20261022/cardiac_mechanism_review"
QUERIES = {
    "cardiac_calibration_primary": '(TITLE_ABS:"cardiac" AND TITLE_ABS:"model" AND (TITLE_ABS:"optimal experimental design" OR TITLE_ABS:"Bayesian calibration" OR TITLE_ABS:"active learning"))',
    "cipa_dynamic_herg_primary": 'DOI:10.1161/CIRCEP.116.004628',
}
URLS = {
    name: "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core", "pageSize": 15})
    for name, query in QUERIES.items()
}
URLS["passini2017_fulltext"] = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5601077/fullTextXML"


def fetch(item):
    name, url = item
    with urllib.request.urlopen(url, timeout=90) as response:
        body = response.read()
        receipt = {"url": url, "status": response.status, "final_url": response.url,
                   "content_type": response.headers.get("Content-Type"), "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest()}
    with (OUT / (name + ".body")).open("xb") as handle:
        handle.write(body)
    with (OUT / (name + ".receipt.json")).open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    print(name, receipt["status"], len(body))


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, URLS.items()))
