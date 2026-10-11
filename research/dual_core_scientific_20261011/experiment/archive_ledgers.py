"""Losslessly archive completed ledgers, or restore exact bytes for verification."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    records = []
    for prefix in ("TEST", "SUPPLEMENT"):
        receipt = json.loads((HERE / f"{prefix}_RECEIPT.json").read_text(encoding="utf-8"))
        expanded = HERE / f"{prefix}_LEDGER.jsonl"
        archive = HERE / f"{prefix}_LEDGER.jsonl.gz"
        if args.restore:
            if not expanded.exists():
                with gzip.open(archive, "rb") as source, expanded.open("wb") as target:
                    shutil.copyfileobj(source, target)
        else:
            assert digest(expanded) == receipt["ledger_sha256"]
            with expanded.open("rb") as source, archive.open("wb") as raw:
                with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as target:
                    shutil.copyfileobj(source, target)
        assert digest(expanded) == receipt["ledger_sha256"]
        records.append({"expanded": expanded.name, "archive": archive.name,
                        "expanded_sha256": digest(expanded), "archive_sha256": digest(archive),
                        "expanded_bytes": expanded.stat().st_size, "archive_bytes": archive.stat().st_size})
    (HERE / "ARCHIVE_RECEIPT.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
