"""Reproduce bounded OASIS metadata receipts without downloading outcome files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / "log/20261021/rsi_next_qualification/agents/liver_metadata_receipt.json"
BUCKET = "https://cellpainting-gallery.s3.amazonaws.com/"
PREFIX = "cpg0037-oasis/axiom/workspace/metadata/prod_25/"
COMMIT = "ca4872de0f1f0a4f203bee41271a6512b314a076"


def main():
    listing = requests.get(BUCKET, params={"list-type": "2", "prefix": PREFIX,
                                          "max-keys": 12}, timeout=25)
    listing.raise_for_status()
    root = ET.fromstring(listing.text)
    ns = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
    entries = [{k: item.findtext("s:" + k, namespaces=ns)
                for k in ("Key", "Size", "LastModified", "ETag")}
               for item in root.findall("s:Contents", ns)]
    response = requests.get("https://zenodo.org/api/records/17067683", timeout=25)
    response.raise_for_status()
    record = response.json()
    receipt = {
        "s3_listing_url": listing.url, "s3_status": listing.status_code,
        "objects": entries,
        "zenodo": {
            "id": record.get("id"), "created": record.get("created"),
            "metadata": {k: record.get("metadata", {}).get(k)
                         for k in ("publication_date", "version", "license")},
            "files": [{k: f.get(k) for k in ("key", "size", "checksum")}
                      for f in record.get("files", [])],
        },
        "upstream_commit": COMMIT, "numeric_payload_downloaded": False,
    }
    biochem = next(item for item in entries if item["Key"].endswith("/biochem.parquet"))
    url = BUCKET + biochem["Key"]
    header = requests.head(url, timeout=20)
    receipt["example_biochem_head"] = {
        "url": url, "status": header.status_code,
        "headers": {k: v for k, v in header.headers.items()
                    if k.lower() in ("content-length", "last-modified", "etag", "content-type")},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Saved metadata only: {OUT}")


if __name__ == "__main__":
    main()
