"""Acquire only bounded public biochemical files; never print their contents."""
import hashlib
import json
from pathlib import Path

import source_list as source

source.LIMIT = 9_900_000


def main():
    listing = json.loads((source.LOG / "SOURCE_LISTING.json").read_text())
    files = [x for x in listing["metadata"]["objects"]
             if x["Key"].endswith("/biochem.parquet") and
             x["Key"].split("/")[-3] in {"prod_25", "prod_26", "prod_27", "prod_30"}]
    network = json.loads((source.LOG / "NETWORK.json").read_text())
    if sum(int(x["Size"]) for x in files) + network["body_bytes"] > source.LIMIT:
        raise RuntimeError("Complete biochemical source would exceed budget; no partial selection made")
    frozen = {}
    for path in [source.LOG / "PROTOCOL.md", source.LOG / "LICENCE_RECORD.md",
                 Path(__file__), Path(__file__).with_name("source_list.py"),
                 Path(__file__).with_name("blind_audit.py")]:
        frozen[str(path.relative_to(source.ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (source.LOG / "PRE_DOWNLOAD_FREEZE.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    manifest = []
    for i, item in enumerate(files, 1):
        batch, plate = item["Key"].split("/")[-3:-1]
        path = source.LOG / "sealed_source" / batch / plate / "biochem.parquet"
        if path.exists():
            raise RuntimeError("Existing sealed source requires an explicit audited resume, not overwrite")
        body = source.get("https://cellpainting-gallery.s3.amazonaws.com/" + item["Key"])
        if len(body) != int(item["Size"]):
            raise RuntimeError("Source size changed since listing")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        manifest.append({**item, "local_path": str(path.relative_to(source.ROOT)),
                         "sha256": hashlib.sha256(body).hexdigest()})
        (source.LOG / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if i % 8 == 0 or i == len(files):
            print(json.dumps({"downloaded_files": i, "total_files": len(files),
                              "body_bytes": json.loads((source.LOG / "NETWORK.json").read_text())["body_bytes"]}), flush=True)


if __name__ == "__main__":
    main()
