"""Retrieve bounded official metadata; never downloads biological outcome matrices."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "jump_readme": "https://raw.githubusercontent.com/jump-cellpainting/datasets/main/README.md",
    "jump_metadata_tree": "https://api.github.com/repos/jump-cellpainting/datasets/contents/metadata",
    "jump_metadata_readme": "https://raw.githubusercontent.com/jump-cellpainting/datasets/main/metadata/README.md",
    "jump_plate_metadata": "https://raw.githubusercontent.com/jump-cellpainting/datasets/main/metadata/plate.csv.gz",
    "cellpainting_gallery": "https://registry.opendata.aws/cellpainting-gallery/",
    "bbbc021": "https://bbbc.broadinstitute.org/BBBC021",
    "bbbc021_compound": "https://data.broadinstitute.org/bbbc/BBBC021/BBBC021_v1_compound.csv",
    "bbbc021_moa": "https://data.broadinstitute.org/bbbc/BBBC021/BBBC021_v1_moa.csv",
    "prism_official": "https://depmap.org/repurposing/",
    "gdsc_download": "https://www.cancerrxgene.org/downloads/bulk_download",
    "lincs_geo": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742&targ=self&form=text&view=full",
    "tahoe_metadata": "https://huggingface.co/api/datasets/tahoebio/Tahoe-100M",
    "tahoe_readme": "https://huggingface.co/datasets/tahoebio/Tahoe-100M/raw/main/README.md",
    "mapkg_metadata": "https://huggingface.co/api/datasets/RainGate/MAP-KG",
    "map_paper_crossref": "https://api.crossref.org/works/10.1038/s42256-026-01286-w",
    "batchie_metadata": "https://zenodo.org/api/records/13871987",
    "batchie_readme": "https://raw.githubusercontent.com/tansey-lab/batchie/main/README.md",
    "rxrx3": "https://www.rxrx.ai/rxrx3",
}
MAX_BYTES = 2_000_000


def fetch(item):
    key, url = item
    row = {"id": key, "requested_url": url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}
    request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research-source-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read(MAX_BYTES + 1)
            row.update(status=response.status, resolved_url=response.url,
                       content_type=response.headers.get("Content-Type"),
                       etag=response.headers.get("ETag"))
        if len(body) > MAX_BYTES:
            row["error"] = "Response exceeded metadata-only size ceiling; not saved."
        else:
            target = ROOT / "sources" / f"{key}.body"
            target.write_bytes(body)
            row.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), path=target.relative_to(ROOT).as_posix())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        row["error"] = str(exc)
    return row


def main():
    (ROOT / "sources").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch, SOURCES.items()))
    (ROOT / "retrieval_log.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in records:
        print(row["id"], row.get("status", "FAILED"), row.get("bytes", ""), row.get("error", ""))


if __name__ == "__main__":
    main()
