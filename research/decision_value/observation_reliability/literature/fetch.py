"""Download explicitly named primary sources and preserve byte receipts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
SOURCES = {
    "rmfbo": "https://proceedings.mlr.press/v206/mikkola23a.html",
    "rmfbo_pdf": "https://proceedings.mlr.press/v206/mikkola23a/mikkola23a.pdf",
    "input_dependent_mfbo": "https://proceedings.mlr.press/v244/fan24a.html",
    "input_dependent_mfbo_pdf": "https://raw.githubusercontent.com/mlresearch/v244/main/assets/fan24a/fan24a.pdf",
    "muscat": "https://www.nature.com/articles/s41467-020-19894-4",
    "systema": "https://www.nature.com/articles/s41587-025-02777-8",
    "biopert_metadata": "https://api.crossref.org/works/10.64898/2026.09.28.755146",
    "biopert": "https://www.biorxiv.org/content/10.64898/2026.09.28.755146v1.full",
    "state_hvg_issue_279": "https://api.github.com/repos/ArcInstitute/state/issues/279",
}


def fetch(item):
    name, url = item
    receipt = {"name": name, "requested_url": url,
               "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    suffix = ".pdf" if name.endswith("_pdf") else ".parquet" if name.endswith("_parquet") else ".json" if "api." in url else ".html"
    path = ROOT / "sources" / (name + suffix)
    try:
        request = Request(url, headers={"User-Agent": "MAESTRO-literature-audit/1.0"})
        with urlopen(request, timeout=45) as response:
            body = response.read()
            receipt.update(http_status=response.status, final_url=response.url,
                           content_type=response.headers.get("Content-Type"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        receipt.update(status="RECEIVED", path=path.relative_to(ROOT).as_posix(),
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        receipt.update(status="FETCH_FAILED", error=f"{type(exc).__name__}: {exc}")
    return receipt


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, SOURCES.items()))
    output = {"schema": "primary_source_receipts_v1", "sources": receipts,
              "boundary": "Literature bytes only; no treated RNA or MAESTRO outcome acquisition."}
    (ROOT / "FETCH_RECEIPTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    for receipt in receipts:
        print(receipt["name"], receipt["status"], receipt.get("bytes", receipt.get("error")))
