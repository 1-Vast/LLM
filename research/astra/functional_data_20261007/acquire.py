"""Retrieve source identity and focused literature; preserve every response."""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "data/external/jaaks2022_provenance/Original_screen_All_tissues_raw_data.csv.zip"
EXPECTED = "51550262aed5440d3c5f54997cc940f429ff5dcb55e6970179d3500ba7c5f61e"
QUERIES = {
    "sparse_drug_response": '(TITLE_ABS:"drug response" AND TITLE_ABS:"single dose") AND OPEN_ACCESS:Y',
    "perturbation_transfer": '(TITLE_ABS:"perturbation" AND TITLE_ABS:"linear models") AND FIRST_PDATE:[2024-01-01 TO 2026-10-07]',
    "compositional": '(TITLE_ABS:"compositional perturbation" OR TITLE_ABS:"chemCPA") AND OPEN_ACCESS:Y',
    "independent_action": 'TITLE:"Drug Independence and the Curability of Cancer by Combination Chemotherapy" OR (AUTH_LAST:Palmer AND AUTH_LAST:Sorger AND FIRST_PDATE:2017)',
    "drugcomb": 'TITLE:"DrugComb" AND OPEN_ACCESS:Y',
    "batchie": 'DOI:10.1038/s41467-024-55287-7',
    "recover": 'DOI:10.1016/j.crmeth.2023.100599',
}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MAESTRO research source qualification"}), timeout=45) as response:
        return response.read()


def main():
    out = HERE / "acquisition"
    out.mkdir(exist_ok=False)
    receipts = []
    urls = {"figshare_raw": "https://api.figshare.com/v2/articles/19141916",
            "figshare_fitted": "https://api.figshare.com/v2/articles/16843597"}
    urls.update({name: "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" +
                 urllib.parse.urlencode({"query": q, "format": "json", "resultType": "core", "pageSize": 12})
                 for name, q in QUERIES.items()})
    def fetch(item):
        name, url = item
        receipt = {"name": name, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
        try:
            data = get(url)
            (out / (name + ".json")).write_bytes(data)
            receipt.update(status="OK", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        except Exception as exc:
            receipt.update(status="FAILED", reason=f"{type(exc).__name__}: {exc}")
        return receipt
    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts.extend(pool.map(fetch, urls.items()))
    meta_path = out / "figshare_raw.json"
    if not meta_path.exists():
        raise RuntimeError("Remote raw-source identity not retrieved; retained failed receipts require retry")
    meta = json.loads(meta_path.read_text())
    info = next(z for z in meta["files"] if z["name"] == RAW.name)
    local = RAW
    if not local.exists() or hashlib.sha256(local.read_bytes()).hexdigest() != EXPECTED:
        local = out / RAW.name
        # New destination, stream the public source; never replace a legacy asset.
        with urllib.request.urlopen(info["download_url"], timeout=60) as source, local.open("xb") as dest:
            while block := source.read(1024 * 1024):
                dest.write(block)
    actual = hashlib.sha256(local.read_bytes()).hexdigest()
    md5 = hashlib.md5(local.read_bytes()).hexdigest()
    assert actual == EXPECTED and local.stat().st_size == info["size"] and md5 == info["computed_md5"]
    receipts.append({"name": "qualified_raw_source", "path": str(local.relative_to(ROOT)), "sha256": actual,
                     "figshare_md5": md5, "bytes": local.stat().st_size,
                     "status": "EXISTING_LOCAL_SOURCE_REVALIDATED" if local == RAW else "DOWNLOADED_NEW_SOURCE",
                     "download_url": info["download_url"], "metadata_license": meta["license"],
                     "description_usage_notice": meta.get("description", "")})
    (out / "receipts.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    papers = {}
    for name in QUERIES:
        path = out / (name + ".json")
        if not path.exists():
            continue
        for record in json.loads(path.read_text()).get("resultList", {}).get("result", []):
            key = record.get("doi") or record.get("id")
            if key not in papers:
                papers[key] = {"queries": [], "title": record.get("title"), "doi": record.get("doi"),
                               "year": record.get("pubYear"), "pmcid": record.get("pmcid"),
                               "abstract": record.get("abstractText", ""), "authors": record.get("authorString", "")}
            papers[key]["queries"].append(name)
    (out / "paper_candidates.json").write_text(json.dumps(list(papers.values()), indent=2) + "\n")
    print(json.dumps({"source": receipts[-1], "search_requests": len(urls), "papers_found": len(papers)}, indent=2))


if __name__ == "__main__":
    main()
