"""Small primary-method metadata/OA retrieval; never requests biological outcomes."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources"


def retrieve(name, url):
    record = {"name": name, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-primary-method-review/1"})
        with urllib.request.urlopen(request, timeout=40) as response:
            payload = response.read()
            record.update(status=response.status, final_url=response.url, bytes=len(payload),
                          sha256=hashlib.sha256(payload).hexdigest(), content_type=response.headers.get("Content-Type"))
        destination = SOURCES / name
        with destination.open("xb") as handle:
            handle.write(payload)
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc).split("?")[0][:200])
    return record


def main():
    SOURCES.mkdir(parents=True, exist_ok=True)
    urls = {
        "kg_correlated_crossref.json": "https://api.crossref.org/works/10.1287/ijoc.1080.0314",
        "kg_correlated_author.html": "https://people.orie.cornell.edu/pfrazier/pub.html",
        "topm_pmlr.html": "https://proceedings.mlr.press/v28/bubeck13.html",
        "topm_pmlr.pdf": "https://proceedings.mlr.press/v28/bubeck13.pdf",
        "neurips2014_index.html": "https://proceedings.neurips.cc/paper_files/paper/2014",
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda pair: retrieve(*pair), urls.items()))
    with (HERE / "METHOD_RETRIEVAL_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2); handle.write("\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
