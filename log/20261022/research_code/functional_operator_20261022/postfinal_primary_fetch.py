"""Three preselected nearest-primary families; exact DOI access, no new searches."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

OUT = Path("log/20261022/operator_renewal/functional/POSTFINAL_sources")
SOURCES = [
    ("chronos", "10.1186/s13059-021-02540-7", "https://genomebiology.biomedcentral.com/articles/10.1186/s13059-021-02540-7"),
    ("quantitative_microbiome", "10.1038/nature24460", "https://www.nature.com/articles/nature24460"),
    ("frailty_vaupel", "10.2307/2061224", "https://doi.org/10.2307/2061224"),
]


def fetch(url, destination):
    receipt = {"url": url, "utc": datetime.now(timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MAESTRO research audit"})
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read()
            receipt.update(status=response.status, final_url=response.url,
                           bytes=len(body), content_type=response.headers.get("Content-Type"),
                           sha256=hashlib.sha256(body).hexdigest())
        destination.write_bytes(body)
    except Exception as exc:
        receipt["error"] = repr(exc)
    return receipt


if __name__ == "__main__":
    receipts = []
    for name, doi, url in SOURCES:
        entry = {"name": name, "doi": doi}
        entry["exact_doi_metadata"] = fetch("https://api.crossref.org/works/"+doi, OUT/(name+"_metadata.json"))
        entry["primary_text_route"] = fetch(url, OUT/(name+".html"))
        receipts.append(entry)
    (OUT/"primary_receipts.json").write_text(json.dumps(receipts, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipts, indent=2))
