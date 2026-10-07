"""Recover primary evidence through alternate public endpoints; no outcome data."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json

HERE = Path(__file__).resolve().parent
SOURCES = {
    "state_model_license": "https://raw.githubusercontent.com/ArcInstitute/state/9bbfe78a434a55205e4de834e1ea99f85f7a3add/MODEL_LICENSE.md",
    "state_model_usage": "https://raw.githubusercontent.com/ArcInstitute/state/9bbfe78a434a55205e4de834e1ea99f85f7a3add/MODEL_ACCEPTABLE_USE_POLICY.md",
    "state_colab": "https://drive.google.com/uc?export=download&id=1bq5v7hixnM-tZHwNdgPiuuDo6kuiwLKJ",
    "hallmark_primary_bioc": "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC4707969/unicode",
    "hallmark_license_plain": "https://www.gsea-msigdb.org/gsea/msigdb/license.jsp?login=false",
    "hallmark_license_static": "https://www.gsea-msigdb.org/gsea/msigdb/collections.jsp",
    "parse_readme": "https://huggingface.co/datasets/arcinstitute/State-Parse-Filtered/raw/7e6acd905c412094330710a721a46280b7ef53de/README.md",
    "parse_license": "https://huggingface.co/datasets/arcinstitute/State-Parse-Filtered/resolve/7e6acd905c412094330710a721a46280b7ef53de/CC-NC-4.0-License.txt",
    "replogle_split": "https://huggingface.co/datasets/arcinstitute/State-Replogle-Filtered/raw/d790193bb2c93726541a75ca3fa873a92ed44da5/hepg2.toml",
    "state_targeted_search": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({"query": 'DOI:10.1016/j.cell.2026.07.052 OR DOI:10.1101/2025.06.26.661135 OR DOI:10.1016/j.cels.2015.12.004', "format": "json", "resultType": "core", "pageSize": 10}),
}


def fetch(pair):
    name, url = pair
    receipt = dict(name=name, url=url, retrieved_utc=datetime.now(timezone.utc).isoformat())
    try:
        with urlopen(Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=30) as response:
            content = response.read(12 * 1024 * 1024)
            receipt.update(status=response.status, bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), final_url=response.geturl())
        with (HERE / "sources" / f"{name}.txt").open("xb") as handle:
            handle.write(content)
    except Exception as error:
        receipt.update(status="failed", error=str(error), error_type=type(error).__name__)
    return receipt


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, SOURCES.items()))
    with (HERE / "FOLLOWUP_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(receipts, handle, indent=2); handle.write("\n")
    for receipt in receipts:
        print(receipt["name"], receipt["status"], receipt.get("bytes", 0))


if __name__ == "__main__":
    main()
