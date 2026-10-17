"""Bounded public literature retrieval, with byte, failure and waiting records."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
OUT = HERE / "source_review"
LIMIT = 6_000_000
DOIS = {
    "functional_panels": "10.1038/s41698-025-00937-2",
    "active_screening": "10.3390/cancers16030530",
    "metric_calibration": "10.1038/s41587-026-03307-w",
    "prism_methods": "10.1038/s43018-019-0018-6",
}


def fetch(name, url):
    started = time.perf_counter()
    result = {"url": url, "limit_bytes": LIMIT}
    data = None
    try:
        with urllib.request.urlopen(url, timeout=35) as response:
            data = response.read(LIMIT + 1)
            result.update(status=response.status, bytes=len(data))
        if len(data) > LIMIT:
            raise ValueError("bounded_response_limit_exceeded")
        (OUT / name).write_bytes(data)
        result["sha256"] = hashlib.sha256(data).hexdigest()
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        data = None
    result["wall_seconds"] = time.perf_counter() - started
    return name, result, data


def main():
    OUT.mkdir(exist_ok=True)
    urls = {
        "functional_panels.html": "https://www.nature.com/articles/s41698-025-00937-2",
        "descriptors.html": "https://arxiv.org/html/2510.19874",
        "descriptors_abstract.html": "https://arxiv.org/abs/2510.19874",
        "mda_v5.html": "https://arxiv.org/html/2608.09696v5",
    }
    for name, doi in DOIS.items():
        urls[name + "_epmc.json"] = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=core&query=" + urllib.parse.quote("DOI:" + doi)
    records = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, result, data in pool.map(lambda item: fetch(*item), urls.items()):
            records[name] = result
    for name in DOIS:
        path = OUT / (name + "_epmc.json")
        if not path.exists():
            continue
        articles = json.loads(path.read_text())["resultList"]["result"]
        for article in articles[:1]:
            pmcid = article.get("pmcid")
            if pmcid:
                name2, result, _ = fetch(name + ".xml", "https://www.ebi.ac.uk/europepmc/webservices/rest/" + pmcid + "/fullTextXML")
                records[name2] = result
            else:
                # Crossref supplies authoritative abstract metadata when available.
                name2, result, _ = fetch(name + "_crossref.json", "https://api.crossref.org/works/" + DOIS[name])
                records[name2] = result
    (OUT / "RETRIEVAL.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {a: v[a] for a in ("status", "bytes", "error") if a in v} for k, v in records.items()}, indent=2))


if __name__ == "__main__":
    main()
