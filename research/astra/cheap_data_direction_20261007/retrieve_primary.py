"""Primary sources, official STATE metadata and a public Hallmark mirror."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import hashlib
import json

HERE = Path(__file__).resolve().parent
SOURCES = {
    "state_readme": "https://raw.githubusercontent.com/ArcInstitute/state/9bbfe78a434a55205e4de834e1ea99f85f7a3add/README.md",
    "state_license": "https://raw.githubusercontent.com/ArcInstitute/state/9bbfe78a434a55205e4de834e1ea99f85f7a3add/LICENSE",
    "hallmark_gmt": "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=MSigDB_Hallmark_2020",
    "hallmark_paper": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4707969/fullTextXML",
    "batchie_fulltext": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11696745/fullTextXML",
    "benchmark_fulltext": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12328236/fullTextXML",
    "parse_metadata": "https://huggingface.co/api/datasets/arcinstitute/State-Parse-Filtered?blobs=true",
    "replogle_metadata": "https://huggingface.co/api/datasets/arcinstitute/State-Replogle-Filtered?blobs=true",
    "state_model_search": "https://huggingface.co/api/models?search=state_generalization&limit=30",
    "msigdb_license": "https://www.gsea-msigdb.org/gsea/msigdb/license.jsp",
}


def fetch(pair):
    name, url = pair
    receipt = {"name": name, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=30) as response:
            content = response.read(12 * 1024 * 1024)
            receipt.update(status=response.status, final_url=response.geturl(), bytes=len(content),
                           sha256=hashlib.sha256(content).hexdigest())
        with (HERE / "sources" / f"{name}.txt").open("xb") as handle:
            handle.write(content)
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__, error=str(error))
    return receipt


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, SOURCES.items()))
    with (HERE / "PRIMARY_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(receipts, handle, indent=2); handle.write("\n")
    for row in receipts:
        print(row["name"], row["status"], row.get("bytes", 0))


if __name__ == "__main__":
    main()
