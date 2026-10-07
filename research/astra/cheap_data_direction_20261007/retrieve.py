"""Bounded primary literature and public asset metadata retrieval, no outcomes."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import hashlib
import json

HERE = Path(__file__).resolve().parent
QUERIES = {
    "state_paper": '(TITLE:"STATE" OR TITLE:"State") AND (AUTH_FIRST:"Adduri" OR ABSTRACT:"cellular perturbation" OR ABSTRACT:"cell state") AND FIRST_PDATE:[2025-01-01 TO 2026-10-07]',
    "batchie": 'TITLE:BATCHIE OR ABSTRACT:BATCHIE',
    "benchmark": 'DOI:10.1038/s41592-025-02772-6',
    "recover": 'DOI:10.1016/j.crmeth.2023.100599',
    "active_perturbation": '(TITLE:"active learning" AND (ABSTRACT:perturbation OR ABSTRACT:transcriptomic)) AND FIRST_PDATE:[2020-01-01 TO 2026-10-07]',
}
SOURCES = {
    "state_repo": "https://api.github.com/repos/ArcInstitute/state",
    "state_repo_tree": "https://api.github.com/repos/ArcInstitute/state/git/trees/main?recursive=1",
    "state_weights": "https://huggingface.co/api/models/arcinstitute/state",
    "state_weights_search": "https://huggingface.co/api/models?author=arcinstitute&search=state&limit=30",
    "tahoe": "https://huggingface.co/api/datasets/arcinstitute/State-Tahoe-Filtered?blobs=true",
    "state_datasets": "https://huggingface.co/api/datasets?author=arcinstitute&search=State&limit=30",
}
for name, query in QUERIES.items():
    SOURCES["search_" + name] = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({"query": query, "format": "json", "resultType": "core", "pageSize": 15})


def fetch(pair):
    name, url = pair
    started = datetime.now(timezone.utc).isoformat()
    receipt = {"name": name, "url": url, "started_utc": started}
    try:
        with urlopen(Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=30) as response:
            payload = response.read(8 * 1024 * 1024)
            receipt.update(status=response.status, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), final_url=response.geturl())
        with (HERE / "sources" / f"{name}.json").open("xb") as handle:
            handle.write(payload)
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__, error=str(error))
    return receipt


def main():
    (HERE / "sources").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, SOURCES.items()))
    with (HERE / "RETRIEVAL_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(receipts, handle, indent=2); handle.write("\n")
    for receipt in receipts:
        print(receipt["name"], receipt["status"], receipt.get("bytes", 0))


if __name__ == "__main__":
    main()
