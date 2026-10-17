"""Bounded public-source audit; never runs upstream download or training scripts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
OUT = HERE / "source_review"
REV = "2c7b231c60cf110c4aab0acf8ecd2c2b3268fffb"
BASE = f"https://raw.githubusercontent.com/Genentech/PRESAGE/{REV}/"
SOURCES = {"presage_" + p.replace("/", "_"): BASE + p for p in (
    "README.md", "LICENSE.txt", "src/presage.py", "src/presage_datamodule.py",
    "src/datamodule.py", "src/evaluator.py", "src/train_presage.py",
    "src/model_harness.py", "src/prep_dataset_utils/download_datasets.sh",
    "src/prep_dataset_utils/TransformscPerturbdatasets.py",
    "shell_scripts/run_presage.sh", "notebooks/PRESAGE_example.ipynb")}
SOURCES.update({
    "zenodo.json": "https://zenodo.org/api/records/15587986",
    "zenodo_README.md": "https://zenodo.org/api/records/15587986/files/README.md/content",
    "presage_full.html": "https://www.biorxiv.org/content/10.1101/2025.06.03.657653v1.full",
    "europepmc.json": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1101/2025.06.03.657653&format=json",
    "mda.html": "https://arxiv.org/html/2608.09696v1",
    "hybrid.html": "https://arxiv.org/html/2603.24647v1",
    "txpert.html": "https://arxiv.org/abs/2505.14919",
    "ReactomePathways.gmt.zip": "https://reactome.org/download/current/ReactomePathways.gmt.zip",
    "reactome_license.html": "https://reactome.org/license",
})


def fetch(item):
    name, url = item
    record = {"url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url, timeout=35) as response:
            data = response.read(8_000_001)
            if len(data) > 8_000_000:
                raise ValueError("source_exceeds_8MB_limit")
            record.update(status=response.status, bytes=len(data),
                          last_modified=response.headers.get("Last-Modified"),
                          sha256=hashlib.sha256(data).hexdigest())
        (OUT / name).write_bytes(data)
    except Exception as exc:
        record.update(error=f"{type(exc).__name__}: {exc}")
    return name, record


def main():
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        records = dict(pool.map(fetch, SOURCES.items()))
    # gzip archives cannot be arbitrarily indexed. Inspect a bounded prefix only.
    url = "https://zenodo.org/api/records/15587986/files/cache.tar.gz/content"
    record = {"url": url, "complete_inventory": False, "limit_bytes": 2_000_000}
    try:
        request = urllib.request.Request(url, headers={"Range": "bytes=0-1999999"})
        with urllib.request.urlopen(request, timeout=35) as response:
            data = response.read(2_000_000)
            record.update(status=response.status, bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest())
        members = []
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r|gz") as archive:
                for member in archive:
                    members.append({"name": member.name, "size": member.size})
                    if len(members) >= 80:
                        break
        except (EOFError, tarfile.TarError, OSError) as exc:
            record["prefix_end"] = type(exc).__name__
        record["members"] = members
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    records["zenodo_cache_prefix"] = record
    (OUT / "RETRIEVAL.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {a: v[a] for a in ("status", "bytes", "error", "members") if a in v}
                      for k, v in records.items()}, indent=2))


if __name__ == "__main__":
    main()
